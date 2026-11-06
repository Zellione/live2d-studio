"""Offline, opt-in auxiliary pose study. No creation, rig or deployment integration."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def digest(file):
    with Path(file).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def dump(file, value):
    Path(file).write_text(json.dumps(value, indent=2) + '\n')


def new_run(folder):
    folder = folder.resolve()
    if (not folder.is_relative_to(ROOT / 'runs') or folder == ROOT / 'runs'
            or folder.is_relative_to(ROOT / 'runs/references')):
        raise ValueError('Study outputs must use a fresh project runs/ directory')
    folder.mkdir(parents=True, exist_ok=False)
    return folder


def body_mask(alpha, config):
    """Broad editable envelope from raster alpha, never semantic GT or Codel coordinates."""
    ys, xs = np.where(alpha > 0)
    if not len(xs):
        raise ValueError('Empty source alpha')
    top, bottom, margin = (config[k] for k in
                          ('top_fraction', 'bottom_fraction', 'horizontal_margin_fraction'))
    if not 0 <= top < bottom <= 1 or not 0 <= margin <= 1:
        raise ValueError('Invalid normalized body envelope')
    height, width = alpha.shape
    span_y, span_x = ys.max() - ys.min() + 1, xs.max() - xs.min() + 1
    mask = np.zeros((height, width), dtype=bool)
    mask[int(ys.min()+top*span_y):int(ys.min()+bottom*span_y),
         max(0, int(xs.min()-margin*span_x)):min(width, int(xs.max()+1+margin*span_x))] = True
    return mask


def prepare(source, config_file, output, denoise=None, poses=None):
    config = json.loads(config_file.read_text())
    if denoise is not None:
        if not 0 < denoise <= 1:
            raise ValueError('Denoising strength must be in (0, 1]')
        config['denoise'] = denoise
    if poses:
        if set(poses) - {row['id'] for row in config['poses']}:
            raise ValueError('Unknown pose subset')
        config['poses'] = [row for row in config['poses'] if row['id'] in poses]
    if digest(source) != config['source_sha256']:
        raise ValueError('Source does not match explicit study pin')
    rgba = Image.open(source).convert('RGBA')
    factor = config['long_edge'] / max(rgba.size)
    size = tuple(max(64, round(n*factor/16)*16) for n in rgba.size)
    alpha = np.asarray(rgba.getchannel('A').resize(size, Image.Resampling.LANCZOS))
    rgb = Image.alpha_composite(Image.new('RGBA', rgba.size, 'white'), rgba).convert('RGB')
    rgb = rgb.resize(size, Image.Resampling.LANCZOS)
    mask = body_mask(alpha, config['body_mask'])
    output = new_run(output)
    shutil.copyfile(source, output/'original.png')
    rgb.save(output/'input.png')
    Image.fromarray(alpha).save(output/'source-alpha.png')
    Image.fromarray(mask.astype(np.uint8)*255).save(output/'edit-mask.png')
    tasks = []
    for pose in config['poses']:
        tasks.append(dict(id=pose['id'], prompt=pose['instruction']+' '+config['constraints'],
                          seed=config['seed'], steps=config['steps'], cfg=config['cfg']))
    dump(output/'tasks.json', tasks)
    dump(output/'config.json', config)
    dump(output/'preparation.json', dict(source=str(source), source_sha256=digest(source),
         original_size=rgba.size, inference_size=size, background='white RGB composite of source alpha',
         generated_alpha=False, mask_semantics='broad body envelope, not an anatomical mask',
         files={n:digest(output/n) for n in ('original.png','input.png','source-alpha.png','edit-mask.png','tasks.json','config.json')},
         config_sha256=digest(config_file), code_sha256=digest(__file__), anatomical_truth=False))


def generate(prepared, output, reuse=None):
    # No model download, Hub login, server or user Comfy installation.
    for name in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_IMPLICIT_TOKEN'):
        os.environ[name] = '1'
    prep = json.loads((prepared/'preparation.json').read_text())
    for name, expected in prep['files'].items():
        if digest(prepared/name) != expected:
            raise ValueError('Prepared input changed: '+name)
    config = json.loads((prepared/'config.json').read_text())
    if (config['sampler'], config['scheduler'], config['shift']) != ('euler','simple',3.0) or not 0 < config['denoise'] <= 1:
        raise ValueError('Unsupported sampler configuration')
    output = new_run(output)
    shutil.copyfile(__file__, output/'generation-source.py')
    reused = {}
    if reuse:
        old = json.loads((reuse/'report.json').read_text())
        if old['preparation_sha256'] != digest(prepared/'preparation.json'):
            raise ValueError('Cannot reuse different prepared inputs/settings')
        for row in old['tasks']:
            name = row['task']['id']
            for kind in ('raw', 'composite'):
                if digest(reuse/name/(kind+'.png')) != row[kind+'_sha256']:
                    raise ValueError('Changed cached pose')
            reused[name] = row
    import torch
    sys.path.insert(0, str(ROOT/'backends/inpainting'))
    from qwen import Qwen
    from worker import LOCK
    if reuse and old['model_lock'] != LOCK:
        raise ValueError('Cached model pins changed')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable; use approved host GPU execution')
    torch.cuda.set_device(0)
    if torch.cuda.get_device_capability() != (12, 0):
        raise RuntimeError('Study is pinned to Blackwell')
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    started = time.perf_counter()
    model = Qwen()  # Hash-verifies all existing weights and pinned inference sources.
    report = dict(status='running', model='Qwen-Image-Edit-2509 Q4_K_S',
                  encoder='Qwen2.5-VL-7B FP8 scaled', dequantization='BF16', model_lock=LOCK,
                  gpu=torch.cuda.get_device_name(), torch=torch.__version__, cuda=torch.version.cuda,
                  preparation_sha256=digest(prepared/'preparation.json'),
                  settings=config,
                  code_sha256={str(p.relative_to(ROOT)):digest(p) for p in
                    [Path(__file__), ROOT/'backends/inpainting/qwen.py', ROOT/'backends/inpainting/worker.py',
                     ROOT/'backends/inpainting/qwen-env/uv.lock']},
                  load_seconds=time.perf_counter()-started, tasks=[], anatomical_truth=False,
                  note='Raw output and protected composite retained separately; no alpha reconstruction')
    dump(output/'report.json', report)
    rgb = np.array(Image.open(prepared/'input.png').convert('RGB'))
    mask = np.array(Image.open(prepared/'edit-mask.png').convert('L')) > 0
    try:
        with torch.inference_mode():
            image = torch.from_numpy(rgb.copy()).float()[None]/255
            # Encode the same canonical image for every pose. Never chain generations.
            for task in json.loads((prepared/'tasks.json').read_text()):
                target = output/task['id']
                target.mkdir()
                if task['id'] in reused:
                    row = dict(reused[task['id']])
                    if row['task'] != task:
                        raise ValueError('Changed cached task settings')
                    for kind in ('raw', 'composite'):
                        shutil.copyfile(reuse/task['id']/(kind+'.png'), target/(kind+'.png'))
                    row['reused_from'] = str(reuse)
                    row['producer_report_sha256'] = digest(reuse/'report.json')
                    report['tasks'].append(row)
                    dump(output/'report.json', report)
                    continue
                torch.cuda.reset_peak_memory_stats()
                torch.manual_seed(task['seed'])
                torch.cuda.synchronize()
                begin = time.perf_counter()
                positive = model.encode(model.clip, task['prompt'], model.vae, image1=image)[0]
                negative = model.encode(model.clip, '', model.vae, image1=image)[0]
                latent = dict(samples=model.vae.encode(image),
                              noise_mask=torch.from_numpy(mask.astype(np.float32))[None])
                sampled = model.sample(model.model, task['seed'], task['steps'], task['cfg'],
                                       'euler','simple',positive,negative,latent,denoise=config['denoise'])[0]
                decoded = model.vae.decode(sampled['samples'])
                if decoded.ndim == 5 and decoded.shape[1] == 1:
                    decoded = decoded[:,0]
                raw = (decoded[0].cpu().numpy()*255).round().clip(0,255).astype(np.uint8)
                if raw.shape != rgb.shape:
                    raise ValueError('Unexpected decoded dimensions')
                composite = rgb.copy()
                composite[mask] = raw[mask]
                Image.fromarray(raw).save(target/'raw.png')
                Image.fromarray(composite).save(target/'composite.png')
                torch.cuda.synchronize()
                report['tasks'].append(dict(task=task, seconds=time.perf_counter()-begin,
                    raw_sha256=digest(target/'raw.png'), composite_sha256=digest(target/'composite.png'),
                    outside_composite_changed=int(np.any(composite[~mask]!=rgb[~mask],axis=-1).sum()),
                    raw_outside_mae=float(np.abs(raw.astype(float)-rgb)[~mask].mean()),
                    max_allocated_bytes=torch.cuda.max_memory_allocated(),
                    max_reserved_bytes=torch.cuda.max_memory_reserved()))
                dump(output/'report.json', report)
                print(task['id'], report['tasks'][-1]['seconds'], flush=True)
                del positive, negative, latent, sampled, decoded
    except Exception as exc:
        report.update(status='failed', error=str(exc))
        dump(output/'report.json', report)
        raise
    finally:
        model.close()
    report.update(status='completed', total_seconds=time.perf_counter()-started)
    dump(output/'report.json', report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--config', type=Path, default=ROOT/'recipes/qwen-pose-study.json')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--denoise', type=float)
    p.add_argument('--poses', nargs='+')
    p = sub.add_parser('generate')
    p.add_argument('--prepared', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--reuse', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.input, args.config, args.output, args.denoise, args.poses)
    else:
        generate(args.prepared, args.output, args.reuse)


if __name__ == '__main__':
    main()
