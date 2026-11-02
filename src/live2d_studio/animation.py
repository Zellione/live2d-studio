"""Girl2 animation recipe. No artwork generation or production installation."""
import itertools
import json
import math
from pathlib import Path

LABELS = 'admiration amusement anger annoyance approval caring confusion curiosity desire disappointment disapproval disgust embarrassment excitement fear gratitude grief joy love nervousness optimism pride realization relief remorse sadness surprise neutral'.split()
EXPRESSIONS = {
    # mood, left/right brow height, left/right eye factor, mouth form, mouth offset, Z
    'neutral': (0, 0, 0, 1, 1, 0, 0, 0),
    'happy': (0, .35, .35, .8, .8, .85, .1, 0),
    'sad': (-1, -.25, -.25, .85, .85, -.65, 0, 0),
    'angry': (1, -.55, -.55, .72, .72, -.5, 0, 0),
    'surprised': (0, .8, .8, 1, 1, -.15, .3, 0),
    'confused': (.15, .65, -.15, 1, .7, -.2, 0, 2),
    'embarrassed': (-.35, .15, .15, .65, .65, .5, 0, -2),
}

def expression(name, values):
    ids = ['ParamBrowMood','ParamBrowLY','ParamBrowRY','ParamEyeLOpen','ParamEyeROpen',
           'ParamMouthForm','ParamMouthOpenY','ParamAngleZ']
    return dict(id='rp_'+name,name=name,fade_in=.45,fade_out=.45,entries=[
        dict(parameter=k,blend='MULTIPLY' if 'Eye' in k else 'ADD',value=v)
        for k,v in zip(ids,values)])


def recipe(brow_axes):
    """Axes come from workspace_inspect, never from another character's coordinates."""
    steps=[]
    for side,axes in brow_axes.items():
        shapes=[]
        for values in itertools.product(*axes.values()):
            for mood in [-1,1]:
                shapes.append(dict(target='warp:DeformBrowShape'+side,value=mood,
                    key=dict(zip(axes,values)),operations=[dict(type='rotate',degrees=(-18 if side=='L' else 18)*mood)]))
        if len(shapes)>64:raise ValueError('Brow topology exceeds reviewed author_axis batch')
        steps.append(dict(operation='author_axis',request=dict(parameter=dict(id='ParamBrowMood',name='Brow emotion',min=-1,max=1,default=0),shapes=shapes)))
    for id in ["smile","sad","angry","surprised"]:
        steps.append(dict(operation="expression_delete",request=dict(id=id)))
    for name,values in EXPRESSIONS.items():
        steps.append(dict(operation='expression_put',request=dict(expression=expression(name,values))))
    # Defaults remain in the editor's generated presets; exclude them from export.
    for builtin in ['Idle','Blink','Nod','Shake']:
        steps.append(dict(operation='motion_preset',request=dict(builtin=builtin,action='update',disabled=True)))
    for clip,duration,loop in [('rpIdle',16,True),('rpNod',2,False)]:
        steps.append(dict(operation='motion_create',request=dict(id=clip,name=clip)))
        steps.append(dict(operation='motion_properties',request=dict(id=clip,duration=duration,loop=loop,fps=30,fade_in=.6,fade_out=.6)))
        curves={}
        if loop:
            for t in range(17):
                curves[t]={'ParamAngleX':round(2*math.sin(t*math.pi/8),6),'ParamAngleY':round(.8*math.sin(t*math.pi/4),6),
                    'ParamAngleZ':round(1.2*math.sin(t*math.pi/8),6),'ParamBodyAngleZ':round(.35*math.sin(t*math.pi/8),6),
                    'ParamBreath':round(.2+.18*(1-math.cos(t*math.pi/2)),6),
                    'ParamBrowLY':0,'ParamBrowRY':0,'ParamBrowMood':0,'ParamMouthForm':0}
            blink={0:1,16:1}
            for onset in [2.8,7.1,12.3,12.85]:
                blink.update({onset:1,onset+.09:0,onset+.14:0,onset+.29:1})
            for t,v in blink.items():curves.setdefault(t,{}).update(ParamEyeLOpen=v,ParamEyeROpen=v)
        else:
            curves={0:{'ParamAngleY':0},.5:{'ParamAngleY':-3},1:{'ParamAngleY':1},2:{'ParamAngleY':0}}
        for t,values in sorted(curves.items()):
            steps.append(dict(operation='motion_pose',request=dict(id=clip,time=t,values=values)))
    steps.append(dict(operation="settings_update",request=dict(changes=dict(rigTuning=dict(eyeLidCurve=8,blinkCorner=50,frontHairSway=4,backHairSway=3,hairRollHold=100,frontHairPerspective=5,frontHairCurl=1,backHairCurl=1)))))
    return steps


def settings():
    groups={'happy':'admiration amusement approval caring desire excitement gratitude joy love optimism pride relief',
            'sad':'disappointment grief remorse sadness','angry':'anger annoyance disapproval disgust',
            'surprised':'fear realization surprise','confused':'confusion curiosity','embarrassed':'embarrassment nervousness'}
    mapping={label:dict(expression=next((name for name,labels in groups.items() if label in labels.split()),'neutral'),motion='none') for label in LABELS}
    return dict(rp_animation=dict(version=1,authored_idle=True,smooth_text_talk=True),scale=.4,x=-75,y=0,eye=45,cursor_param={k:'none' for k in ['idParamAngleX','idParamAngleY','idParamAngleZ','idParamBodyAngleX','idParamBreath','idParamEyeBallX','idParamEyeBallY']},
        param_mouth_open_y_id='ParamMouthOpenY',mouth_open_speed=3,mouth_time_per_character=30,
        animation_starter=dict(expression='neutral',motion='Idle_id=0',delay=0),
        animation_default=dict(expression='neutral',motion='none'),animation_click=dict(expression='none',motion='none',message=''),
        hit_areas={},classify_mapping=mapping)


def package(runtime, output):
    """Fresh portable copy; only select motion groups/settings, never patch Core/texture."""
    import shutil
    from .bundle import validate
    from .manifest import write_json,digest
    runtime,output=Path(runtime),Path(output)
    if output.exists():raise FileExistsError('Use a new runtime directory')
    models=list(runtime.glob('*.model3.json'))
    if len(models)!=1:raise ValueError('Expected one exported model')
    report=validate(models[0])
    if report['status']!='pass':raise ValueError('Invalid source runtime')
    data=json.loads(models[0].read_text())
    motions=data['FileReferences']['Motions']
    # PSD2Live puts authored clips in Idle; select by stable authoring IDs.
    entries=[item for items in motions.values() for item in items]
    chosen={name:[item for item in entries if item['File'].endswith('.'+id+'.motion3.json')] for name,id in [('Idle','rpIdle'),('Nod','rpNod')]}
    if any(len(v)!=1 for v in chosen.values()):raise ValueError('Missing/duplicate authored motion')
    names={e['Name'] for e in data['FileReferences']['Expressions']}
    if not set(EXPRESSIONS)<=names:raise ValueError('Missing RP expressions')
    shutil.copytree(runtime,output)
    data['FileReferences']['Motions']=chosen
    write_json(output/models[0].name,data)
    write_json(output/'sillytavern_settings.json',settings())
    write_json(output/'animation-provenance.json',dict(schema_version=1,source_model_sha256=digest(models[0]),
        change='Select authored Idle/Nod groups and portable ST settings; geometry/artwork untouched',
        force_animation=False,force_loop=False,text_driven_not_audio_lipsync=True))
    return validate(output/models[0].name)
