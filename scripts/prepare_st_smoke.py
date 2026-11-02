"""Copy installed ST code/dependencies into a fresh, isolated test directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--extension', type=Path, required=True)
parser.add_argument('--destination', type=Path, required=True)
args = parser.parse_args()
src, ext, dest = args.source.resolve(), args.extension.resolve(), args.destination.resolve()
if dest.exists():
    parser.error('Destination already exists; use a fresh directory')
if dest.is_relative_to(src) or src.is_relative_to(dest):
    parser.error('Test destination must be separate from source')
dest.mkdir(parents=True)
hashes = {}
for folder in ['src', 'public', 'default']:
    shutil.copytree(src / folder, dest / folder, ignore=shutil.ignore_patterns('third-party'))
for name in ['server.js', 'plugins.js', 'package.json', 'package-lock.json', 'webpack.config.js', 'LICENSE']:
    shutil.copy2(src / name, dest / name)
# Independent copies, never links into the production installation.
subprocess.run(['cp', '-a', '--reflink=auto', str(src / 'node_modules'), str(dest / 'node_modules')], check=True)
extension_dest = dest / 'data/default-user/extensions/Extension-Live2d'
shutil.copytree(ext, extension_dest, ignore=shutil.ignore_patterns('.git'))
fixture = Path(__file__).resolve().parents[1] / 'tests/fixtures/phase0/export'
shutil.copytree(fixture, dest / 'data/default-user/assets/live2d/phase0')
for original_root, copied_root in [(src/'src', dest/'src'), (ext, extension_dest)]:
    for copied in sorted(copied_root.rglob('*')):
        if copied.is_file():
            relative = copied.relative_to(copied_root)
            original = original_root / relative
            digest = hashlib.sha256(copied.read_bytes()).hexdigest()
            assert digest == hashlib.sha256(original.read_bytes()).hexdigest()
            hashes[str(copied.relative_to(dest))] = digest
(dest / 'snapshot-hashes.json').write_text(json.dumps(hashes, indent=2))
# Fresh configuration: no existing config, profiles, secrets or chats copied.
(dest / 'config.yaml').write_text('''listen: false
port: 8766
browserLaunch:
  enabled: false
extensions:
  enabled: true
  autoUpdate: false
  models:
    autoDownload: false
enableServerPlugins: false
''')
print(dest)
