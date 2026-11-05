"""Narrow independent PSD checks, never imported by the creation pipeline."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from live2d_studio.manifest import digest, write_json
from live2d_studio.stages import verify


def pixels(file):
    return np.array(Image.open(file).convert('RGBA'))


def evaluate(run, references, definition):
    d = json.loads(definition.read_text())
    state = json.loads((run / 'creation.json').read_text())

    def stage(name):
        s = state['stages'][name]
        root = run / s['directory']
        verify(root, s['files'])
        return root

    restored = stage('restore') / 'layers'
    facial = stage('facial') / 'layers'
    m = json.loads((restored / 'layer_manifest.json').read_text())
    original = references / d['neutral_png']
    if digest(original) != state['identity']['input_sha256']:
        raise ValueError('Reference does not match run input')
    source = pixels(original)
    foreground = source[..., 3] > 127
    base = Image.open(references / d['base']).convert('RGBA')
    composed = Image.alpha_composite(base, Image.open(references / d['neutral_color']).convert('RGBA'))
    composed = Image.alpha_composite(composed, Image.open(references / d['neutral_ink']).convert('RGBA'))
    difference = np.abs(np.array(composed).astype(int) - source.astype(int))
    alignment = dict(transform='identity; original native canvas; no registration fit',
                     exact_foreground_fraction=float(np.all(difference == 0, axis=2)[foreground].mean()),
                     foreground_rgba_mae=float(difference[foreground].mean()),
                     max_foreground_channel_error=int(difference[foreground].max()))
    # Exporter/compositor rounding differs by one level. Refuse gross mismatch.
    if alignment['foreground_rgba_mae'] > 1:
        raise ValueError('PSD neutral state does not align with the selected PNG')
    ink = pixels(references / d['neutral_ink'])[..., 3] > d['mask_threshold']
    owner = np.full(foreground.shape, -1, np.int16)
    count = np.zeros(foreground.shape, np.uint16)
    copied_exact = True
    for i, layer in enumerate(m['layers']):
        mask = np.array(Image.open(restored / layer['mask_path'])) > 0
        x, y, w, h = (layer[k] for k in ('x', 'y', 'width', 'height'))
        view = owner[y:y+h, x:x+w]
        view[mask] = i
        count[y:y+h, x:x+w] += mask
        copied_exact &= np.array_equal(pixels(restored / layer['rgba_path'])[mask], source[y:y+h, x:x+w][mask])
    ink_results = {}
    for name, region in d['ink_regions'].items():
        x0, y0, x1, y1 = region['box']
        mask = np.zeros_like(ink)
        mask[y0:y1, x0:x1] = ink[y0:y1, x0:x1]
        ids = [i for i, l in enumerate(m['layers']) if l['role'] in region['roles']]
        owners = {l['id']: int((mask & (owner == i)).sum()) for i, l in enumerate(m['layers'])}
        ink_results[name] = dict(reference_ink_pixels=int(mask.sum()),
                                intended_role_recall=float(np.isin(owner[mask], ids).mean()),
                                owners={k: v for k, v in owners.items() if v},
                                caveat='Ink ownership recall only; no fine iris/lash mask IoU')
    composite = pixels(restored / 'preview/composite.png')
    exact = np.all(composite == source, axis=2)
    limb_results = {}
    for name, box in d['source_review_regions'].items():
        x0, y0, x1, y1 = box
        fg = foreground[y0:y1, x0:x1]
        limb_results[name] = dict(source_foreground_pixels=int(fg.sum()),
                                 exact_fraction=float(exact[y0:y1, x0:x1][fg].mean()),
                                 caveat='Source pixels in reviewed region; not an anatomical segmentation score')
    fm = json.loads((facial / 'layer_manifest.json').read_text())
    hidden = {}
    base_array = np.array(base)
    for layer in fm['layers']:
        if layer['role'] != 'face':
            continue
        x, y, w, h = (layer[k] for k in ('x', 'y', 'width', 'height'))
        generated = np.array(Image.open(facial / layer['generated_mask_path'])) > 127
        # Restrict to independently authored neutral facial marks; not the whole
        # inferred head or concealed ears/hair/neck.
        mask = generated & ink[y:y+h, x:x+w]
        arr = pixels(facial / layer['rgba_path'])
        error = np.abs(arr[..., :3].astype(int) - base_array[y:y+h, x:x+w, :3].astype(int))
        hidden[layer['id']] = dict(pixels=int(mask.sum()), rgb_mae=float(error[mask].mean()) if mask.any() else None,
                                  scope='Generated face beneath independently authored neutral ink; artist base, not anatomy')
    quality = json.loads((restored / 'quality.json').read_text())
    return dict(schema_version=1, run=str(run), definition_sha256=digest(definition),
                input_sha256=digest(original), psd_alignment=alignment,
                reference_ink_ownership=ink_results, source_regions=limb_results,
                original_pixel_audit=dict(all_observed_rgba_exact=bool(copied_exact),
                    duplicate_source_owners=int((count > 1).sum()),
                    foreground_with_owner_fraction=float((count[foreground] > 0).mean()),
                    uncertain_copied_samples=quality['uncertain_copied_samples'],
                    copied_samples=quality['source_samples_copied']),
                authored_hidden_face_comparison=hidden, whole_character_semantic_accuracy=None,
                limitations=d['limitations'], user_acceptance=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for key in ['run', 'references', 'definition', 'output']:
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError('Use a fresh report path')
    write_json(a.output, evaluate(a.run, a.references, a.definition))
