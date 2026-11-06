"""Explicit one-case conditioning control; never a reviewer selection or fallback."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
from live2d_studio.pose_review import Store,REPO,digest,write

IDENTITY_INSTRUCTION=('Picture 3 is the original character for identity, facial features, clothing and style only; '
                      'do not restore its angled or crossed-arm pose. ')


def prepare(run,batch_id,output,mode):
    if mode not in ('two-references','skeleton'):raise ValueError('Unknown control')
    store=Store(run);state=store.state();store.verify_pins(state)
    batch=next(b for b in state['batches'] if b['id']==batch_id)
    original=store.safe(batch['directory']+'/plan.json')
    if digest(original)!=batch['plan_sha256']:raise ValueError('Original plan changed')
    plan=json.loads(original.read_text())
    if not plan.get('identity'):raise ValueError('Control requires a three-reference parent')
    plan=copy.deepcopy(plan);plan['tasks']=plan['tasks'][:1]
    output=output.resolve()
    if not output.is_relative_to(REPO/'runs') or output.is_relative_to(REPO/'runs/references'):raise ValueError('Control must use a fresh ignored runs directory')
    output.mkdir(parents=True,exist_ok=False)
    for name,h in plan['inputs'].items():
        source=store.safe(batch['directory']+'/'+name)
        if digest(source)!=h:raise ValueError('Parent input changed')
        shutil.copyfile(source,output/name)
    if mode=='two-references':
        del plan['inputs'][plan.pop('identity')]
        for task in plan['tasks']:
            if IDENTITY_INSTRUCTION not in task['prompt']:raise ValueError('Missing identity instruction')
            task['prompt']=task['prompt'].replace(IDENTITY_INSTRUCTION,'',1)
    else:
        guide=state['poses'][batch['pose']]['guides']['skeleton']
        if digest(store.safe(guide['path']))!=guide['sha256']:raise ValueError('Guide changed')
        shutil.copyfile(store.safe(guide['path']),output/'guide.png');plan['inputs']['guide.png']=guide['sha256']
        plan['tasks'][0]['config']['guidance']='skeleton'
    write(output/'plan.json',plan)
    write(output/'control.json',{'mode':mode,'parent_batch':batch_id,'parent_plan_sha256':batch['plan_sha256'],
          'control_plan_sha256':digest(output/'plan.json'),'producer_pins':state['producer_pins'],
          'seed':plan['tasks'][0]['seed'],'scope':'Single seeded diagnosis, not a five-candidate review batch; never selected automatically',
          'change':'Remove image3 conditioning and its textual instruction; numeric settings/source/guide/seed unchanged' if mode=='two-references' else 'Replace silhouette guide with skeleton; numeric settings/source/identity/seed/text unchanged'})
    return output/'plan.json'


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--batch',required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',choices=['two-references','skeleton'],required=True)
    p.add_argument('--execute',action='store_true');a=p.parse_args()
    store=Store(a.run);fd=store.gpu_lock() if a.execute else None
    try:
        plan=prepare(a.run,a.batch,a.output,a.mode)
        if a.execute:
            with (plan.parent/'worker.log').open('x') as log:
                subprocess.run([str(REPO/'backends/inpainting/qwen-env/.venv/bin/python'),
                                str(REPO/'backends/inpainting/pose_reference_worker.py'),'--plan',str(plan)],
                               cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900,pass_fds=(fd,))
    finally:
        if fd is not None:os.close(fd)

if __name__=='__main__':main()
