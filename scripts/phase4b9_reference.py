"""Read-only accepted-rig evidence and historical original-mask provenance."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image
from live2d_studio.pose_family import load
from live2d_studio.pose_guides import fit
from live2d_studio.pose_review import REPO,digest,write,Store


def run(family,output):
 data=load(family);pin=json.loads((REPO/'docs/references/codel-combined-v1.json').read_text());root=REPO/pin['reference_root']
 if digest(root/pin['manifest'])!=pin['manifest_sha256']:raise ValueError('Accepted manifest changed')
 author=(root/pin['paths']['editable_project']).parent
 if digest(author/'character.psd2live')!=pin['artifacts']['editable_project']['sha256']:raise ValueError('Accepted editable project changed')
 inspection=json.loads((author/'body-inspection.json').read_text())
 historical=REPO/'runs/phase4b8-canonical/selected-assessment-v1';source=historical/'source-1536.png';sam=historical/'source-1536'
 expected=json.loads((REPO/'docs/benchmarks/phase4b8.json').read_text())['selected_semantics']['baseline']['1536']
 for file,key in [(source,'image_sha256'),(sam/'sam.json','sam_metadata_sha256'),(sam/'handwear.png','arm_mask_sha256')]:
  if digest(file)!=expected[key]:raise ValueError('Historical original SAM evidence changed')
 output=output.resolve()
 if not output.is_relative_to(REPO/'runs') or output.is_relative_to(REPO/'runs/references'):raise ValueError('Fresh ignored output required')
 output.mkdir(parents=True,exist_ok=False)
 fit(Image.open(family/data['original']['path']),1536).save(output/'original-fitted.png')
 if digest(output/'original-fitted.png')!=expected['image_sha256']:raise ValueError('Historical SAM does not match original')
 rgb=np.asarray(Image.open(source).convert('RGB')).copy();mask=np.asarray(Image.open(sam/'handwear.png'))>0
 rgb[mask]=(.45*rgb[mask]+.55*np.array([230,70,70])).astype('uint8');Image.fromarray(rgb).save(output/'original-merged-arms.png')
 write(output/'accepted-arm-anatomy.json',inspection['anatomy'])
 state=Store(REPO/data['review_run']).state();guide=state['poses']['torso-open']['guides']['silhouette'];p=guide['joints'];s=p['rs'];e=p['re'];w=p['rw']
 result={'accepted_manifest_sha256':pin['manifest_sha256'],'editable_project_sha256':pin['artifacts']['editable_project']['sha256'],
   'inspection_sha256':digest(author/'body-inspection.json'),'original_sam':expected,'historical_sam_directory':str(historical.relative_to(REPO)),
   'new_original_inference':False,'accepted_independent_arms':inspection['anatomy']['independent_arms'],'limb_candidates':inspection['anatomy']['limb_candidates'],
   'pending_guide':{'sha256':guide['sha256'],'status':state['poses']['torso-open']['status'],'upper_arm_degrees_from_vertical':math.degrees(math.atan2(abs(e[0]-s[0]),e[1]-s[1])),
     'shoulder_wrist_degrees_from_vertical':math.degrees(math.atan2(abs(w[0]-s[0]),w[1]-s[1])),
     'future_only':'Versioned 40–55 degree abduction design in a fresh run, with frame-bound checks; no edit or new generation here'},
   'constraint':'User explicitly requires keeping exact accepted artwork and rig; no canonical body replacement',
   'rig_gate':'blocked: source-view bilateral cut lines, shoulder/joint backing and helper attachment mapping remain unreviewed'}
 write(output/'reference-assessment.json',result);return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--family',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.family,a.output)
