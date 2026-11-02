"""Run inside GIMP 3's python-fu-eval; exports visible Girl2 leaves as raw RGBA.

GIMP3_DIRECTORY must point to an isolated local profile. Supply OGA_XCF and
OGA_OUTPUT as absolute paths. No save operation touches the source XCF.
"""
import json
import os
from pathlib import Path
from gi.repository import Gimp, Gio, Gegl

out = Path(os.environ['OGA_OUTPUT'])
out.mkdir(parents=True, exist_ok=False)
image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, Gio.File.new_for_path(os.environ['OGA_XCF']))
group = next(g for g in image.get_layers() if g.get_name() == 'Girl2')
records = []


def export(layer, ident):
    buffer = layer.get_buffer()
    extent = buffer.get_extent()
    data = bytes(buffer.get(extent, 1.0, "R'G'B'A u8", Gegl.AbyssPolicy.NONE))
    (out/(ident+'.rgba')).write_bytes(data)
    _, x, y = layer.get_offsets()
    return dict(name=layer.get_name(), path=ident+'.rgba', width=extent.width,
                height=extent.height, x=x, y=y, opacity=layer.get_opacity(),
                mode=int(layer.get_mode()))


def walk(layers):
    for layer in layers:
        if not layer.get_visible():
            continue
        if layer.is_group():
            walk(layer.get_children())
        else:
            records.append(export(layer, f'layer-{len(records):02d}'))


walk(group.get_children())
projection = export(group, 'projection')
(out/'extraction.json').write_text(json.dumps(dict(
    width=image.get_width(), height=image.get_height(), group=group.get_name(),
    order='front-to-back', layers=records, projection=projection,
    gimp_version=Gimp.version()), indent=2)+'\n')
image.delete()
