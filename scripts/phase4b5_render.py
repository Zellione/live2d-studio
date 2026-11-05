"""Additional high-resolution visual evidence; existing dense gates are unchanged."""
import argparse
from pathlib import Path
from live2d_studio.creation_validation import validate_runtime, REPO
from live2d_studio.preview_live import DEFAULT_EXTENSION

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    validate_runtime(a.model.resolve(), a.output.resolve(), DEFAULT_EXTENSION,
                     REPO / 'scripts/phase4b5_detail_scenario.js')
