"""Prepare an evaluation-only missing-skin test without giving truth to inference."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from PIL import Image
from live2d_studio.manifest import load_validate,write_json,digest
from live2d_studio.facial_artwork import skin_surface
from live2d_studio.neural_artwork import crop_box


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--layers',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=load_validate(a.layers)
    source=np.array(Image.open(a.layers/data['sources'][0]['normalized_path']).convert('RGBA'))
    face=next(l for l in data['layers'] if l['role']=='face')
    known=np.zeros(source.shape[:2],bool)
    x,y=face['x'],face['y'];known[y:y+face['height'],x:x+face['width']]=np.array(Image.open(a.layers/face['mask_path']))>0
    distance=ndi.distance_transform_edt(known);cy,cx=np.unravel_index(np.argmax(distance),distance.shape)
    radius=max(2,min(8,int(distance[cy,cx]/3)))
    yy,xx=np.indices(known.shape);hole=(xx-cx)**2+(yy-cy)**2<=radius**2
    if not known[hole].all():raise ValueError('No safe source-owned skin patch')
    # The removed truth goes only to a separate evaluator directory.
    known &= ~hole
    deterministic=source.copy();deterministic[hole,:3]=skin_surface(source,known,hole)[hole]
    corrupted=source.copy();corrupted[hole,:3]=0
    box=crop_box(hole,context=4);x,y,x1,y1=box
    requests=a.output/'requests';requests.mkdir(parents=True,exist_ok=False)
    evaluation=a.output/'evaluation';evaluation.mkdir()
    for name,pixels,folder in [('skin-gap',corrupted,requests),('truth',source,evaluation),('deterministic',deterministic,evaluation)]:
        Image.fromarray(pixels[y:y1,x:x1]).save(folder/(name+'.png'))
    Image.fromarray(hole[y:y1,x:x1].astype(np.uint8)*255).save(requests/'skin-gap-mask.png')
    write_json(requests/'tasks.json',[dict(id='skin-gap',image='skin-gap.png',mask='skin-gap-mask.png',scale=1,seed=1729,
        prompt='Fill the missing small skin patch with matching flat anime skin color and shading. No new details.',steps=20,cfg=4.0)])
    write_json(evaluation/'provenance.json',dict(source_sha256=digest(a.layers/data['sources'][0]['normalized_path']),rights=data['sources'][0]['rights'],
        removed_pixels=int(hole.sum()),box=box,truth_is_evaluation_only=True,not_hidden_anatomical_truth=True))


if __name__=='__main__':main()
