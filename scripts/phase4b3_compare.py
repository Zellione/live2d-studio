"""Matched Core face sheets and sampled recordings; no automatic aesthetic pass."""
import argparse,html,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from live2d_studio.manifest import write_json,digest


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--render',action='append',required=True);p.add_argument('--layers',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--diagnostic',action='store_true')
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);runs={k:Path(v) for k,v in (s.split('=',1) for s in a.render)}
 if any(not k.replace('-','').isalnum() for k in runs):raise ValueError('Unsafe label')
 records={k:json.loads((v/'frames/result.json').read_text())['result']['value'] for k,v in runs.items()}
 names=list(next(iter(records.values()))['frames'])
 if a.diagnostic:names=[n for n in names if all(n in q['frames'] for q in records.values())]
 elif any(set(q['frames'])!=set(names) for q in records.values()):raise ValueError('Unmatched suites')
 m=json.loads((a.layers/'layer_manifest.json').read_text());face=next(l for l in m['layers'] if l['role']=='face')
 sb=Image.open(a.layers/m['sources'][0]['normalized_path']).getbbox();rb=Image.open(next(iter(runs.values()))/'frames/neutral.png').getbbox()
 sx=(rb[2]-rb[0])/(sb[2]-sb[0]);sy=(rb[3]-rb[1])/(sb[3]-sb[1]);box=(int(rb[0]+(face['x']-sb[0])*sx),int(rb[1]+(face['y']-sb[1])*sy),int(rb[0]+(face['x']+face['width']-sb[0])*sx),int(rb[1]+(face['y']+face['height']-sb[1])*sy))
 def frame(name):
  out=Image.new('RGB',(260*len(runs),260),'#eeeeee');draw=ImageDraw.Draw(out)
  for j,(label,root) in enumerate(runs.items()):
   im=Image.open(root/'frames'/(name+'.png')).crop(box);im.thumbnail((254,230));out.paste(im,(j*260+(260-im.width)//2,27),im);draw.text((j*260+3,5),label+' '+name,fill='black')
  return out
 sections=[]
 for feature in ['left','right','both','mouth','smile','frown']:
  selected=[n for n in names if n.startswith(feature+'-')];sheet=Image.new('RGB',(260*len(runs),260*len(selected)),'#eeeeee')
  for i,n in enumerate(selected):sheet.paste(frame(n),(0,i*260))
  sheet.save(a.output/(feature+'.png'));sections.append('<h2>'+feature+'</h2><img src="'+feature+'.png">')
 sequences=next(iter(records.values())).get('sequences',{});metrics={}
 for seq,ns in sequences.items():
  if not all(n in names for n in ns):continue
  frames=[frame(n) for n in ns];frames[0].save(a.output/(seq+'.gif'),save_all=True,append_images=frames[1:],duration=65 if seq.startswith('combined') else 50,loop=0)
  sections.append('<h2>'+seq+'</h2><img src="'+seq+'.gif">')
  metrics[seq]={}
  for label,root in runs.items():
   arrays=[np.array(Image.open(root/'frames'/(n+'.png')).crop(box)).astype(float) for n in ns]
   deltas=[float(np.abs(b-c).mean()) for b,c in zip(arrays,arrays[1:])]
   metrics[seq][label]=dict(mean_absolute_frame_changes=deltas,max=max(deltas),caveat='Image change only; pose speed and real detail matter. Not a naturalness score.')
   sheet=Image.new('RGB',(1200,200*((len(ns)+5)//6)),'#eeeeee');draw=ImageDraw.Draw(sheet)
   for i,n in enumerate(ns):
    im=Image.open(root/'frames'/(n+'.png')).crop(box);im.thumbnail((194,174));x=i%6*200;y=i//6*200
    sheet.paste(im,(x,y+24),im);draw.text((x+2,y+3),n,fill='black')
   filename=label+'-'+seq+'.png';sheet.save(a.output/filename)
   sections.append('<a href="'+filename+'">'+label+' full sequence contact sheet</a> ')
 for label,root in runs.items():
  (a.output/label).mkdir()
  for n in names:shutil.copyfile(root/'frames'/(n+'.png'),a.output/label/(n+'.png'))
 write_json(a.output/'temporal-metrics.json',metrics)
 labels=list(runs);options=''.join('<option>'+html.escape(n)+'</option>' for n in names);panels=''.join('<div>'+k+'<img id="'+k+'"></div>' for k in labels)
 (a.output/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Phase 4B.3 transition comparison</title><style>body{font:17px system-ui;background:#eee;color:#223;max-width:1400px;margin:25px auto}img{max-width:100%}.pair{display:flex}.pair>div{flex:1}select{font:inherit}</style><h1>Rig-aware facial transitions</h1><p>Actual local Cubism captures. Developer review is separate from user approval. GIFs replay sampled runtime frames at nominal intervals; they are not a frame-rate benchmark. Numerical checks do not establish natural animation.</p><select id="pose">'''+options+'''</select><div class="pair">'''+panels+'''</div><script>const labels='''+json.dumps(labels)+''';const p=document.querySelector('#pose');function update(){for(const k of labels)document.getElementById(k).src=k+'/'+p.value+'.png'}p.onchange=update;update()</script>'''+''.join(sections))
 print(a.output/'index.html')

if __name__=='__main__':main()
