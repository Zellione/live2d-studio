"""Matched Lightning comparisons in fresh subprocesses; no reviewer mutations."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from live2d_studio.pose_review import Store,REPO,digest,write
from live2d_studio.lightning import WORKER,LOCK

CASES={'quality':(40,4,'none',0),'lightning8':(8,1,'lightning-8',1),'lightning4':(4,1,'lightning-4',1),
       'control8':(8,1,'none',0),'control4':(4,1,'none',0)}


def prepare(run,batch_id,output,cases=tuple(CASES)):
    store=Store(run);state=store.state();store.verify_pins(state)
    batch=next(b for b in state['batches'] if b['id']==batch_id)
    planfile=store.safe(batch['directory']+'/plan.json')
    if digest(planfile)!=batch['plan_sha256']:raise ValueError('Parent plan changed')
    original=json.loads(planfile.read_text())
    if not original.get('identity'):raise ValueError('Three reference parent required')
    output=output.resolve()
    if not output.is_relative_to(REPO/'runs') or output.is_relative_to(REPO/'runs/references'):raise ValueError('Fresh ignored output required')
    output.mkdir(parents=True,exist_ok=False);plans=[]
    for case in cases:
        steps,cfg,lora,strength=CASES[case];folder=output/case;folder.mkdir();plan=copy.deepcopy(original)
        for name,h in plan['inputs'].items():
            source=store.safe(batch['directory']+'/'+name)
            if digest(source)!=h:raise ValueError('Input changed')
            shutil.copyfile(source,folder/name)
        plan['tasks']=plan['tasks'][:1];plan['tasks'][0]['config'].update(steps=steps,cfg=cfg,lora=lora,lora_strength=strength)
        plan['lightning_lock_sha256']=digest(REPO/LOCK);write(folder/'plan.json',plan);plans.append(folder/'plan.json')
    write(output/'comparison.json',{'parent_batch':batch_id,'parent_plan_sha256':batch['plan_sha256'],'cases':list(cases),
          'seed':original['tasks'][0]['seed'],'inputs':original['inputs'],'prompt':original['tasks'][0]['prompt'],
          'worker_sha256':digest(REPO/WORKER),'producer_pins':state['producer_pins'],
          'lightning_lock_sha256':digest(REPO/LOCK),'scope':'Single-seed performance/quality comparison and matched no-LoRA effect controls; no human approval'})
    return plans


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--batch',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cases',nargs='+',choices=list(CASES),default=list(CASES));p.add_argument('--execute',action='store_true');a=p.parse_args()
    store=Store(a.run);fd=store.gpu_lock() if a.execute else None
    try:
        plans=prepare(a.run,a.batch,a.output,a.cases)
        if a.execute:
            for plan in plans:
                start=time.perf_counter()
                with (plan.parent/'worker.log').open('x') as log:
                    result=subprocess.run([str(REPO/'backends/inpainting/qwen-env/.venv/bin/python'),str(REPO/WORKER),'--plan',str(plan)],
                                          cwd=REPO,stdout=log,stderr=subprocess.STDOUT,timeout=1200,pass_fds=(fd,))
                write(plan.parent/'process.json',{'returncode':result.returncode,'wall_seconds':time.perf_counter()-start})
                if result.returncode:raise RuntimeError('Comparison case failed: '+plan.parent.name)
                print(plan.parent.name,'completed',flush=True)
    finally:
        if fd is not None:os.close(fd)

if __name__=='__main__':main()
