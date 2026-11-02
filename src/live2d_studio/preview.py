"""Offline visual QA: no network, browser scripts or proprietary editor required."""
from html import escape
import numpy as np
from PIL import Image, ImageDraw


def preview(root, manifest, original):
    size = original.size
    composite = Image.new('RGBA', size)
    overlay = np.zeros((size[1],size[0],4), np.uint8)
    reconstructed = np.zeros_like(overlay)
    cells = []
    for i, layer in enumerate(manifest['layers']):
        image = Image.open(root/layer['rgba_path'])
        x,y,w,h = (layer[k] for k in ('x','y','width','height'))
        if layer['default_visible']:
            composite.alpha_composite(image, (x,y))
        mask = np.array(Image.open(root/layer['mask_path']))>0
        rec = np.array(Image.open(root/layer['reconstructed_mask_path']))>0
        overlay[y:y+h,x:x+w][mask] = ((i*73+41)%256,(i*113+97)%256,(i*157+53)%256,255)
        reconstructed[y:y+h,x:x+w][rec] = (255,0,150,255)
        tile = Image.new('RGBA',(200,200),(225,225,225,255))
        thumb = image.copy()
        thumb.thumbnail((180,160))
        tile.alpha_composite(thumb,((200-thumb.width)//2,24))
        ImageDraw.Draw(tile).text((5,5), layer['id'], fill='black')
        cells.append(tile)
    composite.save(root/'preview/composite.png')
    Image.fromarray(overlay).save(root/'preview/segmentation.png')
    Image.fromarray(reconstructed).save(root/'preview/reconstructed.png')
    sheet = Image.new('RGBA',(800,200*((len(cells)+3)//4)), 'white')
    for i,cell in enumerate(cells):
        sheet.alpha_composite(cell, ((i%4)*200,(i//4)*200))
    sheet.save(root/'preview/layers.png')
    warnings = ''.join('<li>'+escape(w)+'</li>' for w in manifest['warnings'])
    figures = ''.join(f'<figure><img src="{name}"><figcaption>{label}</figcaption></figure>' for name,label in [
        ('../source/normalized.png','Input'),('composite.png','Composite (default-visible layers)'),
        ('segmentation.png','Visible regions'),('reconstructed.png','Reconstructed/generated pixels'),('layers.png','All layers')])
    rights = escape(manifest['sources'][0]['rights'])
    (root/'preview/index.html').write_text('<!doctype html><meta charset="utf-8"><title>Layer review</title>'
        '<style>body{font:16px sans-serif;background:#eee}figure{display:inline-block;vertical-align:top}'
        'img{max-width:800px;max-height:600px;background:repeating-conic-gradient(#ddd 0% 25%,white 0% 50%) 0/16px 16px}</style>'
        '<h1>Candidate layers — visual review required</h1><p>'+rights+'</p><ul>'+warnings+'</ul>'+figures)
    return np.array(composite)
