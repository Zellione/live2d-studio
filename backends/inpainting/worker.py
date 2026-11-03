"""Offline batch inpainting. Only raster crops, masks and prompts enter inference."""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import time

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parents[2]
LOCK = json.loads(Path(__file__).with_name('models.lock.json').read_text())


def digest(file):
    with open(file, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def weight(group, name, file):
    entry = LOCK['used'][group]['files'][name]
    if file.stat().st_size != entry['size'] or digest(file) != entry['sha256']:
        raise ValueError('Model weight does not match reviewed pin: ' + str(file))
    return file


class Lama:
    def __init__(self):
        from lama import FFCResNetGenerator
        from safetensors.torch import load_file
        file = weight('lama', 'lama-manga.safetensors', ROOT/'models/phase4b2/lama-manga/lama-manga.safetensors')
        self.model = FFCResNetGenerator(4, 3, n_blocks=18, add_out_act='sigmoid',
            init_conv_kwargs=dict(ratio_gin=0, ratio_gout=0, enable_lfu=False),
            downsample_conv_kwargs=dict(ratio_gin=0, ratio_gout=0, enable_lfu=False),
            resnet_conv_kwargs=dict(ratio_gin=.75, ratio_gout=.75, enable_lfu=False))
        self.model.load_state_dict(load_file(file), strict=True)
        self.model.eval().requires_grad_(False).to('cuda')

    def __call__(self, rgb, mask, task):
        scale = task.get('scale', 1)
        im = Image.fromarray(rgb).resize((rgb.shape[1]*scale, rgb.shape[0]*scale), Image.Resampling.LANCZOS)
        ma = Image.fromarray(mask.astype(np.uint8)*255).resize(im.size, Image.Resampling.NEAREST)
        a = np.asarray(im).astype(np.float32)/255
        m = (np.asarray(ma)>0).astype(np.float32)
        h,w = m.shape
        a = np.pad(a, ((0,(-h)%8),(0,(-w)%8),(0,0)), mode='reflect')
        m = np.pad(m, ((0,(-h)%8),(0,(-w)%8)), mode='reflect')
        x = torch.from_numpy(a).permute(2,0,1)[None].cuda()
        y = torch.from_numpy(m)[None,None].cuda()
        prediction = self.model(torch.cat((x*(1-y),y), dim=1))[0,:,:h,:w]
        raw = (prediction.permute(1,2,0).cpu().numpy()*255).round().clip(0,255).astype(np.uint8)
        return np.array(Image.fromarray(raw).resize((rgb.shape[1],rgb.shape[0]), Image.Resampling.LANCZOS))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tasks', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model', choices=['lama','qwen'], required=True)
    args = parser.parse_args()
    tasks = json.loads(args.tasks.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    torch.manual_seed(1729)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.cuda.set_device(0)
    if torch.cuda.get_device_capability() != (12,0):
        raise RuntimeError('This experiment is pinned to the reviewed Blackwell GPU')
    torch.cuda.reset_peak_memory_stats()
    start = time.perf_counter()
    if args.model == 'lama':
        model = Lama()
    else:
        from qwen import Qwen
        model = Qwen()
    report = dict(model=args.model, model_lock_sha256=digest(Path(__file__).with_name('models.lock.json')),
        code_sha256={name:digest(Path(__file__).with_name(name)) for name in ('worker.py','lama.py','qwen.py')},
        gpu=torch.cuda.get_device_name(), torch=torch.__version__, cuda=torch.version.cuda,
        parameters=dict(lama='FP32; pad-to-8; no prompt/steps/CFG conditioning',
            qwen='Q4_K_S transformer + FP8 encoder; BF16 dequantization; Euler/simple; shift 3; 512px long edge; latent noise mask'),
        load_seconds=time.perf_counter()-start, tasks=[], anatomical_truth=False)
    try:
        with torch.inference_mode():
            for task in tasks:
                name = task['id']
                if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in name):
                    raise ValueError('Unsafe task ID')
                target = args.output/name
                target.mkdir()
                image_file,mask_file = (args.tasks.parent/task[k] for k in ('image','mask'))
                rgba = np.array(Image.open(image_file).convert('RGBA'))
                mask = np.array(Image.open(mask_file).convert('L'))>0
                if mask.shape != rgba.shape[:2] or not mask.any():
                    raise ValueError('Empty or mismatched inpainting mask')
                if not 1 <= task.get('scale',1) <= 4 or max(mask.shape)*task.get('scale',1)>2048:
                    raise ValueError('Unbounded crop/scale')
                torch.manual_seed(task.get('seed',1729))
                torch.cuda.synchronize()
                started = time.perf_counter()
                raw = model(rgba[...,:3],mask,task)
                torch.cuda.synchronize()
                elapsed = time.perf_counter()-started
                if raw.shape != rgba[...,:3].shape or raw.dtype != np.uint8:
                    raise ValueError('Invalid neural image')
                result = rgba.copy()
                result[mask,:3] = raw[mask]
                # Hard compositing is independent of the model or its latent mask behavior.
                Image.fromarray(raw).save(target/'raw.png')
                Image.fromarray(result).save(target/'composite.png')
                Image.fromarray(mask.astype(np.uint8)*255).save(target/'generated.png')
                record = dict(task=task, image_sha256=digest(image_file), mask_sha256=digest(mask_file),
                    raw_sha256=digest(target/'raw.png'), composite_sha256=digest(target/'composite.png'),
                    seconds=elapsed, generated_pixels=int(mask.sum()),
                    outside_mask_changed=int(np.any(result[~mask]!=rgba[~mask],axis=-1).sum()),
                    alpha_changed=int((result[...,3]!=rgba[...,3]).sum()),
                    max_allocated_bytes=torch.cuda.max_memory_allocated(),
                    max_reserved_bytes=torch.cuda.max_memory_reserved())
                report['tasks'].append(record)
                (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
                print(name,round(elapsed,3),flush=True)
    finally:
        if hasattr(model,'close'):
            model.close()
        del model
        gc.collect()
        torch.cuda.empty_cache()
    report.update(total_seconds=time.perf_counter()-start, unloaded=True,
        remaining_allocated_bytes=torch.cuda.memory_allocated())
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
