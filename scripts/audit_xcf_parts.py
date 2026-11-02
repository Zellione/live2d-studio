"""Read-only GIMP 3 inventory, including hidden leaves and off-canvas pixels.

Run with python-fu-eval and XCF_AUDIT_INPUT / XCF_AUDIT_OUTPUT environment
variables; optional XCF_AUDIT_GROUP defaults to Girl2. Use an isolated profile.
Raw RGBA exports are audit evidence only, never pipeline inputs.
"""
import hashlib
import json
import os
from pathlib import Path
from gi.repository import Gimp, Gio, Gegl

source = Path(os.environ['XCF_AUDIT_INPUT'])
out = Path(os.environ['XCF_AUDIT_OUTPUT'])
before = hashlib.sha256(source.read_bytes()).hexdigest()
out.mkdir(parents=True, exist_ok=False)
image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, Gio.File.new_for_path(str(source)))
group = next(g for g in image.get_layers() if g.get_name() == os.environ.get('XCF_AUDIT_GROUP', 'Girl2'))
records = []


def walk(layer, parents_visible=True):
    _, x, y = layer.get_offsets()
    record = dict(name=layer.get_name(), visible=layer.get_visible(),
                  effective_visible=parents_visible and layer.get_visible(),
                  group=layer.is_group(), x=x, y=y,
                  width=layer.get_width(), height=layer.get_height())
    records.append(record)
    if layer.is_group():
        for child in layer.get_children():
            walk(child, record['effective_visible'])
    else:
        buffer = layer.get_buffer()
        extent = buffer.get_extent()
        raw = bytes(buffer.get(extent, 1.0, "R'G'B'A u8", Gegl.AbyssPolicy.NONE))
        record['path'] = f'leaf-{len(records):02d}.rgba'
        (out/record['path']).write_bytes(raw)


# The selected group is evaluated independently of other character groups.
for child in group.get_children():
    walk(child)
buffer = group.get_buffer()
extent = buffer.get_extent()
_, x, y = group.get_offsets()
(out/'projection.rgba').write_bytes(bytes(buffer.get(extent, 1.0, "R'G'B'A u8", Gegl.AbyssPolicy.NONE)))
report = dict(source_sha256=before, gimp_version=Gimp.version(), group=group.get_name(),
              canvas=[image.get_width(), image.get_height()], layers=records,
              projection=dict(path='projection.rgba', width=extent.width, height=extent.height, x=x, y=y))
image.delete()
assert hashlib.sha256(source.read_bytes()).hexdigest() == before
(out/'inventory.json').write_text(json.dumps(report, indent=2)+'\n')
