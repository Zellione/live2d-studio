"""Continuous body/idle/gesture evidence using the installed Core and local viewer."""
import argparse
from pathlib import Path
from live2d_studio.creation_validation import validate_runtime,REPO
from live2d_studio.preview_live import DEFAULT_EXTENSION
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--compare-model',type=Path);a=p.parse_args()
 a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
 validate_runtime(a.model.resolve(),a.output,DEFAULT_EXTENSION,REPO/'scripts/phase4b6_body_scenario.js',comparison=a.compare_model)
