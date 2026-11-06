"""Curated elbow diagnostic gallery with source-relative joint corrections."""
import argparse,json,shutil
from pathlib import Path
from PIL import Image
from live2d_studio.manifest import digest,write_json
from live2d_studio.elbow_rig import frozen_reference
from live2d_studio.pose_review import REPO
p=argparse.ArgumentParser()
for n in ('run','render','output'):p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--live-port',type=int,default=8814);a=p.parse_args();out=a.output.resolve()
if not out.is_relative_to(REPO/'runs') or out.exists():raise ValueError('Fresh ignored gallery required')
root,_=frozen_reference('docs/references/codel-frontal-prototype-v1.json');out.mkdir(parents=True)
shutil.copyfile(root/'master/primary.png',out/'master.png')
proposal=json.loads((a.run/'joints.json').read_text());write_json(out/'joints.json',proposal)
family=json.loads(Path('runs/phase4b9-family/family.json').read_text())
for k,r in family['images'].items():shutil.copyfile(Path('runs/phase4b9-family')/r['path'],out/(k+'.png'))
result=json.loads((a.render/'frames/result.json').read_text())['result']['value']
sides=[side for side in ('Right','Left') if side+'-pose-100' in result['frames']]
pose_names=[f'{side}-pose-{v}' for side in sides for v in (10,25,50,75,90,100)] if sides else [f'pose-{v}' for v in (10,25,50,75,90,100)]
for n in ['neutral','restored',*pose_names]:
 shutil.copyfile(a.render/'frames'/(n+'.png'),out/(n+'.png'))
for key,names in result['sequences'].items():
 frames=[Image.open(a.render/'frames'/(n+'.png')) for n in names]
 frames[0].save(out/(key+'.webp'),save_all=True,append_images=frames[1:],duration=70 if key.endswith('sweep') else 100,loop=0,lossless=True)
write_json(out/'evidence.json',{'proposal_sha256':digest(out/'joints.json'),'runtime_sha256':digest(a.run/'rig/exported/runtime/Generated_artwork.model3.json'),'render_sha256':digest(a.render/'frames/result.json'),'status':'unreviewed-diagnostic-not-promoted'})
(out/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Elbow diagnostic review</title><link rel="stylesheet" href="style.css"><h1>Elbow articulation — experimental support check</h1><p><a href="http://127.0.0.1:8814/">Live before/after Cubism viewer</a> · <a href="evidence.json">Exact evidence</a></p><p>The accepted prototype is unchanged. These are diagnostic renders, not an accepted natural gesture. Inspect the sleeve cut, hand visibility and continuity throughout the sweep. No new hidden artwork has been generated.</p><div class="grid"><article><h2>Neutral</h2><img src="neutral.png"></article><article><h2>Elbow sweep and return</h2><img src="sweep.webp"></article><article><h2>Talking/head/idle coexistence</h2><img src="clip.webp"></article></div><h2>Intermediate poses</h2><div class="grid">'''+''.join(f'<article><h3>{n}</h3><a href="{n}.png"><img src="{n}.png"></a></article>' for n in pose_names)+'''</div><h2>Joint hypotheses — editable review</h2><p>Choose a side and joint, then click the master image to propose a correction. Yellow points are hypotheses; the shoulder point is a sleeve surface anchor. Changes stay in this browser, bound to the exact evidence hash, and can be downloaded. They do not modify the rig or grant anatomical approval.</p><select id="side"><option>right</option><option>left</option></select><select id="joint"><option value="elbow">elbow</option><option value="wrist">wrist</option><option value="shoulder_surface">shoulder surface</option></select><button id="undo">Restore proposals</button><button id="download">Download corrections</button><p id="status"></p><canvas id="landmarks" width="800" height="1536"></canvas><h2>Reviewed synthetic helpers</h2><p>Visual references only; their projected limb lengths disagree. The current runtime contains only the accepted neutral artwork.</p><div class="grid">'''+''.join(f'<article><h3>{k}</h3><img src="{k}.png"></article>' for k in family['images'] if k!='canonical')+'''</div><script src="review.js"></script>''')
(out/'style.css').write_text('body{background:#21303d;color:#edf4fa;font:17px system-ui;margin:2rem}a{color:#9cddff}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}img{max-width:100%;max-height:600px;background:#d6d6df}article{background:#304251;padding:1rem}canvas{max-width:500px;width:100%;height:auto;cursor:crosshair}button,select{font:inherit;margin:.4rem;padding:.4rem}')
(out/'review.js').write_text('''(async()=>{const original=await(await fetch('joints.json')).json(),evidence=await(await fetch('evidence.json')).json(),key='elbow-review-'+evidence.proposal_sha256;let saved;try{saved=JSON.parse(localStorage.getItem(key)||'null')}catch{}let current=saved?.proposal||structuredClone(original);const canvas=document.getElementById('landmarks'),ctx=canvas.getContext('2d'),img=new Image();canvas.width=original.canvas[0];canvas.height=original.canvas[1];const status=document.getElementById('status');function draw(){ctx.drawImage(img,0,0,canvas.width,canvas.height);for(const [side,row]of Object.entries(current.arms))for(const name of ['shoulder_surface','elbow','wrist']){const[x,y]=row[name];ctx.strokeStyle=side==='right'?'#ef9b00':'#00a0ff';ctx.lineWidth=4;ctx.beginPath();ctx.arc(x*canvas.width,y*canvas.height,12,0,Math.PI*2);ctx.stroke();ctx.fillStyle='#111';ctx.font='18px sans-serif';ctx.fillText(side+' '+name,x*canvas.width+15,y*canvas.height)}}function persist(){localStorage.setItem(key,JSON.stringify({proposal:current,evidence,reviewer_kind:'human-correction-proposal',anatomy_approved:false}));status.textContent='Saved locally; rig remains unchanged.'}img.onload=draw;img.src='master.png';canvas.onclick=e=>{const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)/r.width,y=(e.clientY-r.top)/r.height;if(x<0||x>1||y<0||y>1)return;current.arms[document.getElementById('side').value][document.getElementById('joint').value]=[x,y];persist();draw()};document.getElementById('undo').onclick=()=>{current=structuredClone(original);persist();draw()};document.getElementById('download').onclick=()=>{persist();const a=document.createElement('a'),url=URL.createObjectURL(new Blob([localStorage.getItem(key)],{type:'application/json'}));a.href=url;a.download='elbow-correction-proposal.json';a.click();URL.revokeObjectURL(url)};})()''')
print(out)

page=out/'index.html';html=page.read_text().replace('127.0.0.1:8814','127.0.0.1:'+str(a.live_port))
overlap=a.run/'rig/overlap/overlap.json'
if overlap.exists():
 shutil.copyfile(overlap,out/'overlap.json');shutil.copyfile(overlap.parent/'sleeve-overlap.png',out/'sleeve-overlap.png')
 html=html.replace('No new hidden artwork has been generated.','A small source-derived concealed sleeve overlap was added after the user rejected the separating elbow. It is an inferred shape, not observed anatomy, and needs explicit human review. Original textures remain unchanged; the patch is invisible at rest.')
 html=html.replace('<h2>Intermediate poses</h2>','<p><a href="overlap.json">Overlap provenance</a> · <a href="sleeve-overlap.png">Exact new patch</a></p><h2>Intermediate poses</h2>')
if sides:
 html=html.replace('src="sweep.webp"','src="Right-sweep.webp"').replace('src="clip.webp"','src="Right-clip.webp"')
 if 'Left' in sides:html=html.replace('<h2>Intermediate poses</h2>','<h2>Left arm</h2><div class="grid"><img src="Left-sweep.webp"><img src="Left-clip.webp"></div><h2>Intermediate poses</h2>')
page.write_text(html)
