"""Fresh portrait regressions for the optional body authoring path. No inference."""
import argparse,json,subprocess
from pathlib import Path
from live2d_studio.body_rig import prepare
from live2d_studio.creation_validation import validate_runtime,REPO
from live2d_studio.preview_live import DEFAULT_EXTENSION
from live2d_studio.manifest import write_json
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
failures=[]
for name,base in [('girl2','phase4b3-girl2-deterministic-final'),('sara','phase4b3-sara-create-final')]:
 out=a.output/name;result=prepare(REPO/'runs'/base,out);model=Path(result['model']);print(name,result,flush=True)
 proc=subprocess.run(['node',str(REPO/'scripts/probe_body.cjs'),str(DEFAULT_EXTENSION/'lib/live2dcubismcore.min.js'),str(model),str(out/'authoring/body-inspection.json')],capture_output=True,text=True)
 (out/'core-body.json').write_text(proc.stdout);(out/'core-body.log').write_text(proc.stderr)
 if proc.returncode:
  failures.append(name+' body Core');print(name,'body Core FAILED; retaining report and continuing independent render evidence',flush=True)
 for suite,scenario in [('body-review','phase4b6_body_scenario.js'),('dense','phase4b3_transition_scenario.js')]:
  folder=out/suite;folder.mkdir();validate_runtime(model,folder,DEFAULT_EXTENSION,REPO/'scripts'/scenario)
 print(name,'runtime suites passed',flush=True)

write_json(a.output/'summary.json',dict(status='fail' if failures else 'pass',failures=failures))
if failures:raise SystemExit(1)
