"""Reproduce documented licensed portrait crops; never used by inference."""
import argparse
import json
from pathlib import Path
import shutil
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from live2d_studio.manifest import digest,write_json


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kind',choices=['sara','hachi'],required=True)
    p.add_argument('--source',type=Path,required=True,help='Sara portrait21.png sheet or Hachi front.png')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    record=json.loads((Path(__file__).resolve().parents[1]/'benchmarks/phase4b-art.json').read_text())[a.kind]
    source_hash=record['source_sha256'] if a.kind=='sara' else record['files']['front.png']
    if digest(a.source)!=source_hash:raise ValueError('Source differs from reviewed licensed artwork')
    transform=record['transform'] if a.kind=='sara' else record['portrait_transform']
    im=Image.open(a.source).convert('RGBA').crop(transform['crop'])
    pixels=np.array(im)
    if a.kind=='sara':
        labels,_=ndi.label((pixels[...,:3]==255).all(axis=2))
        border=np.unique(np.concatenate([labels[0],labels[-1],labels[:,0],labels[:,-1]]))
        pixels[np.isin(labels,border[border>0]),3]=0
    out=Image.new('RGBA',tuple(transform['canvas']))
    out.paste(Image.fromarray(pixels),tuple(transform['paste']))
    a.output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(a.source,a.output/'source-original.png')
    out.save(a.output/'portrait.png')
    expected=record['input_sha256'] if a.kind=='sara' else transform['output_sha256']
    if digest(a.output/'portrait.png')!=expected:raise ValueError('Crop does not reproduce the reviewed input')
    write_json(a.output/'provenance.json',record)
    print(a.output/'portrait.png')


if __name__=='__main__':main()
