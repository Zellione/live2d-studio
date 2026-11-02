"""Numerical warnings and pose sheets from actual extension-rendered RGBA frames.

Counts are diagnostic candidates. Hair gaps, blinking and intentional drawables
can change them legitimately; numerical validity never grants visual acceptance.
"""
import json
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw
from .manifest import digest,write_json


def diagnose(a):
    fg=a[...,3]>127
    labels,n=ndi.label(fg)
    sizes=np.bincount(labels.ravel())[1:]
    holes=ndi.binary_fill_holes(fg)&~fg
    _,hole_n=ndi.label(holes)
    rgb=a[...,:3].astype(float)
    dx=np.max(np.abs(np.diff(rgb,axis=1)),axis=2)
    dy=np.max(np.abs(np.diff(rgb,axis=0)),axis=2)
    internal_x=fg[:,1:]&fg[:,:-1];internal_y=fg[1:]&fg[:-1]
    jumps=int(((dx>96)&internal_x).sum()+((dy>96)&internal_y).sum())
    return dict(foreground_pixels=int(fg.sum()),components=n,
        detached_small_component_pixels=int(sizes[sizes<max(3,int(fg.sum()*.001))].sum()),
        enclosed_transparent_pixels=int(holes.sum()),enclosed_holes=hole_n,
        strong_internal_colour_steps=jumps,
        fractional_alpha_pixels=int(((a[...,3]>0)&(a[...,3]<255)).sum()))


def review(frames,output):
    frames,output=Path(frames),Path(output)
    if output.exists():raise FileExistsError('Choose a fresh QA directory')
    result=json.loads((frames/'result.json').read_text())['result']['value']
    names=[n for n in result['frames'] if n not in ('neutral-repeat','reload')]
    if 'neutral' not in names:raise ValueError('Missing neutral reference')
    arrays={}
    for name in names:
        if not name.replace('_','').replace('-','').isalnum():raise ValueError('Unsafe frame name')
        arrays[name]=np.array(Image.open(frames/(name+'.png')).convert('RGBA'))
    if len({a.shape for a in arrays.values()})!=1:raise ValueError('Frame dimensions differ')
    output.mkdir(parents=True,exist_ok=False)
    masks=[a[...,3]>127 for a in arrays.values()]
    union=np.logical_or.reduce(masks);ys,xs=np.nonzero(union)
    if not len(xs):raise ValueError('No rendered foreground')
    box=(max(0,int(xs.min())-10),max(0,int(ys.min())-10),min(union.shape[1],int(xs.max())+11),min(union.shape[0],int(ys.max())+11))
    records={name:diagnose(a) for name,a in arrays.items()}
    neutral=records['neutral']
    for name,r in records.items():
        r['extra_enclosed_transparent_pixels']=r['enclosed_transparent_pixels']-neutral['enclosed_transparent_pixels']
        r['foreground_area_ratio']=r['foreground_pixels']/max(1,neutral['foreground_pixels'])
        r['source_frame_sha256']=digest(frames/(name+'.png'))
        r['geometry']=result.get('geometry',{}).get(name,{})
        r['warning_candidates']=[]
        if r['extra_enclosed_transparent_pixels']>0:r['warning_candidates'].append('new/increased transparency hole; inspect location')
        if r['detached_small_component_pixels']>neutral['detached_small_component_pixels']:r['warning_candidates'].append('extra small detached components')
        if r['geometry'].get('new_triangle_flips',0):r['warning_candidates'].append('triangle orientation changed; inspect blink/pose geometry')
        if r['geometry'].get('expanded_triangles',0):r['warning_candidates'].append('triangle area grew over 10x')
    sheet=Image.new('RGB',(1400,450*((len(names)+3)//4)),(235,235,235))
    for i,name in enumerate(names):
        im=Image.fromarray(arrays[name]).crop(box);im.thumbnail((340,415))
        x,y=(i%4)*350,(i//4)*450
        sheet.paste(im,(x+(350-im.width)//2,y+28),im)
        ImageDraw.Draw(sheet).text((x+5,y+6),name,fill='black')
    sheet.save(output/'poses.png')
    report=dict(schema_version=1,render_status=result['status'],control_noise_pixels=result['control_noise_pixels'],
        network=result.get('network_validation'),poses=records,
        visual_animation='requires-review',production_ready=False,
        unautomated=['duplicate contours versus legitimate adjacent line art','natural eyelid shape',
            'identity fidelity','plausible hidden geometry','disappearing features versus intended blink'],
        note='Hole/component/colour/triangle counts flag candidates, not aesthetic pass/fail.')
    write_json(output/'quality.json',report)
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Actual runtime pose review</title>'
        '<h1>Actual runtime poses — independent visual judgement required</h1><p>Neutral includes zero head angles. '
        'Single axes ±15°, eight combined poses. Numerical diagnostics are in quality.json.</p>'
        '<img src="poses.png" style="max-width:100%">')
    return report
