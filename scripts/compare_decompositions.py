"""Compare candidate coverage and composites at unchanged source resolution."""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
from live2d_studio.manifest import load_validate,write_json


def measure(project):
    data=load_validate(project)
    source=ImageOps.exif_transpose(Image.open(project/data['sources'][0]['path'])).convert('RGBA')
    original=np.array(source)
    if source.width!=source.height or data['canvas']['width']!=data['canvas']['height']:
        raise ValueError('Comparison currently supports square benchmark images only')
    candidate=Image.new('L',(data['canvas']['width'],data['canvas']['height']))
    combined=np.zeros((candidate.height,candidate.width),np.uint8)
    for layer in data['layers']:
        if not layer['default_visible']:continue
        alpha=np.array(Image.open(project/layer['rgba_path']))[...,3]
        x,y,w,h=(layer[k] for k in ['x','y','width','height'])
        patch=combined[y:y+h,x:x+w]
        patch[alpha>127]=0 if layer['role']=='unknown' else 255
    mask=np.array(Image.fromarray(combined).resize(source.size,Image.Resampling.NEAREST))>127
    comp=Image.open(project/'preview/composite.png').convert('RGBA').resize(source.size,Image.Resampling.LANCZOS)
    result=np.array(comp)
    foreground=original[...,3]>127
    # Changes include resizing effects. This is not a hidden-pixel quality score.
    changed=np.any(result!=original,axis=2)&foreground
    return dict(original_resolution=list(source.size),alpha_threshold=127,foreground_pixels=int(foreground.sum()),
        candidate_covered_pixels=int((mask&foreground).sum()),
        candidate_coverage_fraction=float((mask&foreground).sum()/foreground.sum()),
        correct_semantic_fraction=None,composite_changed_foreground_pixels=int(changed.sum()),
        composite_rgb_mae=float(np.abs(result[...,:3].astype(float)-original[...,:3])[foreground].mean()),
        note='Candidate support is not correct parsing. Composite comparison includes resampling and generated RGB.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--neural',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Use a fresh report')
    if load_validate(args.baseline)['sources'][0]['sha256']!=load_validate(args.neural)['sources'][0]['sha256']:
        raise ValueError('Backends must be compared on the same original input')
    write_json(args.output,dict(baseline=measure(args.baseline),neural=measure(args.neural)))
