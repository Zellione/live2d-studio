"""Run Core, continuous body and dense facial gates on one exported candidate."""
import argparse,subprocess,json
from pathlib import Path
from live2d_studio.creation_validation import validate_runtime,REPO
from live2d_studio.preview_live import DEFAULT_EXTENSION
from live2d_studio.manifest import write_json
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['model','inspection','correspondence','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--compare-model',type=Path);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 r=subprocess.run(['node',str(REPO/'scripts/probe_body.cjs'),str(DEFAULT_EXTENSION/'lib/live2dcubismcore.min.js'),str(a.model.resolve()),str(a.inspection.resolve())],text=True,capture_output=True)
 (out/'core-body.json').write_text(r.stdout);(out/'core-body.log').write_text(r.stderr)
 if r.returncode:raise RuntimeError('Broad Core geometry audit failed')
 for name,scenario in [('body-review','phase4b6_body_scenario.js'),('dense','phase4b3_transition_scenario.js')]:
  folder=out/name;folder.mkdir()
  validate_runtime(a.model.resolve(),folder,DEFAULT_EXTENSION,REPO/'scripts'/scenario,
                   transition_plan=a.correspondence if name=='dense' else None,
                   comparison=a.compare_model if name=='body-review' else None)
  print(name,'pass',flush=True)
 write_json(out/'summary.json',dict(status='pass',visual_acceptance=False))
