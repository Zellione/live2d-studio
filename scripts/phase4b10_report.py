"""Standalone frontal-master review from actual runtime captures; no rendered rig claims from helper stills."""
import argparse,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from live2d_studio.manifest import digest,write_json
from live2d_studio.frontal_master import load
from live2d_studio.pose_review import REPO


def build(master, family, validation, face, layers, output):
    master,family,validation,face,layers,output=map(Path,(master,family,validation,face,layers,output))
    authority=load(master);output=output.resolve()
    if not output.is_relative_to(REPO/'runs') or output.exists():raise ValueError('Fresh ignored gallery required')
    output.mkdir(parents=True)
    def copy(file,name):shutil.copyfile(file,output/name)
    copy(master/authority['primary']['path'],'master.png');copy(master/authority['identity_style_only']['path'],'identity.png')
    copy(layers/'preview/layers.png','layers.png');copy(layers/'preview/reconstructed.png','backing.png')
    data=json.loads((family/'family.json').read_text());poses=[]
    for name,row in data['images'].items():
        if name!='canonical':copy(family/row['path'],name+'.png');poses.append(name)
    result=json.loads((validation/'arms/frames/result.json').read_text())['result']['value']
    for key,names in result['sequences'].items():
        frames=[Image.open(validation/'arms/frames'/(n+'.png')).convert('RGBA') for n in names]
        frames[0].save(output/(key+'.webp'),save_all=True,append_images=frames[1:],duration=70 if key in ('Right','Left') else 100,loop=0,lossless=True)
    copy(validation/'arms/frames/neutral.png','neutral.png')
    alpha=np.asarray(Image.open(face/'frames/neutral.png').convert('RGBA'))[...,3]>127;y,x=np.where(alpha)
    box=(int(x.min()),int(y.min()),int(x.max()+1),int(y.min()+(y.max()-y.min())*.32))
    for emotion in ('neutral','happy','sad','angry','surprised','confused','embarrassed'):
        Image.open(face/'frames'/('full-'+emotion+'.png')).crop(box).save(output/('face-'+emotion+'.png'))
    def pic(name,title,caption=''):
        return f'<article><h3>{title}</h3><a href="{name}" target="_blank"><img src="{name}"></a><p>{caption}</p></article>'
    page='''<!doctype html><meta charset="utf-8"><title>Frontal master rig</title><style>body{font:17px system-ui;background:#1e2934;color:#edf4fa;margin:2rem}a{color:#9cd5ff}p{max-width:95ch}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}article{background:#304151;padding:1rem}img{max-width:100%;max-height:650px;object-fit:contain;background:#ccd2d8}table{border-collapse:collapse}td,th{padding:.6rem;border:1px solid #8295a7}</style><h1>Frontal Codel: primary master and first independent arms</h1><p><a href="http://127.0.0.1:8812/">Open live frontal rig</a> · <a href="http://127.0.0.1:8808/">Human-reviewed helper family</a> · <a href="http://127.0.0.1:8807/">Approved decomposition/backing review</a></p><p>The frontal synthetic master is the primary artwork. The angled illustration is identity/style reference only; its old rig is archived. Human approval covers the master and this limited experiment's decomposition/backing. Final animation review is separate.</p><h2>Primary artwork and recreated neutral</h2><div class="grid">'''
    page+=pic('identity.png','Original identity/style reference')+pic('master.png','Approved frontal master')+pic('neutral.png','Actual Cubism neutral')+'</div>'
    page+='<h2>Actual independent arm motion</h2><p>These loops are exported Cubism renders, including intermediate frames and return to neutral. Anatomical right is viewer left. They are modest shoulder sweeps, not elbow bends or finger animation. No helper-image swap or translucent crossfade is used.</p><div class="grid">'
    for name,title in [('Right','Right arm outward'),('Left','Left arm outward'),('talk-head-Right','Right gesture while talking and turning head'),('talk-head-Left','Left gesture while talking and turning head')]:page+=pic(name+'.webp',title)
    page+='</div><h2>Seven recreated expressions</h2><p>Actual runtime face crops at zero head angles. Facial rendering remains a limited illustration rig; inspect the eyes, mouth contours and hidden-skin transitions in the live viewer.</p><div class="grid">'
    for emotion in ('neutral','happy','sad','angry','surprised','confused','embarrassed'):page+=pic('face-'+emotion+'.png',emotion.title())
    page+='</div><h2>Reviewed helper family</h2><p>All four existing human selections are preserved and locked in the new reviewer. They provide shape/style evidence; the first shoulder gestures use the neutral master artwork. New right/left aside guides use a framed 24° upper-arm target, separate from the ineffective old guide. No new helper generation was required.</p><div class="grid">'
    for pose in poses:page+=pic(pose+'.png',pose)
    page+='</div><h2>Semantic parts and approved uncertain backing</h2><div class="grid">'+pic('layers.png','Editable source parts')+pic('backing.png','Generated backing highlighted in pink')+'</div>'
    page+='<h2>Identity and anatomy checks</h2><p>Recognizable auburn hair and side fringe, gray eyes, lavender turtleneck, brown skirt and dark tights. Face is rounder and more symmetric than the angled source. Both shoulders, arms and hands are visible; source proportions and stylized fingers remain synthetic. Bilateral masks and editable upper/forearm/hand cuts do not establish bone pivots. No finger-level control is present.</p><p>Only each side’s three arm meshes move under its isolated parameter; torso, head and opposite arm remain fixed. Exact neutral restoration is tested separately from visual quality. Full body, mouth, dense facial and coexistence regressions are retained with unchanged thresholds.</p><p>Codel: LisadiKaprio, <a href="https://opengameart.org/content/codel-visual-novel-sprite">CC-BY-4.0</a>; master/helpers are synthetic derivatives. No production SillyTavern deployment.</p>'
    (output/'index.html').write_text(page)
    write_json(output/'gallery.json',{'master_sha256':digest(master/'master.json'),'arm_result_sha256':digest(validation/'arms/frames/result.json'),'face_result_sha256':digest(face/'frames/result.json'),'runtime_review':'pending'})

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('master','family','validation','face','layers','output'):p.add_argument('--'+name,type=Path,required=True)
    build(**vars(p.parse_args()))
