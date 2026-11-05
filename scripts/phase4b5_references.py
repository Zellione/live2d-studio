"""Export evaluation-only PSD evidence after verifying a sealed blind creation run.

Run in the existing See-through environment for psd-tools. Nothing exported here
may be passed to create. Numbered raster layers are artist composition evidence,
not automatically semantic ground truth.
"""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from PIL import Image
from psd_tools import PSDImage


def digest(file):
    with Path(file).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--seal', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    seal = json.loads(a.seal.read_text())
    run = Path(seal['run'])
    for name, expected in seal['files'].items():
        file = (run / name).resolve()
        if not file.is_relative_to(run.resolve()) or digest(file) != expected:
            raise ValueError('Sealed first-run evidence changed: ' + name)
    if digest(a.archive) != seal['archive_sha256']:
        raise ValueError('Archive changed')
    a.output.mkdir(parents=True, exist_ok=False)
    archive = a.output / 'archive'
    archive.mkdir()
    members = []
    with ZipFile(a.archive) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = Path(info.filename)
            if name.name != info.filename or name.suffix.lower() not in {'.psd', '.png'}:
                raise ValueError('Unexpected archive member')
            file = archive / name
            file.write_bytes(z.read(info))
            members.append(dict(name=info.filename, bytes=info.file_size, sha256=digest(file)))
    psd = PSDImage.open(archive / 'Codel.psd')
    rows = []
    (a.output / 'layers').mkdir()

    def visit(container, parents=()):
        for layer in container:
            index = len(rows)
            row = dict(index=index, name=layer.name, parents=list(parents),
                       kind=layer.kind, visible=layer.visible, effective_visible=layer.is_visible(),
                       opacity=layer.opacity, blend_mode=str(layer.blend_mode), bbox=list(layer.bbox))
            rows.append(row)
            if layer.is_group():
                visit(layer, (*parents, layer.name))
            else:
                image = layer.topil()
                if image is not None:
                    canvas = Image.new('RGBA', psd.size)
                    canvas.paste(image.convert('RGBA'), (layer.left, layer.top))
                    dest = a.output / 'layers' / f'{index:02d}.png'
                    canvas.save(dest)
                    row.update(path=str(dest.relative_to(a.output)), sha256=digest(dest))

    visit(psd)
    # Embedded merged preview records the artist's saved visibility state. It is
    # explicitly not assumed to equal the selected neutral PNG.
    merged = psd.topil()
    if merged is not None:
        merged.save(a.output / 'saved-merged.png')
    report = dict(archive_sha256=digest(a.archive), seal_sha256=digest(a.seal),
                  dimensions=list(psd.size), members=members, layers=rows,
                  scope='evaluation-only; no semantic labels inferred from names',
                  psd_tools_version=__import__('importlib.metadata', fromlist=['version']).version('psd-tools'))
    (a.output / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(dimensions=report['dimensions'], layers=rows), indent=2))


if __name__ == '__main__':
    main()
