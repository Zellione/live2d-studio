"""Build an evaluation-only before/after gallery from actual Cubism frames."""
import argparse
import json
from pathlib import Path
import shutil
import numpy as np
from PIL import Image,ImageDraw
from live2d_studio.manifest import write_json,digest


def stage(run,name):
    d=json.loads((run/'creation.json').read_text());return run/d['stages'][name]['directory']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,default=Path('runs/phase4b1-sara-baseline'))
    p.add_argument('--candidate',type=Path,default=Path('runs/phase4b1-sara'))
    p.add_argument('--output',type=Path,required=True);p.add_argument('--benchmark',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    review_file=a.candidate/'reviews/visual.json'
    visual_review=json.loads(review_file.read_text()) if review_file.is_file() else None
    old=a.baseline;new=stage(a.candidate,'validation')
    q0=json.loads((old/'quality.json').read_text());q1=json.loads((new/'quality.json').read_text())
    layers=stage(a.candidate,'facial')/'layers';manifest=json.loads((layers/'layer_manifest.json').read_text())
    art=json.loads((layers/'facial-artwork.json').read_text());face=next(l for l in manifest['layers'] if l['role']=='face')
    original=Image.open(layers/manifest['sources'][0]['normalized_path']).convert('RGBA');sb=original.getbbox()
    neutral=Image.open(new/'frames/neutral.png').convert('RGBA');rb=neutral.getbbox()
    sx=(rb[2]-rb[0])/(sb[2]-sb[0]);sy=(rb[3]-rb[1])/(sb[3]-sb[1])
    box=(int(rb[0]+(face['x']-sb[0])*sx),int(rb[1]+(face['y']-sb[1])*sy),
         int(rb[0]+(face['x']+face['width']-sb[0])*sx),int(rb[1]+(face['y']+face['height']-sb[1])*sy))
    names=list(q1['poses']);missing=set(names)-set(q0['poses'])
    if missing:raise ValueError('Baseline lacks comparable poses: '+str(missing))
    for label,root in [('before',old),('after',new)]:
        (a.output/label).mkdir()
        for name in names:shutil.copyfile(root/'frames'/(name+'.png'),a.output/label/(name+'.png'))
    selected=['neutral','pose-ParamEyeLOpen-0','pose-ParamEyeLOpen-0_25','pose-ParamEyeLOpen-0_5','pose-ParamEyeLOpen-0_75',
              'pose-ParamEyeROpen-0','pose-ParamMouthOpenY-0_25','pose-ParamMouthOpenY-0_5','pose-ParamMouthOpenY-0_75','pose-ParamMouthOpenY-1',
              'face-happy','face-sad','face-angry','face-surprised','face-confused','face-embarrassed','combined-surprised','reset']
    sheet=Image.new('RGB',(1000,330*((len(selected)+1)//2)),(235,235,235));draw=ImageDraw.Draw(sheet)
    for i,name in enumerate(selected):
        for j,label in enumerate(['before','after']):
            im=Image.open(a.output/label/(name+'.png')).crop(box);im.thumbnail((245,295))
            x=(i%2*2+j)*250;y=i//2*330;sheet.paste(im,(x+(250-im.width)//2,y+30),im)
            draw.text((x+4,y+6),label+' '+name,fill='black')
    sheet.save(a.output/'comparison.png')
    Image.open('assets/references/phase4b-sara/sheet.png').save(a.output/'reference-sheet.png')
    # Evaluation reference only: neither this script nor sheet is imported by the pipeline.
    sequence=['neutral','face-happy','talk-happy','face-sad','talk-sad','face-surprised','talk-surprised',
              'pose-ParamEyeLOpen-0_75','pose-ParamEyeLOpen-0_5','pose-ParamEyeLOpen-0_25','pose-ParamEyeLOpen-0','reset']
    gif=[]
    for name in sequence:
        canvas=Image.new('RGB',(600,400),(235,235,235))
        for j,label in enumerate(['before','after']):
            im=Image.open(a.output/label/(name+'.png'));im.thumbnail((300,365));canvas.paste(im,(j*300,25),im)
        ImageDraw.Draw(canvas).text((8,5),'Phase 4B / Phase 4B.1: '+name,fill='black');gif.append(canvas)
    gif[0].save(a.output/'sequence.gif',save_all=True,append_images=gif[1:],duration=300,loop=0)
    records={}
    hashes={}
    for label,q in [('before',q0),('after',q1)]:
        records[label]=dict(render_status=q['render_status'],pose_count=len(q['poses']),geometry=q['geometry'],network=q['network'],
            neutral_holes=q['poses']['neutral']['enclosed_transparent_pixels'],
            max_holes=max(v['enclosed_transparent_pixels'] for v in q['poses'].values()),
            max_detached_pixels=max(v['detached_small_component_pixels'] for v in q['poses'].values()))
        hashes[label]={k:v['source_frame_sha256'] for k,v in q['poses'].items()}
    write_json(a.output/'frame-hashes.json',hashes)
    before=np.array(Image.open(old/'frames/neutral.png'));after=np.array(neutral)
    records['neutral_comparison']=dict(changed_pixels=int(np.any(before!=after,axis=2).sum()),
        rgba_mean_absolute_difference=float(np.abs(before.astype(float)-after).mean()),
        exact_frame_equality=bool(np.array_equal(before,after)),
        caveat='Runtime comparison with old model, separate from exact original observed pixels.')
    report=dict(schema_version=1,base_commit='3e120c8',single_image=True,multi_reference=False,
        source_sha256=manifest['sources'][0]['sha256'],facial_artwork=art,runtime=records,
        frame_hash_manifest_sha256=digest(a.output/'frame-hashes.json'),
        development_visual_assessment='Clearer closed eyes and visible mouth cavity; simplified intermediate lids/interior remain.',
        visual_review=visual_review,production_ready=False,independent_general_purpose_acceptance=False,
        reference_sheet=dict(usage='evaluation-only; never supplied to inference or reconstruction',sha256=digest(a.output/'reference-sheet.png'),
            attribution='Portrait graphics created by RPG Action; graphics designed by ZeNeRIA29; CC-BY-3.0',
            url='https://opengameart.org/content/sara-trevor-puck-anime-portrait-and-expressions'))
    write_json(a.benchmark,report)
    options=''.join(f'<option>{n}</option>' for n in names)
    (a.output/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Phase 4B.1 facial review</title>
<style>body{font:18px system-ui;background:#eee;color:#223;max-width:1280px;margin:30px auto}img{max-width:100%}.pair{display:flex}.pair>div{width:50%}select{font:inherit}a{color:#256}</style>
<h1>Sara facial reconstruction · limited portrait improvement</h1><p>Single-image reconstruction. Before: preserved Phase 4B export. After: local source-derived facial artwork. Actual Cubism renders; no image-model editing of frames. The benchmark records the separate visual review. No general-purpose acceptance or production deployment.</p>
<p>Select a pose: <select id="pose">'''+options+'''</select></p><div class="pair"><div>Phase 4B<img id="before"></div><div>Phase 4B.1<img id="after"></div></div>
<script>const p=document.querySelector('#pose');function update(){for(const side of ['before','after'])document.getElementById(side).src=side+'/'+p.value+'.png'}p.onchange=update;update()</script>
<p>Review both blink sides, all quarter steps, seven expressions, talking, head combinations and reset. The sequence below is a sampled pose montage, not a timing/continuous-motion measurement.</p><img src="sequence.gif">
<p><a href="comparison.png">Full comparative face sheet</a></p><img src="comparison.png">
<h2>Independent artist references — evaluation only</h2><p>Portrait graphics created by RPG Action; graphics designed by ZeNeRIA29; CC-BY 3.0. The other tiles were never reconstruction inputs. Their richer happy mouth/closed-eye curves remain a visual target, not hidden ground truth.</p><img src="reference-sheet.png">''')
    print(a.output/'index.html')

if __name__=='__main__':main()
