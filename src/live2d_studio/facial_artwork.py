"""Single-image facial ownership and concealed-skin reconstruction on the native grid.

No benchmark metadata, neural model, fixed palette or character coordinates are read.
The output is a new manifest; observed pixels remain unique and exact. Hidden skin
and alternatives are explicitly uncertain generated pixels, never inferred truth.
"""
from copy import deepcopy
from pathlib import Path
import shutil
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from .manifest import load_validate, write_json, digest
from .refinement import native_layers, fidelity
from .preview import preview

VERSION = 'facial-local-skin-v1'


def bounds(mask):
    y,x=np.nonzero(mask)
    if not len(x): raise ValueError('Empty facial support')
    return int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)


def skin_surface(source, known, hole):
    """Harmonic fill from nearby known source skin, with no fixed skin colour."""
    if known.sum()<12: raise ValueError('Insufficient source skin around facial feature')
    _,indices=ndi.distance_transform_edt(~known,return_indices=True)
    surface=source[tuple(indices)][...,:3].astype(float)
    # Jacobi interpolation only replaces the occluded domain. Boundary samples stay exact.
    for _ in range(500):
        smooth=ndi.convolve(surface,np.array([[0,1,0],[1,0,1],[0,1,0]])[...,None]/4,mode='nearest')
        delta=np.max(np.abs(smooth[hole]-surface[hole]))
        surface[hole]=smooth[hole]
        if delta<.02: break
    return np.rint(surface).clip(0,255).astype(np.uint8)


def closed_lash(source, lash, skin, box):
    """Project source upper-lash colour/thickness onto a shallow generated lid curve."""
    x0,y0,x1,y1=box;yy,xx=np.indices(lash.shape)
    dark=lash & (source[...,:3].mean(axis=2)<skin.mean(axis=2)*.65) & (yy<y0+(y1-y0)*.65)
    labels,n=ndi.label(dark)
    if not n:raise ValueError('No supported source upper eyelash for closed-eye reconstruction')
    sizes=np.bincount(labels.ravel());sizes[0]=0;part=labels==int(sizes.argmax())
    ys,xs=np.nonzero(part)
    if len(xs)<4 or xs.max()-xs.min()<(x1-x0)*.35:raise ValueError('Insufficient connected upper-eyelash evidence')
    lo,hi=xs.min(),xs.max();center=y0+(y1-y0)*.65
    weights=np.zeros(lash.shape);colours=np.zeros(source.shape[:2]+(3,))
    for x in range(lo,hi+1):
        sy=ys[xs==x]
        if not len(sy):continue
        u=(x-(lo+hi)/2)/max(1,(hi-lo)/2)
        line=center+(hi-lo)*.045*(1-u*u)
        dest=line+(sy-np.mean(sy))*.8
        for y,dy in zip(sy,dest):
            base=int(np.floor(dy))
            for target,w in [(base,1-(dy-base)),(base+1,dy-base)]:
                if 0<=target<lash.shape[0]:
                    a=source[y,x,3]/255*w;weights[target,x]+=a;colours[target,x]+=source[y,x,:3]*a
    rgba=np.zeros_like(source);used=weights>0
    rgba[used,:3]=np.rint(colours[used]/weights[used,None]).astype(np.uint8)
    rgba[...,3]=np.rint(weights.clip(0,1)*255).astype(np.uint8);rgba[rgba[...,3]==0]=0
    return rgba


def prepare(project,output):
    project,output=Path(project),Path(output)
    data=deepcopy(load_validate(project))
    if data['schema_version']!=2: raise ValueError('Facial reconstruction requires native neural layers')
    size=(data['canvas']['width'],data['canvas']['height'])
    if data['sources'][0].get('normalization_transform',{}).get('kind')!='native-source-grid':
        raise ValueError('Facial reconstruction requires native source pixels')
    source=np.array(Image.open(project/data['sources'][0]['normalized_path']).convert('RGBA'))
    arrays=native_layers(project,data,size)
    observed=[]
    for l in data['layers']:
        a=np.zeros(source.shape[:2],np.uint8)
        a[l['y']:l['y']+l['height'],l['x']:l['x']+l['width']]=np.array(Image.open(project/l['mask_path']))
        observed.append(a)
    def one(role,side='none'):
        ids=[i for i,l in enumerate(data['layers']) if l['role']==role and l['side']==side]
        if len(ids)!=1: raise ValueError('Ambiguous facial role: '+role+':'+side)
        return ids[0]
    face=one('face');mouth=one('mouth')
    owner=np.full(source.shape[:2],-1)
    for i,m in enumerate(observed):owner[m>0]=i
    changes=[];alternatives=[];generated_regions=np.zeros(owner.shape,bool)
    for label,ids,target in [('eye-left',[one(r,'left') for r in ('eyewhite','irides','eyelash')],one('eyewhite','left')),
                             ('eye-right',[one(r,'right') for r in ('eyewhite','irides','eyelash')],one('eyewhite','right')),
                             ('mouth',[mouth],mouth)]:
        support=np.logical_or.reduce([arrays[i][...,3]>127 for i in ids])
        x0,y0,x1,y1=bounds(support);width=x1-x0
        if label=='mouth' and (y1-y0)/width>=.32 and (observed[mouth]>0).sum()/(width*(y1-y0))>=.4:
            changes.append(dict(feature=label,bounds=[x0,y0,x1,y1],
                strategy='retain-existing-open-source-mouth',
                reason='Substantial tall source mouth artwork; sparse closed-contour replacement is unsuitable.',
                transferred_source_pixels=0,reconstructed_skin_pixels=0,skin_samples=0))
            continue
        margin=max(1,round(width*.08))
        region=ndi.binary_dilation(ndi.binary_fill_holes(support),iterations=margin)
        # Span disconnected mouth contours; skin-colour evidence selects the actual ink below.
        if label=='mouth':
            region[max(0,y0-margin):min(size[1],y1+margin),max(0,x0-margin):min(size[0],x1+margin)]=True
        allowed=np.isin(owner,[face]+ids)&(source[...,3]>=250)
        region &= allowed
        if region.sum()<10:raise ValueError('Insufficient supported facial area')
        ring=ndi.binary_dilation(region,iterations=max(3,round(width*.3)))&~ndi.binary_dilation(region,iterations=1)
        known=ring&(owner==face)&(source[...,3]>=250)
        # Reject dark contour outliers from the local skin sample, relative to its own median.
        lum=source[...,:3].mean(axis=2)
        if known.any():known &= lum>=np.quantile(lum[known],.25)
        if known.sum()<12: raise ValueError(f'Insufficient skin for {label}: {known.sum()} samples, bounds {(x0,y0,x1,y1)}')
        skin=skin_surface(source,known,region)
        if label=='mouth':
            residual=np.linalg.norm(source[...,:3].astype(float)-skin,axis=2)
            ink=region & (residual>max(10,float(np.quantile(residual[known],.95))*2))
            # Retain all original mouth pixels, including faint antialiasing.
            ink |= observed[mouth]>0
            move=ink&(owner==face)
            # Complete the rest-neutral mouth with exact source pixels; skin below is synthesized.
            observed[mouth][move]=source[...,3][move];arrays[mouth][move]=source[move]
            hole=ndi.binary_dilation(ink,iterations=1)&region
            # Preserve neutral skin in a source mouth patch over the reconstructed domain.
            moved=hole&(owner==face)
            observed[mouth][moved]=source[...,3][moved];arrays[mouth][moved]=source[moved]
        else:
            hole=region
            moved=region&(owner==face)
            observed[target][moved]=source[...,3][moved];arrays[target][moved]=source[moved]
        observed[face][hole]=0
        # Keep exact copied source artwork separate from the generated backing.
        # Runtime backing changes fractional-alpha compositing; measure that separately.
        arrays[face][hole]=0
        # Overlap independently triangulated edges to prevent filtered cracks.
        padded=ndi.binary_dilation(hole,iterations=max(2,round(width*.07)))
        backing=np.zeros_like(source);backing[padded,:3]=skin[padded];backing[padded,3]=255
        edge=padded&~hole&(owner==face);backing[edge,:3]=source[edge,:3]
        alternatives.append((label+'-skin',backing,label,'skin'))
        if label.startswith('eye'):
            closed=closed_lash(source,observed[ids[2]]>0,skin,(x0,y0,x1,y1))
            alternatives.append((label+'-closed',closed,label,'closed-lash'))
        if label=='mouth':
            # A modest dark cavity is supported by contour colour, not teeth/tongue evidence.
            iy,ix=np.nonzero(ink);mx0,mx1=int(ix.min()),int(ix.max())
            cy=float(np.median(iy));cx=(mx0+mx1)/2;rx=max(2,(mx1-mx0)*.45);ry=max(2,rx*.4)
            yy,xx=np.indices(owner.shape);r=((xx-cx)/rx)**2+((yy-cy)/ry)**2
            cavity=np.zeros_like(source)
            samples=source[ink,:3];colour=np.median(samples[np.argsort(samples.mean(axis=1))[:max(1,len(samples)//4)]],axis=0)
            cavity[...,:3]=np.rint(colour).astype(np.uint8)
            cavity[...,3]=np.rint(np.clip((1-r)*min(rx,ry),0,1)*255).astype(np.uint8)
            cavity[cavity[...,3]==0]=0
            alternatives.append(('mouth-interior',cavity,label,'interior'))
            neutral=np.zeros_like(source)
            neutral[observed[mouth]>0]=source[observed[mouth]>0]
            alternatives.append(('mouth-neutral',neutral,label,'source-neutral'))
        generated_regions |= hole
        changes.append(dict(feature=label,bounds=[x0,y0,x1,y1],transferred_source_pixels=int(moved.sum()),
                            reconstructed_skin_pixels=int(hole.sum()),skin_samples=int(known.sum())))
    output.mkdir(parents=True,exist_ok=False)
    shutil.copytree(project/'source',output/'source')
    (output/'alternatives').mkdir()
    variants=[]
    for name,pixels,feature,kind in alternatives:
        rel='alternatives/'+name+'.png';Image.fromarray(pixels).save(output/rel)
        variants.append(dict(path=rel,sha256=digest(output/rel),feature=feature,kind=kind,
            provenance=('Exact source contour variant; replaces procedural mouth rendering' if kind=='source-neutral'
                        else 'Generated from single-image local source skin/contour evidence'),
            uncertainty=('Ownership reviewed as candidate' if kind=='source-neutral' else 'Unvalidated hidden surface'),
            source_pixels=kind=='source-neutral'))
    for f in ('layers','masks','generated','semantic','uncertain','reconstructed','preview'):(output/f).mkdir()
    for a,obs,l in zip(arrays,observed,data['layers']):
        a[a[...,3]==0]=0
        x,y,x1,y1=bounds(a[...,3]>0);crop=np.s_[y:y1,x:x1]
        alpha=a[...,3];gen=np.where(obs>0,0,alpha).astype(np.uint8)
        files=dict(rgba_path='layers',mask_path='masks',generated_mask_path='generated',semantic_mask_path='semantic',uncertain_mask_path='uncertain',reconstructed_mask_path='reconstructed')
        for key,arr in zip(files,(a,obs,gen,alpha,(alpha>0).astype(np.uint8)*255,np.zeros_like(alpha))):
            rel=f'{files[key]}/{l["id"]}.png';Image.fromarray(arr[crop]).save(output/rel);l[key]=rel
        l.update(x=x,y=y,width=x1-x,height=y1-y,sha256={k:digest(output/l[k]) for k in files},
                 observed_pixels=int((obs>0).sum()),generated_pixels=int((gen>0).sum()),reconstructed_pixels=0,
                 quality_status='generated-review',hidden_reconstruction_status='unlocalized')
        l['provenance'].append(VERSION)
    data['provenance']['facial_artwork']=VERSION
    write_json(output/'layer_manifest.json',data)
    composite=preview(output,data,Image.fromarray(source))
    report=dict(algorithm=VERSION,input_manifest_sha256=digest(project/'layer_manifest.json'),changes=changes,
        fidelity=fidelity(source,composite),alternatives=variants,single_image=True,additional_references=False,
        uncertainty='Local skin interpolation is not independently known hidden anatomy.',
        generated_pixels='All non-observed alpha is marked generated and uncertain.',requires_visual_review=True)
    write_json(output/'facial-artwork.json',report)
    Image.fromarray(generated_regions.astype(np.uint8)*255).save(output/'preview/reconstructed-skin.png')
    load_validate(output)
    if report['fidelity']['exact_fraction']<.995:raise ValueError('Facial reconstruction violates source fidelity gate')
    return report
