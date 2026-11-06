"""Build a reviewed frontal candidate with the existing facial/body authoring."""
import argparse
import json
from pathlib import Path
from live2d_studio.manifest import digest
from live2d_studio.stages import Stages, inventory
from live2d_studio.mcp import MCP
from live2d_studio import generic_rig, performance, body_rig
from live2d_studio.frontal_master import load


def build(master, facial, review, output, until='body'):
    master, facial, review, output = [Path(p).resolve() for p in (master, facial, review, output)]
    load(master)
    approval = json.loads((review / 'approval.json').read_text())
    if approval.get('reviewer_kind') != 'human' or approval.get('decision') != 'accept':
        raise ValueError('Human decomposition/backing approval required')
    if digest(review / 'evidence.json') != approval['evidence_sha256']:
        raise ValueError('Review evidence changed')
    for file, expected in approval['files'].items():
        if digest(file) != expected:
            raise ValueError('Approved decomposition changed')
    if digest(facial / 'layers/layer_manifest.json') not in approval['files'].values():
        raise ValueError('Facial layers not reviewed')
    identity = {'pipeline': 'frontal-master-v1', 'master_sha256': digest(master / 'master.json'),
                'approval_sha256': digest(review / 'approval.json')}
    stages = Stages(output, identity); client = MCP('http://127.0.0.1:23871/mcp')
    with stages.locked():
        previous = facial
        for name, author in [
            ('project', lambda p, o: generic_rig.create_project(client, facial / 'layers', o, facial_motion='aligned')),
            ('rig', lambda p, o: generic_rig.author_rig(client, p, o)),
            ('animation', lambda p, o: generic_rig.author_animation(client, p, o)),
            ('mouths', lambda p, o: performance.author_mouths(client, p, facial / 'layers', o)),
            ('body', lambda p, o: body_rig.author(client, p, facial / 'layers', o / 'authoring')),
        ]:
            parent = previous
            print(name, flush=True)
            previous = stages.run(name, {'parent': inventory(parent), 'script_sha256': digest(__file__)},
                                  lambda out: author(parent, out))
            if name == 'body': previous = previous / 'authoring'
            if until == name: break
        stages.data['authoring'] = str(previous.relative_to(output))
        stages.data['status'] = 'candidate-awaiting-motion-validation'
        stages.save()
        return previous


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('master', 'facial', 'review', 'output'): p.add_argument('--'+name, required=True, type=Path)
    p.add_argument('--until', default='body', choices=['project', 'rig', 'animation', 'mouths', 'body'])
    print(build(**vars(p.parse_args())))
