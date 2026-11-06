"""Optional geometry-inspected body motion. Never infers limb anatomy from names."""
import itertools
import json
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from .generic_rig import (overview, objects, inspect, open_stage, save, export_model,
                          locked_editor, archived_art, verify_source_art)
from .manifest import load_validate, write_json, digest
from .mcp import MCP
from .stages import verify
from .bundle import validate

HEAD_ROLES = {'face', 'ears', 'nose', 'mouth', 'eyebrow', 'eyelash', 'eyewhite', 'irides', 'front_hair', 'back_hair'}


def bindings(view, items, details):
    """Find shared ancestors by topology, with required semantic coverage."""
    layers = {l['id']: l for l in view['layers']['items']}
    meshes = [o for o in items if o['target'].startswith('mesh:')]
    role_meshes = {}
    for o in meshes:
        l = layers.get(o.get('layerId'), {})
        role_meshes.setdefault(l.get('role', 'unknown'), []).append(o['target'])
    if len(role_meshes.get('face', [])) != 1:
        raise ValueError('Body motion needs one inspected face')
    chains = {o['target']: [d['target'] for d in details[o['target']].get('inherited', [])] for o in meshes}
    head_meshes = [m for role, ms in role_meshes.items() if role in HEAD_ROLES for m in ms]
    candidates = [t for t in chains[role_meshes['face'][0]] if t.startswith('warp:')
                  and all(t in chains[m] for m in head_meshes)
                  and {'ParamAngleX', 'ParamAngleY'} <= details[t]['axes'].keys()]
    if not candidates:
        raise ValueError('No common head/face/hair XY parent; refusing partial head motion')
    head = candidates[0]
    if any(head in chains[m] for r in ('topwear', 'handwear', 'legwear') for m in role_meshes.get(r, [])):
        raise ValueError('Head parent also owns body/limbs')
    body = [t for t in chains[role_meshes['face'][0]] if 'ParamBreath' in details[t].get('axes', {})]
    rotations = [t for t in chains[role_meshes['face'][0]] if t.startswith('rotation:') and 'ParamAngleZ' in details[t]['axes']]
    if len(body) != 1 or len(rotations) != 1:
        raise ValueError('Missing or ambiguous body breath/head tilt binding')
    hair = {}
    for role, parameter in [('front_hair', 'ParamHairFront'), ('back_hair', 'ParamHairBack')]:
        matches = {t for m in role_meshes.get(role, []) for t in chains[m] if parameter in details[t].get('axes', {})}
        if len(matches) == 1:
            hair[role] = dict(target=next(iter(matches)), parameter=parameter)
    return dict(head=head, rotation=rotations[0], body=body[0], hair=hair, roles=role_meshes)


def anatomy_report(folder):
    """Source support inventory. Components do not establish arm identity/joints."""
    data = load_validate(folder)
    regions = []
    for layer in data['layers']:
        if layer['role'] not in HEAD_ROLES | {'neck', 'topwear', 'handwear', 'arm', 'hand', 'upper_arm', 'forearm', 'shoulder'}:
            continue
        alpha = np.asarray(Image.open(folder / layer['rgba_path']).convert('RGBA'))[:, :, 3] > 0
        labels, _ = ndimage.label(alpha)
        sizes = np.bincount(labels.ravel())[1:]
        regions.append(dict(id=layer['id'], role=layer['role'], side=layer['side'],
            bounds=[layer['x'], layer['y'], layer['width'], layer['height']],
            components=sorted((int(n) for n in sizes if n >= 16), reverse=True),
            observed_pixels=layer.get('observed_pixels'), generated_pixels=layer.get('generated_pixels'),
            ownership_status=layer.get('ownership_status')))
    limbs = [r for r in regions if r['role'] in {'handwear', 'arm', 'hand', 'upper_arm', 'forearm', 'shoulder'}]
    return dict(regions=regions, independent_arms=False, limb_candidates=limbs,
        reason='No reviewed joint landmarks, bilateral ownership and occluded joint backing. Connected components or side labels alone cannot certify articulation.',
        fallback='Keep original pixels and shared body attachment; no arm or hand gestures.',
        generated_hidden_anatomy_verified=False)


def keys(points):
    """Horizontal Bezier tangents: calm rests and equal loop-end derivatives."""
    result = []
    for t, v in points:
        result.append(dict(time=t, value=v, interpolation='BEZIER',
                           **{'in': [1/3, 0], 'out': [1/3, 0]}))
    return result


def motion_clips(parameters):
    channels = {
        'ParamAngleX': [(0,0),(1.2,0),(3.4,8),(5,8),(7.5,-5),(9,-5),(11.8,6),(13,6),(15.3,0),(16,0)],
        'ParamAngleY': [(0,0),(2,0),(3.2,-3),(4.4,1),(6,1),(8.2,4),(10,4),(11.6,-2),(13,-2),(15.4,0),(16,0)],
        'ParamAngleZ': [(0,0),(1.5,0),(4,2.5),(6,2.5),(8.8,-2.5),(10,-2.5),(12.8,1),(14,1),(15.5,0),(16,0)],
        'ParamBodyAngleX': [(0,0),(2,0),(5,-.8),(7,-.8),(10,1),(12,1),(15,0),(16,0)],
        'ParamBodyAngleZ': [(0,0),(2,0),(5,-.35),(7,-.35),(10,.4),(12,.4),(15,0),(16,0)],
        'ParamBreath': [(0,0),(2,.65),(4.5,0),(6.7,.55),(9,0),(11.3,.7),(13.6,0),(14.7,.25),(16,0)],
    }
    # Blink timing stays separate from head/body timing, and expression multipliers.
    blink = [(0,1)]
    for onset in (2.2,6.4,10.8,14.1):
        blink += [(onset,1),(onset+.1,0),(onset+.16,0),(onset+.32,1)]
    blink += [(16,1)]
    channels.update(ParamEyeLOpen=blink, ParamEyeROpen=blink)
    clips=[dict(id='createIdle',name='createIdle',duration=16,loop=True,fps=30,fade_in=.6,fade_out=.6,
                curves=[dict(parameter=k,keys=keys(v)) for k,v in channels.items() if k in parameters])]
    for ident, group, curves in [
        ('bodyNod','Nod', {'ParamAngleY':[(0,0),(.4,1),(1,-6),(1.6,1),(2.4,0),(2.8,0)]}),
        ('bodyQuestion','Question', {'ParamAngleZ':[(0,0),(.7,-4),(1.4,-4),(2.4,0),(2.8,0)],
                                    'ParamAngleX':[(0,0),(.7,4),(1.4,4),(2.4,0),(2.8,0)]})]:
        clips.append(dict(id=ident,name=ident,duration=2.8,loop=False,fps=30,fade_in=.4,fade_out=.6,
                          curves=[dict(parameter=k,keys=keys(v)) for k,v in curves.items() if k in parameters]))
    for clip in clips:
        for curve in clip['curves']:
            p=parameters[curve['parameter']]
            if any(not p['min']<=k['value']<=p['max'] for k in curve['keys']):
                raise ValueError('Motion outside inspected range')
    return clips


def geometry_recipe(binding, details):
    head=binding['head'];axes=details[head]['axes']
    coordinates=[dict(zip(axes,v)) for v in itertools.product(*axes.values())]
    if len(coordinates)>256:raise ValueError('Unsupported head key expansion')
    # Translation is normalized to the inspected head cage, shared by every feature
    # and both hair groups; existing local apparent-turn fields stay intact.
    changes=[]
    for key in coordinates:
        x=key.get('ParamAngleX',0)/max(abs(v) for v in axes['ParamAngleX'])
        y=key.get('ParamAngleY',0)/max(abs(v) for v in axes['ParamAngleY'])
        if x or y:changes.append(dict(target=head,key=key,operations=[dict(type='translate',delta=[.08*x,-.04*y])]))
    return changes


@locked_editor
def author(client, predecessor, layers, output):
    output.mkdir(parents=True,exist_ok=False)
    op=open_stage(client,predecessor,output)
    view=overview(client)['data'];items=objects(client)
    if any(m['id'] in ('bodyNod','bodyQuestion') for m in view['motions']['items']):
        raise ValueError('Body motion already authored; use preserve instead of applying twice')
    from .performance import expressions, assert_expressions_preserved
    expression_before=expressions(client)
    write_json(output/'expressions-before.json',expression_before)
    details={o['target']:inspect(client,dict(target=o['target'])) for o in items}
    binding=bindings(view,items,details)
    report=dict(overview=view,objects=items,details=details,bindings=binding,anatomy=anatomy_report(layers))
    write_json(output/'body-inspection.json',report)
    recipe=geometry_recipe(binding,details);write_json(output/'body-recipe.json',recipe)
    for start in range(0,len(recipe),64):op.call('rig_deform',dict(changes=recipe[start:start+64]))
    # Retain the existing pinned-root hair fields and distinct pendulum timing.
    # A bounded output gain makes their response visible at portrait scale.
    physics=[]
    for role,hair in binding['hair'].items():
        groups=[g for g in view['physics']['items'] if g['outputs']==[hair['parameter']]]
        if len(groups)!=1:raise ValueError('Missing/ambiguous hair physics output')
        change=dict(id=groups[0]['id'],output_scale=3.2 if role=='front_hair' else 5.0)
        physics.append(change);op.call('physics_put',change)
    write_json(output/'body-physics.json',physics)
    clips=motion_clips({p['id']:p for p in view['parameters']['items']})
    write_json(output/'body-motions.json',clips)
    for clip in clips:op.call('motion_put',dict(clip=clip))
    assert_expressions_preserved(expression_before,expressions(client))
    write_json(output/'expressions.json',expression_before)
    if (predecessor/'mouth-inspection.json').is_file():
        shutil.copyfile(predecessor/'mouth-inspection.json',output/'mouth-inspection.json')
        write_json(output/'composition-inspection.json',dict(overview=overview(client)['data'],objects=items,
            details={o['target']:inspect(client,dict(target=o['target'])) for o in items}))
    save(op,output)
    if archived_art(predecessor/'character.psd2live')!=archived_art(output/'character.psd2live'):
        raise ValueError('Body authoring changed raster artwork')
    write_json(output/'source-art.json',verify_source_art(layers,output/'character.psd2live'))
    # This PSD2Live build leaves a dirty flag after saving custom Bezier clips.
    # The complete candidate is safely archived. Restore the predecessor history
    # node before reopening that archive for independent export verification.
    op.call('history_checkout',dict(node_id=view['history_node_id']))
    return report


def prepare(baseline, output, endpoint='http://127.0.0.1:23871/mcp'):
    baseline=Path(baseline).resolve();output=Path(output).resolve()
    if output.is_relative_to(baseline):
        raise ValueError('Body output must be outside the preserved predecessor run')
    root=baseline
    seen=set()
    while not (root/'creation.json').is_file():
        if root in seen or len(seen)>8:raise ValueError('Cyclic/unsupported experiment ancestry')
        seen.add(root)
        exp=json.loads((root/'experiment.json').read_text())
        root=Path(exp['baseline']).resolve()
    state=json.loads((root/'creation.json').read_text())
    for stage in state['stages'].values():verify(root/stage['directory'],stage['files'])
    if baseline==root:
        predecessor=root/state['stages']['animation']['directory']
        layers=root/state['stages']['facial']['directory']/'layers'
    else:
        exp=json.loads((baseline/'experiment.json').read_text())
        predecessor=baseline/'authoring';layers=Path(exp['layers']).resolve()
        load_validate(layers)
    output.mkdir(parents=True,exist_ok=False)
    frozen={str(f.relative_to(baseline)):digest(f) for f in baseline.rglob('*') if f.is_file()}
    write_json(output/'predecessor-inventory.json',frozen)
    client=MCP(endpoint);report=author(client,predecessor,layers,output/'authoring')
    (output/'export').mkdir();export_model(client,output/'authoring',output/'export')
    runtime=output/'export/runtime';model=next(runtime.glob('*.model3.json'))
    data=json.loads(model.read_text());raw=json.loads(next((output/'export/export').glob('*.model3.json')).read_text())
    entries=[m for group in raw['FileReferences']['Motions'].values() for m in group]
    for group,ident in [('Nod','bodyNod'),('Question','bodyQuestion')]:
        chosen=[m for m in entries if m['File'].endswith('.'+ident+'.motion3.json')]
        if len(chosen)!=1:raise ValueError('Missing gesture export '+group)
        data['FileReferences']['Motions'][group]=chosen
    data['StudioBody']={'version':1,'arms':'static shared attachment','gestures':{'Nod':'Small head nod','Question':'Questioning head tilt'},'idle_seconds':16}
    write_json(model,data)
    integrity=validate(model)
    write_json(output/'export/integrity.json',integrity)
    if integrity['status']!='pass':raise ValueError('Body runtime references failed')
    for f,h in frozen.items():
        if digest(baseline/f)!=h:raise ValueError('Predecessor changed: '+f)
    write_json(output/'experiment.json',dict(baseline=str(baseline),layers=str(layers),model=str(model),review='needs-user-visual-review',promotion=False))
    return dict(model=str(model),arms=report['anatomy']['fallback'])
