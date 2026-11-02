"""Assemble exported CC0 Girl2 layers; ground truth never enters inference."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    info=json.loads((args.raw/'extraction.json').read_text())
    args.output.mkdir(parents=True,exist_ok=False)
    size=info['width'],info['height']

    def read(item):
        img=Image.frombytes('RGBA',(item['width'],item['height']),(args.raw/item['path']).read_bytes())
        # Paste, not alpha_composite: retain straight alpha even at partial edges.
        full=Image.new('RGBA',size)
        full.paste(img,(item['x'],item['y']))
        return full

    composite=Image.new('RGBA',size)
    records=[]
    images=[]
    for i,item in enumerate(reversed(info['layers'])):
        if item['opacity']!=100 or item['mode']!=0:
            raise ValueError('Non-normal XCF blending requires independent extraction')
        image=read(item)
        file=f'layer-{i:02d}.png'
        image.save(args.output/file)
        images.append(image)
        composite.alpha_composite(image)
        records.append(dict(name=item['name'],path=file,z_order=i))
    composite.save(args.output/'flat.png')
    projection=read(info['projection'])
    projection.save(args.output/'gimp-projection.png')
    a,b=np.array(composite).astype(int),np.array(projection).astype(int)
    metrics=dict(gimp_version=info['gimp_version'],projection_changed_pixels=int(np.any(a!=b,axis=2).sum()),
        projection_max_channel_error=int(np.abs(a-b).max()),projection_mean_channel_error=float(np.abs(a-b).mean()))
    sheet=Image.new('RGBA',(1000,250*((len(images)+3)//4)),'white')
    for i,(img,item) in enumerate(zip(images,records)):
        tile=Image.new('RGBA',(250,250),(235,235,235,255))
        img.thumbnail((225,215))
        tile.alpha_composite(img,((250-img.width)//2,30))
        ImageDraw.Draw(tile).text((5,5),item['name'],fill='black')
        sheet.alpha_composite(tile,((i%4)*250,(i//4)*250))
    sheet.save(args.output/'layers.png')
    (args.output/'benchmark.json').write_text(json.dumps(dict(canvas=info['width'],layers=records,metrics=metrics,
        rights='stevenburrow; CC0; https://opengameart.org/content/anime-girl-and-boy-portraits',
        source='NewAnime.xcf / Girl2; default visible child variants; no metadata provided to inference'),indent=2)+'\n')
    print(json.dumps(metrics,indent=2))


if __name__=='__main__':main()
