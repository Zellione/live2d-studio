"""Reproduce the read-only Girl2 limb audit from retained XCF and runtime evidence.

This is an evaluation script, not inference or an anatomical segmenter. XCF
ground truth supplies whole shirt/neck masks, not independent sleeve masks.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from live2d_studio.manifest import digest, load_validate, write_json
from live2d_studio.refinement import native_layers, visible_owners


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xcf-raw', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    gt = Path('runs/phase2-5-oga-ground-truth')
    neural = Path('runs/phase2-5-oga-layers')
    refined = Path('runs/phase2-6-oga-release')
    runtime = Path('runs/phase3-final/runtime')
    frame = Path('runs/phase3-final-expressions/neutral.png')
    source = Path('assets/references/oga-portraits/NewAnime.xcf')
    protected = [source, gt/'flat.png', frame, Path('runs/phase3-final/character.psd2live'),
                 Path('runs/phase3-final/character.psd'), Path('runs/phase2-6-oga-v2-build/character.psd2live')]
    protected += sorted(p for root in (runtime, refined, neural) for p in root.rglob('*') if p.is_file())
    hashes = {str(p): digest(p) for p in protected}
    inventory = json.loads((args.xcf_raw/'inventory.json').read_text())
    assert digest(source) == inventory['source_sha256']
    size = tuple(inventory['canvas'])
    original = Image.open(gt/'flat.png').convert('RGBA')
    src = np.array(original)

    def raw(item):
        return Image.frombytes('RGBA', (item['width'], item['height']), (args.xcf_raw/item['path']).read_bytes())

    def canvas(item):
        result = Image.new('RGBA', size)
        result.paste(raw(item), (item['x'], item['y']))
        return result

    leaves = [l for l in inventory['layers'] if not l['group']]
    for leaf in leaves:
        a = np.array(raw(leaf))[..., 3]
        yy, xx = np.indices(a.shape)
        outside = (xx+leaf['x'] < 0) | (xx+leaf['x'] >= size[0]) | (yy+leaf['y'] < 0) | (yy+leaf['y'] >= size[1])
        leaf['nontransparent_outside_canvas'] = int(((a > 0) & outside).sum())
    projection = canvas(inventory['projection'])
    projection.save(args.output/'xcf-projection.png')
    assert np.array_equal(np.array(projection), np.array(Image.open(gt/'gimp-projection.png')))
    ground = json.loads((gt/'benchmark.json').read_text())
    ground_arrays = [np.array(Image.open(gt/l['path']).convert('RGBA')) for l in ground['layers']]
    ground_owner = visible_owners(ground_arrays)
    data = load_validate(refined)
    arrays = native_layers(refined, data, size)
    assert all(l['sha256']['rgba_path'] == r['sha256']['rgba_path'] for l, r in zip(
        data['layers'], load_validate(Path('runs/phase2-6-oga-v2'))['layers']))
    composite = Image.new('RGBA', size)
    owners = np.full(src.shape[:2], -1)
    for i, (layer, array) in enumerate(zip(data['layers'], arrays)):
        composite.alpha_composite(Image.fromarray(array))
        mask = Image.new('L', size)
        mask.paste(Image.open(refined/layer['mask_path']), (layer['x'], layer['y']))
        owners[np.array(mask) > 0] = i
    result = np.array(composite)
    assert np.array_equal(result, np.array(Image.open(refined/'preview/composite.png')))
    regions = {}
    for name in ('G2 Shirt', 'G2 Neck'):
        index = next(i for i, l in enumerate(ground['layers']) if l['name'] == name)
        mask = (ground_owner == index) & (src[..., 3] > 127)
        regions[name] = dict(visible_pixels=int(mask.sum()),
            exactly_preserved_rgba=int((mask & np.all(result == src, axis=2)).sum()),
            missing_alpha_pixels=int((mask & (result[..., 3] <= 127)).sum()),
            observed_ownership={l['id']: int((mask & (owners == i)).sum()) for i, l in enumerate(data['layers']) if (mask & (owners == i)).any()},
            unowned_pixels=int((mask & (owners < 0)).sum()))
    info = json.loads((runtime/'Generated_artwork.psd2live.json').read_text())
    clothes = [l for l in info['layers'] if l['tag'] in ('handwear', 'topwear')]
    source_bounds = original.getchannel('A').getbbox()
    runtime_image = Image.open(frame).convert('RGBA')
    runtime_bounds = runtime_image.getchannel('A').getbbox()
    # Display-only isotropic alignment. Browser pixels are not source-grid metrics.
    fitted = Image.new('RGBA', size)
    crop = runtime_image.crop(runtime_bounds)
    scale = min((source_bounds[2]-source_bounds[0])/crop.width, (source_bounds[3]-source_bounds[1])/crop.height)
    crop = crop.resize((round(crop.width*scale), round(crop.height*scale)), Image.Resampling.LANCZOS)
    fitted.paste(crop, (source_bounds[0], source_bounds[1]))
    ndata = load_validate(neural)
    ncomp = Image.new('RGBA', size)
    for a in native_layers(neural, ndata, size):
        ncomp.alpha_composite(Image.fromarray(a))

    def sheet(tiles, path, columns=5):
        w, h = 320, 380
        result = Image.new('RGB', (w*columns, h*((len(tiles)+columns-1)//columns)), 'white')
        font = ImageFont.load_default(size=16)
        for i, (title, im) in enumerate(tiles):
            tile = Image.new('RGBA', (w, h), 'white')
            draw = ImageDraw.Draw(tile)
            for y in range(48, h, 16):
                for x in range(0, w, 16):
                    draw.rectangle((x, y, x+15, y+15), fill='#dddddd' if (x//16+y//16)%2 else '#f4f4f4')
            thumb = im.copy()
            thumb.thumbnail((w-12, h-56), Image.Resampling.LANCZOS)
            tile.alpha_composite(thumb, ((w-thumb.width)//2, 50))
            draw.multiline_text((6, 5), title, fill='black', font=font)
            result.paste(tile.convert('RGB'), ((i%columns)*w, (i//columns)*h))
        result.save(path)

    tiles = [('Original XCF projection\nFresh GIMP read, full canvas', projection),
             ('Flattened source\nOriginal inference input', original),
             ('See-through generated\nMapped back to source grid', ncomp),
             ('Refined manifest composite\nSource-restored layers', composite),
             ('Final Phase 3 Live2D\nSaved browser frame, fitted', fitted)]
    shirt = next(l for l in leaves if l['name'] == 'G2 Shirt')
    neck = next(l for l in leaves if l['name'] == 'G2 Neck')
    tiles.append(('XCF G2 Shirt\nIncludes BOTH sleeves', canvas(shirt)))
    for role, side in (('handwear', 'left'), ('handwear', 'right'), ('topwear', 'none')):
        i = next(i for i, l in enumerate(data['layers']) if (l['role'], l['side']) == (role, side))
        tiles.append((f'Refined {role} / {side}\nFull canvas; image-side labels', Image.fromarray(arrays[i])))
    tiles.append(('XCF G2 Neck\nExposed collarbone / upper chest', canvas(neck)))
    sheet(tiles, args.output/'comparison.png')
    sheet([(l['name']+'\n'+('visible' if l['effective_visible'] else 'HIDDEN variant'), canvas(l)) for l in leaves], args.output/'xcf-all-leaves.png')
    report = dict(xcf=inventory, source_bounds=list(source_bounds), runtime_bounds=list(runtime_bounds),
                  regions=regions, exported_clothing=clothes,
                  runtime_evidence='Existing Phase 3 actual Core/ST neutral frame; no new runtime session.',
                  runtime_display_transform='Alpha-bbox crop, isotropic resize into source foreground bounds; no RGB comparison across rendered scale.',
                  xcf_projection_matches_previous=True, immutable_sha256=hashes)
    assert all(digest(p) == value for p, value in hashes.items())
    write_json(args.output/'audit.json', report)
    (args.output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Girl2 limb audit</title>'
        '<h1>Girl2 limb audit</h1><p>stevenburrow / CC0. Audit only; no generated anatomy or model edits.</p>'
        '<p>Top: full XCF canvas through retained Phase 3 rendering. Runtime frame fitted for visual comparison only.</p>'
        '<img style="max-width:100%" src="comparison.png"><h2>All XCF leaves, including hidden variants</h2>'
        '<img style="max-width:100%" src="xcf-all-leaves.png"><p><a href="audit.json">Measurements and hashes</a></p>')
    print(json.dumps(dict(source_bounds=source_bounds, regions=regions, exported_clothing=clothes), indent=2))


if __name__ == '__main__':
    main()
