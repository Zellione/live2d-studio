"""Limited independent shoulder fields on inspected bilateral arm owners."""
import itertools
import json
from pathlib import Path
import shutil
from .generic_rig import locked_editor, open_stage, overview, objects, inspect, save, archived_art, verify_source_art, export_model
from .manifest import load_validate, write_json, digest
from .performance import expressions, assert_expressions_preserved
from .body_rig import keys


def bind(view, items, layers):
    roles = {l['id']: l for l in layers['layers'] if l.get('arm_part')}
    result = {}
    for side in ('right', 'left'):
        wanted = {name for name, row in roles.items() if row['anatomical_side'] == side}
        source = {l['id'] for l in view['layers']['items'] if l['name'] in wanted}
        meshes = [o for o in items if o.get('layerId') in source and o['target'].startswith('mesh:')]
        parents = {m['parentId'] for m in meshes}
        if len(wanted) != 3 or len(meshes) != 3 or len(parents) != 1:
            raise ValueError('Expected three arm parts under one independent owner per side')
        target = 'warp:' + next(iter(parents))
        if any(o.get('parentId') in parents and o not in meshes for o in items):
            raise ValueError('Arm owner also moves unrelated artwork')
        result[side] = {'target': target, 'meshes': [m['target'] for m in meshes], 'layers': sorted(wanted)}
    if result['right']['target'] == result['left']['target']:
        raise ValueError('Arms share owner')
    return result


def recipe(binding, details, amount=1):
    if not 0 < amount <= 4/3:
        raise ValueError('Limited shoulder field amplitude must be in (0,4/3]')
    steps = []
    for side, row in binding.items():
        target = row['target']; axes = details[target]['axes']
        combinations = [dict(zip(axes, values)) for values in itertools.product(*axes.values())]
        if len(combinations) > 64: raise ValueError('Unbounded existing arm combinations')
        ident = 'ParamArm' + side.title() + 'Open'
        if ident in axes: raise ValueError('Arm motion already authored')
        steps.append({'parameter': {'id': ident, 'name': 'Anatomical '+side+' arm outward', 'min': 0, 'max': 1, 'default': 0},
                      'shapes': [{'target':target, 'key': key, 'value': 1,
                                  'operations': [{'type':'curve', 'axis':'x',
                                                  'controls':[0,0,(-1 if side == 'right' else 1)*.12*amount,(-1 if side == 'right' else 1)*.4*amount]}]} for key in combinations]})
    return steps


@locked_editor
def author(client, predecessor, layers, output, amount=1):
    output = Path(output).resolve(); output.mkdir(parents=True, exist_ok=False)
    op = open_stage(client, predecessor, output); initial = overview(client)['data']
    saved = expressions(client); items = objects(client)
    binding = bind(initial, items, load_validate(layers))
    details = {row['target']:inspect(client, {'target':row['target']}) for row in binding.values()}
    changes = recipe(binding, details, amount)
    for change in changes: op.call('author_axis', change)
    for side in binding:
        op.call('motion_put', {'clip': {'id':'frontalArm'+side.title(), 'name':'frontalArm'+side.title(),
            'duration':3.2, 'loop':False, 'fps':30, 'fade_in':.25, 'fade_out':.4,
            'curves':[{'parameter':'ParamArm'+side.title()+'Open',
                       'keys':keys([(0,0),(.3,0),(1.1,1),(1.9,1),(2.9,0),(3.2,0)])}]}})
    assert_expressions_preserved(saved, expressions(client))
    for name in ('body-inspection.json','mouth-inspection.json','composition-inspection.json'):
        if (predecessor/name).is_file(): shutil.copyfile(predecessor/name, output/name)
    write_json(output/'arm-inspection.json', {'bindings':binding,'details':details,'recipe':changes,
        'amplitude_scale':amount,'scope':'Zero-slope root cubic shoulder field; no elbow or finger articulation',
        'anatomical_pivots_verified':False,'layer_manifest_sha256':digest(Path(layers)/'layer_manifest.json')})
    save(op,output)
    if archived_art(predecessor/'character.psd2live') != archived_art(output/'character.psd2live'):
        raise ValueError('Arm authoring changed artwork')
    write_json(output/'source-art.json', verify_source_art(layers,output/'character.psd2live'))
    op.call('history_checkout', {'node_id':initial['history_node_id']})


def export(client, predecessor, output):
    output = Path(output).resolve(); output.mkdir(parents=True, exist_ok=False)
    export_model(client,predecessor,output)
    model = next((output/'runtime').glob('*.model3.json'))
    data = json.loads(model.read_text())
    raw = json.loads((output/'export'/model.name).read_text())
    motions = [m for group in raw['FileReferences']['Motions'].values() for m in group]
    for side in ('Right','Left'):
        selected = [m for m in motions if m['File'].endswith('.frontalArm'+side+'.motion3.json')]
        if len(selected) != 1: raise ValueError('Missing arm gesture export')
        data['FileReferences']['Motions']['Arm'+side] = selected
    data['StudioBody']['arms'] = 'independent limited frontal shoulder fields'
    data['StudioArms'] = {'version':1,'anatomicalRight':'ParamArmRightOpen','anatomicalLeft':'ParamArmLeftOpen',
                          'scope':'Two modest outward gestures; no articulated elbows or fingers'}
    write_json(model,data)
    return model
