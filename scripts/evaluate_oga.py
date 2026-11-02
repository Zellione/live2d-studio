"""Independent six-group CC0 benchmark; reads GT only AFTER inference."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
from live2d_studio.manifest import load_validate,write_json,digest

GROUPS=('hair_accessories','face_ears_nose','eyes_brows','mouth','neck','clothing')
GT_GROUP={
    'G2 HairTop':'hair_accessories','G2 HairBottom':'hair_accessories',
    'G2 Ponytail1':'hair_accessories','G2 Ponytail2':'hair_accessories',
    'G2 Face':'face_ears_nose','G2 InnerEyes':'eyes_brows','G2 OuterEyes2':'eyes_brows',
    'G2 Mouth4':'mouth','G2 Neck':'neck','G2 Shirt':'clothing'}
ROLE_GROUP={**{r:'hair_accessories' for r in ['front_hair','back_hair','headwear']},
    **{r:'face_ears_nose' for r in ['face','ears','nose','face_detail']},
    **{r:'eyes_brows' for r in ['irides','eyewhite','eyelash','eyebrow']},
    **{r:'mouth' for r in ['mouth','mouth_open','mouth_close','tooth_t','tooth_b','tongue']},
    'neck':'neck','topwear':'clothing','handwear':'clothing'}


def iou(a,b):
    union=int((a|b).sum())
    return int((a&b).sum())/union if union else None


def maps(layers,size):
    full={g:np.zeros((size[1],size[0]),bool) for g in GROUPS}
    visible=np.full((size[1],size[0]),-1,dtype=np.int16)
    for image,group in layers:
        mask=np.array(image.getchannel('A').resize(size,Image.Resampling.NEAREST))>127
        visible[mask]=GROUPS.index(group) if group in GROUPS else -2
        if group in GROUPS:full[group]|=mask
    return full,visible


def evaluate(project,truth):
    data=load_validate(project)
    if data['sources'][0]['sha256']!=digest(truth/'flat.png'):
        raise ValueError('Ground truth belongs to a different original input')
    gt=json.loads((truth/'benchmark.json').read_text())
    original=Image.open(truth/'flat.png')
    size=original.size
    gt_layers=[(Image.open(truth/l['path']).convert('RGBA'),GT_GROUP[l['name']]) for l in gt['layers']]
    pred_layers=[]
    for l in data['layers']:
        if not l['default_visible']:continue
        canvas=Image.new('RGBA',(data['canvas']['width'],data['canvas']['height']))
        canvas.paste(Image.open(project/l['rgba_path']),(l['x'],l['y']))
        pred_layers.append((canvas,ROLE_GROUP.get(l['role'])))
    if original.width!=original.height or data['canvas']['width']!=data['canvas']['height']:
        raise ValueError('This benchmark recipe requires square canvases; do not silently ignore padding')
    full_gt,visible_gt=maps(gt_layers,size)
    full_pred,visible_pred=maps(pred_layers,size)
    scores={g:dict(full_iou=iou(full_gt[g],full_pred[g]),
                   visible_iou=iou(visible_gt==i,visible_pred==i)) for i,g in enumerate(GROUPS)}
    foreground=visible_gt>=0
    return dict(scope='OGA Girl2 only; six independently reviewed coarse groups',
        mask_threshold=127,resampling='nearest to original 1000x1000; square no crop',
        caveat='Full source layers are authored drawing components, not complete hidden anatomical ground truth.',
        groups=scores,mean_visible_iou=float(np.mean([s['visible_iou'] for s in scores.values()])),
        mean_full_iou=float(np.mean([s['full_iou'] for s in scores.values()])),
        foreground_pixels=int(foreground.sum()),
        correct_visible_semantic_pixels=int((foreground&(visible_pred==visible_gt)).sum()),
        visible_semantic_accuracy=float((foreground&(visible_pred==visible_gt)).sum()/foreground.sum()),
        unknown_or_missing_foreground_pixels=int((foreground&(visible_pred<0)).sum()),
        background_false_positive_pixels=int(((~foreground)&(visible_pred>=0)).sum()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--truth',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Use a fresh report path')
    write_json(args.output,evaluate(args.project,args.truth))


if __name__=='__main__':main()
