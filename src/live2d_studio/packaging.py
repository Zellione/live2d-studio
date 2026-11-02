"""Reproducible, pinned Girl2 runtime packaging. Core is probed, never bundled."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from .bundle import validate
from .completeness import analyze

REPO = Path(__file__).resolve().parents[2]
EXT = 'data/default-user/extensions/Extension-Live2d'
CORE = EXT + '/lib/live2dcubismcore.min.js'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def safe_tree(root):
    """Reject symlinks, hardlinks, special files and case-fold collisions."""
    root = Path(root).absolute()
    for p in (root, *root.parents):
        if p.is_symlink():
            raise ValueError(f'Symlink forbidden: {p}')
    names = set()
    for p in sorted(root.rglob('*')):
        if p.is_symlink() or not (p.is_dir() or p.is_file()):
            raise ValueError(f'Nonregular entry: {p}')
        if p.is_file() and p.stat().st_nlink != 1:
            raise ValueError(f'Hardlink forbidden: {p}')
        key = str(p.relative_to(root)).casefold()
        if key in names:
            raise ValueError('Case-conflicting files')
        names.add(key)


def files(root):
    safe_tree(root)
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(Path(root).rglob('*')) if p.is_file()}


def policy():
    return json.loads((REPO / 'recipes/girl2-package.json').read_text())


def check_runtime(root, spec):
    safe_tree(root)
    model = root / spec['model']
    report = validate(model)
    if report['status'] != 'pass':
        raise ValueError(str(report['errors']))
    expected = spec['runtime_sha256']
    for name, sha in expected.items():
        if digest(root / name) != sha:
            raise ValueError('Accepted runtime hash mismatch: ' + name)
    data = json.loads(model.read_text())['FileReferences']
    names = [e['Name'] for e in data['Expressions']]
    if sorted(names) != sorted(spec['expressions']) or set(data['Motions']) != {'Idle', 'Nod'}:
        raise ValueError('Incomplete/conflicting expressions or authored motions')
    preset = json.loads((root / 'sillytavern_settings.json').read_text())
    if sorted(preset['classify_mapping']) != spec['classifier_labels']:
        raise ValueError('Incomplete classifier mapping')
    motions = {'none'} | {f'{g}_id={i}' for g, items in data['Motions'].items() for i in range(len(items))}
    for item in [*preset['classify_mapping'].values(), preset['animation_default'], preset['animation_starter'], preset['animation_click']]:
        if item['expression'] not in names + ['none'] or item['motion'] not in motions:
            raise ValueError('Preset references missing expression/motion')
    return report


def core_probe(root, core, spec):
    if digest(core) != spec['compatibility']['core_sha256']:
        raise ValueError('Unsupported Cubism Core hash')
    model = json.loads((root / spec['model']).read_text())
    proc = subprocess.run(['node', str(REPO / 'scripts/probe_core.cjs'), str(core),
                           str(root / model['FileReferences']['Moc'])], capture_output=True, text=True, timeout=30)
    if proc.returncode:
        raise ValueError('Core rejected bundle: ' + proc.stdout + proc.stderr)
    report = json.loads(proc.stdout)
    if report['status'] != 'pass' or report['core_version'] != spec['compatibility']['core_version']:
        raise ValueError('Core compatibility failed')
    if not set(spec['required_drawables']).issubset(report['drawable_ids']):
        raise ValueError('Required reviewed sleeve/torso/neck meshes missing')
    return report


def package(source, output, core):
    source, output = Path(source).absolute(), Path(output).absolute()
    spec = policy()
    if '..' in output.parts or not output.is_relative_to(REPO / 'runs') or output == REPO / 'runs':
        raise ValueError('Generated packages must stay under this checkout runs/')
    if output.exists() or output.is_symlink():
        raise FileExistsError('Output already exists')
    for parent in (output.parent, *output.parents):
        if parent.is_symlink():
            raise ValueError('Symlink output parent')
    if files(source) != spec['accepted_source_sha256']:
        raise ValueError('Source differs from accepted Phase 3 runtime')
    check_runtime(source, spec)
    completeness = analyze(spec['completeness'])
    if completeness['portrait_completeness'] != 'pass':
        raise ValueError(str(completeness))
    probe = core_probe(source, core, spec)
    # Build beside the destination, publish only after validation. No existing output replaced.
    with tempfile.TemporaryDirectory(prefix='.package-', dir=output.parent) as tmp:
        stage = Path(tmp) / 'model'
        stage.mkdir()
        for name in spec['runtime_sha256']:
            dest = stage / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, dest)
        manifest = dict(schema_version=1, package_id=spec['package_id'], model=spec['model'],
                        files_sha256=files(stage), provenance=spec['provenance'], compatibility=spec['compatibility'],
                        core_probe=probe, limitations=spec['limitations'], completeness=spec['completeness'],
                        readiness=completeness, production_authorized=False)
        write_json(stage / 'package-manifest.json', manifest)
        verify(stage)
        # mkdir is exclusive; copy failures leave a visibly incomplete output, never a valid package.
        output.mkdir()
        shutil.copytree(stage, output, dirs_exist_ok=True)
    return manifest


def verify(root):
    root = Path(root)
    safe_tree(root)
    manifest = json.loads((root / 'package-manifest.json').read_text())
    spec = policy()
    actual = files(root)
    actual.pop('package-manifest.json')
    if actual != manifest['files_sha256'] or actual != spec['runtime_sha256']:
        raise ValueError('Package file set/hash mismatch')
    for key in ('package_id', 'model', 'compatibility', 'provenance', 'limitations', 'completeness'):
        if manifest[key] != spec[key]:
            raise ValueError('Package policy mismatch: ' + key)
    if manifest['readiness'] != analyze(spec['completeness']):
        raise ValueError('Readiness mismatch')
    check_runtime(root, spec)
    return manifest
