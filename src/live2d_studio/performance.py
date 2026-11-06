"""Optional, resumable composition of existing facial and body authoring."""
import json
from pathlib import Path
from .generic_rig import (open_stage, overview, objects, inspect, save, export_model,
                          locked_editor, archived_art, verify_source_art)
from .manifest import digest, write_json, load_validate
from .stages import Stages, inventory, verify


def expressions(client):
    response=client.tool('workspace_call',dict(operation='expression_list',request={}))
    if not response.get('ok'):raise RuntimeError('Cannot inspect saved expressions')
    return [{k:e[k] for k in ('id','name','fade_in','fade_out','entries')}
            for e in response['data']['expressions']]


def assert_expressions_preserved(before, after):
    if {e['id']:e for e in before}!={e['id']:e for e in after}:
        raise ValueError('Later authoring changed saved expressions')


def validate_export_expressions(saved, folder, references):
    expected={e['name']:e for e in saved if e['id'].startswith('create_')}
    if set(expected)!={e['Name'] for e in references}:raise ValueError('Expression export lost a recipe')
    for ref in references:
        actual=json.loads((folder/ref['File']).read_text())
        wanted=expected[ref['Name']]
        entries=[dict(Id=e['parameter'],Value=e['value'],Blend=e['blend'].title()) for e in wanted['entries']]
        if actual['Parameters']!=entries:raise ValueError('Expression export changed channels: '+ref['Name'])
        if actual['FadeInTime']!=wanted['fade_in'] or actual['FadeOutTime']!=wanted['fade_out']:
            raise ValueError('Expression export changed fades')


@locked_editor
def author_mouths(client, predecessor, layers, output):
    from . import emotion_authoring, mouth_authoring
    op=open_stage(client,predecessor,output)
    initial=overview(client)['data'];before=expressions(client)
    params={p['id'] for p in initial['parameters']['items']}
    if set(mouth_authoring.POSES)!={e['name'] for e in before}:
        raise ValueError('Expected seven named expressions; refusing replacement of custom recipes')
    if 'ParamMouthRound' in params:
        raise ValueError('Coordinated mouths already present; preserve them instead of reauthoring')
    brow_ids={f'ParamBrow{s}{axis}' for s in ('L','R') for axis in ('Incline','Raise')}
    if params & brow_ids and not brow_ids<=params:
        raise ValueError('Incomplete independent brow authoring')
    add_emotions=not brow_ids<=params
    blush=emotion_authoring.install(client,op,layers,output) if add_emotions else 'ParamBlush' in params
    mouth_authoring.install(client,op,layers,output)
    revised=[]
    for old in before:
        entries=emotion_authoring.expression_entries(old['name'],old['entries'],blush) if add_emotions else old['entries']
        exp=dict(old,entries=mouth_authoring.expression_entries(old['name'],entries))
        op.call('expression_put',dict(expression=exp));revised.append(exp)
    assert_expressions_preserved(revised,expressions(client))
    write_json(output/'expressions-before.json',before);write_json(output/'expressions.json',revised)
    items=objects(client)
    write_json(output/'composition-inspection.json',dict(overview=overview(client)['data'],objects=items,
        details={o['target']:inspect(client,dict(target=o['target'])) for o in items}))
    save(op,output)
    previous=archived_art(predecessor/'character.psd2live');current=archived_art(output/'character.psd2live')
    if any(current.get(k)!=v for k,v in previous.items()):raise ValueError('Existing raster artwork changed')
    write_json(output/'source-art.json',verify_source_art(layers,output/'character.psd2live'))
    # Preserve the verified archive before clearing the editor's custom-motion
    # dirty flag by a reversible history checkout, as in body authoring.
    op.call('history_checkout',dict(node_id=initial['history_node_id']))


def compose(stages, predecessor, layers, client_factory, mouths='preserve', body='preserve'):
    from .creation import code_hash
    if mouths not in ('preserve','coordinated') or body not in ('preserve','calm'):
        raise ValueError('Unknown optional performance feature')
    current=predecessor
    if mouths=='coordinated':
        current=stages.run('mouths',dict(parent=inventory(current),layers=inventory(layers),code=code_hash(
            'src/live2d_studio/performance.py','src/live2d_studio/emotion_authoring.py',
            'src/live2d_studio/mouth_authoring.py','src/live2d_studio/generic_rig.py')),
            lambda out:author_mouths(client_factory(),current,layers,out))
    if body=='calm':
        from .body_rig import author
        def build(out):
            # Stages has already created its private directory.
            author(client_factory(),current,layers,out/'authoring')
        stage=stages.run('body',dict(parent=inventory(current),code=code_hash(
            'src/live2d_studio/body_rig.py','src/live2d_studio/performance.py')),build)
        current=stage/'authoring'
    return current


def resolve_baseline(baseline):
    root=baseline;seen=set()
    while not (root/'creation.json').is_file():
        if root in seen or len(seen)>8:raise ValueError('Cyclic/unsupported experiment ancestry')
        seen.add(root);root=Path(json.loads((root/'experiment.json').read_text())['baseline']).resolve()
    state=json.loads((root/'creation.json').read_text())
    if state['identity'].get('pipeline')=='performance-v1':
        verify(root, json.loads((root/'performance.json').read_text())['outputs'])
        spec=json.loads((root/'performance.json').read_text())
        return root/spec['authoring'],Path(spec['layers'])
    for s in state['stages'].values():verify(root/s['directory'],s['files'])
    if root==baseline:
        return root/state['stages']['animation']['directory'],root/state['stages']['facial']['directory']/'layers'
    spec=json.loads((baseline/'experiment.json').read_text());layers=Path(spec['layers']).resolve();load_validate(layers)
    return baseline/'authoring',layers


def prepare(baseline,output,mouths='preserve',body='preserve',endpoint='http://127.0.0.1:23871/mcp'):
    from .mcp import MCP
    baseline=Path(baseline).resolve();output=Path(output).resolve()
    if output.is_relative_to(baseline) or baseline.is_relative_to(output):raise ValueError('Separate output required')
    predecessor,layers=resolve_baseline(baseline)
    # Review browser profiles may contain process-local socket symlinks; they are
    # not authoring inputs. Preserve hashes of all regular predecessor files.
    frozen={str(f.relative_to(baseline)):digest(f) for f in baseline.rglob('*')
            if f.is_file() and not f.is_symlink()}
    stages=Stages(output,dict(pipeline='performance-v1',baseline=str(baseline),source_project=digest(predecessor/'character.psd2live'),mouths=mouths,body=body))
    with stages.locked():
        current=compose(stages,predecessor,layers,lambda:MCP(endpoint),mouths,body)
        exported=stages.run('export',dict(parent=inventory(current),exporter=digest(Path(__file__).with_name('generic_rig.py'))),
            lambda out:export_model(MCP(endpoint),current,out))
        model=next((exported/'runtime').glob('*.model3.json'))
        write_json(output/'predecessor-inventory.json',frozen)
        write_json(output/'performance.json',dict(authoring=str(current.relative_to(output)) if current.is_relative_to(output) else str(current),
            layers=str(layers),model=str(model.relative_to(output)),outputs={str(f.relative_to(output)):digest(f) for folder in [current,exported] for f in folder.rglob('*') if f.is_file() and f.is_relative_to(output)},
            review='needs-user-visual-review',promotion=False))
        stages.data['status']='needs-visual-review';stages.save()
    verify(baseline,frozen)
    return dict(model=str(model),authoring=str(current),status='needs-visual-review')
