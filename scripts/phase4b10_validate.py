"""Run unchanged regression gates on the frontal candidate, retaining every failure."""
import argparse,json,subprocess
from pathlib import Path
from live2d_studio.creation_validation import validate_runtime,REPO
from live2d_studio.preview_live import DEFAULT_EXTENSION
from live2d_studio.manifest import write_json

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('run','output','correspondence'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();root=a.run.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    author=root/'authoring';model=next((root/'exported/runtime').glob('*.model3.json'))
    core=DEFAULT_EXTENSION/'lib/live2dcubismcore.min.js';results={}
    for name,script,args in [('mouth-core','probe_expressions.cjs',[model,author/'mouth-inspection.json',root/'exported/mouth-contract.json']),('body-core','probe_body.cjs',[model,author/'body-inspection.json'])]:
        with (out/(name+'.json')).open('w') as f,(out/(name+'.log')).open('w') as log:
            r=subprocess.run(['node',str(REPO/'scripts'/script),str(core),*map(str,args)],stdout=f,stderr=log)
        results[name]=r.returncode;print(name,r.returncode,flush=True)
    for name,script,plan in [('arms','phase4b10_arm_scenario.js',None),('dense','phase4b3_transition_scenario.js',a.correspondence.resolve()),('body','phase4b6_body_scenario.js',None),('coexistence','phase4b6_1_coexistence_scenario.js',None)]:
        folder=out/name;folder.mkdir()
        try:validate_runtime(model,folder,DEFAULT_EXTENSION,REPO/'scripts'/script,plan)
        except Exception as e:results[name]=str(e)
        else:results[name]=0
        print(name,results[name],flush=True)
    write_json(out/'summary.json',dict(results=results,status='pass' if not any(results.values()) else 'fail',user_review='pending'))
    raise SystemExit(bool(any(results.values())))
