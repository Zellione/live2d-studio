"""Canonical-only raster layer/transition diagnostic. This does not author a rig."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from live2d_studio.pose_family import load
from live2d_studio.pose_review import REPO,digest,write


def run(family,geometry,output,pose='right-lift',side='right'):
 data=load(family);assessment=json.loads((geometry/'assessment.json').read_text())
 if assessment['family_sha256']!=digest(family/'family.json'):raise ValueError('Wrong geometry family')
 if pose not in data['images'] or pose=='canonical':raise ValueError('Approved helper required')
 output=output.resolve()
 if not output.is_relative_to(REPO/'runs') or output.is_relative_to(REPO/'runs/references'):raise ValueError('Fresh ignored output required')
 output.mkdir(parents=True,exist_ok=False)
 rest=Image.open(family/data['images']['canonical']['path']).convert('RGB');helper=Image.open(family/data['images'][pose]['path']).convert('RGB')
 a=assessment['images']['canonical'];b=assessment['images'][pose];anchor=np.array(a['arms'][side]['shoulder_surface']);source=np.array(b['arms'][side]['shoulder_surface']);scale=a['torso_frame']['height_pixels']/b['torso_frame']['height_pixels']
 inverse=(1/scale,0,float(source[0]-anchor[0]/scale),0,1/scale,float(source[1]-anchor[1]/scale))
 registered=helper.transform(rest.size,Image.Transform.AFFINE,inverse,resample=Image.Resampling.BICUBIC,fillcolor='white')
 old=np.asarray(Image.open(geometry/'canonical'/(side+'-arm.png')))>0
 moved=Image.open(geometry/pose/(side+'-arm.png')).transform(rest.size,Image.Transform.AFFINE,inverse,resample=Image.Resampling.NEAREST,fillcolor=0)
 new=np.asarray(moved)>0;original=np.asarray(rest);target=original.copy();target[old]=255;target[new]=np.asarray(registered)[new]
 # Deliberately unfilled holes show why a silhouette alone is not hidden backing.
 unknown=old&~new
 Image.fromarray(target).save(output/'posed.png');rest.save(output/'neutral.png')
 for name,rgb,m in [('rest-arm',original,old),('posed-arm',np.asarray(registered),new)]:
  rgba=np.dstack([rgb,m.astype(np.uint8)*255]);Image.fromarray(rgba).save(output/(name+'.png'))
 gap=original.copy();gap[unknown]=(.35*gap[unknown]+.65*np.array([255,150,0])).astype('uint8');Image.fromarray(gap).save(output/'removed-support.png')
 frames=[];rows=[];union=old|new
 for i,t in enumerate([j/10 for j in range(11)]+[j/10 for j in range(9,-1,-1)]):
  im=Image.blend(rest,Image.fromarray(target),t);im.save(output/f'frame-{i:02d}.png');frames.append(im)
  rows.append({'frame':i,'weight':t,'outside_arm_union_exact':bool(np.array_equal(np.asarray(im)[~union],original[~union])),
               'two_distinct_arm_positions_blended':bool(0<t<1),'old_only_pixels':int((old&~new).sum()),'new_only_pixels':int((new&~old).sum())})
 frames[0].save(output/'crossfade-diagnostic.webp',save_all=True,append_images=frames[1:],duration=140,loop=0,lossless=True)
 report={'family_sha256':digest(family/'family.json'),'assessment_sha256':digest(geometry/'assessment.json'),'pose':pose,'side':side,
   'scope':'Canonical-only raster diagnostic; no PSD2Live project, MOC or preservation claim for accepted angled rig',
   'registration':{'method':'Uniform torso-height scaling and shoulder-surface translation only','scale':scale,'inverse_affine':list(inverse)},
   'return_to_neutral_exact':digest(output/'frame-00.png')==digest(output/'frame-20.png'),'frames':rows,
   'crossfade_status':'reject: simultaneous displaced limbs at intermediate weights',
   'hard_switch_status':'One silhouette at a time, but abrupt pose jump; shoulder seam/backing and accepted angled-rig mapping remain unvalidated',
   'backing_status':'Erased arm support is white for diagnostic visibility, not a reconstructed torso or verified background',
   'rig_authorized_by_probe':False}
 write(output/'probe.json',report);return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--family',type=Path,required=True);p.add_argument('--geometry',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.family,a.geometry,a.output)
