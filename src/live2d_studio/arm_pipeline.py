"""Optional, reviewed native elbow stage. No inference and no implicit acceptance."""
import json
from pathlib import Path
import shutil
import numpy as np
from PIL import Image
from .manifest import digest,load_validate,write_json
from .stages import Stages,inventory,verify,fingerprint
from .pose_review import REPO
from .generic_rig import locked_editor,open_stage,overview,objects,inspect,verify_source_art
from .elbow_rig import frozen_reference,author,export_candidate
from .elbow_overlap import prepare as overlap

CODE=('arm_pipeline.py','elbow_rig.py','elbow_overlap.py','generic_rig.py','frontal_arms.py')


def check_owner(items, meshes, control, params, detail):
    """Validate the live hierarchy, rather than trusting saved semantic names."""
    parents={o.get('parentId') for o in meshes}
    if len(meshes)!=3 or len(parents)!=1 or None in parents:
        raise ValueError('Independent three-part shoulder owner required')
    parent=next(iter(parents))
    if not any(o['target']=='warp:'+parent for o in items):
        raise ValueError('Supported shoulder warp missing')
    if any(o.get('parentId')==parent and o not in meshes for o in items):
        raise ValueError('Unrelated object under shoulder owner')
    if control not in params or any(params[control][k]!=v for k,v in [('default',0),('min',0),('max',1)]):
        raise ValueError('Supported neutral shoulder control missing')
    axes=detail.get('axes',{})
    if axes.get(control)!=[0,1] or any(params.get(k,{}).get('default') not in values for k,values in axes.items()):
        raise ValueError('Shoulder owner lacks supported neutral/shoulder keys')
    return parent


def assess(layers):
    """Raster attachment checks produce hypotheses; they never approve anatomy."""
    layers=Path(layers);data=load_validate(layers);w,h=data['canvas']['width'],data['canvas']['height']
    proposal={'canvas':[w,h],'layer_manifest_sha256':digest(layers/'layer_manifest.json'),
              'arms':{},'anatomy_verified':False,'review':'required'}
    reasons=[]
    for side in ('right','left'):
        candidates=[l for l in data['layers'] if l.get('anatomical_side')==side]
        parts={l.get('arm_part'):l for l in candidates}
        if len(candidates)!=3 or set(parts)!={'upper','forearm','hand'}:
            reasons.append(side+': missing or ambiguous three-part source');continue
        bounds={};arrays={}
        for name,l in parts.items():
            a=np.array(Image.open(layers/l['rgba_path']).convert('RGBA'));yy,xx=np.where(a[...,3]>127)
            if len(xx)<16:reasons.append(side+': insufficient opaque '+name);break
            arrays[name]=(a,yy,xx);bounds[name]=[int(xx.min()+l['x']),int(yy.min()+l['y']),int(xx.max()+l['x']+1),int(yy.max()+l['y']+1)]
        if len(bounds)!=3:continue
        upper,fore,hand=(bounds[n] for n in ('upper','forearm','hand'))
        tolerance=max(2,h*.002)
        if abs(upper[3]-fore[1])>tolerance or abs(fore[3]-hand[1])>tolerance:
            reasons.append(side+': disconnected neutral cuts');continue
        if min(upper[2],fore[2])-max(upper[0],fore[0])<=2 or min(fore[2],hand[2])-max(fore[0],hand[0])<=2:
            reasons.append(side+': no horizontal attachment support');continue
        ratio=(upper[3]-upper[1])/(fore[3]-fore[1])
        if not .3<ratio<3:reasons.append(side+': unsupported segment proportions');continue
        def top(name):
            _,yy,xx=arrays[name];l=parts[name];at_top=yy<=yy.min()+2
            return [(float(np.median(xx[at_top]))+l['x'])/w,(int(yy.min())+l['y'])/h]
        proposal['arms'][side]={'elbow':top('forearm'),'wrist':top('hand'),'shoulder_surface':top('upper'),
             'support':bounds,'projected_upper_forearm_ratio':ratio,
             'uncertainty':'Cut-derived attachment hypothesis, not a verified joint; hidden overlap and motion range require human review'}
    return {'status':'shoulder-only-fallback' if reasons else 'needs-arm-review','reasons':reasons,'proposal':proposal}


@locked_editor
def inspect_source(client,predecessor,layers,out):
    op=open_stage(client,predecessor,out)
    view=overview(client)['data'];items=objects(client);data=load_validate(layers)
    write_json(out/'source-art.json',verify_source_art(layers,predecessor/'character.psd2live'))
    params={p['id']:p for p in view['parameters']['items']};bindings={};topologies={}
    for side in ('right','left'):
        wanted={l['id'] for l in data['layers'] if l.get('anatomical_side')==side}
        ids={l['id'] for l in view['layers']['items'] if l['name'] in wanted}
        meshes=[o for o in items if o.get('layerId') in ids and o['target'].startswith('mesh:')]
        control='ParamArm'+side.title()+'Open'
        parents={o.get('parentId') for o in meshes}
        if len(parents)!=1 or None in parents:raise ValueError('Independent shoulder owner required')
        parent_detail=inspect(client,{'target':'warp:'+next(iter(parents))})
        parent=check_owner(items,meshes,control,params,parent_detail)
        bindings[side]={'parent':parent,'inspection':parent_detail,'meshes':{o['name']:o['target'] for o in meshes}}
        for mesh in meshes:
            detail=inspect(client,{'target':mesh['target']})
            if detail['axes']:raise ValueError('Direct arm keyforms need separate composition review')
            top=client.tool('workspace_call',{'operation':'mesh_get_topology','request':{'target':mesh['target'],'limit':4096}})['data']
            if top.get('next_offset') is not None or len(top['items'])!=top['vertex_count'] or top['triangle_count']<1 or not np.isfinite(np.array(top['items'],float)).all():
                raise ValueError('Incomplete/nonfinite neutral topology')
            topologies[mesh['target']]=top
    write_json(out/'inspection.json',{'overview':view,'objects':items,'bindings':bindings,'topologies':topologies})
    return bindings


def contract(plan):
    return {'source_project_sha256':plan['source_project_sha256'],'layer_manifest_sha256':plan['proposal']['layer_manifest_sha256'],
        'method':'native-rotation-v1','degrees':plan['degrees'],'shoulder_fraction':.15,
        'sides':{side:{'elbow':plan['proposal']['arms'][side]['elbow'],'overlap_sha256':row['sha256']} for side,row in plan['overlaps'].items()}}


def approve(plan_dir,reviewer,notes,decision='accept'):
    plan_dir=Path(plan_dir).resolve();plan=read_plan(plan_dir)
    if plan['status']!='needs-arm-review' or not reviewer.strip() or not notes.strip() or decision not in ('accept','reject'):
        raise ValueError('Explicit review of a complete plan required')
    file=plan_dir/'review.json'
    if file.exists():raise ValueError('Review already recorded; retain its decision')
    write_json(file,{'reviewer_kind':'human','reviewer':reviewer,'notes':notes,'decision':decision,
        'plan_sha256':digest(plan_dir/'plan.json'),'scope':'Exact joint/range/hidden-overlap plan only; final animation review separate'})


def read_plan(plan_dir):
    plan_dir=Path(plan_dir).resolve()
    if not plan_dir.is_relative_to(REPO/'runs'):raise ValueError('Plan outside ignored runs')
    plan=json.loads((plan_dir/'plan.json').read_text());verify(plan_dir,plan['files'])
    return plan


def authorize(plan_dir,reference_pin=None):
    plan_dir=Path(plan_dir).resolve();plan=read_plan(plan_dir);review=plan_dir/'review.json'
    r=None
    if review.exists():
        r=json.loads(review.read_text())
        if r.get('reviewer_kind')!='human' or r.get('plan_sha256')!=digest(plan_dir/'plan.json'):
            raise ValueError('Changed or non-human plan approval')
        if r.get('decision')=='reject':return {'kind':'rejected'}
        if r.get('decision')!='accept':raise ValueError('Unknown plan decision')
    if reference_pin:
        root,_=frozen_reference(reference_pin)
        expected=json.loads((root/'provenance/approved-arm-contract.json').read_text())
        acceptance=json.loads((root/'user-review.json').read_text())
        if acceptance.get('reviewer_kind')!='human' or acceptance.get('decision')!='accept' or contract(plan)!=expected:
            raise ValueError('Existing human review does not cover this exact arm plan')
        return {'kind':'explicit-reuse-of-exact-reviewed-reference','manifest_sha256':digest(root/'manifest.json'),
                'user_review_sha256':digest(root/'user-review.json'),'plan_sha256':digest(plan_dir/'plan.json')}
    if r is None:return None
    return {'kind':'explicit-human-plan-review','review_sha256':digest(review)}


def _plan(predecessor,layers,out,client_factory,degrees):
    shutil.copytree(layers,out/'layers')
    assessment=assess(out/'layers');plan={**assessment,'source_project_sha256':digest(predecessor/'character.psd2live'),
                                       'degrees':degrees,'overlaps':{}}
    missing=[n for n in ('body-inspection.json','mouth-inspection.json','composition-inspection.json','arm-inspection.json') if not (predecessor/n).is_file()]
    if missing:plan.update(status='shoulder-only-fallback',reasons=['Missing existing performance inspection contracts: '+', '.join(missing)])
    if plan['status']=='needs-arm-review':
        inspection=out/'editor';inspection.mkdir()
        try:
            inspect_source(client_factory(),predecessor,out/'layers',inspection)
            for side in ('right','left'):
                plan['overlaps'][side]=overlap(out/'layers',plan['proposal'],side,out/'overlaps'/side)
        except ValueError as error:
            plan.update(status='shoulder-only-fallback',reasons=[str(error)])
    # Opaque editor snapshots remain diagnostic, never review assets.
    plan['files']={str(p.relative_to(out)):digest(p) for root in [out/'layers',out/'overlaps'] for p in root.rglob('*') if p.is_file()}
    write_json(out/'plan.json',plan)
    if plan['status']=='needs-arm-review':
        from PIL import ImageDraw
        source=load_validate(out/'layers')['sources'][0]['normalized_path']
        im=Image.open(out/'layers'/source).convert('RGBA');d=ImageDraw.Draw(im)
        for side,row in plan['proposal']['arms'].items():
            x,y=np.array(row['elbow'])*im.size;r=max(3,im.height*.012);d.ellipse((x-r,y-r,x+r,y+r),outline='orange',width=3);d.text((x+r,y),side+' elbow?',fill='red')
        im.save(out/'joints.png')
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><h1>Optional elbow plan — human review required</h1><p>Cut-derived joints and source-derived concealed caps are uncertain. This does not approve animation.</p><img style="max-height:700px" src="joints.png"><p><a href="plan.json">Exact plan and uncertainty</a></p>'+''.join('<h2>'+s+'</h2><img src="overlaps/'+s+'/sleeve-overlap.png">' for s in plan['overlaps']))


def prepare(predecessor,layers,model,output,*,review_reference=None,endpoint='http://127.0.0.1:23871/mcp',client_factory=None,degrees=120):
    from .mcp import MCP
    from .bundle import validate
    predecessor,layers,model,output=map(lambda p:Path(p).resolve(),(predecessor,layers,model,output))
    if not output.is_relative_to(REPO/'runs') or any(output.is_relative_to(p) or p.is_relative_to(output) for p in [predecessor,layers,model.parent]):
        raise ValueError('Separate ignored arm run required')
    if not 0<degrees<=135:raise ValueError('Unsupported arm range')
    load_validate(layers);bundle=validate(model)
    if bundle['status']!='pass':raise ValueError('Invalid baseline runtime')
    source_files=inventory(predecessor);layer_files=inventory(layers)
    factory=client_factory or (lambda:MCP(endpoint))
    stage=Stages(output,{'pipeline':'optional-arms-v1','predecessor':str(predecessor),'layers':str(layers),
        'project_sha256':digest(predecessor/'character.psd2live'),'layers_sha256':fingerprint(layer_files),
        'model':str(model),'model_sha256':digest(model),'runtime':bundle['files_sha256'],'degrees':degrees})
    with stage.locked():
        code={n:digest(Path(__file__).with_name(n)) for n in CODE}
        planned=stage.run('arm-plan',{'source':source_files,'layers':layer_files,'code':code,'degrees':degrees},
                          lambda out:_plan(predecessor,layers,out,factory,degrees))
        plan=read_plan(planned)
        if plan['status']=='shoulder-only-fallback':
            stage.data['status']=plan['status'];stage.save()
            return {'status':plan['status'],'model':str(model),'authoring':str(predecessor),'reasons':plan['reasons'],'changed':False}
        auth=authorize(planned,review_reference)
        if auth is None or auth.get('kind')=='rejected':
            status='needs-arm-review' if auth is None else 'rejected-arm-plan'
            stage.data['status']=status;stage.save()
            return {'status':status,'model':str(model),'plan':str(planned),'changed':False}
        current=predecessor;last=None;bindings={}
        for side in ('right','left'):
            parent=current
            def build(out):
                author(factory(),planned,plan['proposal'],out/'rig',side,degrees,'rotation',True,parent)
                if digest(out/'rig/overlap/sleeve-overlap.png')!=plan['overlaps'][side]['sha256']:raise ValueError('Authored overlap differs from review')
            last=stage.run('elbow-'+side,{'parent':inventory(parent),'authorization':auth,'code':code,'side':side},build)
            current=last/'rig/authoring'
            info=json.loads((current/'elbow-inspection.json').read_text());cap=json.loads((current/'overlap-inspection.json').read_text())
            bindings[side]={'source_meshes':[t.split(':',1)[1] for t in info['bindings'][side]['meshes']],
                'distal_meshes':[r['target'].split(':',1)[1] for r in info['surfaces']],
                'overlap_mesh':cap['mesh']['target'].split(':',1)[1]}
        def export_to(out):
            # Export helper expects the authoring sibling; use an exact local copy.
            shutil.copytree(current,out/'authoring');exported_model=export_candidate(factory(),out,'left',degrees)
            data=json.loads(exported_model.read_text());data['StudioArmValidation']=bindings;write_json(exported_model,data)
        exported=stage.run('arm-export',{'parent':inventory(current),'code':code},export_to)
        candidate=next((exported/'exported/runtime').glob('*.model3.json'))
        preserved={p.name:digest(p) for p in model.parent.iterdir() if p.name.endswith(('.exp3.json','.physics3.json','.motion3.json'))}
        for name,h in preserved.items():
            if digest(candidate.parent/name)!=h:raise ValueError('Existing expression/physics/motion changed: '+name)
        from .arm_validation import validate_arms,validation_pins
        checked=stage.run('arm-validation',{'runtime':inventory(candidate.parent),'code':validation_pins()},
                          lambda out:validate_arms(candidate,exported/'authoring',out))
        preview_command=['uv','run','--frozen','live2d-studio','preview-live','--model',str(candidate),'--compare-model',str(model)]
        write_json(output/'arm-result.json',{'model':str(candidate),'authoring':str(current),'plan':str(planned),
            'authorization':auth,'validation':str(checked),'preserved_payloads':preserved,'user_animation_review':'pending','promotion':False,
        'preview_command':preview_command})
        stage.data['status']='needs-visual-review';stage.save()
    verify(predecessor,source_files);verify(layers,layer_files)
    return {'status':'needs-visual-review','model':str(candidate),'authoring':str(current),'validation':str(checked),'changed':True,'preview_command':preview_command}
