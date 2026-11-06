"""Opt-in elbow diagnostic: source-relative pivots, independent distal meshes.

Existing cut lines are hypotheses, not anatomical landmarks. No automatic promotion.
"""
import json
import math
from pathlib import Path
import shutil
import numpy as np
from PIL import Image
from .manifest import digest, load_validate, write_json
from .generic_rig import (locked_editor, open_stage, overview, objects, inspect,
                          save, archived_art)
from .frontal_arms import bind, export
from .body_rig import keys
from .emotion_authoring import bounds
from .pose_family import load as load_family
from .pose_review import REPO


def frozen_reference(pin):
    pin = json.loads(Path(pin).read_text()); root = REPO / pin['reference_root']
    if digest(root/'manifest.json') != pin['manifest_sha256']:
        raise ValueError('Frozen reference manifest changed')
    manifest = json.loads((root/'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        p = (root/name).resolve()
        if not p.is_relative_to(root.resolve()) or digest(p) != expected:
            raise ValueError('Frozen reference payload changed')
    return root, manifest


def propose(layers, family, geometry):
    """Keep contour uncertainty and bilateral cut support explicit."""
    layers = Path(layers); data = load_validate(layers); family = load_family(Path(family))
    evidence = json.loads(Path(geometry).read_text())
    if data['sources'][0]['sha256'] != family['images']['canonical']['sha256']:
        raise ValueError('Layers do not use the reviewed canonical')
    for key, row in family['images'].items():
        if evidence['images'][key]['image_sha256'] != row['sha256']:
            raise ValueError('Geometry/family hash mismatch')
    size = np.array([data['canvas']['width'], data['canvas']['height']])
    result = {'canvas':size.tolist(), 'layer_manifest_sha256':digest(layers/'layer_manifest.json'),
              'geometry_sha256':digest(geometry), 'arms':{}, 'review':'pending',
              'anatomy_verified':False, 'range_is_diagnostic':True}
    for side in ('right','left'):
        parts = {l['arm_part']:l for l in data['layers'] if l.get('anatomical_side')==side}
        if set(parts)!= {'upper','forearm','hand'}:raise ValueError('Three separated arm parts required')
        fore = parts['forearm']; hand = parts['hand']
        a=np.array(Image.open(layers/fore['rgba_path']))[...,3]
        yy,xx=np.where(a>127)
        # Exact cut support supplies a reproducible pivot hypothesis, not proof of a joint.
        at_top=yy<=yy.min()+2
        elbow=np.array([np.median(xx[at_top])+fore['x'], yy.min()+fore['y']])
        joint=evidence['images']['canonical']['arms'][side]
        shoulder=np.array(joint['shoulder_surface']); wrist=np.array(joint['wrist'])
        support={}
        for name,l in parts.items():
            im=np.array(Image.open(layers/l['rgba_path']))[...,3];y,x=np.where(im>0)
            support[name]=[int(x.min()+l['x']),int(y.min()+l['y']),int(x.max()+l['x']+1),int(y.max()+l['y']+1)]
        helpers={k:{'elbow':row['arms'][side]['elbow']['point'],
                    'status':row['arms'][side]['elbow']['status'],
                    'upper_over_torso':row['arms'][side]['upper_length_over_torso'],
                    'forearm_over_torso':row['arms'][side]['forearm_length_over_torso']}
                 for k,row in evidence['images'].items() if k in family['images']}
        result['arms'][side]={'elbow':(elbow/size).tolist(),'wrist':(wrist/size).tolist(),
            'shoulder_surface':(shoulder/size).tolist(), 'support':support,
            'elbow_uncertainty':joint['elbow'], 'helpers':helpers,
            'elbow_overlap_rows':max(0,support['upper'][3]-support['forearm'][1]),
            'wrist_overlap_rows':max(0,support['forearm'][3]-support['hand'][1]),
            'forearm_generated_pixels':fore['generated_pixels'],
            'limitation':'Flat sleeve cut has no concealed joint cap; pivot is unreviewed.'}
    return result


def rotation_landmarks(raster_bounds, pivot, degrees):
    """Affine rigid pixel-space rotation, compensating non-square input bounds."""
    b=np.asarray(raster_bounds,float); p=np.asarray(pivot,float)
    extent=b[2:]-b[:2]
    if not np.isfinite(np.r_[b,p,degrees]).all() or np.any(extent<=0) or abs(degrees)>150:
        raise ValueError('Invalid bounded rotation')
    corners=np.array([[0,0],[1,0],[0,1],[1,1]],float)
    theta=math.radians(degrees); rot=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
    target=((corners*extent+b[:2]-p)@rot.T+p-b[:2])/extent
    return {'type':'landmarks','from':corners.tolist(),'to':target.tolist()}


def rotation_keys(target, parameter, side, degrees):
    """Native rotation channels keep the fitted rest pivot and scale unchanged."""
    if side not in ('right','left') or not math.isfinite(degrees) or not 0<degrees<=135:
        raise ValueError('Unsupported rotation range or ownership')
    return [{'op':'seed','target':target,'key':{parameter:0}},
            {'op':'set','target':target,'key':{parameter:1},
             'geometry':{'angle':(-1 if side=='right' else 1)*degrees}}]


@locked_editor
def author(client, reference, proposal, output, side='right', degrees=120, method='rotation', overlap=False, predecessor=None):
    """Diagnostic only: unchanged textures can expose unbacked cuts during bending."""
    if side not in ('right','left') or not 0<degrees<=135:raise ValueError('Unsupported arm/range')
    if method not in ('rotation','landmarks'):raise ValueError('Unknown elbow method')
    reference=Path(reference); output=Path(output).resolve()
    if not output.is_relative_to(REPO/'runs') or output.exists():raise ValueError('Fresh ignored output required')
    layers=reference/'layers'; data=load_validate(layers)
    if digest(layers/'layer_manifest.json')!=proposal['layer_manifest_sha256']:raise ValueError('Proposal source changed')
    output.mkdir(parents=True); dest=output/'authoring';dest.mkdir()
    base=Path(predecessor).resolve() if predecessor else reference/'authoring'
    if not base.resolve().is_relative_to(REPO/'runs'):raise ValueError('Predecessor outside ignored runs')
    op=open_stage(client,base,dest);view=overview(client)['data'];items=objects(client)
    wanted={l['id'] for l in data['layers'] if l.get('anatomical_side')==side and l.get('arm_part')}
    lids={l['id'] for l in view['layers']['items'] if l['name'] in wanted}
    meshes=[o for o in items if o.get('layerId') in lids and o['target'].startswith('mesh:')]
    parents={o['parentId'] for o in meshes}
    if len(wanted)!=3 or len(meshes)!=3 or len(parents)!=1:raise ValueError('Selected arm must have three parts under one owner')
    if any(o.get('parentId') in parents and o not in meshes for o in items):raise ValueError('Selected arm owner includes unrelated objects')
    binding={side:{'target':'warp:'+next(iter(parents)),'meshes':[o['target'] for o in meshes]}}
    settings=inspect(client,{'scope':'layers','limit':64})
    if settings.get('next') is not None:raise ValueError('Incomplete layer inspection')
    normalized=np.array(proposal['arms'][side]['elbow'],float)
    if normalized.shape!=(2,) or not np.isfinite(normalized).all() or np.any(normalized<0) or np.any(normalized>1):
        raise ValueError('Elbow proposal outside source')
    pivot=normalized*np.array(proposal['canvas'])
    records=[];shapes=[];ident='ParamArm'+('R' if side=='right' else 'L')+'Elbow'
    for layer in data['layers']:
        if layer.get('anatomical_side')!=side or layer.get('arm_part') not in ('forearm','hand'):continue
        lid=next(l['id'] for l in view['layers']['items'] if l['name']==layer['id'])
        mesh=next(o for o in items if o.get('layerId')==lid and o['target'].startswith('mesh:'))
        detail=inspect(client,{'target':mesh['target']})
        if detail['axes']:raise ValueError('Existing direct mesh axes require separate reviewed composition')
        top=client.tool('workspace_call',{'operation':'mesh_get_topology','request':{'target':mesh['target'],'limit':4096}})['data']
        if top.get('next_offset') is not None:raise ValueError('Incomplete topology')
        margin=next(l for l in settings['items'] if l['id']==lid)['mesh']['outerMargin']
        b=bounds(Image.open(layers/layer['rgba_path']))+np.array([-margin,-margin,margin,margin])
        local_pivot=pivot-np.array([layer['x'],layer['y']])
        records.append({'layer':layer['id'],'target':mesh['target'],'inspection':detail,'topology':top,
                        'raster_bounds':b.tolist(),'pivot_in_raster':local_pivot.tolist()})
        for step in range(1,17):
            shapes.append({'target':mesh['target'],'value':step/16,'operations':[
                rotation_landmarks(b,local_pivot,(-1 if side=='right' else 1)*degrees*step/16)]})
    if len(records)!=2:raise ValueError('Missing distal surfaces')
    write_json(dest/'elbow-inspection.json',{'proposal':proposal,'bindings':binding,'surfaces':records,
        'parameter':ident,'degrees':degrees,'method':method, 'scope':'Native shared rotation or explicit failed mesh-transform comparison under unchanged shoulder parent',
        'status':'unreviewed-artwork-support-diagnostic'})
    # Moving forearm crosses in front of clothing; explicit experimental depth hypothesis.
    torso_ids={l['id'] for l in view['layers']['items'] if l['role'] in ('topwear','bottomwear')}
    torso=[o for o in items if o.get('layerId') in torso_ids and o['target'].startswith('mesh:')]
    if not torso:raise ValueError('Missing clothing draw order')
    order=max(inspect(client,{'target':o['target']})['static']['draw_order'] for o in torso)
    occupied={inspect(client,{'target':o['target']})['static']['draw_order'] for o in items if o['target'].startswith('mesh:')}
    while order+1 in occupied or order+2 in occupied:order+=1
    if order+2>1000:raise ValueError('No free forearm depth slots')
    op.call('rig_edit_structure',{'edits':[{'action':'static','kind':'mesh','id':r['target'].split(':',1)[1],
        'draw_order':order+1+i} for i,r in enumerate(records)]})
    if method=='landmarks':
        op.call('author_axis',{'parameter':{'id':ident,'min':0,'max':1,'default':0},'shapes':shapes})
    elif method=='rotation':
        rot_id='ExperimentalElbow'+side.title()
        created=op.call('canvas_rotation',{'name':'Experimental '+side+' elbow','id':rot_id,
            'meshes':[r['target'].split(':',1)[1] for r in records],
            'add_to':'parent_of_selected','origin':pivot.tolist(),'angle':0,'preservePose':True})
        target='rotation:'+rot_id
        write_json(dest/'rotation-inspection.json',inspect(client,{'target':target}))
        op.call('parameter_create',{'parameter_id':ident,'name':ident,'min':0,'max':1,'default':0})
        op.call('keyform_apply',{'changes':rotation_keys(target,ident,side,degrees)})
    else:raise ValueError('Unknown elbow method')
    if overlap:
        from .elbow_overlap import prepare
        patch=prepare(layers,proposal,side,output/'overlap')
        old_targets={o['target'] for o in objects(client)}
        upper_name=next(l['id'] for l in data['layers'] if l.get('anatomical_side')==side and l.get('arm_part')=='upper')
        upper_id=next(l['id'] for l in view['layers']['items'] if l['name']==upper_name)
        op.call('layer_import_images',{'paths':[str(output/'overlap'/patch['path'])],
            'parent_deformer_id':binding[side]['target'].split(':',1)[1],
            'anchor_layer_id':upper_id,'in_front':False,'at':patch['center']})
        added=[o for o in objects(client) if o['target'] not in old_targets and o['target'].startswith('mesh:')]
        if len(added)!=1:raise ValueError('Overlap mesh import ambiguous')
        cap=added[0]['target']
        op.call('keyform_apply',{'changes':[{'op':'set','target':cap,'key':{ident:v},'channels':{'opacity':alpha}} for v,alpha in [(0,0),(.02,1),(1,1)]]})
        write_json(dest/'overlap-inspection.json',{'patch':patch,'mesh':inspect(client,{'target':cap}),'review':'pending'})
    existing_params={p['id'] for p in view['parameters']['items']}
    for active in ('right','left'):
        elbow_id='ParamArm'+active[0].upper()+'Elbow'
        shoulder_id='ParamArm'+active.title()+'Open'
        if active!=side and elbow_id not in existing_params:continue
        if shoulder_id not in existing_params:raise ValueError('Coordinated shoulder parameter missing')
        op.call('motion_put',{'clip':{'id':'elbow'+active.title(),'name':'elbow'+active.title(),'duration':4.0,'loop':False,'fps':30,'fade_in':.25,'fade_out':.35,
            'curves':[{'parameter':elbow_id,'keys':keys([(0,0),(.3,0),(1.5,1),(2.2,1),(3.7,0),(4,0)])},
                      {'parameter':shoulder_id,'keys':keys([(0,0),(.3,0),(1.5,.15),(2.2,.15),(3.7,0),(4,0)])}]}})
    for name in ('body-inspection.json','mouth-inspection.json','composition-inspection.json','arm-inspection.json'):
        shutil.copyfile(base/name,dest/name)
    save(op,dest)
    before_art=archived_art(base/'character.psd2live');after_art=archived_art(dest/'character.psd2live')
    if any(after_art.get(k)!=v for k,v in before_art.items()):raise ValueError('Original artwork changed')
    op.call('history_checkout',{'node_id':view['history_node_id']})
    return dest


def export_candidate(client, output, side='right', degrees=120):
    output=Path(output).resolve();dest=output/'authoring'
    ident='ParamArm'+('R' if side=='right' else 'L')+'Elbow'
    model=export(client,dest,output/'exported');m=json.loads(model.read_text())
    raw=json.loads((output/'exported/export'/model.name).read_text())
    for available in ('right','left'):
        clips=[c for group in raw['FileReferences']['Motions'].values() for c in group if c['File'].endswith('.elbow'+available.title()+'.motion3.json')]
        if available==side and len(clips)!=1:raise ValueError('Elbow clip absent')
        if clips:m['FileReferences']['Motions']['Elbow'+available.title()]=clips
    m['StudioElbow']={'side':side,'parameter':ident,'degrees':degrees,'status':'diagnostic-awaiting-visual-review','wrist_independent':False}
    write_json(model,m);return model
