"""Replayable native-grid source restoration; no inference or ground-truth access.

A copied pixel proves its source, not its semantic ownership. Uncertainty masks
remain independent. Each source sample has at most one owner; generated surfaces
under opaque owners survive. Nothing is flattened into an extra overlay layer.
"""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import time

import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage as ndi

from .manifest import digest, load_validate, local_file, write_json
from .preview import preview

VERSION = 'native-owner-v1'
COARSE = dict(front_hair='hair', back_hair='hair', headwear='headwear',
              irides='eyes', eyewhite='eyes', eyelash='eyes', eyebrow='eyes')


def native_layers(project, data, size):
    """Invert the worker's documented center padding on a separate raster copy."""
    w,h = size
    transform = data['sources'][0].get('normalization_transform', {})
    if transform.get('kind') not in ('center-square-pad-resize', 'native-source-grid'):
        raise ValueError('Unsupported source transform; do not guess alignment')
    result = []
    for l in data['layers']:
        im = Image.new('RGBA', (data['canvas']['width'],data['canvas']['height']))
        im.paste(Image.open(project/l['rgba_path']), (l['x'],l['y']))
        if transform['kind']=='center-square-pad-resize':
            side=max(w,h)
            im=im.resize((side,side),Image.Resampling.LANCZOS)
            x,y=(side-w)//2,(side-h)//2
            im=im.crop((x,y,x+w,y+h))
        elif im.size!=size:
            raise ValueError('Native source transform dimensions differ')
        result.append(np.array(im))
    return result


def visible_owners(arrays):
    owner=np.full(arrays[0].shape[:2],-1,np.int16)
    for i,a in enumerate(arrays):owner[a[...,3]>127]=i
    return owner


def sam_masks(root, source_hash, size):
    if root is None:return {}
    root=Path(root)
    data=json.loads((root/'sam.json').read_text())
    if data['input_sha256']!=source_hash:
        raise ValueError('SAM masks belong to a different original')
    result={}
    for tag in data['tags']:
        im=Image.open(local_file(root,tag+'.png'))
        if im.size!=size:raise ValueError('SAM masks must match native input dimensions')
        result[tag]=np.array(im)>127
    return result


def neck_repair(rgba, arrays, layers, owner, sam):
    """Connected source skin extending from parser-agreed neck, bounded by parts.

    Skin palette comes from this image's face/neck, never a benchmark colour.
    Clothing is changed only where a skin component connects to an agreed neck.
    """
    necks=[i for i,l in enumerate(layers) if l['role']=='neck']
    faces=[i for i,l in enumerate(layers) if l['role']=='face']
    clothing=[i for i,l in enumerate(layers) if l['role'] in ('topwear','handwear')]
    changed=np.zeros(owner.shape,bool)
    if len(necks)!=1 or len(faces)!=1 or 'neck' not in sam or 'face' not in sam:
        return changed
    ni,fi=necks[0],faces[0]
    seed=(owner==ni)&sam['neck']&(rgba[...,3]==255)
    face=(owner==fi)&sam['face']&(rgba[...,3]==255)
    if seed.sum()<10 or face.sum()<10:return changed
    rgb=rgba[...,:3].astype(np.int16)
    # Frequent bright colours from independently agreed face and neck regions.
    samples=rgb[seed|face]
    samples=samples[np.min(samples,axis=1)>80]
    if not len(samples):return changed
    bins,counts=np.unique(samples//8,axis=0,return_counts=True)
    bins=bins[np.argsort(-counts,kind='stable')[:8]]*8+4
    skin=np.zeros(owner.shape,bool)
    for c in bins:skin|=np.max(np.abs(rgb-c),axis=2)<=24
    ys,xs=np.nonzero(face)
    yy,xx=np.indices(owner.shape)
    # Relative face geometry limits reach; source colour/connectivity sets border.
    allowed=(np.isin(owner,clothing+[ni]))&(rgba[...,3]>127)
    allowed&=(yy>=ys.min())&(yy<=ys.max()+1.5*(ys.max()-ys.min()+1))
    allowed&=(xx>=xs.min()-.2*(xs.max()-xs.min()+1))&(xx<=xs.max()+.2*(xs.max()-xs.min()+1))
    grown=ndi.binary_propagation(seed,mask=(skin&allowed)|seed)
    # Enclosed collarbone/line art belongs with connected skin, not a detached ink layer.
    holes=ndi.binary_fill_holes(grown)&~grown
    labels,n=ndi.label(holes)
    sizes=np.bincount(labels.ravel())
    keep=np.flatnonzero((sizes<=max(4,int(grown.sum()*.02)))&(np.arange(len(sizes))>0))
    grown|=np.isin(labels,keep)&allowed
    changed=grown&np.isin(owner,clothing)
    owner[changed]=ni
    return changed


def component_flags(arrays,layers):
    flags=[]
    for a,l in zip(arrays,layers):
        labels,n=ndi.label(a[...,3]>127)
        sizes=np.bincount(labels.ravel());total=int(sizes[1:].sum())
        for i in range(1,n+1):
            if sizes[i]<=max(2,total*.001):
                yy,xx=np.nonzero(labels==i)
                flags.append(dict(layer=l['id'],pixels=int(sizes[i]),
                    border=bool((xx==0).any() or (yy==0).any() or (xx==a.shape[1]-1).any() or (yy==a.shape[0]-1).any()),
                    action='retained-uncertain',reason='small relative component; may be legitimate ink/accessory'))
    return flags


def structural_review(arrays,layers,owner,sam):
    reasons=[]
    face=np.zeros(owner.shape,bool);eyes=np.zeros_like(face)
    for i,(a,l) in enumerate(zip(arrays,layers)):
        if l['role']=='face':face|=a[...,3]>127
        if l['role'] in ('eyewhite','irides'):eyes|=a[...,3]>127
    support=float((face&eyes).sum()/max(1,eyes.sum()))
    if eyes.any() and support<.75:reasons.append('Face surface does not support most eye geometry')
    agreement=None
    if sam:
        sf=sam.get('face',np.zeros_like(face))
        visible_face=np.zeros_like(face)
        for i,l in enumerate(layers):
            if l['role']=='face':visible_face|=owner==i
        agreement=float((sf&visible_face).sum()/max(1,sf.sum()))
        if agreement<.5:reasons.append('Strong disagreement on visible face ownership')
    return dict(status='rejected' if reasons else 'requires-review',reasons=reasons,
                face_support_of_eyes=support,sam_face_recall_candidate=agreement)


def fidelity(original,composite):
    fg=original[...,3]>127
    error=np.abs(original.astype(float)-composite.astype(float))
    exact=np.all(original==composite,axis=2)
    def edge(a):
        gray=a[...,:3].astype(float).mean(axis=2)
        return np.hypot(ndi.sobel(gray,0),ndi.sobel(gray,1))
    e1,e2=edge(original),edge(composite)
    ink=(e1>80)&fg
    s1,s2=original[...,3]>127,composite[...,3]>127
    return dict(foreground_pixels=int(fg.sum()),rgb_mae=float(error[...,:3][fg].mean()) if fg.any() else None,
        exactly_preserved_pixels=int((exact&fg).sum()),exact_fraction=float(exact[fg].mean()) if fg.any() else None,
        alpha_mae=float(error[...,3].mean()),silhouette_iou=float((s1&s2).sum()/max(1,(s1|s2).sum())),
        source_edge_pixels=int(ink.sum()),exact_edge_fraction=float(exact[ink].mean()) if ink.any() else None,
        edge_magnitude_mae=float(np.abs(e1-e2)[fg].mean()) if fg.any() else None,
        caveat='Pixel/edge agreement is not semantic correctness or animation acceptance.')


def refine(project,output,sam=None,repair_neck=True):
    started=time.perf_counter()
    project,output=Path(project),Path(output)
    if output.exists():raise FileExistsError('Choose a fresh refinement directory')
    data=deepcopy(load_validate(project))
    if data['schema_version']!=2:raise ValueError('Refinement requires a neural v2 project; baseline is unchanged')
    source=data['sources'][0]
    image=ImageOps.exif_transpose(Image.open(project/source['path'])).convert('RGBA')
    if image.width*image.height>4_194_304:raise ValueError('Refinement limit: 4 megapixels')
    rgba=np.array(image);rgba[rgba[...,3]==0]=0
    arrays=native_layers(project,data,image.size)
    masks=sam_masks(sam,source['sha256'],image.size)
    owner=visible_owners(arrays)
    initial=owner.copy()
    # Only fill very close silhouette gaps; no extrapolation into unsupported parts.
    if (owner>=0).any():
        dist,indices=ndi.distance_transform_edt(owner<0,return_indices=True)
        close=(owner<0)&(dist<=max(1,min(image.size)*.003))&(rgba[...,3]>0)
        owner[close]=owner[tuple(indices[:,close])]
    owner[rgba[...,3]==0]=-1
    changed=neck_repair(rgba,arrays,data['layers'],owner,masks) if repair_neck else np.zeros(owner.shape,bool)
    structure=structural_review(arrays,data['layers'],owner,masks)
    flags=component_flags(arrays,data['layers'])
    output.mkdir(parents=True,exist_ok=False)
    for folder in ('source','layers','masks','generated','semantic','uncertain','reconstructed','preview'):(output/folder).mkdir()
    shutil.copyfile(project/source['path'],output/source['path'])
    Image.fromarray(rgba).save(output/'source/normalized.png')
    source['normalized_path']='source/normalized.png'
    source['normalized_sha256']=digest(output/source['normalized_path'])
    source['normalization_transform']={'kind':'native-source-grid','parent_manifest_sha256':digest(project/'layer_manifest.json')}
    observed_total=0;uncertain_total=0
    for i,(a,l) in enumerate(zip(arrays,data['layers'])):
        owned=owner==i
        # Keep generated geometry only beneath another opaque source owner.
        a[(owner<i)|(rgba[...,3]<255)]=0
        a[owned]=rgba[owned]
        a[a[...,3]==0]=0
        alpha=a[...,3]
        observed=np.where(owned,alpha,0).astype(np.uint8)
        generated=np.where(~owned,alpha,0).astype(np.uint8)
        agreement=masks.get(COARSE.get(l['role'],l['role']),np.zeros(owner.shape,bool))
        uncertain=(alpha>0)&(~owned|~agreement|(initial!=owner))
        # Even parser agreement is evidence, not independent semantic validation.
        if structure['status']=='rejected':uncertain|=alpha>0
        observed_total+=int(owned.sum());uncertain_total+=int((uncertain&owned).sum())
        yy,xx=np.nonzero(alpha)
        if len(xx):x,y,x1,y1=int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)
        else:x,y,x1,y1=0,0,1,1
        crop=np.s_[y:y1,x:x1]
        files=dict(rgba_path=f'layers/{l["id"]}.png',mask_path=f'masks/{l["id"]}.png',
            generated_mask_path=f'generated/{l["id"]}.png',semantic_mask_path=f'semantic/{l["id"]}.png',
            uncertain_mask_path=f'uncertain/{l["id"]}.png',reconstructed_mask_path=f'reconstructed/{l["id"]}.png')
        for key,arr in zip(files,(a,observed,generated,alpha,uncertain.astype(np.uint8)*255,np.zeros_like(alpha))):
            Image.fromarray(arr[crop]).save(output/files[key])
        l.update(files);l.update(x=x,y=y,width=x1-x,height=y1-y,sha256={k:digest(output/v) for k,v in files.items()},
            generated_pixels=int((generated>0).sum()),observed_pixels=int(owned.sum()),
            ownership_status='parser-candidate-not-ground-truth',hidden_reconstruction_status='unlocalized',reconstructed_pixels=0)
        l['provenance'].append(VERSION)
    data['canvas']=dict(width=image.width,height=image.height)
    data['rig_ready']=False
    data['provenance']['refinement']=VERSION
    data['provenance']['unique_source_ownership']=True
    data['warnings']=['Source masks prove exact copying, not semantic ownership. See uncertainty and quality reports.',
        'Generated hidden surfaces retained only beneath opaque source owners; hidden-only anatomy remains unvalidated.',
        'Small components are flagged, not deleted. Procedural PSD2Live blink/mouth requires pose inspection.']
    write_json(output/'layer_manifest.json',data)
    write_json(output/'config.json',dict(algorithm=VERSION,parent_manifest_sha256=digest(project/'layer_manifest.json'),
        sam_sha256=digest(Path(sam)/'sam.json') if sam else None,repair_neck=repair_neck))
    composite=preview(output,data,Image.fromarray(rgba))
    Image.fromarray((changed*255).astype(np.uint8)).save(output/'preview/neck-repair.png')
    Image.fromarray(((owner<0)&(rgba[...,3]>0)).astype(np.uint8)*255).save(output/'preview/unassigned.png')
    report=dict(fidelity=fidelity(rgba,composite),structural_semantics=structure,
        source_samples_copied=observed_total,uncertain_copied_samples=uncertain_total,
        neck_reassigned_pixels=int(changed.sum()),small_components=flags,
        gates=dict(semantic_decomposition=structure['status'],source_preservation='requires-review',
            hidden_reconstruction='requires-review',psd2live_import='not-tested',runtime_geometry='not-tested',visual_animation='not-tested'),
        production_ready=False)
    write_json(output/'quality.json',report)
    write_json(output/'metrics.json',dict(seconds=time.perf_counter()-started,device='cpu',**report))
    load_validate(output)
    return report
