#!/usr/bin/env python3
"""Download the approved, audited See-through snapshots and verify LFS hashes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--approved', action='store_true', required=True)
    args = p.parse_args()
    lock = json.loads((ROOT/'backends/see-through/models.lock.json').read_text())
    env = dict(os.environ, HF_HOME=str(ROOT/'.cache/phase2-5-hf'),
               HF_HUB_DISABLE_IMPLICIT_TOKEN='1', HF_HUB_DISABLE_TELEMETRY='1')
    for key, model in lock['repositories'].items():
        dest = ROOT/'models/see-through'/key/model['revision']
        subprocess.run(['hf', 'download', model['repo'], '--revision', model['revision'],
                        '--local-dir', str(dest), '--max-workers', '4'], env=env, check=True)
        for item in model['files']:
            file = dest/item['path']
            if file.stat().st_size != item['bytes']:
                raise ValueError(f'Wrong size: {file}')
            if item['sha256']:
                with file.open('rb') as stream:
                    checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
                if checksum != item['sha256']:
                    raise ValueError(f'Wrong checksum: {file}')
        print(key, 'verified', flush=True)


if __name__ == '__main__':
    main()
