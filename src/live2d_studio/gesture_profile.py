"""Opt-in canonical-frame gestures. Coordinates are framing hypotheses, not anatomy."""
import numpy as np
from PIL import Image,ImageDraw

PROFILE='chest-forearm-v1'
TITLES={'right-lift':'Anatomical right forearm raised (viewer left)',
        'left-lift':'Anatomical left forearm raised (viewer right)',
        'explain':'Anatomical right hand: small explanation',
        'wave':'Anatomical left hand: modest wave',
        'torso-open':'Anatomical right arm moved aside'}
COMMON=('Retain the front-facing head, chest and hips and original framing of picture 1. '
        'Keep both arms visible with continuous shoulder, upper arm, elbow, forearm, wrist and hand. '
        'Preserve the face, hairstyle, neutral expression, outfit design, body proportions, illustration style and colours. '
        'Use picture 2 for joint placement only, never copy its mannequin rendering. '
        'Keep a natural relaxed hand with five fingers, without extra limbs or merged fingers. ')
INSTRUCTIONS={
 'right-lift':"Bend the character's anatomical RIGHT elbow (viewer LEFT). The upper arm points down beside the torso, the elbow is near waist height, and the forearm points upward so the hand is at chest height, slightly outside the torso. The anatomical LEFT arm (viewer RIGHT) stays relaxed down. Do not leave both hands down and do not cross the forearm over the torso.",
 'left-lift':"Bend the character's anatomical LEFT elbow (viewer RIGHT). The upper arm points down beside the torso, the elbow is near waist height, and the forearm points upward so the hand is at chest height, slightly outside the torso. The anatomical RIGHT arm (viewer LEFT) stays relaxed down. Do not leave both hands down and do not cross the forearm over the torso.",
 'explain':"Raise the anatomical RIGHT forearm (viewer LEFT) with a bent elbow and a gently open palm near the lower chest, as a small explanation. Keep the anatomical LEFT arm relaxed down.",
 'wave':"Raise the anatomical LEFT forearm (viewer RIGHT), bending the elbow, with an open hand beside the shoulder for a modest wave. Keep the anatomical RIGHT arm relaxed down.",
 'torso-open':"Move the anatomical RIGHT arm (viewer LEFT) slightly outward with the hand below the elbow, exposing a narrow gap beside the torso and sleeve. Keep the anatomical LEFT arm relaxed down."
}


def guide(image,pose,kind):
    rgba=np.asarray(image.convert('RGBA'));alpha=rgba[...,3]
    mask=alpha>127
    if np.all(alpha==255):mask=np.max(abs(rgba[...,:3].astype(float)-255),axis=2)>24
    yy,xx=np.where(mask)
    if not len(xx):raise ValueError('No visible character for guide framing')
    y0=float(yy.min());height=float(yy.max()-yy.min());width=min(float(xx.max()-xx.min())*1.12,image.width*.88)
    center=image.width/2
    points={'nose':(.5,.16),'neck':(.5,.25),'rs':(.23,.28),'ls':(.77,.28),
            're':(.18,.52),'le':(.82,.52),'rw':(.13,.72),'lw':(.87,.72),
            'rh':(.32,.60),'lh':(.68,.60),'rk':(.39,.96),'lk':(.61,.96),
            'right_eye':(.42,.12),'left_eye':(.58,.12),'right_ear':(.33,.135),'left_ear':(.67,.135)}
    changes={'right-lift':{'re':(.18,.51),'rw':(.06,.38)},
             'left-lift':{'le':(.82,.51),'lw':(.94,.38)},
             'explain':{'re':(.15,.51),'rw':(.02,.43)},
             'wave':{'le':(.88,.43),'lw':(.96,.24)},
             'torso-open':{'re':(.11,.51),'rw':(.01,.71)}}
    if pose not in changes:raise ValueError('Unknown gesture')
    points.update(changes[pose]);points={k:(center+(x-.5)*width,y0+y*height) for k,(x,y) in points.items()}
    if any(not(0<=x<image.width and 0<=y<image.height) for x,y in points.values()):raise ValueError('Guide outside source framing')
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


def definition(state):
    return {k:{'prompt':p['prompt'],'guides':p['guides']} for k,p in state['poses'].items()}


def apply(store,profile):
    from .pose_review import digest,fingerprint,REPO
    if profile!=PROFILE:raise ValueError('Unknown gesture profile')
    with store.transaction() as state:
        if state['batches'] or state.get('workflow')!='canonical-helpers':raise ValueError('Profile requires a new canonical helper run')
        image=Image.open(store.safe(state['source']['path']))
        for pose,p in state['poses'].items():
            p.update(title=TITLES[pose],prompt=COMMON+INSTRUCTIONS[pose])
            for kind in ('silhouette','skeleton'):
                rendered,points=guide(image,pose,kind);name=f'assets/{pose}-{profile}-{kind}.png';rendered.save(store.root/name)
                p['guides'][kind]={'path':name,'sha256':digest(store.root/name),'joints':points}
        state['gesture_profile']=profile;state['gesture_definition_sha256']=fingerprint(definition(state))
        name='src/live2d_studio/gesture_profile.py';state['producer_pins'][name]=digest(REPO/name)
