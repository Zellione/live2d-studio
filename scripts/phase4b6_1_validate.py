"""Run Core, mouth, dense facial, body and composition suites on a candidate."""
import argparse,json,subprocess
from pathlib import Path
from live2d_studio.creation_validation import validate_runtime,REPO
from live2d_studio.preview_live import DEFAULT_EXTENSION
from live2d_studio.manifest import write_json
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--body-reference',type=Path,required=True);p.add_argument('--correspondence',type=Path,required=True);a=p.parse_args()
root=a.run.resolve();spec=json.loads((root/'performance.json').read_text());author=root/spec['authoring'];model=root/spec['model'];out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);core=DEFAULT_EXTENSION/'lib/live2dcubismcore.min.js';results={}
for name,script,arguments in [
 ('mouth-core','probe_expressions.cjs',[model,author/'mouth-inspection.json',model.parent.parent/'mouth-contract.json']),
 ('body-core','probe_body.cjs',[model,author/'body-inspection.json']),
 ('body-preserved','probe_preserved_body.cjs',[a.body_reference.resolve(),model,author/'composition-inspection.json']),
 ('mouth-precision','probe_mouth_precision.cjs',[model,author/'mouth-inspection.json'])]:
 with (out/(name+'.json')).open('w') as f,(out/(name+'.log')).open('w') as log:
  r=subprocess.run(['node',str(REPO/'scripts'/script),str(core),*map(str,arguments)],stdout=f,stderr=log)
 results[name]=r.returncode;print(name,r.returncode,flush=True)
for name,script,plan in [('mouths','phase4b4_1_mouth_scenario.js',None),('dense','phase4b3_transition_scenario.js',a.correspondence.resolve()),('body','phase4b6_body_scenario.js',None),('face','phase4b6_1_face_scenario.js',None),('coexistence','phase4b6_1_coexistence_scenario.js',None)]:
 folder=out/name;folder.mkdir()
 try:validate_runtime(model,folder,DEFAULT_EXTENSION,REPO/'scripts'/script,plan)
 except Exception as error:results[name]=type(error).__name__
 else:results[name]=0
 print(name,results[name],flush=True)
write_json(out/'summary.json',dict(results=results,status='pass' if not any(results.values()) else 'fail',user_review='pending'))
raise SystemExit(bool(any(results.values())))
