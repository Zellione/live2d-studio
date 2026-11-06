"""Explicit primary-source promotion; synthetic provenance and rig review stay separate."""
import json
from pathlib import Path
import shutil

from .canonical_reference import load_frozen
from .manifest import digest, local_file, write_json
from .pose_family import load as load_family
from .pose_review import REPO


def promote(canonical_run, family, output):
    output = Path(output).resolve()
    if not output.is_relative_to(REPO / 'runs') or output.exists():
        raise ValueError('Use a fresh ignored master directory')
    store, state, canonical = load_frozen(Path(canonical_run))
    selected = load_family(Path(family))
    if canonical['approval'].get('reviewer_kind') != 'human':
        raise ValueError('Human canonical approval required')
    if selected['images']['canonical']['sha256'] != canonical['canonical']['sha256']:
        raise ValueError('Helper family uses another canonical')
    if selected['original']['sha256'] != canonical['original']['sha256']:
        raise ValueError('Helper identity ancestry mismatch')
    root = store.safe(state['canonical_reference']['manifest']).parent
    output.mkdir(parents=True)
    records = {}
    for key, filename in [('canonical', 'primary.png'), ('original', 'identity.png')]:
        shutil.copyfile(root / canonical[key]['path'], output / filename)
        records[key] = {'path': filename, 'sha256': digest(output / filename)}
    shutil.copyfile(root / 'manifest.json', output / 'canonical-provenance.json')
    data = {'schema_version': 1, 'kind': 'primary-frontal-synthetic-artwork',
            'primary': records['canonical'], 'identity_style_only': records['original'],
            'canonical_provenance': {'path': 'canonical-provenance.json',
                                     'sha256': digest(output / 'canonical-provenance.json')},
            'canonical_run': str(Path(canonical_run).resolve().relative_to(REPO)),
            'family': {'path': str(Path(family).resolve().relative_to(REPO)),
                       'sha256': digest(Path(family) / 'family.json')},
            'approval': canonical['approval'], 'rights': canonical['original']['rights'],
            'promotion_authority': 'Explicit user Phase 4B.10 instruction: frontal canonical is the new primary production artwork',
            'pixel_authority': 'Exact synthetic master pixels; not independently verified anatomy',
            'rig_approved': False, 'deployment_authorized': False}
    write_json(output / 'master.json', data)
    for file in output.iterdir():
        file.chmod(0o444)
    return data


def load(master):
    master = Path(master).resolve()
    data = json.loads((master / 'master.json').read_text())
    for key in ('primary', 'identity_style_only', 'canonical_provenance'):
        row = data[key]
        if digest(local_file(master, row['path'])) != row['sha256']:
            raise ValueError('Frontal master payload changed')
    provenance = json.loads(local_file(master, data['canonical_provenance']['path']).read_text())
    if (data['primary']['sha256'] != provenance['canonical']['sha256'] or
            data['identity_style_only']['sha256'] != provenance['original']['sha256'] or
            data['approval'] != provenance['approval'] or
            data['approval'].get('reviewer_kind') != 'human'):
        raise ValueError('Master source roles or approval changed')
    family = REPO / data['family']['path']
    if not family.resolve().is_relative_to(REPO / 'runs'):
        raise ValueError('Family outside ignored runs')
    if digest(family / 'family.json') != data['family']['sha256']:
        raise ValueError('Selected family changed')
    load_family(family)
    return data


def create(master, output, **options):
    """The primary canonical, never the identity reference, enters creation."""
    from .creation import create as create_character
    master = Path(master).resolve()
    data = load(master)
    options.setdefault('facial_motion', 'aligned')
    options.setdefault('mouths', 'coordinated')
    options.setdefault('body_motion', 'calm')
    return create_character(master / data['primary']['path'], output,
                            rights=data['rights'] + '; approved synthetic frontal master', **options)


def matte(master, output):
    """Remove only border-connected near-white backdrop; preserve retained RGB exactly."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    master = Path(master).resolve(); data = load(master)
    output = Path(output).resolve()
    if not output.is_relative_to(REPO / 'runs') or output.exists():
        raise ValueError('Use a fresh ignored matte directory')
    rgba = np.array(Image.open(master / data['primary']['path']).convert('RGBA'))
    rgb = rgba[..., :3].astype(float)
    eligible = (rgb.min(axis=2) >= 225) & (np.ptp(rgb, axis=2) <= 25)
    border = np.zeros(eligible.shape, bool)
    border[0] = eligible[0]; border[-1] = eligible[-1]
    border[:, 0] = eligible[:, 0]; border[:, -1] = eligible[:, -1]
    background = ndimage.binary_propagation(border, mask=eligible)
    result = rgba.copy(); result[background] = 0
    output.mkdir(parents=True)
    Image.fromarray(result).save(output / 'artwork.png')
    Image.fromarray(background.astype('uint8') * 255).save(output / 'removed-background.png')
    report = {'master_sha256': digest(master / 'master.json'), 'primary_sha256': data['primary']['sha256'],
              'artwork_sha256': digest(output / 'artwork.png'),
              'method': 'Border-connected RGB minimum >=225 and channel range <=25; no foreground RGB repaint',
              'removed_pixels': int(background.sum()), 'retained_pixels': int((~background).sum()),
              'retained_rgba_exact': bool(np.array_equal(result[~background], rgba[~background])),
              'human_matte_review': 'pending', 'synthetic_master': True}
    write_json(output / 'matte.json', report)
    return report


def prepare(master, inference_run, geometry, output, repair_brows=False):
    """Convert a verified canonical inference run into matte, parts and facial review assets."""
    from .stages import verify
    from .frontal_layers import prepare as prepare_layers
    from .generic_rig import facial_plan
    from .creation_quality import analyze
    master, inference_run, geometry, output = map(lambda p: Path(p).resolve(), (master,inference_run,geometry,output))
    data = load(master)
    state = json.loads((inference_run/'creation.json').read_text())
    if state['identity']['input_sha256'] != data['primary']['sha256']:
        raise ValueError('Inference did not use primary frontal source')
    for stage in state['stages'].values():
        if stage['status'] == 'complete': verify(inference_run/stage['directory'],stage['files'])
    if not output.is_relative_to(REPO/'runs') or output.exists():
        raise ValueError('Fresh ignored preparation directory required')
    output.mkdir(parents=True)
    matte(master,output/'matte')
    restored=inference_run/state['stages']['restore']['directory']/'layers'
    prepare_layers(master,restored,output/'matte',geometry,output/'layers')
    (output/'readiness').mkdir();quality=analyze(output/'layers',output/'readiness')
    if quality['decision']=='blocked':
        raise ValueError('Frontal semantic gate blocked; inspect readiness/quality.json')
    facial_root=output/('facial-before-brows' if repair_brows else 'facial')
    facial_root.mkdir();facial_plan(output/'layers',facial_root)
    if repair_brows:
        from .frontal_face import repair
        (output/'facial').mkdir();repair(facial_root/'layers',output/'facial/layers')
    evidence={str(p.relative_to(REPO)):digest(p) for p in
              (master/'master.json',output/'matte/matte.json',output/'layers/layer_manifest.json',
               output/'facial/layers/layer_manifest.json',output/'readiness/quality.json')}
    (output/'review').mkdir();write_json(output/'review/evidence.json',evidence)
    write_json(output/'prepared.json',{'primary_sha256':data['primary']['sha256'],
        'master_sha256':digest(master/'master.json'),'review':'review/evidence.json',
        'status':'needs-human-decomposition-and-hidden-backing-review','rig_ready':False})
    return {'status':'needs-human-review','layers':str(output/'facial/layers/preview/index.html'),
            'evidence':str(output/'review/evidence.json')}


def review(folder, decision, reviewer, notes):
    """Explicit local review command, never called automatically by preparation."""
    folder=Path(folder).resolve()
    if decision not in ('accept','reject') or not reviewer.strip() or not notes.strip():
        raise ValueError('Explicit decision, reviewer and notes required')
    if not folder.is_relative_to(REPO/'runs') or (folder/'approval.json').exists():
        raise ValueError('Use an unreviewed ignored evidence directory')
    files=json.loads((folder/'evidence.json').read_text())
    for name,h in files.items():
        file=(REPO/name).resolve()
        if not file.is_relative_to(REPO/'runs') or digest(file)!=h:raise ValueError('Review evidence changed')
    record={'reviewer_kind':'human','reviewer':reviewer,'decision':decision,'notes':notes,
            'scope':'Frontal decomposition and uncertain backing for limited rig experiment; final animation separate',
            'evidence_sha256':digest(folder/'evidence.json'),'files':files,'animation_approved':False}
    write_json(folder/'approval.json',record)
    return record
