# Phase 4B.2 model investigation

Reviewed 2026-11-03. Full public cards and file trees are retained in
`runs/phase4b2-research`. Executed weight pins are in
[`models.lock.json`](../backends/inpainting/models.lock.json). File size is **not**
peak VRAM. Actual hardware measurements and visual decisions belong in the
[results](phase4b2-results.md); entries below distinguish tested and untested paths.

## Candidates and decision

| Candidate | Weight storage | Pipeline and masks | Assessment |
| --- | ---: | --- | --- |
| Anime/Manga LaMa | 204,332,996 bytes | FP32 Big-LaMa FFC, RGB plus binary mask; no text conditioning | First experiment: small, illustrated-image specialization, explicit masks. Local native/2× tests and actual rigs executed. |
| SDXL Inpainting 0.1 FP16 | 6,938,041,649 bytes for UNet, two text encoders, VAE | Diffusers `StableDiffusionXLInpaintPipeline`; trained 9-channel masked UNet | Technically suitable for local masked generation. Metadata inspected; not downloaded/run. Its photorealistic training and tiny facial targets give no demonstrated advantage over the chosen illustrated-image and instruction-editing experiments. |
| Qwen Image Edit 2509 BF16 | 57,699,249,798 bytes for transformer, text encoder, VAE | `QwenImageEditPlusPipeline`; image-conditioned instruction editing | Full resident weights exceed 32 GB, but this does **not** exclude Qwen. Full precision was not downloaded. |
| Qwen GGUF Q4_K_S + FP8 vision/text encoder | 12,204,309,024 + 9,384,670,680 bytes | Pinned ComfyUI `TextEncodeQwenImageEditPlus`, city96 GGUF transformer loader; ordinary FP8 CLIP loader | Selected quantized experiment. 21.59 GB new weights, explicitly approved. Reused hash-verified 253,806,246-byte VAE. Latent noise mask plus final pixel mask; not native mask-trained Qwen. |
| Qwen FP8 e4m3fn transformer | 20,430,698,424 bytes, plus encoder/VAE | ComfyUI native FP8 loader and Edit Plus conditioning | Plausible with offload, but less memory headroom than Q4. Not downloaded/run; no local speed or quality-degradation measurement. |
| Qwen Nunchaku NVFP4 r32 | 11,948,923,656 bytes, plus encoder/VAE | Nunchaku-specific `NunchakuQwenImageTransformer2DModel` with Edit Plus; its own offload API | Explicit Blackwell path; not rejected for VRAM. Requires compatible compiled Nunchaku/Python/Torch/CUDA wheel. Not interchangeable with generic FP4, GGUF or plain Diffusers loader. Not downloaded/run. |
| Qwen Nunchaku INT4 / r128 / distilled variants | Depends on rank and variant | SVDQuant-specific kernels; rank 128 trades size/speed for retained residual capacity; Lightning additionally changes sampling | Inspected as alternatives. INT4 targets pre-Blackwell; NVFP4 is the documented 50-series choice. No extra variant downloaded solely to expand the model list. |

The Comfy file tree also provides `2509_int8_convrot` (20,499,083,752 bytes,
SHA-256 `638402843782296122f42f2ff557a63a9535c4fbc3f6978308042c8d0f4012b4`)
and FP8 mixed precision (20,533,579,421 bytes). These require a loader supporting
their specific quantization metadata; compatibility with our older pinned Comfy
checkout is not established. They were not silently substituted for the selected
Q4_K_S backend. Nunchaku r128 NVFP4 is 13,081,386,856 bytes; its extra low-rank
capacity is a vendor quality tradeoff, not a local measured improvement.

LaMa cannot follow “close this eyelid”: its role is contextual completion/removal.
Qwen offers instruction-guided feature editing, which is a meaningful capability
advantage worth testing after LaMa recreated open eyes. Neither model guarantees
identity, exact style, alignment or anatomical truth. The worker imposes source
preservation after inference, not through prompt wording.

Sources: [LaMa card](https://huggingface.co/mayocream/lama-manga),
[SDXL card](https://huggingface.co/diffusers/stable-diffusion-xl-1.0-inpainting-0.1),
[Qwen card](https://huggingface.co/Qwen/Qwen-Image-Edit-2509),
[GGUF conversion and supported loader](https://huggingface.co/QuantStack/Qwen-Image-Edit-2509-GGUF),
[Comfy FP8 files](https://huggingface.co/Comfy-Org/Qwen-Image-Edit),
[Nunchaku quantizations](https://huggingface.co/nunchaku-ai/nunchaku-qwen-image-edit-2509).

## Immutable provenance and licenses

- **LaMa**: `mayocream/lama-manga`, revision
  `f91c85b26913b3e83f9877867b4c336da3675238`; weight SHA-256
  `a790515e9da839b8d89af7d565ceb110d908b7d6fbdb991f2acb2ec7d9b08bdb`.
  The conversion repository declares MIT. It identifies Sanster's AnimeManga
  release as its source, with an approximately 300k-image fine-tuning claim but
  no supplied dataset artifacts or evaluation. This is declared checkpoint
  provenance, not an independently audited training-rights claim. The upstream
  generator code is Apache-2.0, Samsung Research; our trimmed inference copy
  retains the license and attribution. No weights are redistributed.
- **Original LaMa parity check**: the source TorchScript is 205,717,870 bytes,
  SHA-256 `479d3afdcb7ed2fd944ed4ebcc39ca45b33491f0f2e43eb1000bd623cfb41823`.
  Its archived forward source was inspected before loading. All 989 tensor
  values equal the safetensors conversion; one identical GPU crop produces
  maximum absolute forward difference **0.0**. The original is diagnostic only;
  the runtime worker loads safetensors, with strict tensor-key matching.
- **SDXL**: revision `115134f363124c53c7d878647567d04daf26e41e`, CreativeML
  Open RAIL++-M (use restrictions apply; not an unrestricted software license).
  FP16 SHA-256: UNet `6470840731e98cc16713ddf3ac7ee458c9fdbcb881a98c6727cd4a938f227d3f`,
  encoder 1 `fc83cf401d930147807e7c44021c164bcc5508c9d4cc0ff35f4e354685ca9cd0`,
  encoder 2 `a8622bd41f8d359df484fdf9de091edb9337a2fd747f0a5c9c320a62e24d1fd3`,
  VAE `4ad62825e5c8b31eefb77355ba6693785619bf7d669d9b1a6fd9f19dec6d65b3`.
- **Qwen upstream**: revision `d3968ef930e841f4c73640fb8afa3b306a78167e`, Apache-2.0.
  QuantStack conversion revision `84a3006979126011422eeeefe0c9485ddf431ef5`, Apache-2.0.
  The exact Q4_K_S weight and companion hashes are enforced by `models.lock.json`.
  QuantStack identifies the base model but does not pin the source conversion
  toolchain/base SHA; that supply-chain limitation remains explicit. No BF16/Q4
  paired quality experiment was performed, so defects cannot be attributed to
  quantization alone.
- **Qwen companion files**: `Comfy-Org/Qwen-Image_ComfyUI` revision
  `1f12b17be14c89b026c51a91d67c32f84bb047bc`, Apache-2.0. FP8 encoder SHA-256
  `cb5636d852a0ea6a9075ab1bef496c0db7aef13c02350571e388aea959c5c0b4`;
  VAE `a70580f0213e67967ee9c95f05bb400e8fb08307e017a924bf3441223e023d1f`.
  The existing ComfyUI VAE matches this hash and was copied into the project.
- **Other Qwen variants**: Comfy revision `f68ace85e60b4a02a323e394253731947657b7d2`,
  FP8 e4m3fn SHA-256 `318568f61951ab9da21100c7b896e3c1da67f0d2efad6421545e022cfaa2b2b4`;
  Nunchaku revision `e93a5fb77403d02a5a73c7cc8707b292c6ebc659`, NVFP4 r32 SHA-256
  `d6f4684e2e89bf22480019e773108de129c22694f0314d2bca00e3d60ed8c031`.
  Both declare Apache-2.0. These are metadata-verified hashes, not locally
  verified/downloaded weights.

## Backend compatibility and practical memory strategy

LaMa uses Torch 2.8.0+cu128 FP32 convolutions and FFT on the 5090, with no custom
CUDA extension. Torch/NumPy/Pillow/safetensors have an independent frozen uv lock.
Its small cropped workload is distinct from full-resolution VRAM requirements.

Qwen uses an isolated headless ComfyUI 0.3.60 checkout at
`b8730510db30c8858e1e5d8e126ef19eac395560` (GPL-3.0), and ComfyUI-GGUF at
`6ea2651e7df66d7585f6ffee804b20e92fb38b8a` (Apache-2.0). The latter explicitly
recognizes `qwen_image`; ordinary llama.cpp text generation is not a compatible
image-editing backend. The selected FP8 vision/text encoder is loaded through
Comfy's native loader, not its GGUF CLIP loader (which refuses mixed scaled FP8).
No user ComfyUI installation/custom-node environment is modified or started.

Comfy manages encoder/model offload; the quantized transformer dequantizes linear
operations to BF16 as needed. This avoids assuming that all weights and activation
buffers coexist on the GPU. The 512px crop output and Edit Plus reference encoding
are recorded separately; reference encoding internally uses the pinned upstream
1024px area transform. RGB crop output is resized to the native grid and copied
only inside the explicit mask. This is an experimental masked editing wrapper,
not a claim that the base model was trained as an inpainting UNet.

Nunchaku's [Edit Plus example](https://nunchaku.tech/docs/nunchaku/usage/qwen-image-edit.html)
and [installation matrix](https://nunchaku.tech/docs/nunchaku/installation/installation.html)
establish a concrete alternative: NVFP4 plus matched compiled kernels and its own
CPU offload. Its quality/speed claims are not local measurements. We chose GGUF
for this comparison to reuse standard Torch operations and avoid another binary
extension, not because NVFP4 or a 16 GB execution strategy is impossible.

Cache inspection covered project weights/cache, Hugging Face cache, `/data/models`
and ComfyUI model folders. No matching Image Edit 2509 transformer or Qwen2.5-VL
encoder was found; similarly named Qwen language-model weights are incompatible.
No secret stores were read. Downloads stayed in project-local caches, with implicit
Hub authentication disabled. Slow dependency transfers were resumed as the exact
uv-lock-hashed wheels; the final environment still passes frozen uv synchronization.
