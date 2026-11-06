"""Local source-derived sleeve overlap, explicitly inferred and review-required."""
from pathlib import Path
import numpy as np
from PIL import Image
from .manifest import load_validate, digest, write_json
from .pose_review import REPO


def prepare(layers, proposal, side, output):
    layers=Path(layers);output=Path(output).resolve();data=load_validate(layers)
    if not output.is_relative_to(REPO/'runs') or output.exists():raise ValueError('Fresh ignored overlap directory required')
    if digest(layers/'layer_manifest.json')!=proposal['layer_manifest_sha256']:raise ValueError('Changed overlap source')
    w,h=proposal['canvas'];pivot=np.array(proposal['arms'][side]['elbow'])*[w,h]
    arm=np.zeros((h,w,4),np.uint8)
    for l in data['layers']:
        if l.get('anatomical_side')!=side:continue
        a=np.array(Image.open(layers/l['rgba_path']).convert('RGBA'));x,y=l['x'],l['y'];area=arm[y:y+a.shape[0],x:x+a.shape[1]];area[a[...,3]>0]=a[a[...,3]>0]
    row=int(round(pivot[1]));xs=np.where(arm[row,:,3]>127)[0]
    if len(xs)<8:raise ValueError('No substantial sleeve at pivot')
    radius=min(pivot[0]-xs.min(),xs.max()-pivot[0])
    if radius<4:raise ValueError('Pivot near sleeve edge; review landmark first')
    yy,xx=np.indices((h,w));circle=((xx-pivot[0])/radius)**2+((yy-pivot[1])/(radius*1.05))**2<=1
    patch=arm.copy();patch[~circle]=0;y,x=np.where(patch[...,3]>0)
    box=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1));output.mkdir(parents=True)
    Image.fromarray(patch).crop(box).save(output/'sleeve-overlap.png')
    record={'layer_manifest_sha256':digest(layers/'layer_manifest.json'),'side':side,'pivot':pivot.tolist(),
        'radius_pixels':float(radius),'bbox':list(box),'center':[(box[0]+box[2])/2,(box[1]+box[3])/2],
        'path':'sleeve-overlap.png','sha256':digest(output/'sleeve-overlap.png'),
        'classification':'generated source-derived concealed overlap; duplicated samples are not observed ownership',
        'method':'Elliptical source sleeve patch beneath existing upper and moving forearm; alpha zero at rest',
        'new_rgb_inference':False,'new_hidden_shape':True,'human_review':'pending'}
    write_json(output/'overlap.json',record);return record
