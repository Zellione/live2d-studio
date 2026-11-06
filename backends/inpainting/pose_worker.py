"""Pinned offline multi-reference pose worker. No server, downloads or acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_HUB_DISABLE_IMPLICIT_TOKEN'):os.environ[key]='1'
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from PIL import Image
import torch
from qwen import Qwen
from worker import digest, LOCK
from live2d_studio.pose_guides import fit,layout


def dump(file,data):
    tmp=file.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(file)


def run(plan_file):
    plan=json.loads(plan_file.read_text());root=plan_file.parent
    for rel,h in plan['inputs'].items():
        file=(root/rel).resolve()
        if not file.is_relative_to(root.resolve()) or digest(file)!=h:raise ValueError('Input pin mismatch')
    if plan['model_lock_sha256']!=digest(Path(__file__).with_name('models.lock.json')):raise ValueError('Model lock changed')
    torch.cuda.set_device(0);torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.benchmark=False
    start=time.perf_counter();model=Qwen()
    from comfy_extras.nodes_model_advanced import ModelSamplingAuraFlow
    from comfy_extras.nodes_cfg import CFGNorm
    report={'status':'running','model_lock':LOCK,'gpu':torch.cuda.get_device_name(),'torch':torch.__version__,
            'load_seconds':time.perf_counter()-start,'plan_sha256':digest(plan_file),
            'worker_sha256':digest(__file__),'tasks':[]}
    dump(root/'report.json',report)
    try:
        with torch.inference_mode():
            for task in plan['tasks']:
                target=root/task['id']
                if not target.resolve().is_relative_to(root.resolve()) or target.exists():raise ValueError('Output must be new and confined')
                target.mkdir();cfg=task['config'];beg=time.perf_counter();torch.cuda.reset_peak_memory_stats()
                original=Image.open(root/plan['source']).convert('RGBA')
                rgb=np.asarray(fit(original,cfg['long_edge'])).copy()
                image=torch.from_numpy(rgb).float()[None]/255
                guide=None
                if cfg['guidance']!='none':
                    guide=torch.from_numpy(np.asarray(fit(Image.open(root/task['guide']),cfg['long_edge'])).copy()).float()[None]/255
                positive=model.encode(model.clip,task['prompt'],model.vae,image1=image,image2=guide)[0]
                negative=model.encode(model.clip,task.get('negative_prompt',''),model.vae,image1=image,image2=guide)[0]
                refs=positive[0][1].get('reference_latents',[])
                expected=1 if guide is None else 2
                if len(refs)!=expected:raise ValueError('Conditioning did not retain all image references')
                samples=model.vae.encode(image)
                latent={'samples':samples if cfg['latent']=='source' else torch.zeros_like(samples)}
                if cfg['mask']=='legacy-body':
                    m=torch.zeros((1,*rgb.shape[:2]));m[:,int(.24*rgb.shape[0]):int(.88*rgb.shape[0]),:]=1
                    latent['noise_mask']=m
                patched=ModelSamplingAuraFlow().patch_aura(model.model,cfg['shift'])[0]
                if cfg['cfg_norm']:patched=CFGNorm.execute(patched,1.0)[0]
                torch.manual_seed(task['seed'])
                result=model.sample(patched,task['seed'],cfg['steps'],cfg['cfg'],cfg['sampler'],cfg['scheduler'],
                                    positive,negative,latent,denoise=cfg['denoise'])[0]
                decoded=model.vae.decode(result['samples'])
                if decoded.ndim==5:decoded=decoded[:,0]
                array=(decoded[0].cpu().numpy()*255).round().clip(0,255).astype(np.uint8)
                Image.fromarray(array).save(target/'image.png')
                torch.cuda.synchronize()
                record={'id':task['id'],'seed':task['seed'],'config':cfg,'prompt':task['prompt'],
                    'negative_prompt':task.get('negative_prompt',''),'image_sha256':digest(target/'image.png'),
                    'guide_sha256':plan['inputs'].get(task.get('guide')),'reference_latent_count':len(refs),
                    'reference_latent_shapes':[list(v.shape) for v in refs],'output_size':list(Image.fromarray(array).size),
                    'seconds':time.perf_counter()-beg,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
                    'peak_reserved_bytes':torch.cuda.max_memory_reserved()}
                dump(target/'result.json',record);report['tasks'].append(record);dump(root/'report.json',report)
                print(task['id'],record['seconds'],flush=True)
                del positive,negative,latent,result,decoded,refs,samples,patched
        report['status']='completed'
    except Exception as exc:
        report.update(status='failed',error=str(exc));raise
    finally:
        report['total_seconds']=time.perf_counter()-start;dump(root/'report.json',report);model.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);a=p.parse_args();run(a.plan.resolve())
