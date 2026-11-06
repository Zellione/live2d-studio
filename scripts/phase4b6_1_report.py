"""Build controlled facial review and collect expression/body preservation evidence."""
import argparse,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from live2d_studio.manifest import digest,write_json
from live2d_studio.generic_rig import archived_art
from live2d_studio.stages import verify
from phase4b6_report import record
REPO=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def browser(p):return read(p/'frames/result.json')['result']['value']
def build(run,before,reference,output):
 output.mkdir(parents=True,exist_ok=False);spec=read(run/'performance.json');model=run/spec['model'];author=run/spec['authoring'];validation=run/'validation';face=run/'face-final';layerdata=read(Path(spec['layers'])/'layer_manifest.json')
 canvas=layerdata['canvas'];scale=570/max(canvas['width'],canvas['height']);left=(600-canvas['width']*scale)/2
 def box(role,padding):
  l=next(l for l in layerdata['layers'] if l['role']==role);x,y,w,h=l['x'],l['y'],l['width'],l['height'];pad=w*padding
  return tuple(round(v*3) for v in (left+(x-pad)*scale,35+(y-pad)*scale,left+(x+w+pad)*scale,35+(y+h+pad)*scale))
 face_box=box('face',.12);mouth_box=box('mouth',.8)
 poses=[('Phase 4B.6 / Confused',before,'confused'),('Improved reference / Confused',reference,'confused'),('Combined / Confused',face,'confused'),('Combined / Surprised',face,'surprised'),('Combined / Sad',face,'sad')]
 def sheet(mode,region,file,entries=poses):
  crops=[Image.open(folder/'frames'/f'{mode}-{emotion}.png').convert('RGBA').crop(region) for _,folder,emotion in entries]
  width=max(im.width for im in crops);height=max(im.height for im in crops);result=Image.new('RGBA',(width*len(crops),height+50),'#e4e8e4');pen=ImageDraw.Draw(result)
  for i,(im,(label,_,_)) in enumerate(zip(crops,entries)):
   result.alpha_composite(im,(i*width,50));pen.text((i*width+5,12),label,fill='#172b26')
  result.save(output/file)
 sheet('mouth',face_box,'mouth-only-faces.png');sheet('mouth',mouth_box,'mouth-closeups.png');sheet('full',face_box,'full-expressions.png')
 sheet('full',face_box,'seven-expressions.png',[(n,face,n) for n in ['neutral','happy','sad','angry','confused','surprised','embarrassed']])
 # Exact comparison uses identically sized Core render buffers, including alpha.
 neutral=np.asarray(Image.open(face/'frames/neutral.png'));original=np.asarray(Image.open(before/'frames/neutral.png'))
 counts={}
 for mode in ['mouth','full']:
  a=np.asarray(Image.open(face/'frames'/f'{mode}-confused.png'));b=np.asarray(Image.open(reference/'frames'/f'{mode}-confused.png'))
  counts[mode]=int(np.any(a!=b,axis=2).sum())
 beforemodel=REPO/'runs/phase4b6-codel-v7/export/runtime/Generated_artwork.model3.json'
 a=read(model);b=read(beforemodel);preserved={}
 for category in ['Physics']:
  preserved[category]=digest(model.parent/a['FileReferences'][category])==digest(beforemodel.parent/b['FileReferences'][category])
 for group in ['Idle','Nod','Question']:
  preserved[group]=digest(model.parent/a['FileReferences']['Motions'][group][0]['File'])==digest(beforemodel.parent/b['FileReferences']['Motions'][group][0]['File'])
 oldart=archived_art(REPO/'runs/phase4b6-codel-v7/authoring/character.psd2live');newart=archived_art(author/'character.psd2live')
 assert all(newart.get(k)==v for k,v in oldart.items())
 seal=read(REPO/'runs/phase4b5-freeze/first-run-seal.json');verify(Path(seal['run']),seal['files'])
 # The earlier body reference's own inventory also covers accepted authoring and
 # its runtime. Browser process symlinks are excluded, not model files.
 verify(REPO/'runs/phase4b6-codel-v7',read(REPO/'runs/phase4b6-1-codel-v2/predecessor-inventory.json'))
 cores={n:read(validation/(n+'.json')) for n in ['mouth-core-final','body-core','body-preserved','mouth-precision']}
 results={}
 for n,folder in [('mouths',validation/'mouths'),('dense',validation/'dense'),('body',validation/'body'),('face',face),('coexistence',validation/'coexistence')]:
  r=browser(folder);results[n]=dict(status=r['status'],frames=len(r['frames']),geometry=r['geometry'],reload=r.get('reload'))
 report=dict(phase='4B.6.1',candidate=str(run.relative_to(REPO)),model_sha256=digest(model),body_reference='runs/phase4b6-codel-v7',body_motion_user_feedback='accepted by user; preserved',visual_review='pending',promoted=False,
  runtime_files={str(f.relative_to(model.parent)):digest(f) for f in sorted(model.parent.rglob('*')) if f.is_file()},
  source_pngs_preserved=len(oldart),new_archived_pngs=len(newart)-len(oldart),source_layers=read(author/'source-art.json') if (author/'source-art.json').exists() else None,
  neutral_pixels_equal=bool(np.array_equal(neutral,original)),confused_pixels_different_from_improved_reference=counts,preserved_runtime_files=preserved,
  core={n:{k:v for k,v in r.items() if k not in ['samples','expressions']} for n,r in cores.items() if n!='mouth-precision'},render=results,
  expressions={e['Name']:read(model.parent/e['File']) for e in a['FileReferences']['Expressions']},
  old_strict_failure_preserved='runs/phase4b5-codel-mouths/expression-core.json',girl2_inherited_failure='runs/phase4b6-portrait-final/girl2/predecessor-core-body.json',
  numerical_policy='Structural opening independence plus eight float32 steps at mesh coordinate magnitude, capped at .001 source pixel. Legacy 1e-7 diagnostic retained separately.',
  frozen_codel_seal='verified unchanged',accepted_body_inventory='verified unchanged')
 assert all(preserved.values()) and report['neutral_pixels_equal']
 for n,r in report['core'].items():assert r['status']=='pass',n
 for n,r in results.items():assert r['status']=='pass',n
 for label in ['codel','sara']:
  r=read(REPO/f'runs/phase4b6-1-diagnosis/{label}-contract-core.json')
  report.setdefault('independent_numerical_checks',{})[label]=dict(status=r['status'],poses=len(r['samples']),seam_groups=len(r['seam_measurements']),maximum_source_pixel_change=max(v['source_pixels'] for v in r['seam_measurements']))
 write_json(output/'benchmark.json',report)
 write_json(output/'development-review.json',dict(reviewer='development-agent',decision='candidate-for-user-review',user_approval=False,promoted=False,
  runtime_files=report['runtime_files'],project_sha256=digest(author/'character.psd2live'),
  evidence_sha256={str(f.relative_to(REPO)):digest(f) for f in [validation/'mouth-core-final.json',validation/'body-preserved.json',validation/'coexistence/frames/result.json',face/'frames/result.json']},
  scope='Controlled mouth-only/full-expression sheets and sampled continuous behavior',
  observations=['Small parted Confused oval; larger Surprised opening; distinct downward Sad mouth','Confused stills exactly match improved mouth reference','Approved body files and non-authored region vertices preserved','Plain cavity, inherited eye/backing defects and static limb articulation remain']))
 r=browser(validation/'coexistence');record(validation/'coexistence',r,'confused-moving',output/'confused-moving.webm')
 (output/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Codel · Confused expression repair</title><style>body{font:16px/1.5 system-ui;max-width:1400px;margin:40px auto;padding:0 24px;background:#edf0eb;color:#213930}h1,h2{font-weight:500}img,video{max-width:100%;background:#c8d3ce;border-radius:12px}section{margin:40px 0}.note{padding:20px;background:white;border-radius:12px}a{color:#225c4b}</style><h1>Codel · improved expressions with the approved body motion</h1><div class="note">Candidate for explicit user visual review; not promoted. Head geometry, physics and all three body clips are preserved.<p><a href="http://127.0.0.1:8792/">Interactive before/after viewer</a> · <a href="benchmark.json">Measurements</a></p></div><section><h2>Mouth-only comparison</h2><p>Identical scale, head position, neutral eyes/brows and settled state. Left to right: Phase 4B.6 Confused; improved mouth reference; combined Confused; combined Surprised; combined Sad.</p><img src="mouth-only-faces.png"><p>Same rendered pixels enlarged for contour inspection:</p><img src="mouth-closeups.png"></section><section><h2>Complete expressions</h2><p>Same ordering and framing. Supported brow/eye expression differences are restored.</p><img src="full-expressions.png"></section><section><h2>All seven expressions</h2><img src="seven-expressions.png"></section><section><h2>Confused during motion and conversation</h2><video controls loop muted playsinline src="confused-moving.webm"></video><p>Idle and hair dynamics, Question gesture, talking, then return to the slightly parted resting mouth. Timed browser samples; not every display refresh.</p></section><p>Arms remain shared/static for articulation. Existing near-closed eye artifacts, inferred facial backing and the plain cavity remain. The new numerical seam contract does not establish naturalness; the legacy strict failure and Girl2 lip reversals remain preserved.</p><p>Codel by LisadiKaprio, <a href="https://opengameart.org/content/codel-visual-novel-sprite">OpenGameArt</a>, CC BY 4.0. Local decomposition and rigging modifications.</p></html>''')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--before',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=build(a.run.resolve(),a.before.resolve(),a.reference.resolve(),a.output.resolve());print(json.dumps({k:r[k] for k in ['neutral_pixels_equal','confused_pixels_different_from_improved_reference','preserved_runtime_files']},indent=2))
