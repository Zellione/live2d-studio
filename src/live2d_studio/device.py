"""Optional PyTorch/CUDA execution probe; importing pipeline never loads Torch."""
import importlib.util
import time


def doctor():
    report = dict(pipeline_device='cpu',torch_installed=False,cuda_tested=False,
                  model_inference_tested=False)
    if importlib.util.find_spec('torch') is None:
        report['reason']='PyTorch not installed in this project; CPU image baseline available'
        return report
    import torch
    report.update(torch_installed=True,torch_version=torch.__version__,cuda_build=torch.version.cuda)
    if not torch.cuda.is_available():
        report['reason']='CUDA unavailable to this process; check permissions and wheel support'
        return report
    # Prefer RTX 5090 when several GPUs are installed; never assume device zero.
    devices = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    index = next((i for i,n in enumerate(devices) if '5090' in n),0)
    try:
        with torch.cuda.device(index), torch.inference_mode():
            torch.cuda.reset_peak_memory_stats()
            started = time.perf_counter()
            x = torch.ones((256,256),device=f'cuda:{index}')
            y = x@x
            torch.cuda.synchronize()
            if float(y[0,0]) != 256:
                raise RuntimeError('CUDA arithmetic failed')
            report.update(cuda_tested=True,device=devices[index],device_index=index,
                capability=list(torch.cuda.get_device_capability(index)),
                arch_list=torch.cuda.get_arch_list(),probe_seconds=time.perf_counter()-started,
                peak_vram_bytes=torch.cuda.max_memory_allocated())
            del x,y
            torch.cuda.empty_cache()
    except RuntimeError as error:
        report['reason']=str(error)
    return report
