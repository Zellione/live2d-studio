"""Reproducible stages with immutable input copies and fresh output directories."""
import importlib.metadata
from pathlib import Path
import shutil
import time

import numpy as np
from PIL import Image, ImageOps

from .manifest import digest, write_json, load_validate
from .segmentation import segment, bounds
from .reconstruction import reconstruct
from .preview import preview

EXPECTED = [('face','none'), ('neck','none'), ('topwear','none'), ('nose','none'),
            ('mouth_open','none'), ('mouth_close','none')] + [
    (role, side) for role in ('eyewhite','irides','eyelash','eyebrow','eye_close')
    for side in ('left','right')]


def prepare(source, output, rights='unspecified-local-only'):
    started = time.perf_counter()
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError('Output already exists; choose a new directory')
    original_hash = digest(source)
    with Image.open(source) as im:
        if im.format not in {'PNG','WEBP','JPEG'}:
            raise ValueError('Use PNG, WebP or JPEG input')
        if im.width*im.height > 4_194_304:
            raise ValueError('CPU MVP limit: 4 megapixels; prepare a separate smaller input copy')
        image = ImageOps.exif_transpose(im).convert('RGBA')
    rgba = np.array(image)
    regions, alpha, background = segment(rgba)
    segmentation_seconds = time.perf_counter()-started
    output.mkdir(parents=True, exist_ok=False)
    for name in ('source','layers','masks','reconstructed','preview'):
        (output/name).mkdir()
    copied = output/'source'/('original'+source.suffix.lower())
    shutil.copyfile(source,copied)
    image.save(output/'source/normalized.png')
    # Background removal changes only the processing copy's alpha.
    processing = rgba.copy()
    processing[...,3] = alpha
    layers = []
    for i, region in enumerate(regions):
        pixels, rebuilt = reconstruct(processing, region.mask, region.role, region.generated,
                                      colour=region.colour)
        box = bounds(pixels[...,3]>0)
        x0,y0,x1,y1 = box
        crop = np.s_[y0:y1,x0:x1]
        ident = region.role + ('' if region.side=='none' else '_'+region.side)
        mask = np.zeros_like(alpha) if region.generated else np.where(region.mask, alpha, 0).astype(np.uint8)
        files = {'rgba_path':f'layers/{ident}.png', 'mask_path':f'masks/{ident}.png',
                 'reconstructed_mask_path':f'reconstructed/{ident}.png'}
        for key,array in zip(files,(pixels,mask,rebuilt.astype(np.uint8)*255)):
            Image.fromarray(array[crop]).save(output/files[key])
        layers.append(dict(id=ident,name=ident.replace('_',' '),role=region.role,side=region.side,
            z_order=i,x=x0,y=y0,width=x1-x0,height=y1-y0,**files,
            sha256={key:digest(output/value) for key,value in files.items()}, source_id='source-0',
            default_visible=region.default_visible, confidence=0.0 if region.generated or region.role=='unknown' else .5,
            quality_status='generated-review' if region.generated else ('unresolved' if region.role=='unknown' else 'candidate'),
            provenance=['flat-colour-components-v1','bounded-nearest-fill-v1'],
            reconstructed_pixels=int(rebuilt.sum())))
    found = {(l['role'],l['side']) for l in layers}
    missing = [role+':'+side for role,side in EXPECTED if (role,side) not in found]
    warnings = ['Heuristic candidates, not calibrated semantic probabilities; review before rigging.',
                'Hair front/back, head back, pupils, teeth and hidden anatomical contours are unsupported.',
                'Closed eyes and closed mouth, when present, are generated alternate shapes.',
                'Only enclosed small gaps and bounded eye-white row gaps are filled; no verified hidden anatomy.']
    if missing:
        warnings.append('Missing expected regions: '+', '.join(missing))
    if background == 'unresolved-background':
        warnings.append('Nonuniform opaque background unresolved; unknown pixels retained.')
    manifest = dict(schema_version=1, canvas=dict(width=image.width,height=image.height),
        side_convention='image-left/image-right (PSD2Live convention)',
        sources=[dict(id='source-0',path=copied.relative_to(output).as_posix(),sha256=original_hash,
                      normalized_path='source/normalized.png', normalized_sha256=digest(output/'source/normalized.png'),rights=rights)],
        provenance=dict(algorithm_version='0.2.0', models=[], packages={
            p:importlib.metadata.version(p) for p in ('Pillow','numpy','scipy')}),
        layers=layers,missing_regions=missing,warnings=warnings)
    write_json(output/'config.json',dict(schema_version=1,backend='flat-colour-v1',quantization=16,
        max_colours=48,max_components=96,fill_max_fraction=.25,background=background,rights=rights))
    write_json(output/'layer_manifest.json',manifest)
    composite = preview(output,manifest,image)
    target = processing.copy()
    target[target[...,3]==0]=0
    changed = int(np.any(composite != target,axis=2).sum())
    unknown = sum(int(r.mask.sum()) for r in regions if r.role=='unknown')
    metrics = dict(status='needs-review',device='cpu',gpu_inference=False,peak_vram_bytes=0,
        segmentation_seconds=segmentation_seconds,total_seconds=time.perf_counter()-started,
        composite_changed_pixels=changed,visible_original_pixels_changed=0,
        unknown_foreground_pixels=unknown,foreground_pixels=int((alpha>0).sum()),
        missing_regions=missing,reconstructed_pixels=sum(l['reconstructed_pixels'] for l in layers))
    load_validate(output)
    if digest(source) != original_hash or digest(copied) != original_hash:
        raise ValueError('Input changed during preparation')
    write_json(output/'metrics.json', metrics)
    return metrics


def reconstruct_project(project, output, max_fraction=.25):
    """Replay only reconstruction and preview from persisted visible masks."""
    if not 0 <= max_fraction <= 1:
        raise ValueError('Fill fraction must be between 0 and 1')
    project, output = Path(project),Path(output)
    data = load_validate(project)
    if output.exists():
        raise FileExistsError('Output already exists; choose a new directory')
    started = time.perf_counter()
    # Copy only prepared artifacts; never copy unrelated secrets or build outputs.
    output.mkdir(parents=True,exist_ok=False)
    for directory in ('source','layers','masks','reconstructed'):
        shutil.copytree(project/directory,output/directory)
    (output/'preview').mkdir()
    original = Image.open(output/data['sources'][0]['normalized_path']).convert('RGBA')
    rgba = np.array(original)
    for layer in data['layers']:
        if layer['quality_status']=='generated-review':
            continue
        x,y,w,h=(layer[k] for k in ('x','y','width','height'))
        mask = np.array(Image.open(output/layer['mask_path']))>0
        crop = rgba[y:y+h,x:x+w]
        pixels, rebuilt = reconstruct(crop,mask,layer['role'],max_fraction=max_fraction)
        Image.fromarray(pixels).save(output/layer['rgba_path'])
        Image.fromarray(rebuilt.astype(np.uint8)*255).save(output/layer['reconstructed_mask_path'])
        layer['reconstructed_pixels']=int(rebuilt.sum())
        layer['sha256']={key:digest(output/layer[key]) for key in layer['sha256']}
    import json
    config=json.loads((project/'config.json').read_text())
    config['fill_max_fraction']=max_fraction
    write_json(output/'config.json',config)
    write_json(output/'layer_manifest.json',data)
    composite=preview(output,data,original)
    load_validate(output)
    result=dict(stage='reconstruction-replay',device='cpu',peak_vram_bytes=0,
                elapsed_seconds=time.perf_counter()-started,
                reconstructed_pixels=sum(l['reconstructed_pixels'] for l in data['layers']))
    write_json(output/'metrics.json',result)
    return result
