"""Read-only accepted Codel Core/browser regressions; no candidate rig is authored."""
import argparse
import json
from pathlib import Path
import subprocess
from live2d_studio.pose_review import REPO,digest,write
from live2d_studio.preview_live import DEFAULT_EXTENSION
from live2d_studio.creation_validation import validate_runtime


def run(output):
 pin=json.loads((REPO/'docs/references/codel-combined-v1.json').read_text());root=REPO/pin['reference_root'];model=root/pin['paths']['model']
 if digest(root/pin['manifest'])!=pin['manifest_sha256']:raise ValueError('Reference manifest changed')
 for name,h in pin['runtime_files'].items():
  if digest(model.parent/name)!=h:raise ValueError('Runtime reference changed')
 output=output.resolve()
 if not output.is_relative_to(REPO/'runs') or output.is_relative_to(REPO/'runs/references'):raise ValueError('Fresh ignored output required')
 output.mkdir(parents=True,exist_ok=False);author=(root/pin['paths']['editable_project']).parent;core=DEFAULT_EXTENSION/'lib/live2dcubismcore.min.js';results={}
 for name,script,extra in [('body','probe_body.cjs',[author/'body-inspection.json']),('mouth','probe_expressions.cjs',[author/'mouth-inspection.json',model.parent.parent/'mouth-contract.json'])]:
  p=subprocess.run(['node',str(REPO/'scripts'/script),str(core),str(model),*[str(v) for v in extra]],text=True,capture_output=True,timeout=60)
  (output/(name+'-core.json')).write_text(p.stdout);(output/(name+'-core.log')).write_text(p.stderr)
  if p.returncode:raise ValueError(name+' Core regression failed')
  r=json.loads(p.stdout);results[name]={'status':r['status'],'samples':len(r['samples']),'report_sha256':digest(output/(name+'-core.json'))};print(name,'Core passed',flush=True)
 for name,scenario in [('dense','phase4b3_transition_scenario.js'),('body','phase4b6_body_scenario.js'),('coexistence','phase4b6_1_coexistence_scenario.js')]:
  folder=output/name;folder.mkdir();validate_runtime(model,folder,DEFAULT_EXTENSION,REPO/'scripts'/scenario)
  r=json.loads((folder/'frames/result.json').read_text())['result']['value'];results[name+'-browser']={'status':r['status'],'frames':len(r['frames']),'result_sha256':digest(folder/'frames/result.json')};print(name,'browser passed',flush=True)
 write(output/'summary.json',{'scope':'Fresh regressions of unchanged accepted reference; not a new arm-rig validation','reference_manifest_sha256':pin['manifest_sha256'],'results':results})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
