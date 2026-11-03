"""Compare matched real Cubism captures without assigning aesthetic acceptance."""
import argparse
import html
import json
from pathlib import Path
import shutil
import numpy as np
from PIL import Image,ImageDraw
from live2d_studio.manifest import write_json,digest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--render',action='append',required=True,help='label=validation directory')
    p.add_argument('--layers',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--transitions',action='store_true',help='Compare the time-sampled ramp/talk suite')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    runs={k:Path(v) for k,v in (s.split('=',1) for s in a.render)}
    if any(not k.replace('-','').isalnum() for k in runs):raise ValueError('Unsafe label')
    reports={k:json.loads((v/'quality.json').read_text()) for k,v in runs.items()}
    names=list(next(iter(reports.values()))['poses'])
    if any(set(q['poses'])!=set(names) for q in reports.values()):raise ValueError('Mismatched pose suites')
    data=json.loads((a.layers/'layer_manifest.json').read_text());face=next(l for l in data['layers'] if l['role']=='face')
    original=Image.open(a.layers/data['sources'][0]['normalized_path']).convert('RGBA');sb=original.getbbox()
    neutral=Image.open(next(iter(runs.values()))/'frames/neutral.png').convert('RGBA');rb=neutral.getbbox()
    sx=(rb[2]-rb[0])/(sb[2]-sb[0]);sy=(rb[3]-rb[1])/(sb[3]-sb[1])
    box=(int(rb[0]+(face['x']-sb[0])*sx),int(rb[1]+(face['y']-sb[1])*sy),
        int(rb[0]+(face['x']+face['width']-sb[0])*sx),int(rb[1]+(face['y']+face['height']-sb[1])*sy))
    selected=['neutral','pose-ParamEyeLOpen-0','pose-ParamEyeLOpen-0_25','pose-ParamEyeLOpen-0_5',
        'pose-ParamEyeROpen-0','pose-ParamMouthOpenY-0_5','pose-ParamMouthOpenY-1','face-happy','face-sad',
        'face-angry','face-surprised','face-confused','face-embarrassed','combined-surprised','reset']
    if a.transitions:
        selected=['neutral']+[f'blink-ramp-{i}' for i in range(11)]+[f'mouth-ramp-{i}' for i in (0,3,6,10)]+['reset']
    sheet=Image.new('RGB',(300*len(runs),260*len(selected)),(235,235,235));draw=ImageDraw.Draw(sheet)
    summary={};gif=[]
    for label,root in runs.items():
        (a.output/label).mkdir()
        for name in names:shutil.copyfile(root/'frames'/(name+'.png'),a.output/label/(name+'.png'))
        q=reports[label]
        summary[label]=dict(render_status=q['render_status'],poses=len(q['poses']),geometry=q['geometry'],network=q['network'],
            neutral_holes=q['poses']['neutral']['enclosed_transparent_pixels'],max_holes=max(v['enclosed_transparent_pixels'] for v in q['poses'].values()),
            max_detached_pixels=max(v['detached_small_component_pixels'] for v in q['poses'].values()),
            quality_sha256=digest(root/'quality.json'))
    for i,name in enumerate(selected):
        frame=Image.new('RGB',(300*len(runs),260),(235,235,235))
        for j,(label,root) in enumerate(runs.items()):
            im=Image.open(root/'frames'/(name+'.png')).crop(box);im.thumbnail((294,230))
            frame.paste(im,(j*300+(300-im.width)//2,26),im)
            ImageDraw.Draw(frame).text((j*300+4,4),label+' '+name,fill='black')
        sheet.paste(frame,(0,i*260));gif.append(frame)
    sheet.save(a.output/'comparison.png')
    gif[0].save(a.output/'poses.gif',save_all=True,append_images=gif[1:],duration=450,loop=0)
    if a.transitions:
        sequence=['neutral']
        for emotion in ['neutral','happy','sad','angry','surprised','confused','embarrassed']:
            sequence += [f'talk-{emotion}-{i}' for i in range(10)]+[f'fade-{emotion}-{i}' for i in range(4)]
        sequence += [f'blink-ramp-{i}' for i in range(11)]+[f'mouth-ramp-{i}' for i in range(11)]+['reset']
        frames=[];durations=[]
        for name in sequence:
            frame=Image.new('RGB',(300*len(runs),260),(235,235,235))
            for j,(label,root) in enumerate(runs.items()):
                im=Image.open(root/'frames'/(name+'.png')).crop(box);im.thumbnail((294,230));frame.paste(im,(j*300+(300-im.width)//2,26),im)
                ImageDraw.Draw(frame).text((j*300+4,4),label+' '+name,fill='black')
            frames.append(frame);durations.append(150 if name.startswith('fade') else 70 if '-ramp-' in name else 100 if name.startswith('talk') else 700)
        frames[0].save(a.output/'transitions.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0)
    write_json(a.output/'metrics.json',dict(runtime=summary,visual_acceptance='not granted by metrics',
        notes='Actual Core frames. GIF is a pose montage, not continuous motion. Hole/component counts include legitimate details.'))
    labels=list(runs)
    options=''.join('<option>'+html.escape(n)+'</option>' for n in names)
    panels=''.join('<div>'+html.escape(k)+'<img id="'+k+'"></div>' for k in labels)
    (a.output/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Phase 4B.2 runtime comparison</title>
<style>body{font:17px system-ui;max-width:1400px;margin:25px auto;background:#eee;color:#223}.pair{display:flex}.pair>div{flex:1}img{max-width:100%}select{font:inherit}</style>
<h1>Facial inpainting · actual Cubism comparison</h1><p>Development experiment. No automatic promotion, user visual approval or production deployment. Numerical validity and source preservation are separate from visual quality. Read the results report for accepted/rejected features.</p>
<select id="pose">'''+options+'''</select><div class="pair">'''+panels+'''</div>
<script>const labels='''+json.dumps(labels)+''';const p=document.querySelector('#pose');function update(){for(const k of labels)document.getElementById(k).src=k+'/'+p.value+'.png'}p.onchange=update;update()</script>
<p>Sampled pose montage (not continuous animation):</p><img src="poses.gif"><p><a href="comparison.png">Full face comparison</a> · <a href="metrics.json">Raw summary</a></p><img src="comparison.png">''')
    if a.transitions:
        with (a.output/'index.html').open('a') as f:f.write('<h2>Time-sampled animation</h2><p>Actual runtime captures replayed at nominal sample intervals; not a frame-rate benchmark.</p><img src="transitions.gif">')
    print(a.output/'index.html')


if __name__=='__main__':main()
