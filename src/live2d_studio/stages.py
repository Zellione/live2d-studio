"""Content-verified, resumable local stages. Failed attempts are never overwritten."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import time
import uuid

from .manifest import digest, local_file, write_json


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def inventory(root):
    root = Path(root)
    result = {}
    for file in sorted(root.rglob('*')):
        if file.is_symlink():
            raise ValueError('Stage artifacts must not contain symbolic links')
        if file.is_file():
            result[file.relative_to(root).as_posix()] = digest(file)
    return result


def verify(root, files):
    for name, expected in files.items():
        if digest(local_file(Path(root), name)) != expected:
            raise ValueError('Stage artifact changed: ' + name)


def atomic_json(file, value):
    temporary = file.with_name(file.name + '.tmp')
    write_json(temporary, value)
    temporary.replace(file)


class Stages:
    def __init__(self, output, identity):
        self.root = Path(output).resolve()
        self.identity = identity
        self.file = self.root / 'creation.json'

    @contextmanager
    def locked(self):
        if self.root.exists() and not self.file.exists():
            raise ValueError('Existing output is not a creation run; choose a new directory')
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / '.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('Another creation process owns this run') from None
            if self.file.exists():
                self.data = json.loads(self.file.read_text())
                if self.data['identity'] != self.identity:
                    raise ValueError('Input/configuration changed; use a new output directory')
            else:
                self.data = dict(schema_version=1, identity=self.identity, stages={}, history=[], status='running')
                self.save()
            yield self

    def save(self):
        atomic_json(self.file, self.data)

    def run(self, name, inputs, action):
        key = fingerprint(inputs)
        previous = self.data['stages'].get(name)
        if previous and previous['status'] == 'complete' and previous['key'] == key:
            root = self.root / previous['directory']
            if not root.resolve().is_relative_to(self.root):
                raise ValueError('Stage directory escapes run')
            verify(root, previous['files'])
            return root
        directory = 'stages/' + name + '-' + uuid.uuid4().hex[:12]
        root = self.root / directory
        root.mkdir(parents=True)
        record = dict(key=key, directory=directory, status='running', inputs=inputs, started=time.time())
        if previous:
            self.data['history'].append(dict(stage=name, **previous))
        self.data['stages'][name] = record
        self.save()
        try:
            action(root)
            record.update(status='complete', files=inventory(root), finished=time.time())
        except BaseException as error:
            # No arbitrary exception content: subprocess errors may contain credentials.
            record.update(status='failed', error_type=type(error).__name__, finished=time.time())
            self.data['status'] = 'failed-' + name
            self.save()
            raise
        self.save()
        return root
