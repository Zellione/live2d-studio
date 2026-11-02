"""See-through raster bridge. No neural dependencies, model downloads or GT reads."""
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image

from .manifest import digest, local_file, write_json, load_validate, ROLES
from .pipeline import EXPECTED
from .preview import preview

PINNED_SOURCE = 'df019de5129d6c4b406587a14c3501669441a783'
MODEL_REVISIONS = {'layerdiff':'4477e6ce529bc6a141732e1a55a4932176db3b89',
                   'depth':'4f4ffc46050b6feb764b628859968a26e76e6b6a'}


def semantics(name):
    side = 'none'
    # Upstream part_lr_split names image-left '-r' (character right).
    if name.endswith(('-l','-r')):
        side = 'right' if name.endswith('-l') else 'left'
        name = name[:-2]
    role = {'front hair':'front_hair','back hair':'back_hair','hairf':'front_hair',
            'hairb':'back_hair'}.get(name,name)
    return (role if role in ROLES else 'unknown'),side


def import_decomposition(source, output, rights, decomposition):
    source, output, root = Path(source),Path(output),Path(decomposition)
    if output.exists():
        raise FileExistsError('Output already exists; choose a new directory')
    data = json.loads((root/'decomposition.json').read_text())
    if data['format_version']!=1 or data['order']!='back-to-front':
        raise ValueError('Unsupported bridge format/order')
    if data['source_revision']!=PINNED_SOURCE or data['models']!=MODEL_REVISIONS:
        raise ValueError('Unaudited See-through source/model revision')
    source_hash = digest(source)
    if source_hash!=data['input_sha256']:
        raise ValueError('Decomposition belongs to a different input')
    normalized = Image.open(local_file(root,data['normalized_path'])).convert('RGBA')
    w,h = normalized.size
    if data['canvas']!={'width':w,'height':h} or not 0<w<=4096 or not 0<h<=4096:
        raise ValueError('Invalid decomposition canvas')
    if not 1<=len(data['layers'])<=32:
        raise ValueError('PSD2Live requires 1..32 layers; do not silently drop semantic parts')
    orders = [l['z_order'] for l in data['layers']]
    if orders!=sorted(set(orders)):
        raise ValueError('Invalid layer order')
    # Validate every path/dimension before creating output.
    inputs=[]
    for layer in data['layers']:
        if layer['opacity']!=255 or layer['blend_mode']!='BlendMode.NORMAL':
            raise ValueError('Only normal fully opaque PSD layer settings are supported')
        image=Image.open(local_file(root,layer['path'])).convert('RGBA')
        x,y=layer['x'],layer['y']
        if type(x)!=int or type(y)!=int or min(x,y)<0 or x+image.width>w or y+image.height>h:
            raise ValueError('Decomposition layer outside canvas')
        inputs.append(image)
    output.mkdir(parents=True,exist_ok=False)
    for folder in ('source','layers','masks','generated','reconstructed','uncertain','semantic','preview'):
        (output/folder).mkdir()
    original=output/'source'/('original'+source.suffix.lower())
    shutil.copyfile(source,original)
    normalized.save(output/'source/normalized.png')
    layers=[]
    coverage=np.zeros((h,w),bool)
    role_coverage=np.zeros((h,w),bool)
    for i,(item,image) in enumerate(zip(data['layers'],inputs)):
        pixels=np.array(image)
        pixels[pixels[...,3]==0]=0
        alpha=pixels[...,3]
        role,side=semantics(item['name'])
        ident=f'st-{i:02d}-{role}-{side}'
        files=dict(rgba_path=f'layers/{ident}.png',mask_path=f'masks/{ident}.png',
                   generated_mask_path=f'generated/{ident}.png',reconstructed_mask_path=f'reconstructed/{ident}.png',
                   semantic_mask_path=f'semantic/{ident}.png',uncertain_mask_path=f'uncertain/{ident}.png')
        zero=np.zeros_like(alpha)
        for key,array in zip(files,(pixels,zero,alpha,zero,alpha,(alpha>0).astype(np.uint8)*255)):
            Image.fromarray(array).save(output/files[key])
        x,y=item['x'],item['y']
        coverage[y:y+image.height,x:x+image.width] |= alpha>0
        if role!='unknown':
            role_coverage[y:y+image.height,x:x+image.width] |= alpha>0
        layers.append(dict(id=ident,name=item['name'],role=role,side=side,z_order=i,x=x,y=y,
            width=image.width,height=image.height,**files,
            sha256={k:digest(output/v) for k,v in files.items()},source_id='source-0',default_visible=True,
            confidence=0.0,quality_status='generated-review',provenance=['see-through-v3',PINNED_SOURCE],
            reconstructed_pixels=0,generated_pixels=int((alpha>0).sum()),hidden_reconstruction_status='unlocalized'))
    found={(l['role'],l['side']) for l in layers}
    missing=[role+':'+side for role,side in EXPECTED if (role,side) not in found]
    warnings=['Neural semantic candidates; zero confidence means uncalibrated, not confirmed absence.',
        'All output pixels marked generated; no trusted hidden-only reconstruction mask is available.',
        'Zero observed pixels: visible-original preservation is unverified, not a zero-change success.',
        'Depth order and component-based image sides require visual validation.',
        'Missing animation variants are not fabricated. Full semantic masks include occluded pixels.']
    manifest=dict(schema_version=2,canvas=data['canvas'],side_convention='image-left/image-right (PSD2Live convention)',
        sources=[dict(id='source-0',path=original.relative_to(output).as_posix(),sha256=source_hash,
            normalized_path='source/normalized.png',normalized_sha256=digest(output/'source/normalized.png'),
            rights=rights,normalization_transform=data['transform'])],
        provenance=dict(backend='see-through',source_revision=PINNED_SOURCE,models=MODEL_REVISIONS),
        layers=layers,missing_regions=missing,warnings=warnings,rig_ready=False)
    write_json(output/'layer_manifest.json',manifest)
    write_json(output/'config.json',dict(backend='see-through',bridge_sha256=digest(root/'decomposition.json'),rights=rights))
    composite=preview(output,manifest,normalized)
    rgba=np.array(normalized)
    foreground=rgba[...,3]>0
    changed=np.any(composite!=rgba,axis=2)
    uncovered=foreground & ~coverage
    Image.fromarray(uncovered.astype(np.uint8)*255).save(output/'preview/unassigned.png')
    metrics=dict(status='needs-semantic-and-animation-review',foreground_pixels=int(foreground.sum()),
        unassigned_foreground_pixels=int(uncovered.sum()),candidate_covered_foreground_pixels=int((foreground&role_coverage).sum()),
        candidate_coverage_fraction=float((foreground&role_coverage).sum()/max(1,foreground.sum())),
        correct_semantic_assignments=None,visible_original_pixels_changed=None,
        observed_pixels=0,generated_pixels=sum(l['generated_pixels'] for l in layers),
        composite_changed_foreground_pixels=int((changed&foreground).sum()),
        composite_foreground_rgb_mae=float(np.abs(composite[...,:3].astype(float)-rgba[...,:3])[foreground].mean()) if foreground.any() else None,
        hidden_reconstruction_quality='unvalidated',missing_regions=missing,
        recognized_part_candidates=[l['name'] for l in layers])
    write_json(output/'metrics.json',metrics)
    load_validate(output)
    if digest(source)!=source_hash or digest(original)!=source_hash:
        raise ValueError('Input changed during import')
    return metrics
