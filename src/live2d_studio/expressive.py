"""Phase 3.1 Girl2-only facial edits; the accepted Phase 3 recipe is immutable."""
import itertools
from .animation import expression

VALUES = {
    'neutral': (0,0,0,1,1,0,0,0),
    'happy': (0,.45,.45,.8,.8,1,.32,0),
    'sad': (0,-.15,-.15,.82,.82,-1,0,0),
    'angry': (1,-.75,-.75,.6,.6,-1,.08,0),
    'surprised': (0,1,1,1,1,0,.85,0),
    'confused': (.1,.9,-.5,1,.72,-.4,.08,3),
    'embarrassed': (-.25,.15,.15,.68,.68,.75,.12,-2),
}


def recipe():
    axes={'ParamAngleX':[-45,0,45],'ParamAngleY':[-30,0,30],'ParamBodyLean':[-10,0,10]}
    keys=[dict(zip(axes,v)) for v in itertools.product(*axes.values())]
    steps=[]
    shapes=[]
    for key in keys:
        for value,controls in [(1,[-.12,.6,.6,-.12]),(-1,[.18,-.8,-.8,.18])]:
            shapes.append(dict(target='warp:DeformMouthShapeBoth',key=key,value=value,
                operations=[dict(type='curve',axis='y',controls=controls)]))
    steps.append(dict(operation='author_axis',request=dict(parameter=dict(id='ParamMouthCurve',name='Smile / frown',min=-1,max=1,default=0),shapes=shapes)))
    # A rounded surprised mouth retains the same lips and interior at every opening.
    shapes=[dict(target='warp:DeformMouthShapeBoth',key=dict(key,ParamMouthCurve=curve),value=1,
        operations=[dict(type='scale',factors=[.65,1.3])]) for key in keys for curve in [-1,0,1]]
    # API limit 64 shapes: use the same axis in two reviewed batches.
    for i in range(0,len(shapes),54):
        steps.append(dict(operation='author_axis',request=dict(parameter=dict(id='ParamMouthRound',name='Rounded mouth',min=0,max=1,default=0),shapes=shapes[i:i+54])))
    for side in ['L','R']:
        target='warp:DeformBrowShape'+side
        changes=[dict(target=target,key=dict(key,ParamBrowMood=mood),operations=[dict(type='rotate',degrees=(-3 if side=='L' else 3)*mood)]) for key in keys for mood in [-1,1]]
        steps.append(dict(operation='rig_deform',request=dict(changes=changes)))
        # Separate sad axis preserves the other six tested expressions. The original
        # sad endpoint steepened the angry source brow; a vertical field raises the
        # inner ends while preserving eyebrow width, unlike a large rotation.
        controls=[-.65,-.217,.217,.65] if side=='R' else [.65,.217,-.217,-.65]
        shapes=[dict(target=target,key=dict(key,ParamBrowMood=mood),value=1,
            operations=[dict(type='curve',axis='y',controls=controls)]) for key in keys for mood in [-1,0,1]]
        for i in range(0,len(shapes),54):
            steps.append(dict(operation='author_axis',request=dict(parameter=dict(id='ParamBrowSad',name='Relaxed sad brow',min=0,max=1,default=0),shapes=shapes[i:i+54])))
    for name,values in VALUES.items():
        exp=expression(name,values)
        extra={'ParamMouthCurve':{'happy':1,'sad':-1,'angry':-.65,'confused':-.35,'embarrassed':.45}.get(name,0),
               'ParamMouthRound':1 if name=='surprised' else 0,
               'ParamBlush':1 if name=='embarrassed' else 0,
               'ParamBrowSad':1 if name=='sad' else 0}
        exp['entries'] += [dict(parameter=k,blend='ADD',value=v) for k,v in extra.items()]
        steps.append(dict(operation='expression_put',request=dict(expression=exp)))
    return steps


def blush_png(output):
    """Original procedural cheek tint, native alpha; no source pixels modified."""
    import numpy as np
    from PIL import Image
    y,x=np.mgrid[:1000,:1000]
    alpha=np.zeros((1000,1000))
    for cx,cy in [(386,350),(527,350)]:
        alpha=np.maximum(alpha,70*np.exp(-2*((x-cx)/25)**2-2*((y-cy)/12)**2))
    rgba=np.zeros((1000,1000,4),dtype=np.uint8)
    rgba[:,:,:3]=[229,100,111]
    rgba[:,:,3]=np.rint(alpha).astype(np.uint8)
    Image.fromarray(rgba).save(output)
