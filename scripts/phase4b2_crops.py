"""Prepare/run reproducible single-image facial crops from a frozen baseline."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
from live2d_studio.neural_artwork import tasks,infer
from live2d_studio.manifest import write_json
from live2d_studio.stages import verify


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--model',choices=['lama','qwen']);p.add_argument('--scale',type=int,default=1)
    p.add_argument('--targets',help='Comma-separated alternative IDs')
    p.add_argument('--controlled',action='store_true',help='40-step blank-skin / half-from-open controls')
    p.add_argument('--half-from-closed',action='store_true',help='Retain the initial, ambiguous half-lid diagnostic')
    a=p.parse_args();d=json.loads((a.baseline/'creation.json').read_text());stage=d['stages']['facial']
    layers=a.baseline/stage['directory']/'layers';verify(layers.parent,stage['files'])
    a.output.mkdir(parents=True,exist_ok=False)
    request=a.output/'requests'
    if a.controlled:
        tasks(layers,a.output/'preparation',scale=1,targets=['eye-left-skin'])
        prep=a.output/'preparation';b=json.loads((prep/'bindings.json').read_text())['bindings'][0];x,y,x1,y1=b['box']
        source=np.array(Image.open(prep/'eye-left-skin.png').convert('RGBA'));mask=np.array(Image.open(prep/'eye-left-skin-mask.png'))>0
        skin=np.array(Image.open(layers/'alternatives/eye-left-skin.png'))[y:y1,x:x1]
        filled=source.copy();filled[mask]=skin[mask]
        request.mkdir();Image.fromarray(filled).save(request/'prefill.png');Image.fromarray(source).save(request/'open.png')
        Image.fromarray(mask.astype(np.uint8)*255).save(request/'mask.png')
        batch=[dict(id='skin-prefill-40',image='prefill.png',mask='mask.png',seed=1729,scale=1,steps=40,cfg=4.0,
            prompt='Keep the blank skin patch on the viewer-left side of this face completely blank. Smooth its shading to match the surrounding skin. No eye, iris, eyelashes, line or other feature in that blank patch. Preserve the same anime art style.'),
            dict(id='half-from-open-40',image='open.png',mask='mask.png',seed=1729,scale=1,steps=40,cfg=4.0,
            prompt='Make only the viewer-left eye half closed. Lower its upper eyelid to halfway across its original iris. Preserve the original iris color and size, clean thin anime contour, and same character identity. The other eye stays unchanged.')]
        write_json(request/'tasks.json',batch)
    else:
        batch=tasks(layers,request,scale=a.scale,targets=a.targets.split(',') if a.targets else None)
        if a.half_from_closed:
            item=next(t for t in batch if t['id']=='eye-left-closed').copy()
            item.update(id='eye-left-half',prompt='Make this eye half closed: lower the upper eyelid halfway across the iris, keep a natural clean anime lash contour. Preserve this character, eye color and hand-drawn art style. No duplicate contours.')
            batch.append(item);write_json(request/'tasks.json',batch)
    if a.model:infer(request/'tasks.json',a.output/'predictions',a.model)
    print(request/'tasks.json')


if __name__=='__main__':main()
