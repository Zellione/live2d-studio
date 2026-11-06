"""Optional source-exact brow patches over local generated skin; no global redraw."""
import json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from .manifest import load_validate,digest,write_json
from .facial_artwork import skin_surface
from .preview import preview
from .pose_review import REPO


def repair(project,output):
    project=Path(project);output=Path(output).resolve();data=load_validate(project)
    if not output.is_relative_to(REPO/'runs') or output.exists():raise ValueError('Fresh ignored output required')
    source=np.array(Image.open(project/data['sources'][0]['normalized_path']).convert('RGBA'))
    h,w=source.shape[:2];arrays=[];observed=[]
    for l in data['layers']:
        a=np.zeros_like(source);m=np.zeros((h,w),np.uint8);x,y,lw,lh=[l[k] for k in ('x','y','width','height')]
        a[y:y+lh,x:x+lw]=np.array(Image.open(project/l['rgba_path']));m[y:y+lh,x:x+lw]=np.array(Image.open(project/l['mask_path']))
        arrays.append(a);observed.append(m)
    face=next(i for i,l in enumerate(data['layers']) if l['role']=='face');owner=np.full((h,w),-1)
    for i,m in enumerate(observed):owner[m>0]=i
    changes=[]
    for i,l in enumerate(data['layers']):
        if l['role']!='eyebrow':continue
        support=arrays[i][...,3]>127;yy,xx=np.where(support)
        if not len(xx):raise ValueError('Empty brow')
        width=xx.max()-xx.min()+1;region=np.zeros((h,w),bool)
        mx=max(3,round(width*.45));my=max(2,round(width*.12))
        region[max(0,yy.min()-my):min(h,yy.max()+my+1),max(0,xx.min()-mx):min(w,xx.max()+mx+1)]=True
        region&=np.isin(owner,[face,i])&(source[...,3]==255)
        known=ndi.binary_dilation(region,iterations=max(3,round(width*.25)))&~region&(owner==face)
        lum=source[...,:3].mean(2);known&=lum>=np.median(lum[known])
        skin=skin_surface(source,known,region)
        move=region&(owner==face);arrays[i][move]=source[move];observed[i][move]=source[...,3][move]
        observed[face][region]=0;arrays[face][region,:3]=skin[region];arrays[face][region,3]=255
        changes.append({'layer':l['id'],'source_pixels_transferred':int(move.sum()),'generated_skin_pixels':int(region.sum())})
    shutil.copytree(project,output)
    for i,l in enumerate(data['layers']):
        a=arrays[i];obs=observed[i];yy,xx=np.where(a[...,3]>0);x,y,x1,y1=int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)
        gen=np.where(obs>0,0,a[...,3]).astype(np.uint8);unc=np.where(a[...,3]>0,255,0).astype(np.uint8)
        for key,arr in [('rgba_path',a),('mask_path',obs),('generated_mask_path',gen),('semantic_mask_path',a[...,3]),('uncertain_mask_path',unc),('reconstructed_mask_path',np.zeros((h,w),np.uint8))]:
            Image.fromarray(arr[y:y1,x:x1]).save(output/l[key]);l['sha256'][key]=digest(output/l[key])
        l.update(x=x,y=y,width=x1-x,height=y1-y,observed_pixels=int((obs>0).sum()),generated_pixels=int((gen>0).sum()))
    data['provenance']['frontal_brow_backing']={'parent_manifest_sha256':digest(project/'layer_manifest.json'),'algorithm':'local-harmonic-source-brow-patch-v1','review':'pending'}
    write_json(output/'layer_manifest.json',data)
    write_json(output/'brow-repair.json',{'changes':changes,'source_preserved':True,'generated_skin':'uncertain; human review required'})
    preview(output,data,Image.fromarray(source));load_validate(output)
    return changes
