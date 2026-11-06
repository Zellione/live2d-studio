"""Promote a reviewed canonical or create its frontal character in a fresh run."""
import argparse
import json
from pathlib import Path
from live2d_studio.frontal_master import promote, create, prepare, review

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    f = sub.add_parser('promote')
    f.add_argument('--canonical-run', type=Path, required=True)
    f.add_argument('--family', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    f = sub.add_parser('create')
    f.add_argument('--master', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    f.add_argument('--sam', type=Path)
    f.add_argument('--until', default='readiness')
    f = sub.add_parser('prepare')
    for name in ('master','inference-run','geometry','output'): f.add_argument('--'+name,type=Path,required=True)
    f.add_argument('--repair-brows',action='store_true')
    f = sub.add_parser('helpers')
    for name in ('master','output','presets'): f.add_argument('--'+name,type=Path,required=True)
    f = sub.add_parser('review')
    f.add_argument('--folder',type=Path,required=True)
    f.add_argument('--decision',choices=['accept','reject'],required=True)
    f.add_argument('--reviewer',required=True);f.add_argument('--notes',required=True)
    f = sub.add_parser('repair-brows')
    f.add_argument('--project',type=Path,required=True);f.add_argument('--output',type=Path,required=True)
    a = vars(p.parse_args()); command = a.pop('command')
    if command == 'review': result = review(**a)
    elif command == 'repair-brows':
        from live2d_studio.frontal_face import repair
        result = repair(**a)
    elif command == 'promote': result = promote(**a)
    elif command == 'prepare': result = prepare(**a)
    elif command == 'helpers':
        from live2d_studio.frontal_family import initialize
        a['presets'] = json.loads(a['presets'].read_text())
        result = {'run':str(initialize(**a).root)}
    else: result = create(**a, preview=False)
    print(json.dumps(result, indent=2))
