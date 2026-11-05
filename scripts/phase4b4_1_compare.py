"""Mouth-only/full-expression sheets and opening samples; no recognition score."""
import argparse,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw
from live2d_studio.manifest import write_json,digest
NAMES=['neutral','happy','sad','angry','confused','surprised','embarrassed']
OPENINGS=['0','0_05','0_1','0_15','0_25','0_5','0_75','1']
p=argparse.ArgumentParser(description=__doc__)
for k in ['before','after','layers','output']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
m=json.loads((a.layers/'layer_manifest.json').read_text())
sb=Image.open(a.layers/m['sources'][0]['normalized_path']).getbbox();rb=Image.open(a.before/'frames/neutral.png').getbbox()
sx=(rb[2]-rb[0])/(sb[2]-sb[0]);sy=(rb[3]-rb[1])/(sb[3]-sb[1])
def crop(role,pad):
 l=next(l for l in m['layers'] if l['role']==role);w=l['width'];h=l['height']
 return tuple(round(v) for v in (rb[0]+(l['x']-pad*w-sb[0])*sx,rb[1]+(l['y']-pad*h-sb[1])*sy,rb[0]+(l['x']+(1+pad)*w-sb[0])*sx,rb[1]+(l['y']+(1+pad)*h-sb[1])*sy))
face=crop('face',0);mouth=crop('mouth',.6)
sections=[];mouth_sections=[];full_sections=[]
roots={'previous':a.before,'candidate':a.after}
records={label:json.loads((root/'frames/result.json').read_text())['result']['value'] for label,root in roots.items()}
for label,r in records.items():
 if r['status']!='pass':raise ValueError('Incomplete render: '+label)

def sheet(filename,rows,box,size):
 w,h=size;im=Image.new('RGB',(w*len(rows[0]),h*len(rows)),'#eee');d=ImageDraw.Draw(im)
 for ri,row in enumerate(rows):
  for ci,(label,root,key) in enumerate(row):
   src=Image.open(root/'frames'/(key+'.png')).convert('RGBA')
   if box:src=src.crop(box)
   scale=min((w-12)/src.width,(h-28)/src.height);src=src.resize((round(src.width*scale),round(src.height*scale)),Image.Resampling.LANCZOS)
   im.paste(src,(ci*w+(w-src.width)//2,ri*h+25),src);d.text((ci*w+7,ri*h+6),label,fill='black')
 im.save(a.output/filename)
 return '<a href="'+filename+'"><img loading="lazy" src="'+filename+'"></a>'

for prefix,title in [('mouth','Mouth only — every other channel neutral'),('full','Complete expressions')]:
 start=len(sections)
 rows=[[(label+' / '+n,root,prefix+'-'+n) for n in NAMES] for label,root in roots.items()]
 sections.append('<h2>'+title+'</h2>'+sheet(prefix+'-faces.png',rows,face,(240,280)))
 if prefix=='mouth':sections.append(sheet('mouth-details.png',rows,mouth,(240,140)))
 sections.append('<details><summary>Normal-size framing</summary>'+sheet(prefix+'-normal.png',rows,None,(600,680))+'</details>')
 (mouth_sections if prefix=='mouth' else full_sections).extend(sections[start:])
for left,right in [('happy','sad'),('sad','angry'),('confused','surprised'),('happy','embarrassed')]:
 start=len(sections)
 rows=[[(label+' / '+n,root,'mouth-'+n) for n in (left,right)] for label,root in roots.items()]
 sections.append('<h2>'+left+' vs '+right+'</h2>'+sheet(left+'-'+right+'.png',rows,mouth,(440,220)))
 mouth_sections.extend(sections[start:])
for n in NAMES:
 start=len(sections)
 rows=[[(label+' / '+v.replace('_','.'),root,'open-'+n+'-'+v) for v in OPENINGS] for label,root in roots.items()]
 sections.append('<h2>'+n+' — explicit opening 0 → 1</h2>'+sheet('opening-'+n+'.png',rows,mouth,(180,120)))
 mouth_sections.extend(sections[start:])
for label,root in roots.items():
 (a.output/label).mkdir()
 for n in NAMES:
  for prefix in ['mouth','full']:shutil.copyfile(root/'frames'/(prefix+'-'+n+'.png'),a.output/label/(prefix+'-'+n+'.png'))
write_json(a.output/'comparison.json',dict(face_crop=face,mouth_crop=mouth,
 report_hashes={label:digest(root/'frames/result.json') for label,root in roots.items()},user_approval=False,recognition_score=None))
header='''<!doctype html><meta charset="utf-8"><title>Phase 4B.4.1 mouth review</title><style>body{font:17px system-ui;color:#223;background:#eee;margin:30px auto;max-width:1700px}img{max-width:100%}h2{margin-top:45px}summary{cursor:pointer}</style><h1>Mouth redesign — user review required</h1><p>Previous: Phase 4B.4. Candidate: coordinated mouth contour/cavity. Same render framing; idle, talk and blink stopped; head angles zero; expression settled after neutral restoration. The mouth-only rows force every non-mouth parameter to its identical neutral default (including open eyes, brows, gaze and blush). Full expressions follow separately.</p><p>Opening sheets override only openness, retaining the emotional mouth shape. No pixel-distance recognition score or automatic promotion. Please judge the mouth pairs independently of brows and blush.</p>'''
nav='<p><a href="mouth-only.html">Mouth-only gallery</a> · <a href="full-expressions.html">Full expressions</a> · <a href="index.html">All comparisons</a></p>'
for filename,content in [('index.html',sections),('mouth-only.html',mouth_sections),('full-expressions.html',full_sections)]:
 (a.output/filename).write_text(header+nav+''.join(content))
print(a.output/'index.html')
