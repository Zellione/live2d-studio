"""Review independent SAM predictions; overlapping masks stay explicit."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from live2d_studio.manifest import write_json
from evaluate_oga import GROUPS, GT_GROUP, maps, iou

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--sam',type=Path,required=True)
p.add_argument('--input',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--truth',type=Path)
args=p.parse_args()
args.output.mkdir(parents=True,exist_ok=False)
source=Image.open(args.input).convert('RGBA')
rgba=np.array(source)
tags=json.loads((args.sam/'sam.json').read_text())['tags']
masks={t:np.array(Image.open(args.sam/(t+'.png')))>0 for t in tags}
count=np.sum(list(masks.values()),axis=0)
foreground=rgba[...,3]>127
overlay=np.zeros_like(rgba)
present=[t for t,m in masks.items() if m.any()]
sheet=Image.new('RGBA',(800,200*((len(present)+3)//4)), 'white')
for i,tag in enumerate(present):
    mask=masks[tag]
    overlay[mask]=((i*73+41)%256,(i*113+97)%256,(i*157+53)%256,200)
    cut=rgba.copy();cut[~mask]=0
    tile=Image.new('RGBA',(200,200),(235,235,235,255))
    thumb=Image.fromarray(cut);thumb.thumbnail((180,165))
    tile.alpha_composite(thumb,((200-thumb.width)//2,25))
    ImageDraw.Draw(tile).text((5,5),tag,fill='black')
    sheet.alpha_composite(tile,((i%4)*200,(i//4)*200))
sheet.save(args.output/'layers.png')
Image.alpha_composite(source,Image.fromarray(overlay)).save(args.output/'overlay.png')
metrics=dict(parts=present,foreground_pixels=int(foreground.sum()),
    candidate_coverage_fraction=float(((count>0)&foreground).sum()/foreground.sum()),
    overlapping_pixels=int((count>1).sum()),unknown_foreground_pixels=int(((count==0)&foreground).sum()),
    warning='SAM predictions are not independent ground truth and supply no hidden-pixel inpainting.')
if args.truth:
    truth=json.loads((args.truth/'benchmark.json').read_text())
    _,gt=maps([(Image.open(args.truth/l['path']).convert('RGBA'),GT_GROUP[l['name']]) for l in truth['layers']],source.size)
    groups={'hair_accessories':['hair','headwear'],'face_ears_nose':['face','ears','nose'],
            'eyes_brows':['eyes'],'mouth':['mouth'],'neck':['neck'],'clothing':['topwear','handwear']}
    scores={g:iou(gt==GROUPS.index(g),np.any([masks[t] for t in ts],axis=0)) for g,ts in groups.items()}
    metrics['coarse_visible_iou']=scores
    metrics['mean_coarse_visible_iou']=float(np.mean(list(scores.values())))
    metrics['metric_note']='Each overlapping predicted class mask independently scored against visible XCF group; not exclusive-label accuracy.'
write_json(args.output/'metrics.json',metrics)
print(json.dumps(metrics,indent=2))
