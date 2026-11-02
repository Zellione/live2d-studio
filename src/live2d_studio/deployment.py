"""Fail-closed isolated deployment with durable write-ahead recovery records.

Only copies created under this checkout's .cache/phase4a-* are writable targets.
No production switch exists. Run with the disposable server stopped.
"""
from contextlib import contextmanager
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import uuid

from .packaging import REPO, EXT, CORE, digest, files, policy, safe_tree, verify, core_probe

MARKER = '.phase4a-isolated.json'
ACTIVE = '.phase4a-active.json'


def ancestors(path):
    for p in (Path(path).absolute(), *Path(path).absolute().parents):
        if p.is_symlink():
            raise ValueError('Symlink path forbidden: ' + str(p))


def writable(path):
    if not os.access(path, os.W_OK) or not Path(path).stat().st_mode & 0o222:
        raise PermissionError('Not writable: ' + str(path))


def atomic_json(path, value):
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temp.open('x') as out:
        json.dump(value, out, indent=2, sort_keys=True)
        out.write('\n'); out.flush(); os.fsync(out.fileno())
    os.replace(temp, path)
    sync_dir(path.parent)


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def isolated(root):
    root = Path(root).absolute()
    ancestors(root)
    if root.parent != REPO / '.cache' or not root.name.startswith('phase4a-'):
        raise ValueError('Production writes disabled: target must be a fresh .cache/phase4a-* copy')
    ancestors(root / MARKER)
    marker = json.loads((root / MARKER).read_text())
    if marker.get('root') != str(root) or marker.get('purpose') != 'phase4a-disposable':
        raise ValueError('Invalid isolated-instance marker')
    if marker.get('snapshot_sha256') and digest(root / 'snapshot-hashes.json') != marker['snapshot_sha256']:
        raise ValueError('Isolated snapshot marker mismatch')
    source = Path(marker['source']).resolve()
    if root.is_relative_to(source) or source.is_relative_to(root):
        raise ValueError('Target overlaps production source')
    # Scan deployment-relevant trees, not node_modules symlinks. Hardlinks forbidden.
    for p in (root / EXT, root / 'data/default-user/assets/live2d'):
        safe_tree(p)
        writable(p)
    if (root / ACTIVE).is_symlink():
        raise ValueError('Invalid transaction pointer')
    return root


@contextmanager
def locked(root):
    with (root / MARKER).open('rb') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def snapshot(path):
    if not path.exists():
        return None
    if path.is_file():
        if path.is_symlink() or path.stat().st_nlink != 1:
            raise ValueError('Unsafe file')
        return {'type': 'file', 'sha256': digest(path), 'mode': stat.S_IMODE(path.stat().st_mode), 'mtime_ns': path.stat().st_mtime_ns}
    safe_tree(path)
    return {'type': 'directory', 'entries': {
        str(p.relative_to(path)): {'type': 'directory' if p.is_dir() else 'file',
                                  'sha256': None if p.is_dir() else digest(p),
                                  'mode': stat.S_IMODE(p.stat().st_mode),
                                  'mtime_ns': p.stat().st_mtime_ns}
        for p in [path, *sorted(path.rglob('*'))]}}


def copy(source, dest):
    if source.is_dir():
        shutil.copytree(source, dest, copy_function=shutil.copy2)
    else:
        shutil.copy2(source, dest)
    for p in ([dest] if dest.is_file() else [p for p in dest.rglob('*') if p.is_file()]):
        with p.open('rb') as f:
            os.fsync(f.fileno())
    sync_dir(dest.parent)


def remove(path):
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def adapter_bytes(root):
    spec = importlib.util.spec_from_file_location('phase3_patch', REPO / 'scripts/patch_st_phase3.py')
    patch = importlib.util.module_from_spec(spec); spec.loader.exec_module(patch)
    return patch.patched((root / EXT / 'live2d.js').read_text()).encode()


def versions(root, compatibility):
    for name, sha in compatibility['target_sha256'].items():
        if digest(root / name) != sha:
            raise ValueError('Incompatible target version/hash: ' + name)


def record_path(path):
    path = Path(path).absolute()
    ancestors(path)
    if '..' in path.parts or not path.is_relative_to(REPO / 'runs') or path == REPO / 'runs':
        raise ValueError('Transaction records/backups must be under runs/')
    return path


def deploy(package, target, record, name='girl2', adapter=False, replace=False, execute=False, _checkpoint=None):
    package, record = Path(package).absolute(), record_path(record)
    root = isolated(target)
    with locked(root):
        if (root / ACTIVE).exists():
            raise ValueError('Active deployment exists; rollback its record first')
        if record.exists():
            raise FileExistsError('Transaction record already exists')
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', name):
            raise ValueError('Invalid model directory name')
        manifest = verify(package)
        versions(root, manifest['compatibility'])
        core_probe(package, root / CORE, policy())
        dest = root / 'data/default-user/assets/live2d' / name
        if any(p.name.casefold() == name.casefold() and p.name != name for p in dest.parent.iterdir()):
            raise ValueError('Case-conflicting model destination')
        if dest.exists() and not replace:
            raise FileExistsError('Model exists; explicit --replace required for verified backup and replacement')
        if dest.exists() and not dest.is_dir():
            raise ValueError('Model destination is not a directory')
        changes = [(dest, package)]
        patch_bytes = None
        if adapter:
            patch_bytes = adapter_bytes(root)
            companion = root / EXT / 'rp-talk.mjs'
            if companion.exists():
                raise FileExistsError('Adapter companion conflict')
            changes.extend([(root / EXT / 'live2d.js', None), (companion, REPO / 'integrations/sillytavern/rp-talk.mjs')])
        for path, _ in changes:
            ancestors(path)
            writable(path.parent)
            if path.exists():
                writable(path)
        plan = dict(schema_version=1, target=str(root), destination=str(dest), package=str(package),
                    package_manifest_sha256=digest(package / 'package-manifest.json'), adapter=adapter,
                    settings_policy='Never write settings; browser-created chat/settings changes are not deployment-owned',
                    status='planned', operations=[dict(path=str(p.relative_to(root)), before=snapshot(p)) for p, _ in changes])
        if not execute:
            return plan
        record.mkdir(parents=True)
        if record.stat().st_dev != dest.parent.stat().st_dev:
            raise ValueError('Backups and target must share a filesystem for atomic rename')
        for i, ((path, source), op) in enumerate(zip(changes, plan['operations'])):
            if op['before'] is not None:
                copy(path, record / f'backup-{i}')
                if snapshot(record / f'backup-{i}') != op['before']:
                    raise ValueError('Backup verification failed')
            stage = record / f'new-{i}'
            if source is None:
                stage.write_bytes(patch_bytes)
                shutil.copystat(path, stage)
                with stage.open('rb') as handle: os.fsync(handle.fileno())
            else:
                copy(source, stage)
            op.update(after=snapshot(stage), state='prepared', backup=f'backup-{i}' if op['before'] else None)
        plan['status'] = 'prepared'
        atomic_json(record / 'deployment.json', plan)
        atomic_json(root / ACTIVE, {'record': str(record)})
        # Journal survives exceptions/SIGKILL; rollback accepts the before/after/rename-gap states.
        for i, op in enumerate(plan['operations']):
            path = root / op['path']
            if snapshot(path) != op['before']:
                raise ValueError('Target changed since preflight')
            op['state'] = 'installing'
            atomic_json(record / 'deployment.json', plan)
            if path.exists():
                os.rename(path, record / f'displaced-{i}')
                sync_dir(path.parent)
                sync_dir(record)
            if _checkpoint: _checkpoint('removed', i)
            os.rename(record / f'new-{i}', path)
            sync_dir(path.parent)
            if _checkpoint: _checkpoint('installed', i)
            op['state'] = 'installed'
            atomic_json(record / 'deployment.json', plan)
        plan['status'] = 'installed'
        atomic_json(record / 'deployment.json', plan)
        return plan


def rollback(record, execute=False, _checkpoint=None):
    record = record_path(record)
    safe_tree(record)
    plan = json.loads((record / 'deployment.json').read_text())
    if plan.get('schema_version') != 1:
        raise ValueError('Unsupported deployment journal schema')
    root = isolated(plan['target'])
    with locked(root):
        if plan['status'] == 'rolled-back':
            if (root / ACTIVE).exists() and json.loads((root / ACTIVE).read_text()) == {'record': str(record)}:
                if execute:
                    (root / ACTIVE).unlink()
                    sync_dir(root)
            return plan
        active = json.loads((root / ACTIVE).read_text())
        if active != {'record': str(record)}:
            raise ValueError('Transaction pointer mismatch')
        destination = Path(plan['destination'])
        if destination.parent != root / 'data/default-user/assets/live2d':
            raise ValueError('Invalid recorded destination')
        allowed = [str(destination.relative_to(root))]
        if plan['adapter']:
            allowed += [EXT + '/live2d.js', EXT + '/rp-talk.mjs']
        if [op['path'] for op in plan['operations']] != allowed:
            raise ValueError('Invalid recorded operation paths')
        for i, op in enumerate(plan['operations']):
            path = root / op['path']; ancestors(path); writable(path.parent)
            if op['before'] is not None and snapshot(record / f'backup-{i}') != op['before']:
                raise ValueError('Backup damaged; refusing rollback')
            current = snapshot(path)
            allowed_states = [op['before'], op['after']]
            if op['state'] in {'installing', 'restoring'}:
                allowed_states.append(None)
            if current not in allowed_states:
                raise ValueError('User modifications conflict with rollback: ' + op['path'])
        if not execute:
            return dict(plan, rollback_preflight='pass')
        for i in reversed(range(len(plan['operations']))):
            op = plan['operations'][i]; path = root / op['path']
            op['state'] = 'restoring'
            atomic_json(record / 'deployment.json', plan)
            if snapshot(path) != op['before']:
                restore = record / f'restore-{i}'
                # Incomplete recovery staging is owned by this journal, never user assets.
                if restore.exists(): remove(restore)
                if op['before'] is not None: copy(record / f'backup-{i}', restore)
                if path.exists():
                    # Atomic quarantine: a permission/error/crash can never leave a
                    # partly deleted model that a subsequent recovery cannot identify.
                    os.rename(path, record / f'removed-{i}-{uuid.uuid4().hex}')
                    sync_dir(path.parent)
                    sync_dir(record)
                if _checkpoint: _checkpoint('removed', i)
                if restore.exists(): os.rename(restore, path)
                sync_dir(path.parent)
                if _checkpoint: _checkpoint('restored', i)
            if snapshot(path) != op['before']:
                raise ValueError('Restoration verification failed')
            op['state'] = 'restored'
            atomic_json(record / 'deployment.json', plan)
        plan['status'] = 'rolled-back'
        atomic_json(record / 'deployment.json', plan)
        (root / ACTIVE).unlink()
        sync_dir(root)
        return plan
