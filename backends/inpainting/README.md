# Optional local facial inpainting

The main application remains CPU-only and deterministic by default. This directory
contains separate offline workers; neither installs itself or downloads models at
runtime. Read [model provenance](../../docs/phase4b2-model-evaluation.md) and the
[experiment results](../../docs/phase4b2-results.md) before choosing a neural mode.
Source layers, observed masks and source-neutral mouth artwork are never changed
by inpainting. All outputs remain candidates requiring visual review.

## Environments and weights

From the repository root:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --project backends/inpainting --frozen
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --project backends/inpainting/qwen-env --frozen
```

The first environment is only LaMa; the second is the headless Qwen comparison.
Both use Python 3.12 and Torch 2.8.0+cu128. Main/See-through locks remain unchanged.
The LaMa generator was trimmed from advimman/lama at the revision in the lock:
training/discriminator imports removed, unused SE/spatial-transform branches
explicitly refused. License: Apache-2.0, see LICENSE.lama. All 989 safetensors keys
must load strictly. The model is FP32 because its FFT path is not assumed to work
in arbitrary low precision.

Download the 204 MB LaMa checkpoint after reviewing its declared MIT/source terms:

```sh
HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HOME="$PWD/.cache/phase4b2-hf" hf download \
  mayocream/lama-manga lama-manga.safetensors config.json README.md \
  --revision f91c85b26913b3e83f9877867b4c336da3675238 \
  --local-dir models/phase4b2/lama-manga
```

Qwen additionally requires the **separately approved 21.59 GB download** documented
in this phase. Do not download full-precision Qwen as an implicit fallback. Its
worker expects these exact local files, each SHA-256 checked before loading:

- `models/phase4b2/qwen/Qwen-Image-Edit-2509-Q4_K_S.gguf`
- `models/phase4b2/qwen/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors`
- `models/phase4b2/qwen/qwen_image_vae.safetensors`

Repositories/revisions/hashes are in `models.lock.json`. The original local VAE
was hash-verified and reused; filename presence alone is insufficient. Qwen's
headless source checkouts must be clean at the pinned revisions:

```sh
git clone --branch v0.3.60 --depth 1 https://github.com/comfyanonymous/ComfyUI.git .cache/phase4b2-comfy
git clone https://github.com/city96/ComfyUI-GGUF.git .cache/phase4b2-comfy-gguf
git -C .cache/phase4b2-comfy-gguf checkout 6ea2651e7df66d7585f6ffee804b20e92fb38b8a
```

No Comfy server or unrelated custom nodes are loaded. The isolated worker imports
only the pinned core and GGUF implementation. It uses single-crop Edit Plus
conditioning, native FP8 encoder loading, BF16 GGUF dequantization, Euler/simple,
shift 3, 20 steps, CFG 4 and seed 1729. Output long edge is 512 pixels; the pinned
reference encoder separately resizes its input. A latent noise mask limits the
denoising region; native-grid hard compositing provides the exact source guarantee.
This is not native mask-trained Qwen. LaMa ignores prompts/steps/CFG entirely.

## CLI and review

```sh
uv run --frozen live2d-studio create --input portrait.png --output runs/NEW \
  --rights 'Author; license; URL' --reconstruction deterministic

uv run --frozen live2d-studio create --input portrait.png --output runs/NEW-neural \
  --rights 'Author; license; URL' --reconstruction neural \
  --inpainting-config recipes/inpainting/lama.json
```

The same existing semantic and visual review gates apply. Reuse source-matched
`--decomposition`/`--sam` to avoid repeating expensive parsing. `--until facial`
stops at inspectable layers, crop requests, raw model output, masks and diagnostics.
Do not resume a frozen accepted run after code changes; choose a fresh run.

Configuration contains `model` (`lama`/`qwen`), `scale` (LaMa crop resampling),
`seed` and optional `targets` (alternative names such as `mouth-skin`). Default
neural mode evaluates every supported generated alternative. Missing requested
features fail rather than forcing a sparse-mouth treatment onto already-open art.
The original geometric open-mouth fallback remains intact.

For controlled comparisons, configuration may also contain `prediction_cache`,
pointing to a previous worker output. The pipeline verifies the model lock, exact
task parameters, input/mask hashes and raw/composited output hashes, copies the
selected artifacts into the new run, and records that inference was reused. The
producer's original code hashes and measurements stay intact. The cache inventory
participates in stage invalidation; it cannot silently supply another character's
artwork. This permits comparisons of neural and hybrid composites from identical
model samples without keeping a GPU model resident.

`--reconstruction hybrid --inpainting-review review.json` blends selected neural
interiors while preserving deterministic boundary pixels and all other alternatives.
It requires a prior image review with `decision: accept-selected`, `reviewer`,
`selected` (alternative IDs), and `images` mapping each selected ID to its exact
`image_sha256`, `mask_sha256`, `composite_sha256` from the preceding prediction
report. Recomputed image hashes must match; nondeterministic differences require
new review. A review is specific to one character/input/configuration. Image review
does not grant runtime acceptance. Never label development-agent review as user
approval. Empty selection is a valid explicit deterministic fallback.

Generated alternatives include full-canvas neural masks and uncertain boundary
masks with hashes. The source-neutral alternative remains copied source. Outside
each approved pixel mask, RGBA is byte-identical; inside it, generated RGB is
marked uncertain. Closed-lash candidates can include opaque generated skin within
the approved mask. Runtime compositing is measured separately from source copying.

The standalone worker accepts a JSON batch of relative raster image/mask paths,
IDs, seeds and prompts. It reads no benchmark metadata/expression sprites. Each
task retains raw output and hard-composited output, input/output hashes, changed
pixel counts, time and Torch allocated/reserved VRAM. Weights load once per batch;
the process unloads them and exits afterwards. There is no coding-agent dependency.
The actual supported hardware experiment is the RTX 5090 (compute capability 12.0).

## Reproduce evidence

```sh
uv run --frozen python scripts/phase4b2_experiment.py \
  --baseline runs/phase4b1-sara --output runs/NEW-lama-rig \
  --config recipes/inpainting/lama.json
uv run --frozen python scripts/phase4b2_crops.py \
  --baseline runs/phase4b1-sara --output runs/NEW-crops --model qwen --controlled
uv run --frozen python scripts/phase4b1_render.py \
  --model MODEL.model3.json --output runs/NEW-poses
uv run --frozen python scripts/phase4b1_render.py \
  --model MODEL.model3.json --output runs/NEW-transitions --transitions
uv run --frozen python -m unittest discover -s tests -v
node tests/test_rp_talk.mjs
```

The experiment helper reuses semantic review only if the complete quality report
is byte-identical to the reviewed predecessor, identifies that replay as development
evidence, and builds a new PSD/project/runtime through loopback MCP. New neural
artwork is never automatically accepted. Test failures and rejected candidates
remain under their original run directories. Production deployment is unchanged.
