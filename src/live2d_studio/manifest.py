"""Portable v1/v2 layer contracts and strict file/pixel integrity validation."""
import hashlib
import json
from pathlib import Path, PurePosixPath

import numpy as np
from PIL import Image

ROLES = set('back_hair front_hair headwear face face_detail irides eyebrow eyewhite eyelash eye_close eyewear ears earwear nose mouth mouth_open mouth_close tooth_t tooth_b tongue neck neckwear topwear handwear bottomwear legwear footwear tail wings objects unknown'.split())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')


def local_file(root, name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('Expected portable relative file reference')
    rel = PurePosixPath(name)
    target = (root / name).resolve()
    if rel.is_absolute() or '..' in rel.parts or not target.is_relative_to(root.resolve()):
        raise ValueError('File reference escapes project')
    if not target.is_file():
        raise ValueError(f'Missing project file: {name}')
    return target


def load_validate(root):
    root = Path(root)
    data = json.loads((root/'layer_manifest.json').read_text())
    version = data['schema_version']
    if version not in (1, 2):
        raise ValueError('Unsupported manifest version')
    w, h = data['canvas']['width'], data['canvas']['height']
    if not all(type(v) is int and 0 < v <= 8192 for v in (w,h)):
        raise ValueError('Invalid canvas')
    if len(data['sources']) != 1:
        raise ValueError('v1 accepts exactly one reference; multi-reference fusion is not implemented')
    source = data['sources'][0]
    if digest(local_file(root, source['path'])) != source['sha256']:
        raise ValueError('Original source hash changed')
    original = np.array(Image.open(local_file(root, source['normalized_path'])).convert('RGBA'))
    if digest(local_file(root, source['normalized_path'])) != source['normalized_sha256']:
        raise ValueError('Normalized source changed')
    if original.shape != (h,w,4):
        raise ValueError('Source dimensions differ')
    ids, orders = set(), []
    if not 1 <= len(data['layers']) <= 32:
        raise ValueError('PSD2Live requires 1..32 layers')
    for layer in data['layers']:
        if layer['id'] in ids or layer['role'] not in ROLES or layer['side'] not in {'left','right','none'}:
            raise ValueError('Duplicate ID or invalid semantics')
        ids.add(layer['id'])
        if layer['source_id'] != source['id'] or not layer['provenance']:
            raise ValueError('Missing source/provenance')
        if not 0 <= layer['confidence'] <= 1 or layer['quality_status'] not in {'candidate','unresolved','generated-review'}:
            raise ValueError('Invalid quality annotation')
        x,y,lw,lh = (layer[k] for k in ('x','y','width','height'))
        if not all(type(v) is int for v in (x,y,lw,lh)) or min(x,y)<0 or min(lw,lh)<1 or x+lw>w or y+lh>h:
            raise ValueError('Layer outside canvas')
        arrays = {}
        keys = ['rgba_path','mask_path','reconstructed_mask_path']
        if version == 2:
            keys += ['generated_mask_path', 'semantic_mask_path', 'uncertain_mask_path']
        for key in keys:
            path = local_file(root, layer[key])
            if digest(path) != layer['sha256'][key]:
                raise ValueError(f'Layer checksum changed: {layer["id"]}')
            with Image.open(path) as im:
                if im.size != (lw,lh) or im.mode != ('RGBA' if key=='rgba_path' else 'L'):
                    raise ValueError('Wrong layer mode/dimensions')
                arrays[key] = np.array(im)
        pixels, mask, rebuilt = (arrays[k] for k in ('rgba_path','mask_path','reconstructed_mask_path'))
        visible = mask>0
        if np.any(visible & (rebuilt>0)) or not set(np.unique(rebuilt)) <= {0,255}:
            raise ValueError('Overlapping or nonbinary reconstruction mask')
        generated = arrays['generated_mask_path'] if version == 2 else rebuilt
        if version == 2:
            uncertain = arrays['uncertain_mask_path']
            if np.any(visible & (generated>0)) or np.any((rebuilt>0) & (generated==0)):
                raise ValueError('Invalid generated/observed/hidden mask relationship')
            if not set(np.unique(uncertain)) <= {0,255} or np.any((uncertain>0) & (pixels[...,3]==0)):
                raise ValueError('Invalid uncertainty mask')
            if not np.array_equal(arrays['semantic_mask_path'], pixels[...,3]):
                raise ValueError('Semantic mask differs from layer alpha')
            if layer['hidden_reconstruction_status'] not in {'unlocalized', 'validated'}:
                raise ValueError('Missing hidden reconstruction status')
        if not np.array_equal(pixels[...,3], np.maximum(mask,generated)):
            raise ValueError('Alpha differs from mask union')
        if np.any(pixels[pixels[...,3]==0] != 0):
            raise ValueError('Nonzero transparent RGB')
        if not np.array_equal(pixels[visible], original[y:y+lh,x:x+lw][visible]):
            raise ValueError('Visible original pixels changed')
        orders.append(layer['z_order'])
    if orders != sorted(set(orders)):
        raise ValueError('Z order must be strictly increasing')
    return data


def artwork_request(root):
    data = load_validate(root)
    return dict(width=data['canvas']['width'], height=data['canvas']['height'], layers=[
        dict(path=str(local_file(Path(root), l['rgba_path'])), name=l['id'],
             role=l['role'], side=l['side'], x=l['x'], y=l['y']) for l in data['layers']])
