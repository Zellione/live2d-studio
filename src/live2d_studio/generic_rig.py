"""Role-derived PSD2Live authoring for reviewed frontal portrait candidates."""
import itertools
import json
import math
from pathlib import Path
import shutil
import fcntl
from functools import wraps
import hashlib
import io
import zipfile
from PIL import Image

from .manifest import artwork_request, load_validate, write_json, digest
from .mcp import Operations, validate_import
from .bundle import validate


def profile():
    data = json.loads(Path(__file__).with_name('portrait_profile.json').read_text())
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported portrait profile')
    for key in ('mouth_curve','brow_inner_raise'):
        if len(data[key]) != 4 or not all(math.isfinite(v) and abs(v)<=1 for v in data[key]):
            raise ValueError('Unsafe relative facial profile')
    if not all(math.isfinite(v) and 0<=v<=5 for v in data['idle_degrees'].values()):
        raise ValueError('Portrait idle amplitudes must remain modest')
    return data


def locked_editor(function):
    """Serialize creation stages sharing the one local authoring workspace."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        folder = Path(__file__).resolve().parents[2]/'.cache'
        folder.mkdir(exist_ok=True)
        with (folder/'creation-editor.lock').open('a') as lock:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('Another creation stage owns PSD2Live; resume when it finishes') from None
            return function(*args, **kwargs)
    return wrapper


def facial_plan(project, output):
    data = load_validate(project)
    write_json(output/'facial-plan.json', dict(schema_version=1,
        source_manifest_sha256=digest(Path(project)/'layer_manifest.json'),
        source_artwork='unchanged', generated_by='PSD2Live procedural import',
        blink='source eyelash/white deformation; intermediate lid skin unavailable',
        mouth='source mouth plus generated lip outlines and procedural interior; no teeth/tongue',
        smile_frown='relative curve field on inspected mouth parent',
        brows='separate relative sad/angry fields on inspected brow parents',
        concealed_face='reviewed See-through candidate; no independent anatomy claim',
        optional_blush='omitted; not needed for basic expression acceptance',
        source_layers=[dict(id=l['id'],role=l['role'],side=l['side'],
                            sha256=l['sha256']['rgba_path']) for l in data['layers']],
        limitations=['No newly painted skin eyelids','No phonemes','No full-body rig'],
        requires_visual_review=True))


def inspect(client, request):
    value = client.tool('workspace_inspect',{'request':request})
    if not value.get('ok'):
        raise RuntimeError('PSD2Live inspection failed')
    return value['data']


def overview(client):
    value = client.tool('workspace_overview',{'request':{}})
    if not value.get('ok'):
        raise RuntimeError('PSD2Live overview failed')
    for name in ('layers','deformers','parameters'):
        if value['data'][name]['total'] != len(value['data'][name]['items']):
            raise ValueError('Truncated project overview: ' + name)
    return value


def objects(client):
    found = []
    offset = 0
    while True:
        page = inspect(client,dict(scope='objects',offset=offset,limit=64))
        found.extend(page['items'])
        if page.get('next') is None:
            if len(found) != page['total']:
                raise ValueError('Truncated object inventory')
            return found
        if page['next'] <= offset:
            raise ValueError('Invalid inventory pagination')
        offset = page['next']


def targets(data, items):
    """Bind by source layer semantics and actual mesh ancestry, never opaque IDs."""
    deformers = {d['target'].split(':',1)[1]:d['target'] for d in data['deformers']['items']}
    result = {}
    for role,side in [('eyebrow','left'),('eyebrow','right'),('mouth','none')]:
        ids = {l['id'] for l in data['layers']['items'] if l['role']==role and l['side']==side}
        parents = {o.get('parentId') for o in items if o.get('layerId') in ids and o['target'].startswith('mesh:')}
        if len(parents) != 1:
            raise ValueError('Ambiguous/missing semantic parent: ' + role + ':' + side)
        parent = deformers.get(next(iter(parents)))
        if not parent or not parent.startswith('warp:'):
            raise ValueError('Unsupported semantic parent type')
        result[role+':'+side] = parent
    if len(set(result.values())) != 3:
        raise ValueError('Facial roles unexpectedly share a deformer')
    return result


def axis_steps(target, axes, ident, shapes):
    if ident in axes:
        raise ValueError('Fresh rig unexpectedly contains generated facial axis')
    keys = [dict(zip(axes,v)) for v in itertools.product(*axes.values())]
    if len(keys) > 256:
        raise ValueError('Unsupported facial topology; refusing unbounded key expansion')
    forms = [dict(target=target,key=key,value=value,operations=ops) for key in keys for value,ops in shapes]
    parameter = dict(id=ident,name=ident.removeprefix('Param'),min=min(0,*[v for v,_ in shapes]),max=1,default=0)
    return [dict(operation='author_axis',request=dict(parameter=parameter,shapes=forms[i:i+54]))
            for i in range(0,len(forms),54)]


def rig_recipe(bindings, details):
    config = profile()
    steps = []
    mouth = bindings['mouth:none']
    steps += axis_steps(mouth, details[mouth]['axes'], 'ParamMouthCurve', [
        (1,[dict(type='curve',axis='y',controls=config['mouth_curve'])]),
        (-1,[dict(type='curve',axis='y',controls=[-v for v in config['mouth_curve']])])])
    for side in ('left','right'):
        target = bindings['eyebrow:'+side]
        controls = config['brow_inner_raise'] if side=='left' else [-v for v in config['brow_inner_raise']]
        # Positive raises the inner end (sad); negative lowers it (angry).
        steps += axis_steps(target, details[target]['axes'], 'ParamBrowEmotion', [
            (1,[dict(type='curve',axis='y',controls=controls)]),
            (-1,[dict(type='curve',axis='y',controls=[-x for x in controls])])])
    return steps


def save(op, output):
    op.call('project_save_as',dict(path=str(output/'character.psd2live')))


def archived_art(project):
    with zipfile.ZipFile(project) as archive:
        return {name:hashlib.sha256(archive.read(name)).hexdigest()
                for name in archive.namelist() if name.startswith('assets/') and name.endswith('.png')}


def verify_source_art(layers, project):
    """PNG encodings may differ; compare all decoded source RGBA exactly."""
    def rgba_hash(image):
        rgba=image.convert('RGBA')
        return (rgba.size,hashlib.sha256(rgba.tobytes()).hexdigest())
    with zipfile.ZipFile(project) as archive:
        available={rgba_hash(Image.open(io.BytesIO(archive.read(name)))) for name in archive.namelist()
                   if name.startswith('assets/') and name.endswith('.png')}
    data=load_validate(layers)
    missing=[layer['id'] for layer in data['layers']
             if rgba_hash(Image.open(Path(layers)/layer['rgba_path'])) not in available]
    if missing:
        raise ValueError('Source layers missing/changed in editor archive: '+', '.join(missing))
    return dict(status='pass',exact_source_layers=len(data['layers']),
                caveat='Exact imported RGBA, including marked generated hidden pixels; original input preservation is measured separately.')


def open_stage(client, predecessor, output):
    op = Operations(client,output)
    # Save current workspace to a new local snapshot; never discard unsaved edits.
    current = inspect(client,{'scope':'project'})
    if current.get('loaded'):
        op.call('project_save_as',dict(path=str(output/'editor-snapshot.psd2live')))
    op.call('project_open',dict(path=str(predecessor/'character.psd2live')))
    return op


@locked_editor
def create_project(client, project, output):
    request = artwork_request(project)
    write_json(output/'artwork-request.json',request)
    op = Operations(client,output)
    if inspect(client,{'scope':'project'}).get('loaded'):
        op.call('project_save_as',dict(path=str(output/'editor-snapshot.psd2live')))
    op.call('project_create_artwork',request)
    view = overview(client)
    write_json(output/'overview.json',view)
    write_json(output/'import-validation.json',validate_import(request,view))
    save(op,output)
    write_json(output/'source-art.json',verify_source_art(project,output/'character.psd2live'))


@locked_editor
def author_rig(client, predecessor, output):
    op = open_stage(client,predecessor,output)
    data = overview(client)['data']
    items = objects(client)
    binding = targets(data,items)
    details = {target:inspect(client,dict(target=target)) for target in binding.values()}
    steps = rig_recipe(binding,details)
    write_json(output/'inspection.json',dict(overview=data,objects=items,bindings=binding,details=details))
    write_json(output/'recipe.json',steps)
    write_json(output/'profile.json',profile())
    for step in steps:
        op.call(step['operation'],step['request'])
    save(op,output)


def animation_recipe(parameters):
    amplitude = profile()['idle_degrees']
    params = {p['id']:p for p in parameters}
    required = {'ParamMouthCurve','ParamBrowEmotion','ParamEyeLOpen','ParamEyeROpen',
                'ParamMouthOpenY','ParamAngleX','ParamAngleY','ParamAngleZ','ParamBreath'}
    if required - params.keys():
        raise ValueError('Missing authored animation parameters')
    expressions = {
        'neutral':(0,0,1,1,0), 'happy':(1,0,.8,.8,.25),
        'sad':(-1,1,.85,.85,0), 'angry':(-.7,-1,.7,.7,.08),
        'surprised':(0,0,1,1,.8), 'confused':(-.25,.2,1,.7,.05),
        'embarrassed':(.4,.2,.75,.75,.12)}
    ids = ['ParamMouthCurve','ParamBrowEmotion','ParamEyeLOpen','ParamEyeROpen','ParamMouthOpenY']
    def bounded(ident,value):
        p = params[ident]
        if not p['min'] <= value <= p['max']:
            raise ValueError('Expression/motion exceeds inspected parameter range: '+ident)
        return value
    steps = []
    for name,values in expressions.items():
        entries = [dict(parameter=k,blend='MULTIPLY' if 'Eye' in k else 'ADD',value=bounded(k,v)) for k,v in zip(ids,values)]
        steps.append(dict(operation='expression_put',request=dict(expression=dict(
            id='create_'+name,name=name,fade_in=.35,fade_out=.35,entries=entries))))
    for preset in ('Idle','Blink','Nod','Shake'):
        steps.append(dict(operation='motion_preset',request=dict(builtin=preset,action='update',disabled=True)))
    steps += [dict(operation='motion_create',request=dict(id='createIdle',name='createIdle')),
              dict(operation='motion_properties',request=dict(id='createIdle',duration=12,loop=True,fps=30,fade_in=.5,fade_out=.5))]
    poses = {}
    for t in range(13):
        poses[t] = dict(ParamAngleX=amplitude['x']*math.sin(t*math.pi/6),ParamAngleY=amplitude['y']*math.sin(t*math.pi/3),
                        ParamAngleZ=amplitude['z']*math.sin(t*math.pi/6),ParamBreath=.2*(1-math.cos(t*math.pi/2)))
    for onset in (2.5,6.5,10.5):
        for dt,v in [(0,1),(.1,0),(.16,0),(.32,1)]:
            poses.setdefault(onset+dt,{}).update(ParamEyeLOpen=v,ParamEyeROpen=v)
    for t in (0,12):
        poses[t].update(ParamEyeLOpen=1,ParamEyeROpen=1)
    for t,values in sorted(poses.items()):
        steps.append(dict(operation='motion_pose',request=dict(id='createIdle',time=t,
            values={k:bounded(k,round(v,6)) for k,v in values.items()})))
    return steps


@locked_editor
def author_animation(client, predecessor, output):
    op = open_stage(client,predecessor,output)
    data = overview(client)['data']
    listed = client.tool('workspace_call',dict(operation='expression_list',request={}))
    if not listed.get('ok'):
        raise RuntimeError('Cannot inspect default expressions')
    write_json(output/'default-expressions.json',listed)
    for expression in listed['data']['expressions']:
        op.call('expression_delete',dict(id=expression['id']))
    steps = animation_recipe(data['parameters']['items'])
    write_json(output/'recipe.json',steps)
    for step in steps:
        op.call(step['operation'],step['request'])
    save(op,output)


@locked_editor
def export_model(client, predecessor, output):
    op = open_stage(client,predecessor,output)
    save(op,output)
    if archived_art(predecessor/'character.psd2live') != archived_art(output/'character.psd2live'):
        raise ValueError('Archived source artwork changed during export preparation')
    op.call('project_export_psd',dict(path=str(output/'character.psd'),scale=1))
    op.call('project_open',dict(path=str(output/'character.psd2live')))
    op.call('project_export_model',dict(output_directory=str(output/'export')))
    models = list((output/'export').glob('*.model3.json'))
    if len(models) != 1 or validate(models[0])['status'] != 'pass':
        raise ValueError('Invalid Cubism export')
    shutil.copytree(output/'export',output/'runtime')
    model = output/'runtime'/models[0].name
    data = json.loads(model.read_text())
    refs = data['FileReferences']
    entries = [m for group in refs.get('Motions',{}).values() for m in group if m['File'].endswith('.createIdle.motion3.json')]
    if len(entries) != 1:
        raise ValueError('Missing/ambiguous authored idle')
    refs['Motions'] = {'Idle':entries}
    refs['Expressions'] = [e for e in refs['Expressions'] if '.create_' in e['File']]
    if len(refs['Expressions']) != 7:
        raise ValueError('Expected seven generated expressions')
    write_json(model,data)
    write_json(output/'integrity.json',validate(model))
