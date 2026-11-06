"""Timed optional model-only Lightning on the unchanged pinned Qwen GGUF backend."""
import time
PROCESS_START=time.perf_counter()
import argparse
from contextlib import contextmanager
import json
import logging
import os
from pathlib import Path
import sys
for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_HUB_DISABLE_IMPLICIT_TOKEN'):os.environ[key]='1'
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from PIL import Image
import torch
from qwen import Qwen
from worker import digest,LOCK
from live2d_studio.pose_guides import fit
from live2d_studio.lightning import weight,register_weight,LOCK as LORA_LOCK
from live2d_studio.pose_review import validate_preset


def dump(file,data):
    tmp=file.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(file)


class StrictLora(logging.Handler):
    def emit(self,record):
        message=record.getMessage()
        if any(x in message for x in ('lora key not loaded','NOT LOADED','Calculate Weight Failed','SHAPE MISMATCH','WEIGHT NOT MERGED','patch type not recognized')):
            raise ValueError('Incompatible Lightning patch: '+message)


@contextmanager
def timed(timings,name):
    torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();start=time.perf_counter()
    try:yield
    finally:
        torch.cuda.synchronize()
        timings[name]={'seconds':time.perf_counter()-start,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
                       'peak_reserved_bytes':torch.cuda.max_memory_reserved()}


def apply_lora(model,config,loader):
    file,record=weight(config)
    if file is None:return model,record
    import folder_paths
    register_weight(folder_paths,file)
    patched=loader.load_lora_model_only(model,file.name,record['strength'])[0]
    keys=sorted(patched.patches)
    # Official pinned BF16 files have one alpha/up/down triplet for every patched weight.
    tensors=loader.loaded_lora[1];expected=sum(k.endswith('.lora_down.weight') for k in tensors)
    if expected==0 or len(keys)!=expected or any(k not in patched.patches for k in model.patches):
        raise ValueError('Lightning weights were not completely applied')
    if type(patched).__name__!='GGUFModelPatcher':raise ValueError('GGUF patcher was lost')
    record.update(loader='LoraLoaderModelOnly',patcher=type(patched).__name__,patch_count=len(keys),
                  tensor_count=len(tensors),patch_dtype='bfloat16',patch_on_device=patched.patch_on_device,
                  patch_keys_sha256=__import__('hashlib').sha256('\n'.join(keys).encode()).hexdigest())
    return patched,record


def run(plan_file):
    plan=json.loads(plan_file.read_text());root=plan_file.parent
    if len(plan['tasks'])>5:raise ValueError('At most five tasks per invocation')
    for rel,h in plan['inputs'].items():
        p=(root/rel).resolve()
        if not p.is_relative_to(root) or digest(p)!=h:raise ValueError('Input pin mismatch')
    if not plan.get('identity') or len(plan['inputs'])!=3:raise ValueError('Exactly three reference inputs required')
    if plan['model_lock_sha256']!=digest(Path(__file__).with_name('models.lock.json')):raise ValueError('Model lock changed')
    if plan['lightning_lock_sha256']!=digest(ROOT/LORA_LOCK):raise ValueError('Lightning lock changed')
    for task in plan['tasks']:
        validate_preset(task['config']);weight(task['config'])  # Fail before expensive model loading.
    torch.cuda.set_device(0);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.benchmark=False
    phases={};model=None;guard=StrictLora();logging.getLogger().addHandler(guard)
    report={'status':'running','plan_sha256':digest(plan_file),'worker_sha256':digest(__file__),
            'model_lock':LOCK,'lightning_lock_sha256':plan['lightning_lock_sha256'],
            'gpu':torch.cuda.get_device_name(),'torch':torch.__version__,'startup_seconds':time.perf_counter()-PROCESS_START,'tasks':[]}
    dump(root/'report.json',report)
    try:
        with timed(phases,'model_loading'):model=Qwen()
        from nodes import LoraLoaderModelOnly
        from comfy_extras.nodes_model_advanced import ModelSamplingAuraFlow
        from comfy_extras.nodes_cfg import CFGNorm
        loader=LoraLoaderModelOnly();report['model_loading']=phases['model_loading'];dump(root/'report.json',report)
        with torch.inference_mode():
            for task in plan['tasks']:
                target=(root/task['id']).resolve()
                if not target.is_relative_to(root) or target.exists():raise ValueError('Output must be new and confined')
                target.mkdir();cfg=task['config'];times={};beg=time.perf_counter()
                with timed(times,'input_preparation'):
                    def tensor(name):return torch.from_numpy(np.asarray(fit(Image.open(root/name),cfg['long_edge'])).copy()).float()[None]/255
                    image=tensor(plan['source']);guide=tensor(task['guide']);identity=tensor(plan['identity'])
                with timed(times,'reference_encoding'):
                    positive=model.encode(model.clip,task['prompt'],model.vae,image1=image,image2=guide,image3=identity)[0]
                    negative=model.encode(model.clip,task.get('negative_prompt',''),model.vae,image1=image,image2=guide,image3=identity)[0]
                    refs=positive[0][1].get('reference_latents',[])
                    if len(refs)!=3 or len(negative[0][1].get('reference_latents',[]))!=3:raise ValueError('Three-image conditioning was lost')
                with timed(times,'latent_initialization'):
                    samples=model.vae.encode(image);latent={'samples':samples if cfg['latent']=='source' else torch.zeros_like(samples)}
                    if cfg['mask']=='legacy-body':
                        m=torch.zeros((1,*image.shape[1:3]));m[:,int(.24*image.shape[1]):int(.88*image.shape[1]),:]=1;latent['noise_mask']=m
                with timed(times,'lora_loading'):
                    patched,lora=apply_lora(model.model,cfg,loader)
                    patched=ModelSamplingAuraFlow().patch_aura(patched,cfg['shift'])[0]
                    if cfg['cfg_norm']:patched=CFGNorm.execute(patched,1.0)[0]
                with timed(times,'sampling'):
                    torch.manual_seed(task['seed'])
                    result=model.sample(patched,task['seed'],cfg['steps'],cfg['cfg'],cfg['sampler'],cfg['scheduler'],positive,negative,latent,denoise=cfg['denoise'])[0]
                with timed(times,'decoding'):
                    decoded=model.vae.decode(result['samples'])
                    if decoded.ndim==5:decoded=decoded[:,0]
                with timed(times,'image_save'):
                    array=(decoded[0].cpu().numpy()*255).round().clip(0,255).astype(np.uint8);Image.fromarray(array).save(target/'image.png')
                record={'id':task['id'],'seed':task['seed'],'config':cfg,'prompt':task['prompt'],'negative_prompt':task.get('negative_prompt',''),
                    'image_sha256':digest(target/'image.png'),'source_sha256':plan['inputs'][plan['source']],
                    'guide_sha256':plan['inputs'][task['guide']],'identity_sha256':plan['inputs'][plan['identity']],
                    'reference_latent_count':3,'reference_latent_shapes':[list(v.shape) for v in refs],
                    'reference_roles':['canonical geometry','target guide','original identity/style'],
                    'output_size':list(Image.fromarray(array).size),'seconds':time.perf_counter()-beg,'timings':times,'lora':lora,
                    'lightning_lock_sha256':plan['lightning_lock_sha256'],
                    'peak_allocated_bytes':max(v['peak_allocated_bytes'] for v in times.values()),
                    'peak_reserved_bytes':max(v['peak_reserved_bytes'] for v in times.values())}
                dump(target/'result.json',record);report['tasks'].append(record);dump(root/'report.json',report)
                print(task['id'],record['seconds'],lora['id'],flush=True)
                del positive,negative,latent,result,decoded,refs,samples,patched
        report['status']='completed'
    except Exception as exc:
        report.update(status='failed',error=str(exc));raise
    finally:
        if model is not None:
            with timed(phases,'model_unloading'):model.close()
        report['phases']=phases;report['total_seconds']=time.perf_counter()-PROCESS_START
        dump(root/'report.json',report);logging.getLogger().removeHandler(guard)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);a=p.parse_args();run(a.plan.resolve())
