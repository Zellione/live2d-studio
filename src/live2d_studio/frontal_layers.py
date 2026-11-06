"""Native frontal matte and bilateral sleeve partitions, with explicit uncertainty."""
from copy import deepcopy
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image

from .frontal_master import load
from .manifest import digest, load_validate, write_json
from .pose_review import REPO
from .preview import preview
from .refinement import fidelity

KEYS = ('rgba_path', 'mask_path', 'generated_mask_path', 'semantic_mask_path',
        'uncertain_mask_path', 'reconstructed_mask_path')
FOLDERS = ('layers', 'masks', 'generated', 'semantic', 'uncertain', 'reconstructed')


def prepare(master, project, matte, geometry, output):
    master, project, matte, geometry, output = map(Path, (master, project, matte, geometry, output))
    authority = load(master); data = deepcopy(load_validate(project))
    m = json.loads((matte / 'matte.json').read_text())
    if m['primary_sha256'] != authority['primary']['sha256'] or digest(matte / 'artwork.png') != m['artwork_sha256']:
        raise ValueError('Matte does not match primary artwork')
    if data['sources'][0]['sha256'] != authority['primary']['sha256']:
        raise ValueError('Decomposition is not the frontal primary')
    evidence = json.loads((geometry / 'assessment.json').read_text())
    joints = evidence['images']['canonical']
    if joints['image_sha256'] != authority['primary']['sha256']:
        raise ValueError('Joint hypotheses use another source')
    output = output.resolve()
    if not output.is_relative_to(REPO / 'runs') or output.exists():
        raise ValueError('Fresh ignored output required')
    shutil.copytree(project, output)
    original = np.array(Image.open(matte / 'artwork.png').convert('RGBA'))
    height, width = original.shape[:2]
    if data['canvas'] != dict(width=width, height=height):
        raise ValueError('Native source grid required')
    foreground = original[..., 3] > 0
    Image.fromarray(original).save(output / 'source/normalized.png')
    data['sources'][0]['normalized_sha256'] = digest(output / 'source/normalized.png')
    data['sources'][0]['normalization_transform'] = {'kind': 'native-source-grid',
        'matte_sha256': digest(matte / 'matte.json'), 'source_kind': 'approved-synthetic-master'}
    layers = []; arm_rows = {}
    for layer in data['layers']:
        arrays = {}
        x, y, w, h = (layer[k] for k in ('x', 'y', 'width', 'height'))
        for key in KEYS:
            arr = np.array(Image.open(project / layer[key])); arr[~foreground[y:y+h, x:x+w]] = 0
            arrays[key] = arr
        variants = [('whole', np.ones((h, w), bool))]
        if layer['role'] == 'handwear':
            yy, xx = np.where(arrays['mask_path'] > 0)
            if not len(xx):
                raise ValueError('Empty visible arm')
            side = 'right' if np.mean(xx + x) < width / 2 else 'left'
            if side in arm_rows:
                raise ValueError('Multiple arm layers on same side')
            joint = joints['arms'][side]
            elbow_y = joint['elbow']['point'][1]; wrist_y = joint['wrist'][1]
            rows = np.indices((h, w))[0] + y
            variants = [('upper', rows < elbow_y), ('forearm', (rows >= elbow_y) & (rows < wrist_y)), ('hand', rows >= wrist_y)]
            arm_rows[side] = {'shoulder_surface': joint['shoulder_surface'], 'elbow_hypothesis': joint['elbow'],
                             'wrist_hypothesis': joint['wrist'], 'layers': [],
                             'scope': 'Editable sleeve/cuff partitions; no validated skeletal pivot or finger rig'}
        for part, support in variants:
            item = deepcopy(layer)
            if part != 'whole':
                item['id'] = 'arm-' + side + '-' + part
                item['name'] = item['id']; item['anatomical_side'] = side; item['arm_part'] = part
                arm_rows[side]['layers'].append(item['id'])
            item['z_order'] = len(layers)
            for key, folder in zip(KEYS, FOLDERS):
                arr = arrays[key].copy(); arr[~support] = 0
                name = folder + '/' + item['id'] + '.png'
                Image.fromarray(arr).save(output / name); item[key] = name
            item['sha256'] = {key: digest(output / item[key]) for key in KEYS}
            item['observed_pixels'] = int(((arrays['mask_path'] > 0) & support).sum())
            item['generated_pixels'] = int(((arrays['generated_mask_path'] > 0) & support).sum())
            item['provenance'].append('frontal-master-matte-and-partitions-v1')
            layers.append(item)
    if set(arm_rows) != {'left', 'right'}:
        raise ValueError('Bilateral source arms required')
    data['layers'] = layers
    data['provenance']['primary_master_sha256'] = digest(master / 'master.json')
    data['provenance']['synthetic_master'] = True
    data['provenance']['matte_sha256'] = digest(matte / 'matte.json')
    data['warnings'].append('Observed means copied from the approved synthetic master, not verified original anatomy. Elbow cuts remain hypotheses.')
    write_json(output / 'layer_manifest.json', data)
    composite = preview(output, data, Image.fromarray(original))
    quality = json.loads((project / 'quality.json').read_text())
    quality['fidelity'] = fidelity(original, composite)
    quality['source_samples_copied'] = sum(l['observed_pixels'] for l in layers)
    quality['source_scope'] = 'Canonical foreground with explicit border-connected background matte'
    write_json(output / 'quality.json', quality)
    write_json(output / 'frontal-parts.json', {'master_sha256': digest(master / 'master.json'),
        'parent_manifest_sha256': digest(project / 'layer_manifest.json'),
        'geometry_sha256': digest(geometry / 'assessment.json'), 'arms': arm_rows,
        'hidden_review': 'pending; inherited See-through backing is unverified',
        'rig_ready': False})
    load_validate(output)
    return quality
