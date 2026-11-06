"""Opt-in Lightning pins and configuration; no Torch import or implicit download."""
import json
import math
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]
WORKER='backends/inpainting/pose_lightning_worker.py'
LOCK='backends/inpainting/lightning.lock.json'
PROFILE='qwen-lightning-v1'


def validate(config):
    name=config.get('lora','none');strength=config.get('lora_strength',0 if name=='none' else 1)
    if name not in ('none','lightning-4','lightning-8'):raise ValueError('Unknown pinned Lightning adapter')
    if type(strength) not in (int,float) or not math.isfinite(strength) or (strength!=0 if name=='none' else strength!=1):
        raise ValueError('Use strength 0 without LoRA or strength 1 with pinned Lightning')
    return name,strength


def weight(config):
    from .pose_review import digest
    name,strength=validate(config)
    if name=='none':return None,{'id':name,'strength':strength,'patch_count':0}
    lock=json.loads((REPO/LOCK).read_text());row=lock['files'][name];file=REPO/row['path']
    if not file.is_file() or file.stat().st_size!=row['size'] or digest(file)!=row['sha256']:
        raise ValueError('Missing or hash-mismatched Lightning weights: '+name)
    return file,dict(row,id=name,strength=strength,repo=lock['repo'],revision=lock['revision'],license=lock['license'])


def register_weight(folder_paths,file):
    """Comfy resolves loader names through a search path; reject name shadowing."""
    folder_paths.add_model_folder_path('loras',str(file.parent))
    resolved=folder_paths.get_full_path('loras',file.name)
    if resolved is None or Path(resolved).resolve()!=file.resolve():
        raise ValueError('Comfy LoRA filename does not resolve to the pinned file')


def enable(store):
    from .pose_review import digest
    with store.transaction() as state:
        if state['batches'] or state.get('workflow')!='canonical-helpers':raise ValueError('Lightning requires a fresh canonical helper run')
        state['inference_profile']=PROFILE;state['worker']=WORKER
        for name in (WORKER,LOCK,'src/live2d_studio/lightning.py'):
            state['producer_pins'][name]=digest(REPO/name)
