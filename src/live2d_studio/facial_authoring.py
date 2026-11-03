"""Install provenance-bearing generated facial artwork through standalone MCP."""
import itertools
import json
from .generic_rig import inspect,overview,objects
from .manifest import digest,write_json


def install(client,op,layers,output):
    report=json.loads((layers/'facial-artwork.json').read_text())
    data=overview(client)['data'];items=objects(client)
    manifest=json.loads((layers/'layer_manifest.json').read_text())
    names={l['id'] for l in manifest['layers']}
    faces=[l for l in data['layers']['items'] if l['role']=='face' and l['name'] in names]
    mouths=[l for l in data['layers']['items'] if l['role']=='mouth' and l['name'] in names]
    if len(faces)!=1 or len(mouths)!=1:raise ValueError('Ambiguous facial art anchor')
    def mesh(layer):
        found=[o for o in items if o.get('layerId')==layer['id'] and o['target'].startswith('mesh:')]
        if len(found)!=1:raise ValueError('Ambiguous source mesh for generated art')
        return found[0]
    face,mouth=mesh(faces[0]),mesh(mouths[0]);installed=[]
    eye_edits=[]
    for side,parameter in [('left','ParamEyeLOpen'),('right','ParamEyeROpen')]:
        for role in ('eyewhite','eyelash'):
            candidates=[l for l in data['layers']['items'] if l['role']==role and l['side']==side and l['name'] in names]
            if len(candidates)!=1:raise ValueError('Ambiguous eye artwork')
            target=mesh(candidates[0])['target'];axes=inspect(client,dict(target=target))['axes']
            if axes!={parameter:[0,1]}:raise ValueError('Unsupported blink mesh axes')
            # The importer leaves the bottom contour at rest while lowering the top.
            # Contract the complete source surface toward a common relative lid line.
            op.call('keyform_apply',dict(changes=[dict(op='copy',target=target,**{'from':{parameter:1}},key={parameter:0},channels=['geometry'])]))
            edit=dict(target=target,key={parameter:0},operations=[dict(type='scale',factors=[1,.12 if role=='eyelash' else .04],pivot=[.5,.7])])
            op.call('rig_deform',dict(changes=[edit]));eye_edits.append(edit)
            op.call('keyform_apply',dict(changes=[dict(op='set',target=target,key={parameter:v},channels=dict(opacity=a)) for v,a in [(0,0),(.25,1),(1,1)]]))
        iris=[l for l in data['layers']['items'] if l['role']=='irides' and l['side']==side and l['name'] in names]
        if len(iris)!=1:raise ValueError('Ambiguous iris source')
        iris_target=mesh(iris[0])['target']
        op.call('keyform_apply',dict(changes=[dict(op='set',target=iris_target,key={parameter:v},channels=dict(opacity=a)) for v,a in [(0,0),(.25,1),(1,1)]]))
    write_json(output/'blink-reconstruction.json',eye_edits)
    # Generated lips inferred from skin-bearing sparse contours are unreliable.
    # Preserve their source/rig, replace their rendering with explicit source/cavity assets.
    mouth_layers={l['id'] for l in data['layers']['items'] if l['role']=='mouth'}
    old_mouth=[o['target'] for o in items if o.get('layerId') in mouth_layers and o['target'].startswith('mesh:')]
    if any(v['kind']=='interior' for v in report['alternatives']):
        op.call('keyform_apply',dict(changes=[dict(op='multi_key',targets=old_mouth,opacity=0)]))
        op.call('parameter_create',dict(parameter_id='ParamMouthCurve',name='Smile / frown',min=-1,max=1,default=0))
    result=lambda d:d.get('result',d)
    for variant in report['alternatives']:
        png=layers/variant['path']
        if digest(png)!=variant['sha256']:raise ValueError('Generated artwork hash changed')
        name='facial-'+variant['feature']+'-'+variant['kind'];lid='agent:'+name
        ref=result(op.call('asset_prepare_reference',dict(layer_id=faces[0]['id'],piece_id=name,background_color='#FFFFFF',
            target_anchors={'origin':dict(x=0,y=0),'extent':dict(x=manifest['canvas']['width'],y=manifest['canvas']['height'])})))
        asset=result(op.call('asset_import_png',dict(reference_id=ref['id'],png_path=str(png),require_transparency=True)))
        registration=result(op.call('asset_register',dict(asset_id=asset['assetId'],mode='absolute',transform=dict(x=0,y=0,scale_x=1,scale_y=1))))
        parent=mouth['parentId'] if variant['kind'] in ('interior','source-neutral') else face['parentId']
        if variant['kind']=='closed-lash':
            side=variant['feature'].split('-')[1]
            anchor=[l for l in data['layers']['items'] if l['role']=='eyelash' and l['side']==side and l['name'] in names]
            parent=mesh(anchor[0])['parentId']
        op.call('layer_add_from_asset',dict(asset_id=asset['assetId'],registration_id=registration['id'],layer_id=lid,name=name,
            semantic_tag='unknown',parent_deformer_id=parent,insertion=dict(mode='above',reference_layer_id=faces[0]['id'])))
        found=[o for o in objects(client) if o.get('layerId')==lid and o['target'].startswith('mesh:')]
        if len(found)!=1:raise ValueError('Generated artwork mesh is ambiguous')
        target=found[0]['target'];detail=inspect(client,dict(target=target))
        parameter={'eye-left':'ParamEyeLOpen','eye-right':'ParamEyeROpen','mouth':'ParamMouthOpenY'}[variant['feature']]
        if variant['kind']=='interior':
            op.call('author_axis',dict(parameter=dict(id=parameter,min=0,max=1,default=0),shapes=[
                dict(target=target,key={},value=v,operations=[dict(type='scale',factors=[1,v])]) for v in [.25,.5,.75,1]]))
            op.call('rig_deform',dict(changes=[dict(target=target,key={parameter:0},operations=[dict(type='scale',factors=[1,.03])])]))
            values=[(0,0),(.05,1),(1,1)]
        elif variant['kind'] in ('source-neutral','closed-lash'):values=[(0,1),(.25,0),(1,0)]
        elif variant['feature'].startswith('eye'):
            values=[(0,1),(1,1)]
        else:values=[(0,1),(1,1)]
        changes=[dict(op='set',target=target,key={parameter:v},channels=dict(opacity=a)) for v,a in values]
        if variant['kind']=='skin' and variant['feature']=='mouth':
            changes=[dict(op='set',target=target,key={parameter:v,'ParamMouthCurve':curve},channels=dict(opacity=max(a,abs(curve))))
                     for v,a in values for curve in [-1,0,1]]
        op.call('keyform_apply',dict(changes=changes))
        # Inspect draw order, never assume a character's imported layer index.
        face_detail=inspect(client,dict(target=face['target']))
        order=face_detail.get('static',{}).get('draw_order')
        if order is None:raise ValueError('Missing inspected face draw order')
        offset={'skin':1,'interior':2,'source-neutral':3,'closed-lash':4}[variant['kind']]
        op.call('rig_edit_structure',dict(edits=[dict(action='static',kind='mesh',id=target.split(':',1)[1],draw_order=int(order)+offset)]))
        installed.append(dict(**variant,target=target,parent=parent,parameter=parameter))
    write_json(output/'facial-installed.json',installed)
