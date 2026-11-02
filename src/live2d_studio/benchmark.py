"""Fixture metadata is confined to benchmark generation/evaluation, never inference."""
from pathlib import Path
import json
import numpy as np
from PIL import Image

from .manifest import load_validate, write_json


def flatten(art, output):
    art, output = Path(art), Path(output)
    data = json.loads((art/'artwork.json').read_text())
    output.mkdir(parents=True,exist_ok=False)
    (output/'ground_truth').mkdir()
    canvas = Image.new('RGBA',(data['width'],data['height']))
    truth = []
    for layer in data['layers']:
        if layer['role'] in {'eye_close','mouth_close'}:
            continue  # Mutually exclusive alternate poses are not simultaneously visible.
        image = Image.open(art/Path(layer['path']).name).convert('RGBA')
        placed = Image.new('RGBA',canvas.size)
        placed.alpha_composite(image,(layer['x'],layer['y']))
        canvas = Image.alpha_composite(canvas,placed)
        ident = layer['role'] + ('' if layer['side']=='none' else '_'+layer['side'])
        name = 'ground_truth/'+ident+'.png'
        placed.getchannel('A').save(output/name)
        truth.append(dict(id=ident,path=name))
    canvas.save(output/'flat.png')
    # Visible ground truth subtracts all later opaque masks; full masks retained.
    covered = np.zeros((canvas.height,canvas.width),bool)
    for entry in reversed(truth):
        mask = np.array(Image.open(output/entry['path']))
        visible = np.where(covered,0,mask).astype(np.uint8)
        covered |= mask>0
        entry['visible_path'] = entry['path'].replace('.png','-visible.png')
        Image.fromarray(visible).save(output/entry['visible_path'])
    write_json(output/'ground_truth.json',dict(layers=truth,rights='Original repository geometric artwork'))
    return output/'flat.png'


def evaluate(project, truth_dir):
    project, truth_dir = Path(project), Path(truth_dir)
    data = load_validate(project)
    truth = json.loads((truth_dir/'ground_truth.json').read_text())
    layers = {l['id']:l for l in data['layers']}
    scores = {}
    for entry in truth['layers']:
        gt = np.array(Image.open(truth_dir/entry['path']))>0
        visible_gt = np.array(Image.open(truth_dir/entry['visible_path']))>0
        pred, visible = np.zeros_like(gt),np.zeros_like(gt)
        if entry['id'] in layers:
            l=layers[entry['id']]
            x,y,w,h=(l[k] for k in ('x','y','width','height'))
            pred[y:y+h,x:x+w] = np.array(Image.open(project/l['rgba_path']))[...,3]>0
            visible[y:y+h,x:x+w] = np.array(Image.open(project/l['mask_path']))>0
        def iou(a,b):
            union = int((a|b).sum())
            return float((a&b).sum()/union) if union else 1.0
        scores[entry['id']] = dict(full_iou=iou(gt,pred),visible_iou=iou(visible_gt,visible))
    return dict(scope='synthetic-only',layers=scores,
                mean_full_iou=float(np.mean([s['full_iou'] for s in scores.values()])),
                mean_visible_iou=float(np.mean([s['visible_iou'] for s in scores.values()])))
