"""Author fresh transition candidates from verified frozen artwork and MCP projects."""
import argparse,json,shutil
from pathlib import Path
from live2d_studio.generic_rig import open_stage,save,export_model,verify_source_art,locked_editor
from live2d_studio.mcp import MCP
from live2d_studio.manifest import write_json,digest
from live2d_studio.stages import verify
from live2d_studio.transition_authoring import install

@locked_editor
def author(client,base,output,layers,installed):
    output.mkdir(parents=True,exist_ok=False)
    op=open_stage(client,base,output)
    shutil.copyfile(installed,output/'facial-installed.json')
    install(client,op,layers,output);save(op,output)
    write_json(output/'source-art.json',verify_source_art(layers,output/'character.psd2live'))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--pipeline',action='store_true',help='Exercise resumable create with deterministic artwork and aligned motion')
    a=p.parse_args();a.output=a.output.resolve()
    if not a.pipeline:a.output.mkdir(parents=True,exist_ok=False)
    base=a.baseline.resolve();state=json.loads((base/'creation.json').read_text())
    def stage(n):
        s=state['stages'][n];d=base/s['directory'];verify(d,s['files']);return d
    if a.pipeline:
        from live2d_studio.creation import create,review
        from live2d_studio.creation_quality import CHECKS,validate_review
        evidence=stage('readiness')/'quality.json'
        validate_review(json.loads((base/'reviews/semantic.json').read_text()),digest(evidence),CHECKS)
        source=next(stage('ingest').glob('original.*'))
        kw=dict(rights=state['identity']['rights'],decomposition=stage('inference')/'bridge',sam=stage('semantics')/'sam',preview=False,facial_motion='aligned')
        create(source,a.output,until='readiness',**kw)
        s=json.loads((a.output/'creation.json').read_text())['stages']['readiness']
        if digest(a.output/s['directory']/'quality.json')!=digest(evidence):raise ValueError('Semantic evidence changed; new review required')
        if not (a.output/'reviews/semantic.json').exists():
            review(a.output,'semantic','accept','development-agent; exact prior semantic replay','Identical source/semantic evidence; temporal candidate is not visually accepted.',list(CHECKS))
        print(json.dumps(create(source,a.output,until='validation',**kw),indent=2))
    else:
        client=MCP('http://127.0.0.1:23871/mcp')
        author(client,stage('animation'),a.output/'authoring',stage('facial')/'layers',stage('project')/'facial-installed.json')
        (a.output/'export').mkdir();export_model(client,a.output/'authoring',a.output/'export')
        write_json(a.output/'experiment.json',dict(baseline=str(base),layers=str(stage('facial')/'layers'),review='needs-temporal-review'))
    print(a.output)
