"""Deterministic original geometric face; standard library only, no AI assets."""
import argparse
import json
import struct
import zlib
from pathlib import Path

def png(w, h, rgba):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    rows = b''.join(b'\0' + rgba[y*w*4:(y+1)*w*4] for y in range(h))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w,h,8,6,0,0,0)) + chunk(b'IDAT', zlib.compress(rows,9)) + chunk(b'IEND',b'')

def create(dest):
    dest.mkdir(parents=True, exist_ok=False)
    layers=[]
    def ellipse(name, role, side, x, y, w, h, color):
        pixels=bytearray()
        for j in range(h):
            for i in range(w):
                inside=((i+.5-w/2)/(w/2))**2+((j+.5-h/2)/(h/2))**2<=1
                pixels.extend((*color,255) if inside else (0,0,0,0))
        (dest/(name+'.png')).write_bytes(png(w,h,pixels))
        layers.append(dict(path=str((dest/(name+'.png')).resolve()),name=name,role=role,side=side,x=x,y=y))
    ellipse('neck','neck','none',110,185,36,52,(220,161,116))
    ellipse('shirt','topwear','none',63,220,130,70,(40,150,180))
    ellipse('face','face','none',48,28,160,180,(247,202,155))
    for side,x in [('left',77),('right',144)]:
        ellipse('white_'+side,'eyewhite',side,x,99,36,25,(255,255,255))
        ellipse('iris_'+side,'irides',side,x+10,102,16,20,(30,65,110))
        ellipse('lid_'+side,'eyelash',side,x-1,96,38,6,(62,36,32))
        ellipse('closed_'+side,'eye_close',side,x-1,111,38,5,(62,36,32))
        ellipse('brow_'+side,'eyebrow',side,x-1,81,38,7,(80,45,30))
    ellipse('nose','nose','none',124,128,8,16,(210,137,101))
    ellipse('mouth_inside','mouth_open','none',109,158,38,24,(110,27,48))
    ellipse('mouth_line','mouth_close','none',109,168,38,4,(110,27,48))
    request=dict(width=256,height=300,layers=layers)
    (dest/'artwork.json').write_text(json.dumps(request,indent=2)+'\n')
    return request

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    print(json.dumps(create(parser.parse_args().destination),indent=2))
