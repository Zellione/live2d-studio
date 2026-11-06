"""Exploratory 2-D arm evidence from visible masks, never skeletal ground truth."""
import heapq
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
from .pose_review import digest,write


def components(mask):
    labels,_=ndimage.label(mask);minimum=max(32,int(mask.sum()*.05));regions=[]
    for n,size in enumerate(np.bincount(labels.ravel())[1:],1):
        if size>=minimum:
            y,x=np.where(labels==n);regions.append({'label':n,'pixels':int(size),'center':[float(x.mean()),float(y.mean())]})
    return labels,sorted(regions,key=lambda r:r['center'][0])


def centerline(mask,start,end,step=4):
    """Distance-weighted interior path; a sleeve centerline is not a bone."""
    small=mask[::step,::step];dist=ndimage.distance_transform_edt(small);ys,xs=np.where(small)
    if not len(xs):raise ValueError('Empty limb')
    def nearest(point):
        i=np.argmin((xs-point[0]/step)**2+(ys-point[1]/step)**2);return int(ys[i]),int(xs[i])
    a=nearest(start);b=nearest(end);cost={a:0.0};prev={};queue=[(0.0,a)]
    while queue:
        value,u=heapq.heappop(queue)
        if value!=cost[u]:continue
        if u==b:break
        for dy,dx in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
            v=(u[0]+dy,u[1]+dx)
            if not(0<=v[0]<small.shape[0] and 0<=v[1]<small.shape[1]) or not small[v]:continue
            new=value+np.hypot(dx,dy)*(.02+1/(1+dist[v])**2)
            if new<cost.get(v,float('inf')):cost[v]=new;prev[v]=u;heapq.heappush(queue,(new,v))
    if b not in cost:raise ValueError('Disconnected shoulder-to-wrist mask')
    path=[b]
    while path[-1]!=a:path.append(prev[path[-1]])
    return np.array([(x*step,y*step) for y,x in reversed(path)],float)


def segment_distance(points,a,b):
    delta=b-a;projection=np.clip(((points-a)@delta)/max(float(delta@delta),1e-9),0,1)
    return np.linalg.norm(points-(a+projection[:,None]*delta),axis=1)


def fit_elbow(path):
    if len(path)<8:raise ValueError('Too little sleeve path for a joint hypothesis')
    begin=max(2,int(len(path)*.15));end=min(len(path)-2,int(len(path)*.85));fits=[]
    for i in range(begin,end):
        e=path[i];err=np.r_[segment_distance(path[:i+1],path[0],e),segment_distance(path[i:],e,path[-1])]
        fits.append((float(np.mean(err**2)),i))
    best,index=min(fits);joint=path[index];u=path[0]-joint;v=path[-1]-joint
    angle=float(np.degrees(np.arccos(np.clip((u@v)/max(np.linalg.norm(u)*np.linalg.norm(v),1e-9),-1,1))))
    ambiguous=angle>155
    plausible=[path[i] for err,i in fits if ambiguous or err<=best+16]
    bounds=np.array(plausible)
    return {'point':joint.tolist(),'angle_degrees':angle,'fit_rms_pixels':float(np.sqrt(best)),
        'status':'unresolved-near-straight' if ambiguous else 'visible-contour-bend-hypothesis',
        'candidate_bbox':[float(bounds[:,0].min()),float(bounds[:,1].min()),float(bounds[:,0].max()),float(bounds[:,1].max())],
        'upper_length_pixels':float(np.linalg.norm(u)),'forearm_length_pixels':float(np.linalg.norm(v)),
        'warning':'Cloth silhouette fit; joint center, depth and underlying bone lengths are not independently observed.'}


def assess_image(image_file,sam,output):
    metadata=json.loads((sam/'sam.json').read_text())
    if metadata['input_sha256']!=digest(image_file):raise ValueError('SAM belongs to another image')
    rgb=np.asarray(Image.open(image_file).convert('RGB'));height,width=rgb.shape[:2]
    masks={name:np.asarray(Image.open(sam/(name+'.png')).convert('L'))>0 for name in ('handwear','topwear','face')}
    if any(m.shape!=(height,width) for m in masks.values()):raise ValueError('SAM/image grid mismatch')
    arm=masks['handwear'];torso=masks['topwear'];labels,regions=components(arm)
    if not torso.any():raise ValueError('No torso frame')
    ty,tx=np.where(torso);cx=float(np.median(tx));torso_height=float(np.percentile(ty,99)-np.percentile(ty,1))
    output.mkdir(parents=True,exist_ok=False)
    face=masks['face'];skin=np.median(rgb[face],axis=0) if face.any() else None
    cloth=np.median(rgb[torso],axis=0)
    near_torso=ndimage.distance_transform_edt(~torso)<=max(4,width*.015)
    report={'image_sha256':digest(image_file),'sam_sha256':digest(sam/'sam.json'),'mask_hashes':{k:digest(sam/(k+'.png')) for k in masks},
        'torso_frame':{'center_x':cx,'height_pixels':torso_height},'component_count':len(regions),'arm_torso_overlap_pixels':int((arm&torso).sum()),
        'skin_color_hint_rgb':None if skin is None else skin.tolist(),'arms':{},'independently_verified_anatomy':False}
    canvas=Image.fromarray(rgb.copy()).convert('RGBA');tint=np.zeros((height,width,4),np.uint8)
    if len(regions)!=2:
        report['blocked']='Two substantial separate arm-category regions required; no automatic component-to-joint inference'
    else:
        for row,side,color in zip(regions,('right','left'),((230,70,70),(40,125,235))):
            m=labels==row['label'];y,x=np.where(m)
            if (side=='right' and np.median(x)>=cx) or (side=='left' and np.median(x)<=cx):
                report['arms'][side]={'blocked':'Ambiguous side ownership'};continue
            tint[m]=(*color,100)
            # Raised fingertips can lie above shoulders. Require a torso-adjacent sleeve surface.
            attached=m&near_torso&(np.indices(m.shape)[0]<=np.percentile(ty,1)+torso_height*.3)
            ay,ax=np.where(attached)
            if not len(ax):
                report['arms'][side]={'blocked':'No torso-adjacent upper sleeve attachment'};continue
            top=ay<=np.percentile(ay,8);shoulder=np.array([np.mean(ax[top]),np.mean(ay[top])])
            record={'ownership':'anatomical '+side+' under frontal non-mirrored assumption','visible_mask_pixels':int(m.sum()),
                'shoulder_surface':shoulder.tolist(),'shoulder_uncertainty_pixels':float(max(8,np.ptp(ax[top])/2)),
                'shoulder_note':'Top of parsed sleeve; attachment surface, not an observed rotation pivot.'}
            try:
                if skin is None:raise ValueError('No face colour hint for cuff discovery')
                possible=m&(np.linalg.norm(rgb.astype(float)-skin,axis=2)<65)
                skin_labels,skin_regions=components(possible)
                if not skin_regions:raise ValueError('No connected skin-colour hand hypothesis')
                largest=max(skin_regions,key=lambda r:r['pixels']);hand=skin_labels==largest['label']
                hand=ndimage.binary_fill_holes(hand)
                chroma=rgb.astype(float)/np.maximum(rgb.sum(axis=2,keepdims=True),1)
                skin_chroma=skin/max(skin.sum(),1);cloth_chroma=cloth/max(cloth.sum(),1)
                if np.linalg.norm(skin_chroma-cloth_chroma)<.035:raise ValueError('Skin/cloth colours too similar for cuff inference')
                cloth_pixels=m&(np.linalg.norm(chroma-cloth_chroma,axis=2)<np.linalg.norm(chroma-skin_chroma,axis=2))
                cloth_labels,cloth_regions=components(cloth_pixels)
                if not cloth_regions:raise ValueError('No connected cloth hypothesis')
                cloth_pixels=cloth_labels==max(cloth_regions,key=lambda r:r['pixels'])['label']
                boundary=ndimage.binary_dilation(hand,iterations=max(3,round(width*.01)))&cloth_pixels&~hand
                by,bx=np.where(boundary)
                if len(bx)<8:raise ValueError('No reliable cuff transition')
                wrist=np.array([np.mean(bx),np.mean(by)])
                path=centerline(m,shoulder,wrist);elbow=fit_elbow(path)
                # A shortest interior path can cut across touching upper/forearm sleeves.
                # Keep that failure and offer a separate visible-lobe hypothesis, not a bone fit.
                cy,cx_=np.where(cloth_pixels);cp=np.column_stack([cx_,cy]).astype(float)
                radius=ndimage.distance_transform_edt(m);radii=radius[cy,cx_]
                away=segment_distance(cp,shoulder,wrist)
                if len(away) and away.max()>3*max(4,float(np.percentile(radii,80))):
                    score=away*np.sqrt(radii);extent=cp[score>=score.max()*.95].mean(axis=0)
                    alternative=elbow
                    path=np.vstack([centerline(m,shoulder,extent),centerline(m,extent,wrist)[1:]])
                    elbow=fit_elbow(path)
                    elbow['shortest_path_alternative']=alternative
                    elbow['alternative_disagreement_pixels']=float(np.linalg.norm(np.array(alternative['point'])-elbow['point']))
                    elbow['status']='visible-lobe-hypothesis-with-overlap-ambiguity'
                    elbow['uncertainty_pixels']=max(24,float(radius[round(extent[1]),round(extent[0])]))
                record.update(wrist=wrist.tolist(),wrist_uncertainty_pixels=float(max(6,np.hypot(np.std(bx),np.std(by)))),
                    hand_pixels=int(hand.sum()),hand_center=largest['center'],hand_note='Skin-colour component only; not a finger count or topology validation.',
                    elbow=elbow,centerline=path.tolist())
                record['upper_length_over_torso']=elbow['upper_length_pixels']/torso_height
                record['forearm_length_over_torso']=elbow['forearm_length_pixels']/torso_height
                points=np.column_stack([x,y]).astype(float);joint=np.array(elbow['point'])
                du=segment_distance(points,shoulder,joint);df=segment_distance(points,joint,wrist)
                upper=np.zeros_like(m);upper[y,x]=du<=df;upper&=~hand
                forearm=m&~upper&~hand
                for name,mask in [('arm',m),('upper',upper),('forearm',forearm),('hand',hand)]:
                    Image.fromarray(mask.astype(np.uint8)*255).save(output/(side+'-'+name+'.png'))
                record['partition_note']='Nearest two-segment partition of the SAM sleeve; cut lines and joint overlaps remain unreviewed.'
            except ValueError as exc:record['blocked']=str(exc)
            report['arms'][side]=record
    canvas=Image.alpha_composite(canvas,Image.fromarray(tint));d=ImageDraw.Draw(canvas)
    for side,row in report['arms'].items():
        if 'blocked' in row:continue
        s=tuple(row['shoulder_surface']);e=tuple(row['elbow']['point']);w=tuple(row['wrist']);d.line([s,e,w],fill='yellow',width=3)
        for tag,p,r in [('S?',s,row['shoulder_uncertainty_pixels']),('E?',e,row['elbow'].get('uncertainty_pixels',24)),('W?',w,row['wrist_uncertainty_pixels'])]:
            d.ellipse((p[0]-r,p[1]-r,p[0]+r,p[1]+r),outline='yellow',width=2);d.text((p[0]+5,p[1]),side+' '+tag,fill='black',stroke_width=1,stroke_fill='white')
        if row['elbow']['status']=='unresolved-near-straight':d.rectangle(row['elbow']['candidate_bbox'],outline='orange',width=3)
    canvas.save(output/'overlay.png');write(output/'evidence.json',report);return report


def compare(reports):
    result={}
    for side in ('right','left'):
        rows={pose:r['arms'].get(side,{}) for pose,r in reports.items()}
        rows={pose:r for pose,r in rows.items() if 'elbow' in r and r['elbow']['status']!='unresolved-near-straight'}
        result[side]={'bent_views':list(rows),'measurements':{pose:{k:r[k] for k in ('upper_length_over_torso','forearm_length_over_torso')} for pose,r in rows.items()}}
        for metric in ('upper_length_over_torso','forearm_length_over_torso'):
            vals=[r[metric] for r in rows.values()];result[side][metric+'_max_min_ratio']=max(vals)/min(vals) if len(vals)>1 and min(vals)>0 else None
    return {'sides':result,'scope':'Projected cloth-axis lengths, normalized by torso height; changes can reflect foreshortening, mask errors or redraw. No automatic skeletal acceptance.',
            'hidden_torso':'Visible synthetic torso surfaces only; occluded attachment backing, depth and original hidden pixels remain unverified.'}
