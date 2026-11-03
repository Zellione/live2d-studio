"""Source-derived shared closure curves for optional, review-gated facial motion."""
import json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from .generic_rig import inspect, objects, overview
from .manifest import digest, write_json

VERSION='shared-closure-v5'
DENSE_VALUES=[0,.05,.10,.15,.20,.25,.35,.50,.65,.75,.90,1]


def ink_curve(rgba, upper=False, isolated=False):
    """Connected dark stroke, with no fixed character colour or pixel location."""
    a=np.asarray(rgba);support=a[...,3]>127
    yy,xx=np.nonzero(support)
    if len(xx)<4:raise ValueError('Insufficient contour support')
    lum=a[...,:3].mean(2)
    low,high=np.quantile(lum[support],[.05,.9])
    # A transparent stroke is already isolated; selecting only its darkest
    # quantile fragments antialiased lashes and gives an unstable fitted curve.
    dark=support if isolated else support&(lum<=low+.45*(high-low))
    if upper:dark &= np.indices(support.shape)[0]<=yy.min()+.65*(yy.max()-yy.min()+1)
    labels,n=ndi.label(dark)
    if not n:raise ValueError('No connected facial contour')
    if isolated:part=dark
    else:
        components=ndi.find_objects(labels)
        index=max(range(n),key=lambda i:components[i][1].stop-components[i][1].start)
        part=labels==index+1
    y,x=np.nonzero(part);xs=np.unique(x)
    if len(xs)<4:raise ValueError('Unsupported narrow facial contour')
    ys=np.array([np.mean(y[x==v]) for v in xs])
    return xs.astype(float),ys


def bernstein(x):
    return np.array([(1-x)**3,3*x*(1-x)**2,3*x*x*(1-x),x**3]).T


def correspondence(source_x,source_y,target_x,target_y,bounds,compression=.08):
    """Positive vertical scale plus smooth curve displacement in one parent space.

    Fits the target's curve by normalized horizontal correspondence; the actual
    stroke extent is retained. Source and target are resampled on shared x's.
    """
    x0,y0,x1,y1=map(float,bounds);w=x1-x0;h=y1-y0
    if w<=0 or h<=0 or not 0<compression<=1:raise ValueError('Degenerate correspondence bounds')
    lo=max(min(source_x),min(target_x));hi=min(max(source_x),max(target_x))
    if hi-lo<w*.3:raise ValueError('Insufficient shared contour extent')
    x=np.linspace(x0,x1,49)
    sy=np.interp(x,source_x,source_y);ty=np.interp(x,target_x,target_y)
    values=(ty-y0-compression*(sy-y0))/h
    controls=np.linalg.lstsq(bernstein((x-x0)/w),values,rcond=None)[0]
    residual=bernstein((x-x0)/w)@controls-values
    if not np.isfinite(controls).all() or np.max(np.abs(controls))>3:raise ValueError('Unbounded contour mapping')
    return controls.tolist(),float(np.sqrt(np.mean(residual**2))*h)


def opacity_schedule(kind):
    # Extreme squash can fold a coarse source triangle. Keep it hidden until
    # the eye has unfolded; exported Core audits reject any visible reversal.
    if kind=='lash':return [(v,float(np.clip((v-.1)/.15,0,1))) for v in [0,.05,.1,.15,.25,.35,1]]
    # The replacement is below the original opaque assembly. Keep it opaque
    # through the handoff: two half-alpha strokes otherwise yield only .75
    # coverage under source-over. Retire it once white/lash opacity reaches one.
    if kind=='closed':return [(0,1),(.05,1),(.15,1),(.25,1),(.35,0),(1,0)]
    if kind=='interior':return [(0,0),(.15,0),(.25,1),(1,1)]
    raise ValueError('Unknown opacity schedule')


def install(client,op,layers,output):
    data=overview(client)['data'];items=objects(client)
    page=inspect(client,dict(scope='layers',limit=64))
    if page.get('next') is not None or page['total']!=len(page['items']):raise ValueError('Incomplete layer settings')
    layer_settings={l['id']:l for l in page['items']}
    manifest=json.loads((layers/'layer_manifest.json').read_text());art=json.loads((layers/'facial-artwork.json').read_text())
    installed=json.loads((output/'facial-installed.json').read_text())
    results=dict(version=VERSION,eyes=[],mouth={},requires_temporal_review=True)
    def mesh(role,side):
        ls=[l for l in manifest['layers'] if l['role']==role and l['side']==side]
        if len(ls)!=1:raise ValueError('Ambiguous semantic contour')
        matches=[l for l in data['layers']['items'] if l['name']==ls[0]['id']]
        ms=[o for o in items if len(matches)==1 and o.get('layerId')==matches[0]['id'] and o['target'].startswith('mesh:')]
        if len(ms)!=1:raise ValueError('Ambiguous contour mesh')
        return ls[0],ms[0]
    def topology(target):
        r=client.tool('workspace_call',dict(operation='mesh_get_topology',request=dict(target=target,limit=4096)))
        if not r.get('ok') or r['data'].get('next_offset') is not None:raise ValueError('Incomplete mesh topology')
        item=next(o for o in items if o['target']==target)
        r['data']['outer_margin']=layer_settings[item['layerId']]['mesh']['outerMargin']
        return r['data']
    def contour(image,top,upper=False,isolated=False):
        a=np.array(Image.open(image).convert('RGBA'));x,y=ink_curve(a,upper,isolated)
        yy,xx=np.nonzero(a[...,3]>0)
        # Use the inspected mesh outer margin, not a character-specific padding.
        # The rest-space
        # bounding box supplies the shared parent coordinate conversion.
        margin=top['outer_margin']
        p0=np.array([xx.min()-margin,yy.min()-margin]);p1=np.array([xx.max()+margin,yy.max()+margin])
        b=np.array(top['bounds']);q=np.column_stack((x,y))
        q=b[:2]+(q-p0)/(p1-p0)*(b[2:]-b[:2])
        return q[:,0],q[:,1]
    for side,param in [('left','ParamEyeLOpen'),('right','ParamEyeROpen')]:
        layer,lash=mesh('eyelash',side);target=lash['target'];detail=inspect(client,dict(target=target))
        if detail['axes']!={param:[0,1]}:raise ValueError('Expected fresh two-key eye mesh')
        closed=next(v for v in installed if v['feature']=='eye-'+side and v['kind']=='closed-lash')
        if closed['parent']!=lash['parentId']:raise ValueError('Closure curves need a common parent')
        closed_detail=inspect(client,dict(target=closed['target']))
        white_detail=inspect(client,dict(target=mesh('eyewhite',side)[1]['target']))
        if closed_detail['static']['masked_by'] or not all(closed_detail['static']['draw_order']<d['static']['draw_order'] for d in [detail,white_detail]):
            raise ValueError('Opaque handoff requires an unclipped replacement below source white and lash')
        st=topology(target);tt=topology(closed['target'])
        sx,sy=contour(layers/layer['rgba_path'],st,True)
        tx,ty=contour(layers/closed['path'],tt,isolated='neural_mask_path' not in closed)
        controls,error=correspondence(sx,sy,tx,ty,st['bounds'])
        # Both strokes follow the same interpolated curve during the handoff.
        # The closed stroke keeps its thickness while the source eye opens.
        for role in ['eyelash','eyewhite']:
            sl,sm=mesh(role,side);t=sm['target'];top=topology(t)
            if role=='eyelash':co=controls
            else:
                b=top['bounds'];x=np.linspace(b[0],b[2],33)
                # Collapse the white aperture onto the same curve, then hide it.
                co=np.linalg.lstsq(bernstein((x-b[0])/(b[2]-b[0])),
                    (np.interp(x,tx,ty)-b[1])/(b[3]-b[1])-.04*.5,rcond=None)[0].tolist()
            op.call('keyform_apply',dict(changes=[dict(op='copy',target=t,**{'from':{param:1}},key={param:0},channels=['geometry'])]))
            op.call('rig_deform',dict(changes=[dict(target=t,key={param:v},operations=[
                dict(type='scale',factors=[1,.08 if role=='eyelash' else .04],pivot=[0,0]),
                dict(type='curve',axis='y',controls=co)]) for v in [0]]))
            op.call('keyform_apply',dict(changes=[dict(op='set',target=t,key={param:v},channels=dict(opacity=a)) for v,a in opacity_schedule('lash' if role=='eyelash' else 'interior')]))
        _,iris=mesh('irides',side)
        b=tt['bounds'];x=np.linspace(b[0],b[2],49)
        offset=(np.interp(x,sx,sy)-np.interp(x,tx,ty))/(b[3]-b[1])
        follow=np.linalg.lstsq(bernstein((x-b[0])/(b[2]-b[0])),offset,rcond=None)[0]
        op.call('author_axis',dict(parameter=dict(id=param,min=0,max=1,default=1),shapes=[
            dict(target=closed['target'],key={},value=v,operations=[dict(type='curve',axis='y',controls=(follow*v).tolist())]) for v in [0,.35]]))
        for t,kind in [(iris['target'],'interior'),(closed['target'],'closed')]:
            op.call('keyform_apply',dict(changes=[dict(op='set',target=t,key={param:v},channels=dict(opacity=a)) for v,a in opacity_schedule(kind)]))
        results['eyes'].append(dict(side=side,source=target,closed=closed['target'],before=detail,source_topology=st,target_topology=tt,
            iris=iris['target'],white=mesh('eyewhite',side)[1]['target'],
            source_curve=[sx.tolist(),sy.tolist()],closed_curve=[tx.tolist(),ty.tolist()],controls=controls,fit_rms_parent_units=error,
            closed_before=closed_detail,white_before=white_detail,
            follow_controls=follow.tolist(),artwork_sha256=digest(layers/closed['path']),after=inspect(client,dict(target=target))))
    # Mouth: keep exact source seam visible through the start of opening while
    # the cavity grows from a line. Fade it before it can bisect the open cavity.
    # Already-open artwork retains its inspected importer branch.
    for v in installed:
        if v['kind']=='source-neutral':
            op.call('keyform_apply',dict(changes=[dict(op='set',target=v['target'],key={'ParamMouthOpenY':k},channels=dict(opacity=a)) for k,a in [(0,1),(.05,1),(.15,0),(.25,0),(1,0)]]))
        if v['kind']=='interior':
            target=v['target'];param='ParamMouthOpenY'
            # Same corner span and center at every key. Positive scale avoids
            # degenerate triangles; zero opacity makes exact closure invisible.
            for k in [0,.05,.15,.25,.5,.75,1]:
                op.call('keyform_apply',dict(changes=[dict(op='copy',target=target,**{'from':{param:1}},key={param:k},channels=['geometry'])]))
                op.call('rig_deform',dict(changes=[dict(target=target,key={param:k},operations=[dict(type='scale',factors=[1,max(.02,k)])])]))
            op.call('keyform_apply',dict(changes=[dict(op='set',target=target,key={param:k},channels=dict(opacity=a)) for k,a in [(0,0),(.05,.5),(.15,1),(1,1)]]))
            results['mouth']=dict(strategy='corner-preserving cavity scale and early seam handoff',artwork_sha256=digest(layers/v['path']))
    if not results['mouth']:results['mouth']=dict(strategy='retain-existing-open-source-mouth')
    write_json(output/'transition-correspondence.json',results)
    return results
