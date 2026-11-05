"""Optional coordinated sparse-source mouth surfaces, authored through local MCP.

All distances come from inspected raster support. Source/cavity PNGs are immutable;
shape keys replace the former parent smile and mesh displeasure fields in a copy.
"""
import itertools
import json
import numpy as np
from PIL import Image
from .emotion_authoring import bounds, mouth_baseline
from .transition_authoring import bernstein
from .generic_rig import inspect, overview, objects, targets, axis_steps
from .manifest import digest, write_json

OPENINGS = [0, .05, .1, .15, .25, .5, .75, 1]
AXES = {'ParamMouthCurve': [-1, 0, 1], 'ParamMouthRound': [0, 1],
        'ParamMouthTension': [0, 1], 'ParamMouthOpenY': OPENINGS}
POSES = {
    'neutral': (0, 0, 0, 0, 0, 0),
    'happy': (1, 0, 0, 0, .42, .15),
    'sad': (-1, 0, 0, 0, 0, 0),
    'angry': (0, 0, 1, 0, 0, .1),
    'confused': (0, 1, 0, .08, .35, -.25),
    'surprised': (0, 1, 0, 0, .85, 0),
    'embarrassed': (.5, 0, .1, -.65, 0, -.7),
}


def expression_entries(name, entries):
    values = dict(zip(['ParamMouthCurve', 'ParamMouthRound', 'ParamMouthTension',
                      'ParamMouthSkew', 'ParamMouthOpenY', 'ParamMouthWidth'], POSES[name]))
    result = [dict(e, value=values.pop(e['parameter'], e['value'])) for e in entries
              if e['parameter'] != 'ParamMouthDispleasure']
    result += [dict(parameter=k, value=v, blend='ADD') for k, v in values.items()]
    return result


def pose_geometry(fit, width, center, curve, rounded, tension):
    """Absolute desired seam in source x coordinates, y down; never assumed sign.

    Positive curvature has higher corners (smile); negative lowers them (sad).
    Roundness removes the source smile; tension flattens and compresses the seam.
    Width and height are coupled to these supported shapes, not redundant axes.
    """
    target = center + width * (np.array([-.13, .13, .13, -.13]) if curve >= 0
                               else np.array([.075, -.075, -.075, .075]))
    seam = fit * (1-abs(curve)) + target * abs(curve)
    seam = seam * (1-rounded) + center * rounded
    tense = center + width * np.array([.012, -.004, -.004, .012])
    seam = seam * (1-tension) + tense * tension
    sx = (1-.50*rounded)*(1-.22*tension)*(1-.10*max(-curve, 0))
    return seam, sx


def surface_operations(kind, raster_bounds, mouth_bounds, fit, center, curve, rounded, tension, opening):
    """Compose a positive-scale surface and y shear in fixed input bounds.

    Cavity and source use different original baselines, but exactly the same
    desired seam/corners. The cavity height is bounded for every opening 0..1.
    """
    b = np.asarray(raster_bounds, float); mb = np.asarray(mouth_bounds, float)
    w, h = b[2:]-b[:2]; width = mb[2]-mb[0]
    seam, sx = pose_geometry(fit, width, center, curve, rounded, tension)
    x = np.linspace(b[0], b[2], 41); u = (x-mb[0])/width
    desired = bernstein(u) @ seam
    if kind == 'source-neutral':
        original = bernstein(u) @ fit
        sy = 1
    else:
        original = np.full_like(x, (b[1]+b[3])/2)
        sy = max(.02, opening) * (1+.6*rounded) * (1-.38*tension)
    # Scale about the source mouth centre, then bend in original x coordinates.
    # rig_deform uses fixed input bounds even after earlier operations.
    pivot_y = (center-b[1])/h
    after_scale = center + sy*(original-center)
    co = np.linalg.lstsq(bernstein((x-b[0])/w), (desired-after_scale)/h, rcond=None)[0]
    return [dict(type='scale', factors=[sx, sy], pivot=[((mb[0]+mb[2])/2-b[0])/w, pivot_y]),
            dict(type='curve', axis='y', controls=co.tolist())]


def install(client, op, layers, output):
    data=overview(client)['data']; items=objects(client); bindings=targets(data,items)
    manifest=json.loads((layers/'layer_manifest.json').read_text())
    art=json.loads((layers/'facial-artwork.json').read_text())
    variants=[v for v in art['alternatives'] if v['feature']=='mouth' and v['kind'] in ('source-neutral','interior')]
    if sorted(v['kind'] for v in variants)!=['interior','source-neutral']:
        raise ValueError('Mouth redesign requires one explicit sparse-source neutral and cavity')
    source=Image.open(layers/next(v['path'] for v in variants if v['kind']=='source-neutral')).convert('RGBA')
    fit,width,center=mouth_baseline(np.asarray(source)); mb=bounds(source)
    settings=inspect(client,dict(scope='layers',limit=64))
    if settings.get('next') is not None:raise ValueError('Incomplete layer settings')
    evidence=dict(version='coordinated-mouth-v1', source_fit=fit.tolist(),source_bounds=mb.tolist(),
                  center=center,parameters=data['parameters']['items'],parent=inspect(client,dict(target=bindings['mouth:none'])),
                  surfaces=[],poses=POSES,source_pixels_changed=False,new_raster_artwork=False)
    surfaces=[]
    for variant in variants:
        if digest(layers/variant['path'])!=variant['sha256']:raise ValueError('Changed source/cavity artwork')
        lids={l['id'] for l in data['layers']['items'] if l['name']=='facial-mouth-'+variant['kind']}
        matches=[o for o in items if o.get('layerId') in lids and o['target'].startswith('mesh:')]
        if len(matches)!=1 or matches[0]['parentId']!=bindings['mouth:none'].split(':',1)[1]:
            raise ValueError('Mouth alternatives must share inspected mouth parent')
        item=matches[0];t=item['target'];detail=inspect(client,dict(target=t))
        top=client.tool('workspace_call',dict(operation='mesh_get_topology',request=dict(target=t,limit=4096)))['data']
        if top.get('next_offset') is not None:raise ValueError('Incomplete mouth topology')
        margin=next(l for l in settings['items'] if l['id']==item['layerId'])['mesh']['outerMargin']
        b=bounds(Image.open(layers/variant['path']))+np.array([-margin,-margin,margin,margin])
        surfaces.append((variant,t,b))
        evidence['surfaces'].append(dict(**variant,target=t,before=detail,topology=top,raster_bounds=b.tolist()))
    write_json(output/'mouth-inspection.json',evidence)
    # Collapse conflicting legacy fields at neutral, retaining all head/body keys.
    for ident in ['ParamMouthCurve','ParamMouthDispleasure','ParamMouthSkew']:
        op.call('parameter_delete',dict(parameter_id=ident))
    for ident,values in AXES.items():
        if ident=='ParamMouthOpenY':continue
        op.call('parameter_create',dict(parameter_id=ident,name=ident.removeprefix('Param'),min=min(values),max=max(values),default=0))
    recipe=[]
    for variant,t,b in surfaces:
        geometry_axes = AXES if variant['kind']=='interior' else {k:v for k,v in AXES.items() if k!='ParamMouthOpenY'}
        allkeys=[dict(zip(geometry_axes,v)) for v in itertools.product(*geometry_axes.values())]
        edits=[]
        for key in allkeys:
            c,r,tension=[key[k] for k in list(AXES)[:3]];o=key.get('ParamMouthOpenY',0)
            ops=surface_operations(variant['kind'],b,mb,fit,center,c,r,tension,o)
            # Reset immediately before each deformation. Copying equal forms can
            # be optimized away by the editor, so a later missing key can otherwise
            # start from an already deformed neighbour and accumulate curvature.
            edits.append(dict(operation='keyform_apply',request=dict(changes=[dict(op='reset',target=t,key=key,to='rest')])))
            if not (variant['kind']=='source-neutral' and c==r==tension==0):
                edits.append(dict(operation='rig_deform',request=dict(changes=[dict(target=t,key=key,operations=ops)])))
        for i in range(0,len(edits),64):
            op.call('workspace_apply_edits',dict(edits=edits[i:i+64],summary='Independent rest-derived mouth keys'))
        alpha=[]
        for o in OPENINGS:
            a=float(np.clip((.15-o)/.10,0,1)) if variant['kind']=='source-neutral' else float(np.clip(o/.1,0,1))
            alpha.append(dict(op='set',target=t,key={'ParamMouthOpenY':o},channels=dict(opacity=a)))
        op.call('keyform_apply',dict(changes=alpha))
        recipe.append(dict(target=t,edits=edits,opacity=alpha))
        evidence['surfaces'][len(recipe)-1]['after']=inspect(client,dict(target=t))
    # A source-width-relative asymmetric shear on each visible surface; the
    # previous broad parent field barely changed the tiny mouth. Independent width
    # belongs on the common parent so source and cavity always contract together.
    for variant,t,b in surfaces:
        x=np.linspace(b[0],b[2],41)
        offset=((x-(mb[0]+mb[2])/2)/width)*.11*width/(b[3]-b[1])
        co=np.linalg.lstsq(bernstein((x-b[0])/(b[2]-b[0])),offset,rcond=None)[0]
        steps=axis_steps(t,inspect(client,dict(target=t))['axes'],'ParamMouthSkew',[
            (v,[dict(type='curve',axis='y',controls=(co*v).tolist())]) for v in [-1,1]])
        for step in steps:op.call(step['operation'],step['request'])
    parent=bindings['mouth:none']
    for step in axis_steps(parent,inspect(client,dict(target=parent))['axes'],'ParamMouthWidth',[
            (-1,[dict(type='scale',factors=[.65,1])]),(1,[dict(type='scale',factors=[1.15,1])])]):
        op.call(step['operation'],step['request'])
    write_json(output/'mouth-rig-recipe.json',recipe)
    write_json(output/'mouth-inspection.json',evidence)
