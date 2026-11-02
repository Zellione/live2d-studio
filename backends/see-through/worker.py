"""Offline, headless upstream runner. Execute only in this directory's uv env."""
import argparse
import gc
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
for key, value in {'HF_HUB_OFFLINE':'1', 'HF_HUB_DISABLE_IMPLICIT_TOKEN':'1',
                   'HF_HUB_DISABLE_TELEMETRY':'1', 'TRANSFORMERS_OFFLINE':'1',
                   'HF_HOME':str(ROOT/'.cache/phase2-5-hf'),
                   'TORCH_HOME':str(ROOT/'.cache/phase2-5-torch'),
                   'MPLCONFIGDIR':str(ROOT/'.cache/phase2-5-mpl'),
                   'OMP_NUM_THREADS':'8', 'OPENBLAS_NUM_THREADS':'8'}.items():
    os.environ[key] = value


def dump(file, value):
    file.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT/'.cache/see-through/source')
    parser.add_argument('--resolution', type=int, default=1280)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--sam', action='store_true')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Choose a fresh worker output directory')
    lock = json.loads((Path(__file__).parent/'models.lock.json').read_text())
    revision = subprocess.check_output(['git','-C',str(args.source),'rev-parse','HEAD'], text=True).strip()
    if revision != lock['upstream_revision'] or subprocess.check_output(
            ['git','-C',str(args.source),'status','--porcelain'], text=True).strip():
        raise ValueError('Upstream checkout must be pinned and unmodified')
    models = {k:ROOT/'models/see-through'/k/v['revision'] for k,v in lock['repositories'].items()}
    for key in (['sam'] if args.sam else ['layerdiff','depth']):
        for item in lock['repositories'][key]['files']:
            file = models[key]/item['path']
            if file.stat().st_size != item['bytes']:
                raise ValueError(f'Wrong model size: {file}')
            if item['sha256']:
                with file.open('rb') as stream:
                    if hashlib.file_digest(stream,'sha256').hexdigest() != item['sha256']:
                        raise ValueError(f'Wrong model hash: {file}')
    sys.path.insert(0,str(args.source/'common'))
    import torch
    import numpy as np
    from PIL import Image
    from utils import inference_utils as upstream
    from utils.torch_utils import seed_everything
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is required for this neural experiment; use deterministic for CPU')
    device = next((i for i in range(torch.cuda.device_count()) if '5090' in torch.cuda.get_device_name(i)), None)
    if device is None:
        raise RuntimeError('Expected RTX 5090 was not found')
    torch.cuda.set_device(device)
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError('BF16 is unavailable')
    args.output.mkdir(parents=True, exist_ok=False)
    original_hash = hashlib.sha256(args.input.read_bytes()).hexdigest()
    metrics = dict(device=torch.cuda.get_device_name(device), capability=list(torch.cuda.get_device_capability(device)),
        seed=args.seed, dtype='float32' if args.sam else 'bfloat16', upstream_revision=revision,
        input_sha256=original_hash, packages={p:importlib.metadata.version(p) for p in
        ['torch','torchvision','diffusers','transformers','numpy','Pillow','psd-tools']}, stages=[])
    samples = []
    stop = threading.Event()

    def poll():
        while not stop.is_set():
            try:
                raw = subprocess.check_output(['nvidia-smi','--query-gpu=name,utilization.gpu,memory.used',
                    '--format=csv,noheader,nounits'], text=True, timeout=5)
                row = next(line for line in raw.splitlines() if '5090' in line)
                _, util, mem = row.split(',')
                samples.append(dict(elapsed=time.perf_counter()-start, utilization_percent=int(util), memory_mib=int(mem)))
            except (OSError, ValueError, StopIteration, subprocess.SubprocessError):
                pass
            stop.wait(.5)

    def stage(name, operation):
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        begin = time.perf_counter()
        try:
            operation()
            torch.cuda.synchronize()
        finally:
            metrics['stages'].append(dict(name=name, seconds=time.perf_counter()-begin,
                peak_allocated_bytes=torch.cuda.max_memory_allocated(), peak_reserved_bytes=torch.cuda.max_memory_reserved()))
            dump(args.output/'metrics.json',metrics)

    start = time.perf_counter()
    monitor = threading.Thread(target=poll, daemon=True)
    monitor.start()
    try:
        seed_everything(args.seed)
        if args.sam:
            def sam():
                from modules.semanticsam import SemanticSam
                checkpoint = torch.load(models['sam']/'checkpoint-18000.pt', map_location='cpu', weights_only=True)
                if 'state_dict' in checkpoint:
                    checkpoint = checkpoint['state_dict']
                model = SemanticSam(class_num=19)
                model.load_state_dict(checkpoint, strict=True)
                del checkpoint
                model.eval().cuda()
                img = np.array(Image.open(args.input).convert('RGB'))
                with torch.inference_mode():
                    preds = model.inference(img)[0]
                masks = (preds > 0).cpu().numpy()
                for tag, mask in zip(upstream.VALID_BODY_PARTS_V2,masks):
                    Image.fromarray(mask.astype(np.uint8)*255).save(args.output/(tag+'.png'))
                dump(args.output/'sam.json',dict(tags=upstream.VALID_BODY_PARTS_V2, threshold_logit=0,
                    hidden_pixel_provenance='not provided',input_sha256=original_hash))
            stage('sam',sam)
        else:
            stage('layerdiff',lambda:upstream.apply_layerdiff(str(args.input),str(models['layerdiff']),
                save_dir=str(args.output), seed=args.seed,resolution=args.resolution,num_inference_steps=30))
            upstream.layerdiff_pipeline = None
            gc.collect()
            torch.cuda.empty_cache()
            stage('marigold',lambda:upstream.apply_marigold(str(args.input),str(models['depth']),
                save_dir=str(args.output),seed=args.seed,resolution=768,num_inference_steps=4))
            upstream.marigold_pipeline = None
            gc.collect()
            torch.cuda.empty_cache()
            saved = args.output/args.input.stem
            stage('export',lambda:upstream.further_extr(str(saved), rotate=False,save_to_psd=True,tblr_split=True))
            # Preserve the PSD's actual order, offsets and fractional alpha for the bridge.
            from psd_tools import PSDImage
            psd_path = args.output/(args.input.stem+'.psd')
            psd = PSDImage.open(psd_path)
            exported = args.output/'bridge'
            exported.mkdir()
            layers = []
            for i, layer in enumerate(psd):
                png = f'layer-{i:02d}.png'
                layer.topil().convert('RGBA').save(exported/png)
                layers.append(dict(name=layer.name,path=png,x=layer.left,y=layer.top,z_order=i,
                                   opacity=layer.opacity,blend_mode=str(layer.blend_mode)))
            Image.open(saved/'src_img.png').save(exported/'normalized.png')
            dump(exported/'decomposition.json',dict(format_version=1,order='back-to-front',
                canvas=dict(width=psd.width,height=psd.height),layers=layers,
                input_sha256=original_hash, normalized_path='normalized.png',
                source_revision=revision,models={k:lock['repositories'][k]['revision'] for k in ['layerdiff','depth']},
                transform=dict(kind='center-square-pad-resize',resolution=args.resolution),
                generation_provenance='All output pixels are generated; hidden-only mask is unavailable.'))
        metrics['status']='completed'
    except Exception as error:
        metrics['status']='failed'
        metrics['error']=str(error)
        raise
    finally:
        stop.set()
        monitor.join(timeout=6)
        metrics['seconds']=time.perf_counter()-start
        metrics['gpu_samples']=len(samples)
        if samples:
            metrics['sampled_device_peak_mib']=max(s['memory_mib'] for s in samples)
            metrics['sampled_gpu_utilization_mean']=sum(s['utilization_percent'] for s in samples)/len(samples)
            metrics['sampled_gpu_utilization_peak']=max(s['utilization_percent'] for s in samples)
        metrics['input_unchanged']=hashlib.sha256(args.input.read_bytes()).hexdigest()==original_hash
        dump(args.output/'metrics.json',metrics)
        dump(args.output/'gpu-samples.json',samples)


if __name__ == '__main__':
    main()
