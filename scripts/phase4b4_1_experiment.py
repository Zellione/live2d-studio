"""Fresh mouth candidate from an explicitly selected Phase 4B.4 project."""
import argparse,json,shutil
from pathlib import Path
from live2d_studio.generic_rig import open_stage,save,export_model,verify_source_art,locked_editor
from live2d_studio.mouth_authoring import install,expression_entries
from live2d_studio.mcp import MCP
from live2d_studio.manifest import write_json,digest
from live2d_studio.stages import verify

@locked_editor
def author(client,base,output,layers):
    output.mkdir(parents=True,exist_ok=False);op=open_stage(client,base/'authoring',output)
    install(client,op,layers,output)
    expressions=json.loads((base/'authoring/expressions.json').read_text())
    for step in expressions:
        exp=step['request']['expression'];exp['entries']=expression_entries(exp['name'],exp['entries'])
        op.call(step['operation'],step['request'])
    write_json(output/'expressions.json',expressions);save(op,output)
    write_json(output/'source-art.json',verify_source_art(layers,output/'character.psd2live'))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();base=a.baseline.resolve();out=a.output.resolve()
    exp=json.loads((base/'experiment.json').read_text());layers=Path(exp['layers'])
    creation=Path(exp['baseline']);state=json.loads((creation/'creation.json').read_text())
    for s in state['stages'].values():verify(creation/s['directory'],s['files'])
    frozen={str(f.relative_to(base)):digest(f) for f in base.rglob('*') if f.is_file()}
    out.mkdir(parents=True,exist_ok=False)
    write_json(out/'predecessor-inventory.json',frozen)
    client=MCP('http://127.0.0.1:23871/mcp');author(client,base,out/'authoring',layers)
    (out/'export').mkdir();export_model(client,out/'authoring',out/'export')
    shutil.copyfile(base/'transition-correspondence.json',out/'transition-correspondence.json')
    write_json(out/'experiment.json',dict(baseline=str(base),layers=str(layers),review='needs-user-visual-review',promotion=False))
    for f,h in frozen.items():
        if digest(base/f)!=h:raise ValueError('Predecessor changed: '+f)
    print(out)
