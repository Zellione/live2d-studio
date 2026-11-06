"""Opt-in frontal working bases; original artwork and synthetic geometry stay distinct."""
import numpy as np
from PIL import Image,ImageDraw

TITLE='Front-facing neutral base'
PROMPT=('Redraw the character in picture 1 as a straight-on front-facing neutral character base. '
        'The face, chest and pelvis face directly toward the viewer, with the nose centered between the eyes, '
        'level shoulders and both shoulders equally visible. No three-quarter turn, body lean or head tilt. '
        'Both arms hang relaxed slightly away from the torso, with both sleeves, wrists and hands visible. '
        'Leave a narrow background gap between each forearm and the torso. No crossed arms or hands behind the body. '
        'Use picture 2 only for the frontal body placement, not its mannequin appearance. '
        'Preserve the same recognizable facial features, neutral expression, hairstyle, outfit design, neckline, '
        'sleeves, hem, body proportions, illustration style and colour palette from picture 1. '
        'Keep the same head-to-upper-leg framing on plain white. Do not add feet beyond the original crop. '
        'Only reconstruct the previously hidden areas needed for this frontal neutral view.')
WORKER='backends/inpainting/pose_reference_worker.py'


def frontal_guide(image,pose='canonical',kind='silhouette'):
    rgba=np.asarray(image.convert('RGBA'));a=rgba[...,3]
    mask=a>127
    if np.all(a==255):mask=np.max(abs(rgba[...,:3].astype(float)-255),axis=2)>24
    yy,xx=np.where(mask)
    if not len(xx):raise ValueError('No visible character for guide framing')
    y0,y1=float(yy.min()),float(yy.max());height=y1-y0
    width=min(float(xx.max()-xx.min())*1.22,image.width*.88)
    center=image.width/2
    points={'nose':(.5,.16),'neck':(.5,.25),'rs':(.25,.27),'ls':(.75,.27),
            're':(.19,.45),'le':(.81,.45),'rw':(.10,.64),'lw':(.90,.64),
            'rh':(.34,.64),'lh':(.66,.64),'rk':(.39,.96),'lk':(.61,.96),
            'right_eye':(.42,.12),'left_eye':(.58,.12),'right_ear':(.33,.135),'left_ear':(.67,.135)}
    changes={'canonical':{},'right-lift':{'re':(.12,.43),'rw':(.03,.56)},
             'left-lift':{'le':(.88,.43),'lw':(.97,.56)},
             'explain':{'re':(.16,.43),'rw':(.01,.36)},
             'wave':{'le':(.88,.39),'lw':(.96,.22)},
             'torso-open':{'re':(.12,.43),'rw':(.02,.61),'le':(.88,.43),'lw':(.98,.61)}}
    if pose not in changes:raise ValueError('Unknown canonical-frame pose')
    points.update(changes[pose]);points={k:(center+(x-.5)*width,y0+y*height) for k,(x,y) in points.items()}
    if any(x<0 or y<0 or x>=image.width or y>=image.height for x,y in points.values()):raise ValueError('Guide outside source framing')
    out=Image.new('RGB',image.size,'black' if kind=='skeleton' else 'white');d=ImageDraw.Draw(out)
    unit=max(3,round(image.height/180))
    edges=[('neck','rs'),('rs','re'),('re','rw'),('neck','ls'),('ls','le'),('le','lw'),
           ('neck','rh'),('rh','rk'),('neck','lh'),('lh','lk'),('rh','lh'),('nose','neck'),
           ('nose','right_eye'),('right_eye','right_ear'),('nose','left_eye'),('left_eye','left_ear')]
    colors=['#ff0000','#ffaa00','#ffff00','#aaff00','#55ff00','#00ff00','#00ffaa','#00aaff',
            '#0055ff','#5500ff','#aa00ff','#ff0055','#ff00ff','#ff0055','#aa00ff','#ff00aa']
    if kind=='silhouette':
        d.polygon([points[k] for k in ('rs','ls','lh','rh')],fill='#aaaaaa')
        cy=y0+.13*height;rx=width*.17;ry=height*.105
        d.ellipse((center-rx,cy-ry,center+rx,cy+ry),fill='#aaaaaa')
    for i,(a,b) in enumerate(edges):d.line([points[a],points[b]],fill=colors[i] if kind=='skeleton' else '#777777',width=unit if kind=='skeleton' else unit*5)
    for x,y in points.values():d.ellipse((x-unit,y-unit,x+unit,y+unit),fill='white' if kind=='skeleton' else '#555555')
    return out,points

