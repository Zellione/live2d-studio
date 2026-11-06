# Phase 4B.7b — guided local generation

This experiment uses the immutable flat Codel source, not the PSD. Synthetic
poses remain auxiliary inferences. Neither pixel equality nor a successful model
invocation establishes anatomy or user acceptance.

## Audit of the previous implementation

The actual 4B.7a task records used **528 × 1024**, 40 steps, CFG 4,
Euler/simple, model shift 3, one image reference and source-VAE latent
initialization. A body noise mask and post-decode composition protected the face;
strengths were 1.0 and .6. The older facial implementation's 512-pixel/20-step
settings were not the pose settings. Hard composition clipped edited limbs and
created seams. The original image still contains one crossed arm and one hanging
arm; the existing decomposition merges both.

The new worker returns the raw decoded image, with no hard source paste. It uses
uniform scaling and minimal letterboxing to a multiple of 16: the 1078 × 2089
source becomes **544 × 1024** or **800 × 1536**. The character is never stretched
to fill a different aspect ratio. Transparent source pixels are composited on
white for conditioning; the original RGBA file is copied and hash-checked.

The first calibration's masked baseline approximates the old body mask; it is
not a byte-identical replay of 4B.7a. Comparisons within the new study hold seed
1729 constant and change the recorded parameter family. Adding image2 also adds
the necessary prompt reference to that image. This is an explicit conditioning
change, not an isolated prompt-word experiment.

## Official workflows and installed capabilities

[Qwen's 2509 description](https://github.com/QwenLM/Qwen-Image/blob/main/Qwen-Image-Edit-2509.md)
describes multi-image editing and pose/keypoint use. The
[Comfy announcement](https://blog.comfy.org/p/wan22-animate-and-qwen-image-edit-2509)
provides workflow context. The
[current Comfy template](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/templates/image_qwen_image_edit_2509.json)
was saved under `runs/phase4b7b-audit/official-workflow.json`. Its current default
includes a four-step Lightning LoRA; this experiment does **not** load that LoRA
or copy its four-step setting. The template also contains non-turbo settings and
recommendations that differ in steps/CFG. These are comparison points, not a
universal optimum.

The installed `TextEncodeQwenImageEditPlus` accepts image1/image2/image3. We use
image1 for identity and image2 for a programmatic pose hypothesis. The actual
GGUF execution checks that two reference latents survive conditioning and records
their shapes. Image3 is supported by the installed signature but untested here.
A retained reference does not guarantee that the output follows its pose.

Internally, this pinned node independently resamples each vision input to about
384² pixels of **area**, and each VAE reference to about 1024² pixels of **area**,
with VAE dimensions rounded to multiples of eight. Neither means a fixed square
crop. For our canvases the vision inputs are approximately 280 × 527 or
277 × 532; VAE references approximately 744 × 1408 or 736 × 1416.
Output resolution and internal conditioning resolution are separate.

Source and empty latent initialization, mask removal, concise text, skeleton vs
silhouette, output resolution, CFG normalization and step count are compared.
The follow-up changes head landmarks, then representation, denoise or steps.
Sampler, scheduler, CFG and shift remain Euler/simple, 4 and 3 in the executed
study. Their alternatives were inspected, not exhaustively optimized. Negative
prompts are explicitly empty. No user workflow JSON exists for a direct old-PC
comparison; no unrelated workflows or private settings were inspected.

## Pinned backend

- Transformer: `QuantStack/Qwen-Image-Edit-2509-GGUF`, Q4_K_S, revision
  `84a3006979126011422eeeefe0c9485ddf431ef5`.
- Local transformer: `models/phase4b2/qwen/Qwen-Image-Edit-2509-Q4_K_S.gguf`.
- Separate encoder: `qwen_2.5_vl_7b_fp8_scaled.safetensors`, under
  `models/phase4b2/qwen/split_files/text_encoders/`.
- Encoder/VAE source: `Comfy-Org/Qwen-Image`, revision
  `1f12b17be14c89b026c51a91d67c32f84bb047bc`; VAE local
  `models/phase4b2/qwen/qwen_image_vae.safetensors`.
- Model files are Apache-2.0; exact file SHA-256 values remain in the unchanged
  `backends/inpainting/models.lock.json` and copied execution reports.
- Headless ComfyUI 0.3.60, commit
  `b8730510db30c8858e1e5d8e126ef19eac395560` (GPL-3.0);
  ComfyUI-GGUF `6ea2651e7df66d7585f6ffee804b20e92fb38b8a` (Apache-2.0).
- Existing isolated frozen uv environment, Torch 2.8.0+cu128, RTX 5090 32 GB.
  No model downloads, new custom nodes or global package installs.

The Q4 transformer and FP8 encoder execute together at both output sizes.
There is no full-precision control, so this does not measure quantization quality.
Per-pose wall time includes conditioning, sampling and decode. Reported peaks
are Torch allocated/reserved CUDA memory, not whole-device NVML usage.

## Reproduction

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --frozen
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b7b_calibrate.py \
  --output runs/NEW-calibration
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen --offline \
  --project backends/inpainting/qwen-env python backends/inpainting/pose_worker.py \
  --plan runs/NEW-calibration/plan.json
```

To replay a recorded case exactly, copy its saved source, guide and plan to a new
ignored directory, retaining hashes/settings/seed and selecting the desired task.
Never run into an existing task output. The original first-study guide/code
snapshot is retained in `runs/phase4b7b-audit/producer-v1/`; current guide generation
adds facial landmarks. Rebuilding a guide with newer code is not exact replay.
Saved metadata makes replay reproducible; bit-exact GPU replay has not been
claimed from the CPU deterministic-runner test.

Guides are source-bounds-relative head-to-upper-leg hypotheses, not detected
anatomy or a general full-body pose estimator. Face anchors constrain framing;
hand orientation still depends on text, without finger keypoints. Out-of-frame
joint proposals are marked unsupported. A misleading in-frame guide may still
need a human unsupported decision. Seeds vary rendering while source, guide,
prompt and settings remain fixed within each five-image batch.
