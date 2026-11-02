"""Rig preparation analysis, deliberately separate from import and visual acceptance."""
from pathlib import Path
import numpy as np
from PIL import Image
from .manifest import load_validate,digest,write_json


def analyze(project,output):
    project,output=Path(project),Path(output)
    if output.exists():raise FileExistsError('Choose a new readiness report')
    data=load_validate(project)
    parts={}
    for layer in data['layers']:
        if np.array(Image.open(project/layer['rgba_path']))[...,3].max()==0:continue
        parts.setdefault(layer['role'],[]).append(layer['side'])
    pairs={r:all(s in parts.get(r,[]) for s in ('left','right')) for r in ('eyewhite','irides','eyelash','eyebrow')}
    missing=[r+':paired' for r,ok in pairs.items() if not ok]
    for r in ('face','neck','mouth','front_hair','back_hair'):
        if r not in parts:missing.append(r)
    report=dict(schema_version=1,manifest_sha256=digest(project/'layer_manifest.json'),
        available_parts=parts,paired_eye_parts=pairs,missing_basic_parts=missing,
        alternatives=dict(blink='prefer PSD2Live procedural eyelash/white rig; half/combined poses require review',
            mouth='prefer PSD2Live procedural lips; source mouth is not a complete mouth-interior model'),
        unprovided_structures=['separate pupils','eyelid skin','independently validated hidden face and neck',
            'teeth/tongue system','authored closed/open mouth variants'],
        generated_alternatives=[],
        decision='blocked-missing-basic-parts' if missing else 'eligible-for-reviewed-experiment',
        semantic_acceptance='not-established-by-part-presence',
        production_ready=False,manual_intervention='visual review required; no manual painting performed')
    write_json(output,report)
    return report


def occlusion_guard(pixels, higher_opaque, max_radius):
    """Small generated underlap only where another layer already hides it."""
    from scipy import ndimage as ndi
    support=pixels[...,3]>127
    added=np.zeros(support.shape,bool)
    if not support.any():return pixels.copy(),added
    distance=ndi.distance_transform_edt(~support)
    added=(pixels[...,3]==0)&higher_opaque&(distance<=max_radius)
    if added.sum()>support.sum()*.1:
        return pixels.copy(),np.zeros_like(added)
    interior=ndi.binary_erosion(support,iterations=2)
    if not interior.any():return pixels.copy(),np.zeros_like(added)
    nearest=ndi.distance_transform_edt(~interior,return_distances=False,return_indices=True)
    result=pixels.copy();result[added]=pixels[tuple(nearest[:,added])];result[added,3]=255
    return result,added


def prepare(project,output):
    """Preserve reviewed ownership; add separately marked small hidden guard bands."""
    from copy import deepcopy
    import shutil
    from .preview import preview
    project,output=Path(project),Path(output)
    if output.exists():raise FileExistsError('Choose a fresh rig preparation directory')
    data=deepcopy(load_validate(project))
    if data['schema_version']!=2 or not data.get('provenance',{}).get('unique_source_ownership'):
        raise ValueError('Rig guards require uniquely owned source-preserving v2 layers')
    w,h=data['canvas']['width'],data['canvas']['height'];arrays=[]
    keys=['rgba_path','mask_path','generated_mask_path','semantic_mask_path','uncertain_mask_path','reconstructed_mask_path']
    for l in data['layers']:
        record={}
        for key in keys:
            im=Image.new('RGBA' if key=='rgba_path' else 'L',(w,h));im.paste(Image.open(project/l[key]),(l['x'],l['y']));record[key]=np.array(im)
        arrays.append(record)
    output.mkdir(parents=True,exist_ok=False);shutil.copytree(project/'source',output/'source')
    for name in ('layers','masks','generated','semantic','uncertain','reconstructed','preview'):(output/name).mkdir()
    added_counts={};higher=np.zeros((h,w),bool)
    for l,record in reversed(list(zip(data['layers'],arrays))):
        if l['role'] in ('face','neck','back_hair','topwear'):
            result,added=occlusion_guard(record['rgba_path'],higher,max(1,min(w,h)*.006))
            record['rgba_path']=result
            for key in ('generated_mask_path','semantic_mask_path','uncertain_mask_path','reconstructed_mask_path'):record[key][added]=255
            added_counts[l['id']]=int(added.sum())
        higher|=record['rgba_path'][...,3]==255
    for l,record in zip(data['layers'],arrays):
        alpha=record['rgba_path'][...,3];yy,xx=np.nonzero(alpha)
        if len(xx):x,y,x1,y1=int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)
        else:x,y,x1,y1=0,0,1,1
        for key in keys:Image.fromarray(record[key][y:y1,x:x1]).save(output/l[key])
        l.update(x=x,y=y,width=x1-x,height=y1-y,sha256={k:digest(output/l[k]) for k in keys},
            reconstructed_pixels=int((record['reconstructed_mask_path']>0).sum()),generated_pixels=int((record['generated_mask_path']>0).sum()))
        l['provenance'].append('small-occlusion-guard-v1')
    data['provenance']['rig_preparation']='small-occlusion-guard-v1'
    data['warnings'].append('Guard bands are inferred nearest-interior colour, not original or validated anatomy.')
    data['rig_ready']=False
    write_json(output/'layer_manifest.json',data)
    write_json(output/'config.json',dict(algorithm='small-occlusion-guard-v1',parent_manifest_sha256=digest(project/'layer_manifest.json'),radius_fraction=.006,max_area_fraction=.1))
    composite=preview(output,data,Image.open(output/data['sources'][0]['normalized_path']))
    old=np.array(Image.open(project/'preview/composite.png'))
    if not np.array_equal(composite,old):raise ValueError('Guard bands changed neutral composite')
    load_validate(output)
    report=dict(neutral_pixel_changes=0,generated_guard_pixels=added_counts,hidden_reconstruction='requires-review',production_ready=False)
    write_json(output/'guard-report.json',report);analyze(output,output/'readiness.json')
    return report
