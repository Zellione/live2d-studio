"""Offline Cubism bundle validator; preserved historical CLI."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from live2d_studio.bundle import validate

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path)
    args=parser.parse_args()
    result=validate(args.model)
    print(json.dumps(result,indent=2))
    sys.exit(result['status']!='pass')
