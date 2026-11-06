"""Local review gallery for selected-only anatomy evidence and failed rig prerequisites."""
import argparse
import html
import json
from pathlib import Path
import shutil
import numpy as np
from PIL import Image
from live2d_studio.pose_family import load
from live2d_studio.pose_review import REPO,digest,write


def build(family,geometry,probe,audit,output):
 data=load(family);report=json.loads((geometry/'assessment.json').read_text());trial=json.loads((probe/'probe.json').read_text())
 if report['family_sha256']!=digest(family/'family.json') or trial['family_sha256']!=digest(family/'family.json'):raise ValueError('Mixed family evidence')
 output=output.resolve()
 if not output.is_relative_to(REPO/'runs') or output.is_relative_to(REPO/'runs/references'):raise ValueError('Fresh ignored output required')
 output.mkdir(parents=True,exist_ok=False)
 def cp(file,name):shutil.copyfile(file,output/name);return name
 def picture(title,file,name,caption=''):
  cp(file,name);return f'<article><h3>{html.escape(title)}</h3><a href="{name}" target="_blank"><img src="{name}" alt="{html.escape(title)}"></a><p>{html.escape(caption)}</p></article>'
 page='''<!doctype html><meta charset="utf-8"><title>Phase 4B.9 arm evidence</title><style>body{background:#19222d;color:#edf3fa;font:16px system-ui;margin:2rem}p{max-width:100ch}a{color:#9acbff}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1rem}article{background:#283647;padding:1rem}img{width:100%;max-height:75vh;object-fit:contain;background:white}table{border-collapse:collapse}td,th{padding:.55rem;border:1px solid #6c8095}.warning{border-left:5px solid #e6a047;padding:1rem;background:#283647}</style><h1>Four reviewed poses: arm reconstruction assessment</h1><p class="warning">Assessment complete; rig authoring stopped. Helpers improve visible arm separation, but the exact accepted angled rig still has merged arms and unreviewed cut lines/backing. No new editable gesture rig or runtime is claimed. The fifth pose remains pending and was not generated.</p><p><a href="http://127.0.0.1:8806/">Inspect unchanged accepted animated rig</a> · <a href="assessment.json">Exact geometry hypotheses</a> · <a href="family.json">Approval-bound family manifest</a></p><h2>Original and human-reviewed family</h2><div class="grid">'''
 page+=picture('Original identity / accepted-rig basis',family/data['original']['path'],'original.png','Angled original. Helpers do not provide pixel-aligned hidden anatomy for this body.')
 for pose,row in data['images'].items():page+=picture(pose,family/row['path'],pose+'.png','Human-approved synthetic image. Visual approval is distinct from joint or rig approval.')
 page+='</div><h2>Proposed segmentation and joint hypotheses</h2><p>Red/blue identify anatomical right/left under the inspected frontal, non-mirrored assumption. Yellow circles are heuristic inspection regions, not statistical confidence. Orange boxes mark unresolved straight-arm elbows. All upper/forearm/hand cuts remain exploratory.</p>'
 for pose,row in report['images'].items():
  base=np.asarray(Image.open(family/data['images'][pose]['path']).convert('RGB')).copy();tint=base.copy();colors=[(235,65,65),(245,155,35),(240,225,50),(55,120,240),(55,210,225),(170,100,240)]
  for (side,part),color in zip([(s,p) for s in ('right','left') for p in ('upper','forearm','hand')],colors):
   file=geometry/pose/(side+'-'+part+'.png')
   if file.exists():
    m=np.asarray(Image.open(file))>0;tint[m]=(.45*base[m]+.55*np.array(color)).astype('uint8')
  Image.fromarray(tint).save(output/(pose+'-parts.png'))
  page+='<h3>'+html.escape(pose)+'</h3><div class="grid">'+picture('Side masks and uncertain landmarks',geometry/pose/'overlay.png',pose+'-joints.png')
  page+=f'<article><h3>Candidate part partitions</h3><a href="{pose}-parts.png" target="_blank"><img src="{pose}-parts.png"></a><p>Right: red upper sleeve, orange forearm, yellow hand. Left: blue upper sleeve, cyan forearm, purple hand. These are proposals, including uncertain cloth seams and skin/ink assignment.</p></article></div>'
 page+='<h2>Cross-pose consistency</h2><table><tr><th>Pose</th><th>Side</th><th>Upper / torso height</th><th>Forearm / torso height</th><th>Joint status</th></tr>'
 for pose,r in report['images'].items():
  for side,a in r['arms'].items():
   if 'elbow' in a:page+=f"<tr><td>{pose}</td><td>{side}</td><td>{a['upper_length_over_torso']:.3f}</td><td>{a['forearm_length_over_torso']:.3f}</td><td>{html.escape(a['elbow']['status'])}</td></tr>"
 page+='</table><p>The explanatory forearm has only about 36% of the raised-pose projected length. Foreshortening, silhouette ambiguity and redraw cannot be separated from these views. Straight-neutral elbow splits are unresolved, so their point estimates are not bone-length measurements. Torso front views are useful synthetic references, not recovered original hidden pixels.</p><h2>Why the exact accepted rig is not ready for an independent arm</h2><div class="grid">'
 page+=picture('Original SAM: merged arm region',audit/'original-merged-arms.png','original-merged-arms.png','Historical input-matched parser output. Both original arms remain in one substantial component and one accepted handwear mesh.')
 page+=picture('Canonical-only swap endpoint: rejected join',probe/'posed.png','probe-posed.png','A simple shoulder registration leaves a white cut seam and old outline pixels. This is a raster diagnostic, not an editable rig or proposed accepted-model replacement.')
 page+=picture('Intermediate crossfade: rejected',probe/'frame-05.png','probe-midpoint.png','Both displaced arms are visible simultaneously. Replacing the entire body instead would violate the exact-artwork requirement.')
 page+='</div><h2>Transition diagnostic and neutral restoration</h2><div class="grid">'+picture('Rejected raster crossfade loop',probe/'crossfade-diagnostic.webp','crossfade-diagnostic.webp','21 sampled frames, neutral → pose → neutral. Outside the arm-mask union stays exact. The returned neutral is byte-identical; that does not make intermediate frames usable.')+'</div>'
 page+='<h2>Method decision</h2><p>Continuous shoulder/elbow articulation is not supported yet: rest elbows, source-side ownership, occluded joint backing and a consistent 2-D length model are unresolved. Gesture-specific layers are the preferred next experiment after original-view cut lines, shoulder attachment and backing are reviewed. A hard swap avoids translucent duplicate limbs but cannot repair attachment seams or supply hidden torso pixels.</p><p>The next review should resolve the original angled arm/torso partition and one source-view-compatible gesture attachment. No fifth helper is required. The historical torso-open guide tilts its upper arm only 13.4° from vertical; a future separately versioned 40–55° abduction target needs a framing check and a fresh review run.</p>'
 page+='<h2>Accepted behavior retained</h2><p>The existing facial, mouth, head, hair, breathing, idle, Nod and Question rig stays unchanged. The linked local viewer loads the frozen runtime. Fresh Core and browser regression results are recorded separately; they validate preservation, not a new arm gesture.</p><p>Codel artwork: LisadiKaprio, <a href="https://opengameart.org/content/codel-visual-novel-sprite">CC-BY-4.0 source</a>. Selected helper images are synthetic derivatives. Stop for human review of these proposals.</p>'
 for file,name in [(geometry/'assessment.json','assessment.json'),(family/'family.json','family.json'),(probe/'probe.json','probe.json')]:cp(file,name)
 (output/'index.html').write_text(page)
 write(output/'gallery.json',{'family_sha256':digest(family/'family.json'),'assessment_sha256':digest(geometry/'assessment.json'),'probe_sha256':digest(probe/'probe.json'),'new_rig':False})

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for key in ('family','geometry','probe','audit','output'):p.add_argument('--'+key,type=Path,required=True)
 a=p.parse_args();build(a.family,a.geometry,a.probe,a.audit,a.output)
