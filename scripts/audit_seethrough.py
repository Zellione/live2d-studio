#!/usr/bin/env python3
"""Fetch public metadata/licenses only; never download weights or use credentials."""
import argparse
import json
from pathlib import Path
import urllib.request

REPOSITORIES = {
    'layerdiff': 'layerdifforg/seethroughv0.0.2_layerdiff3d',
    'depth': '24yearsold/seethroughv0.0.1_marigold',
    'sam': '24yearsold/l2d_sam_iter2',
}


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read(2_000_000)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    result = {}
    for name, repo in REPOSITORIES.items():
        info = json.loads(fetch(f'https://huggingface.co/api/models/{repo}?blobs=true'))
        revision = info['sha']
        files = [{'path': f['rfilename'], 'bytes': f['size'],
                  'sha256': f.get('lfs', {}).get('sha256')}
                 for f in info['siblings']]
        record = {'repo': repo, 'revision': revision, 'card': info.get('cardData'),
                  'files': files, 'total_bytes': sum(f['bytes'] for f in files)}
        result[name] = record
        for f in files:
            if f['path'] in {'README.md', 'LICENSE', 'NOTICE', 'model_index.json', 'unet/config.json'}:
                content = fetch(f"https://huggingface.co/{repo}/resolve/{revision}/{f['path']}")
                (args.output/(name+'-'+f['path'].replace('/', '-'))).write_bytes(content)
        print(name, revision, record['total_bytes'], record['card'], flush=True)
    (args.output/'models.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
