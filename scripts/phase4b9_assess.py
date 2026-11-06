"""Freeze approved pose evidence and run the existing offline SAM parser."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from live2d_studio.pose_family import freeze,load
from live2d_studio.pose_review import Store,REPO,digest,write


def infer(family,output,runner=subprocess.run):
    family=family.resolve();data=load(family);output=output.resolve()
    if not output.is_relative_to(REPO/'runs') or output.is_relative_to(REPO/'runs/references'):raise ValueError('Fresh ignored output required')
    store=Store(REPO/data['review_run']);fd=store.gpu_lock()
    try:
        output.mkdir(parents=True,exist_ok=False)
        for pose,row in data['images'].items():
            file=family/row['path']
            if digest(file)!=row['sha256']:raise ValueError('Frozen image changed')
            with (output/(pose+'.log')).open('x') as log:
                runner([str(REPO/'backends/see-through/.venv/bin/python'),str(REPO/'backends/see-through/worker.py'),
                    '--input',str(file),'--output',str(output/pose),'--sam'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600,pass_fds=(fd,))
            print(pose,'parsed',flush=True)
        write(output/'inference.json',{'family_sha256':digest(family/'family.json'),'parser_worker_sha256':digest(REPO/'backends/see-through/worker.py'),
            'parser_lock_sha256':digest(REPO/'backends/see-through/models.lock.json'),'images':{k:v['sha256'] for k,v in data['images'].items()},'only_human_approved':True})
    finally:os.close(fd)


if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('freeze');a.add_argument('--run',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--export-if-missing',action='store_true')
    a=sub.add_parser('infer');a.add_argument('--family',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='freeze':freeze(a.run,a.output,export_if_missing=a.export_if_missing)
    else:infer(a.family,a.output)
