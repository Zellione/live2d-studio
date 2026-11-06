"""Real installed Core and browser gates for optional arm outputs."""
import json
from pathlib import Path
import subprocess
import shutil
from .manifest import digest,write_json
from .preview_live import DEFAULT_EXTENSION
from .creation_validation import validate_runtime,REPO


def validation_pins():
    names=['src/live2d_studio/arm_validation.py','src/live2d_studio/creation_validation.py',
           'src/live2d_studio/preview_ui/viewer.js','scripts/arm_pipeline_scenario.js',
           'scripts/probe_body.cjs','scripts/probe_expressions.cjs','scripts/phase4b6_1_coexistence_scenario.js']
    return {n:digest(REPO/n) for n in names}|{'core':digest(DEFAULT_EXTENSION/'lib/live2dcubismcore.min.js')}


def validate_arms(model,authoring,out):
    results={};core=DEFAULT_EXTENSION/'lib/live2dcubismcore.min.js'
    for name,script,args in [('body-elbows','probe_body.cjs',[model,authoring/'body-inspection.json','--elbows']),
        ('mouth','probe_expressions.cjs',[model,authoring/'mouth-inspection.json',model.parent.parent/'mouth-contract.json'])]:
        with (out/(name+'.json')).open('w') as f,(out/(name+'.log')).open('w') as log:
            r=subprocess.run(['node',str(REPO/'scripts'/script),str(core),*map(str,args)],stdout=f,stderr=log)
        results[name]=r.returncode
    for name,scenario in [('arms','arm_pipeline_scenario.js'),('coexistence','phase4b6_1_coexistence_scenario.js')]:
        folder=out/name;folder.mkdir()
        try:validate_runtime(model,folder,DEFAULT_EXTENSION,REPO/'scripts'/scenario)
        except Exception as e:results[name]=type(e).__name__
        else:results[name]=0
        finally:
            # Keep Chromium's sockets/profile diagnostics outside the immutable
            # stage inventory. Do not delete them or relax symlink rejection.
            profile=folder.parent/(folder.name+'-browser-profile')
            if profile.exists():
                archive=out.parents[1]/'browser-profiles'/out.name
                archive.mkdir(parents=True,exist_ok=True)
                shutil.move(str(profile),str(archive/profile.name))
    write_json(out/'summary.json',{'results':results,'status':'pass' if not any(results.values()) else 'fail','visual_acceptance':False})
    if any(results.values()):raise ValueError('Arm validation failed; retain diagnostic reports')
