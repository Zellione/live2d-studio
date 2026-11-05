"""Fresh expression candidate from hash-verified aligned creation stages."""
import argparse,json,shutil
from pathlib import Path
from live2d_studio.generic_rig import open_stage,save,export_model,verify_source_art,locked_editor,overview,animation_recipe
from live2d_studio.emotion_authoring import install,expression_entries
from live2d_studio.mcp import MCP
from live2d_studio.manifest import write_json,digest
from live2d_studio.stages import verify

@locked_editor
def author(client,base,output,layers):
    output.mkdir(parents=True,exist_ok=False)
    op=open_stage(client,base,output)
    blush=install(client,op,layers,output)
    recipes=animation_recipe(overview(client)['data']['parameters']['items'])
    expressions=[]
    for step in recipes:
        if step['operation']!='expression_put':continue
        exp=step['request']['expression']
        exp['entries']=expression_entries(exp['name'],exp['entries'],blush)
        op.call(step['operation'],step['request']);expressions.append(step)
    write_json(output/'expressions.json',expressions)
    save(op,output)
    write_json(output/'source-art.json',verify_source_art(layers,output/'character.psd2live'))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();base=a.baseline.resolve();out=a.output.resolve()
    state=json.loads((base/'creation.json').read_text())
    def stage(n):
        s=state['stages'][n];d=base/s['directory'];verify(d,s['files']);return d
    # Verify every predecessor inventory before changing the editor.
    for n in state['stages']:stage(n)
    out.mkdir(parents=True,exist_ok=False)
    client=MCP('http://127.0.0.1:23871/mcp')
    author(client,stage('animation'),out/'authoring',stage('facial')/'layers')
    (out/'export').mkdir();export_model(client,out/'authoring',out/'export')
    shutil.copyfile(stage('project')/'transition-correspondence.json',out/'transition-correspondence.json')
    write_json(out/'experiment.json',dict(baseline=str(base),baseline_state_sha256=digest(base/'creation.json'),
        layers=str(stage('facial')/'layers'),review='needs-user-visual-review',promotion=False))
    for n in state['stages']:stage(n)
    print(out)
