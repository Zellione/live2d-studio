"""Matched still expression gallery; metrics never stand in for human recognition."""
import argparse,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from live2d_studio.manifest import write_json,digest
p=argparse.ArgumentParser(description=__doc__)
for k in ['before','after','layers','output']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
runs={'before':a.before,'after':a.after}
names=['neutral','angry','confused','embarrassed','happy','sad','surprised']
m=json.loads((a.layers/'layer_manifest.json').read_text());face=next(l for l in m['layers'] if l['role']=='face')
sb=Image.open(a.layers/m['sources'][0]['normalized_path']).getbbox();rb=Image.open(a.before/'frames/neutral.png').getbbox()
sx=(rb[2]-rb[0])/(sb[2]-sb[0]);sy=(rb[3]-rb[1])/(sb[3]-sb[1]);box=(int(rb[0]+(face['x']-sb[0])*sx),int(rb[1]+(face['y']-sb[1])*sy),int(rb[0]+(face['x']+face['width']-sb[0])*sx),int(rb[1]+(face['y']+face['height']-sb[1])*sy))
metrics={};sections=[]
for label,root in runs.items():
 record=json.loads((root/'frames/result.json').read_text())['result']['value']
 if record['status']!='pass':raise ValueError('Incomplete expression run')
 (a.output/label).mkdir()
 for name in names:shutil.copyfile(root/'frames'/('face-'+name+'.png'),a.output/label/(name+'.png'))
metrics['pixels_changed']={n:int(np.any(np.array(Image.open(a.before/'frames'/('face-'+n+'.png')))!=np.array(Image.open(a.after/'frames'/('face-'+n+'.png'))),axis=2).sum()) for n in names}
for group,subset in [('primary',names[:4]),('regressions',names[4:])]:
 for crop in [True,False]:
  w,h=(300,340) if crop else (600,680)
  sheet=Image.new('RGB',(w*len(subset),h*2),'#eeeeee');draw=ImageDraw.Draw(sheet)
  for row,(label,root) in enumerate(runs.items()):
   for col,n in enumerate(subset):
    im=Image.open(root/'frames'/('face-'+n+'.png'))
    if crop:
     im=im.crop(box);scale=min((w-10)/im.width,(h-35)/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    sheet.paste(im,(col*w+(w-im.width)//2,row*h+30),im);draw.text((col*w+10,row*h+8),label+' / '+n,fill='black')
  filename=group+('-close' if crop else '-normal')+'.png';sheet.save(a.output/filename)
  sections.append('<h2>'+group+(' close-up' if crop else ' normal-size')+'</h2><a href="'+filename+'"><img src="'+filename+'"></a>')
write_json(a.output/'comparison.json',dict(**metrics,face_crop=box,before_quality_sha256=digest(a.before/'quality.json'),after_quality_sha256=digest(a.after/'quality.json'),user_approval=False,recognition_score=None))
(a.output/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Phase 4B.4 expression comparison</title><style>body{font:17px system-ui;background:#eee;color:#223;margin:30px auto;max-width:1400px}img{max-width:100%}.pair{display:flex}.pair>div{width:50%}select{font:inherit}</style><h1>Distinct facial expressions · candidate for review</h1><p>Before: Phase 4B.3 deterministic Sara. After: independent brow controls, asymmetric mouth and procedural blush. Idle paused, talking stopped, blink inactive, head X/Y/Z zero, neutral restored between poses, expression fully settled. Same canvas and crop for both versions.</p><p>No automatic promotion or emotion-recognition score. Please judge legibility, character identity and any unwanted distortion.</p><select id="pose">'''+''.join('<option>'+n+'</option>' for n in names)+'''</select><div class="pair"><div>Before<img id="before"></div><div>Candidate<img id="after"></div></div><script>const p=document.getElementById('pose');function show(){for(const k of ['before','after'])document.getElementById(k).src=k+'/'+p.value+'.png'}p.onchange=show;show()</script>'''+''.join(sections))
print(a.output/'index.html')
