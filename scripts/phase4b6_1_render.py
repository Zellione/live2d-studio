"""Controlled expression stills or continuous expression/body coexistence."""
import argparse
from pathlib import Path
from live2d_studio.creation_validation import validate_runtime,REPO
from live2d_studio.preview_live import DEFAULT_EXTENSION
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',choices=['face','coexistence','comparison'],required=True);p.add_argument('--compare-model',type=Path);a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
validate_runtime(a.model.resolve(),a.output,DEFAULT_EXTENSION,REPO/f'scripts/phase4b6_1_{a.mode}_scenario.js',comparison=a.compare_model)
