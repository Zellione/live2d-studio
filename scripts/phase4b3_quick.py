"""Diagnostic dense static poses only; never a substitute for full temporal review."""
import argparse
from pathlib import Path
from live2d_studio.creation_validation import validate_runtime,REPO
from live2d_studio.preview_live import DEFAULT_EXTENSION
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
source=(REPO/'scripts/phase4b3_transition_scenario.js').read_text().split('  // Continuous parameter trajectories')[0]
source+="report.status='pass';}catch(e){report.status='fail';report.error=String(e)}window.phase4b3Frames=report.frames;report.frames=Object.keys(report.frames);report.remote_frames=true;return report;})()"
scenario=a.output/'static-scenario.js';scenario.write_text(source)
validate_runtime(a.model.resolve(),a.output,DEFAULT_EXTENSION,scenario)
