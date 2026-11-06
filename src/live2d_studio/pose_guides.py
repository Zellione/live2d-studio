"""Programmatic pose hypotheses on a source-relative skeleton; no anatomical truth."""
import math
from PIL import Image, ImageDraw
import numpy as np

POSES = {
    'right-lift': ('Right arm slight lift', 'Move her right arm (viewer left) away from her torso, elbow low, hand beside her waist. Keep the left arm hanging.'),
    'left-lift': ('Left arm slight lift', 'Move her left arm (viewer right) slightly away from her side with the hand low. Keep the other arm relaxed.'),
    'explain': ('Small explanatory gesture', 'Bend her right elbow close to her waist and turn the right palm upward in a small explanatory gesture.'),
    'wave': ('Modest greeting', 'Bend her left elbow beside her torso and raise the left hand near shoulder height, palm forward, in a modest wave.'),
    'torso-open': ('Expose torso clothing', 'Uncross her right arm and move it aside, leaving both arms slightly away from the torso to reveal the front of the same clothing.')}


def layout(size, long_edge):
    if long_edge not in (1024,1536):
        raise ValueError('Output long edge must be 1024 or 1536')
    scale=long_edge/max(size)
    dims=tuple(math.ceil(v*scale/16)*16 for v in size)
    return dims,scale,tuple((d-v*scale)/2 for d,v in zip(dims,size))


def fit(image, long_edge):
    dims,scale,(ox,oy)=layout(image.size,long_edge)
    rgb=Image.alpha_composite(Image.new('RGBA',image.size,'white'),image.convert('RGBA')).convert('RGB')
    return rgb.transform(dims,Image.Transform.AFFINE,(1/scale,0,-ox/scale,0,1/scale,-oy/scale),
                         Image.Resampling.BICUBIC,fillcolor='white')


def joints(image, pose):
    if pose not in POSES:raise ValueError('Unsupported pose')
    a=np.asarray(image.convert('RGBA'))[...,3]
    yy,xx=np.where(a>127)
    if not len(xx):raise ValueError('Empty character')
    x0,y0,x1,y1=xx.min(),yy.min(),xx.max(),yy.max()
    w,h=x1-x0,y1-y0
    # Configurable framing hypothesis: head-to-upper-leg illustration, not detected joints.
    p={'nose':(.60,.16),'neck':(.54,.235),'rs':(.27,.26),'ls':(.78,.25),
       'right_eye':(.49,.12),'left_eye':(.69,.125),'right_ear':(.39,.13),'left_ear':(.77,.135),
       're':(.17,.44),'rw':(.13,.61),'le':(.81,.45),'lw':(.68,.70),
       'rh':(.36,.62),'lh':(.67,.62),'rk':(.40,.96),'lk':(.66,.96)}
    changes={
        'right-lift':{'re':(.10,.43),'rw':(.04,.58)},
        'left-lift':{'le':(.88,.44),'lw':(.96,.62),'rw':(.38,.47)},
        'explain':{'re':(.13,.43),'rw':(-.02,.36)},
        'wave':{'le':(.94,.39),'lw':(.98,.21)},
        'torso-open':{'re':(.10,.43),'rw':(.01,.60),'le':(.87,.44),'lw':(.96,.62)}}
    p.update(changes[pose])
    out={k:(float(x0+x*w),float(y0+y*h)) for k,(x,y) in p.items()}
    if any(x<0 or y<0 or x>=image.width or y>=image.height for x,y in out.values()):
        raise ValueError('Target pose exceeds source framing; mark unsupported or revise guide')
    return out


def guide(image,pose,kind='skeleton'):
    p=joints(image,pose);out=Image.new('RGB',image.size,'black' if kind=='skeleton' else 'white')
    draw=ImageDraw.Draw(out);unit=max(3,round(image.height/180))
    edges=[('nose','neck'),('neck','rs'),('rs','re'),('re','rw'),('neck','ls'),('ls','le'),('le','lw'),
           ('neck','rh'),('rh','rk'),('neck','lh'),('lh','lk'),('rh','lh'),
           ('nose','right_eye'),('right_eye','right_ear'),('nose','left_eye'),('left_eye','left_ear')]
    colors=['#ff0000','#ff5500','#ffaa00','#ffff00','#aaff00','#55ff00','#00ff00',
            '#00ffaa','#00aaff','#0055ff','#5500ff','#aa00ff','#ff00ff','#ff0055','#aa00ff','#ff00aa']
    if kind=='silhouette':
        draw.polygon([p[k] for k in ('rs','ls','lh','rh')],fill='#aaaaaa')
        x,y=p['nose'];r=image.height*.07;draw.ellipse((x-r,y-r,x+r,y+r),fill='#aaaaaa')
    for i,(a,b) in enumerate(edges):draw.line([p[a],p[b]],fill=colors[i] if kind=='skeleton' else '#777777',width=unit if kind=='skeleton' else unit*5)
    for x,y in p.values():draw.ellipse((x-unit,y-unit,x+unit,y+unit),fill='white' if kind=='skeleton' else '#555555')
    return out,p


def prompt(pose, guidance='skeleton'):
    instruction=POSES[pose][1]
    ref=(' Use the body pose in picture 2 as the placement guide. Picture 2 is only a pose guide; '
         'do not copy its colors, sticks or mannequin into the illustration.' if guidance!='none' else '')
    return ('Edit the illustrated character in picture 1. '+instruction+ref+
            ' Preserve her face, neutral expression, hairstyle, clothing design, body proportions, '
            'drawing style and palette. Keep the same camera and framing on a plain white background. '
            'Draw natural hands and only the cloth changes needed for the new arm pose.')
