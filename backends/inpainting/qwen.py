"""Pinned headless ComfyUI 0.3.60 + GGUF Image Edit Plus, no server/custom nodes."""
import importlib.util
import subprocess
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from worker import ROOT, LOCK, weight


class Qwen:
    def close(self):
        import comfy.model_management
        comfy.model_management.unload_all_models()
        self.model=self.clip=self.vae=None
        comfy.model_management.soft_empty_cache()

    def __init__(self):
        comfy_root=ROOT/'.cache/phase4b2-comfy'
        gguf_root=ROOT/'.cache/phase4b2-comfy-gguf'
        for name,root in [('comfy',comfy_root),('gguf',gguf_root)]:
            revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
            if revision!=LOCK['sources'][name]:raise ValueError('Unreviewed inference source: '+name)
            if subprocess.check_output(['git','-C',str(root),'diff','--name-only','HEAD'],text=True).strip():
                raise ValueError('Modified inference source: '+name)
        base=ROOT/'models/phase4b2/qwen'
        transformer=weight('qwen_transformer','Qwen-Image-Edit-2509-Q4_K_S.gguf',base/'Qwen-Image-Edit-2509-Q4_K_S.gguf')
        encoder_name='split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors'
        encoder=weight('qwen_parts',encoder_name,base/encoder_name)
        vae=weight('qwen_parts','split_files/vae/qwen_image_vae.safetensors',base/'qwen_image_vae.safetensors')
        sys.path.insert(0,str(comfy_root))
        # Comfy's CLI parser must not see the worker's own command arguments.
        saved=sys.argv;sys.argv=[sys.argv[0]]
        import comfy.options
        comfy.options.enable_args_parsing()
        import nodes
        sys.argv=saved
        import comfy.sd
        import comfy.utils
        import folder_paths
        from comfy_extras.nodes_qwen import TextEncodeQwenImageEditPlus
        from comfy_extras.nodes_model_advanced import ModelSamplingAuraFlow
        folder_paths.add_model_folder_path('unet',str(base))
        spec=importlib.util.spec_from_file_location('phase4b2_gguf',gguf_root/'__init__.py',submodule_search_locations=[str(gguf_root)])
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        model=module.NODE_CLASS_MAPPINGS['UnetLoaderGGUF']().load_unet(transformer.name,dequant_dtype='bfloat16',patch_dtype='bfloat16')[0]
        self.model=ModelSamplingAuraFlow().patch_aura(model,3.0)[0]
        self.clip=comfy.sd.load_clip(ckpt_paths=[str(encoder)],embedding_directory=[],clip_type=comfy.sd.CLIPType.QWEN_IMAGE)
        self.vae=comfy.sd.VAE(sd=comfy.utils.load_torch_file(str(vae)))
        self.encode=TextEncodeQwenImageEditPlus().encode
        self.sample=nodes.common_ksampler

    def __call__(self,rgb,mask,task):
        # A single context crop is the only reference. No expression tiles or GT.
        w,h=Image.fromarray(rgb).size
        factor=512/max(w,h)
        width=max(64,round(w*factor/16)*16);height=max(64,round(h*factor/16)*16)
        resized=np.asarray(Image.fromarray(rgb).resize((width,height),Image.Resampling.LANCZOS)).copy()
        image=torch.from_numpy(resized).float()[None]/255
        positive=self.encode(self.clip,task['prompt'],self.vae,image1=image)[0]
        negative=self.encode(self.clip,'',self.vae,image1=image)[0]
        samples=self.vae.encode(image)
        ma=Image.fromarray(mask.astype(np.uint8)*255).resize((width,height),Image.Resampling.NEAREST)
        # The mask is imposed through the sampler, not claimed as native Qwen mask training.
        latent=dict(samples=samples,noise_mask=torch.from_numpy(np.asarray(ma).copy()).float()[None]/255)
        result=self.sample(self.model,task.get('seed',1729),task.get('steps',20),task.get('cfg',4.0),
            'euler','simple',positive,negative,latent,denoise=1.0)[0]
        decoded=self.vae.decode(result['samples'])
        # Qwen's video-family VAE can retain a singleton frame dimension.
        if decoded.ndim==5 and decoded.shape[1]==1:
            decoded=decoded[:,0]
        if decoded.ndim!=4 or decoded.shape[0]!=1 or decoded.shape[-1]!=3:
            raise ValueError('Unexpected Qwen VAE output shape: '+str(decoded.shape))
        raw=(decoded[0].cpu().numpy()*255).round().clip(0,255).astype(np.uint8)
        return np.array(Image.fromarray(raw).resize((w,h),Image.Resampling.LANCZOS))
