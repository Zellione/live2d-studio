"""Replay a hash-verified prefilled skin task; retain deterministic source contours."""
import argparse,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from live2d_studio.manifest import digest,write_json
from live2d_studio.neural_artwork import tasks,reuse_predictions
from live2d_studio.stages import verify
from live2d_studio.generic_rig import create_project,author_rig,author_animation,export_model
from live2d_studio.mcp import MCP

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for k in ['baseline','cache','output']:p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--feature',default='eye-left-skin');p.add_argument('--task',default='skin-prefill-40')
 a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
 state=json.loads((a.baseline/'creation.json').read_text());s=state['stages']['facial'];base=a.baseline/s['directory'];verify(base,s['files'])
 layers=a.output/'layers';shutil.copytree(base/'layers',layers)
 tasks(layers,a.output/'preparation',scale=1,targets=[a.feature])
 b=json.loads((a.output/'preparation/bindings.json').read_text())['bindings'][0];x,y,x1,y1=b['box']
 req=a.cache/'requests';task=next(t for t in json.loads((req/'tasks.json').read_text()) if t['id']==a.task)
 mask=np.array(Image.open(req/task['mask']))>0
 expected_mask=np.array(Image.open(a.output/'preparation'/(a.feature+'-mask.png')))>0
 if not np.array_equal(mask,expected_mask):raise ValueError('Cache mask differs from source-derived skin region')
 old=np.array(Image.open(layers/b['variant']).convert('RGBA'))
 expected=np.array(Image.open(a.output/'preparation'/(a.feature+'.png')).convert('RGBA'));expected[mask]=old[y:y1,x:x1][mask]
 actual=np.array(Image.open(req/task['image']).convert('RGBA'))
 if not np.array_equal(expected,actual):raise ValueError('Prefilled conditioning belongs to different source artwork')
 local=a.output/'requests';local.mkdir();shutil.copyfile(req/task['image'],local/task['image']);shutil.copyfile(req/task['mask'],local/task['mask']);write_json(local/'tasks.json',[task])
 reuse_predictions(local,a.output/'predictions',a.cache/'predictions','qwen')
 new=old.copy();rgb=np.array(Image.open(a.output/'predictions'/a.task/'composite.png').convert('RGBA'))
 if not np.array_equal(rgb[~mask],expected[~mask]):raise ValueError('Protected conditioning changed')
 # Keep deterministic boundary and blend generated interior only.
 weight=np.clip((ndi.distance_transform_edt(mask)-1)/2,0,1)
 crop=new[y:y1,x:x1];crop[...,:3]=np.rint(crop[...,:3]*(1-weight[...,None])+rgb[...,:3]*weight[...,None]).astype('uint8')
 if not np.array_equal(new[...,3],old[...,3]):raise ValueError('Skin alpha changed')
 Image.fromarray(new).save(layers/b['variant'])
 generated=np.zeros(old.shape[:2],np.uint8);generated[y:y1,x:x1]=(weight>0)*255
 maskname='alternatives/'+a.feature+'-reused-neural-mask.png';Image.fromarray(generated).save(layers/maskname)
 boundaryname='alternatives/'+a.feature+'-reused-neural-boundary.png';Image.fromarray((ndi.binary_dilation(generated>0)&~ndi.binary_erosion(generated>0)).astype('uint8')*255).save(layers/boundaryname)
 report=json.loads((layers/'facial-artwork.json').read_text());variant=next(v for v in report['alternatives'] if v['path']==b['variant'])
 variant.update(sha256=digest(layers/b['variant']),provenance='Reused hash-verified Qwen prefilled skin; deterministic boundary blend',
  neural_mask_path=maskname,neural_mask_sha256=digest(layers/maskname),uncertain_boundary_path=boundaryname,uncertain_boundary_sha256=digest(layers/boundaryname))
 write_json(layers/'facial-artwork.json',report)
 client=MCP('http://127.0.0.1:23871/mcp')
 for stage,fn,parent in [('project',create_project,layers),('rig',author_rig,a.output/'project'),('animation',author_animation,a.output/'rig'),('export',export_model,a.output/'animation')]:
  folder=a.output/stage;folder.mkdir();fn(client,parent,folder,**({'facial_motion':'aligned'} if stage=='project' else {}))
 write_json(a.output/'experiment.json',dict(baseline=str(a.baseline),skin_cache=str(a.cache),input_sha256=digest(local/task['image']),
  model_report_sha256=digest(a.output/'predictions/producer-report.json'),original_layers_unchanged=True,review='needs-temporal-review'))
 print(a.output)
