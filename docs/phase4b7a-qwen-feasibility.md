# Phase 4B.7a — controlled Qwen pose expansion protocol

This is a local feasibility experiment from `6205158`, outside `create`, the
reviewed runtime and production. [Results](phase4b7a-results.md) distinguish
plausible images, useful segmentation proposals and reliable articulation evidence.
Generated pixels are auxiliary hypotheses, never observed source pixels or truth.

## Input and model provenance

The sole generation input is the frozen original Codel3 PNG by LisadiKaprio,
[Codel Visual Novel Sprite](https://opengameart.org/content/codel-visual-novel-sprite),
CC BY 4.0. SHA-256:
`98589fb8750ccfc3664935985fc42810381b2e09f22e1ae8cf4cd6dd45d39a2d`.
Original framing is 1078 × 2089, including both hands but excluding lower legs/feet.
Neither the layered PSD, other expression images nor rig renders enter generation.
The reviewed runtime capture and semantic decomposition are evaluation references.

The existing local model was reused without downloads:

| Component | Exact local choice |
| --- | --- |
| Transformer | `models/phase4b2/qwen/Qwen-Image-Edit-2509-Q4_K_S.gguf`, 12,204,309,024 bytes |
| Conversion snapshot | `QuantStack/Qwen-Image-Edit-2509-GGUF`, `84a3006979126011422eeeefe0c9485ddf431ef5` |
| Transformer SHA-256 | `07e64364812e527e0e39db3770440f76a5ed4732926c54a0a0e7da841cbe0ce6` |
| Encoder | `models/phase4b2/qwen/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors`, 9,384,670,680 bytes |
| VAE | `models/phase4b2/qwen/qwen_image_vae.safetensors`, 253,806,246 bytes |
| Companion snapshot | `1f12b17be14c89b026c51a91d67c32f84bb047bc`, exact hashes in the unchanged inpainting lock |
| Backend | Headless ComfyUI 0.3.60, `b8730510db30c8858e1e5d8e126ef19eac395560`; GGUF loader `6ea2651e7df66d7585f6ffee804b20e92fb38b8a` |
| Arithmetic | Q4_K_S transformer, BF16 dequantization/patch dtype, native scaled-FP8 vision/text encoder; automatic offloading |
| Environment | Separate `backends/inpainting/qwen-env/uv.lock`, Python 3.12, Torch 2.8.0+cu128 |

The transformer, encoder and VAE are SHA-256 checked before loading; inference
source checkouts must match their pins and have no tracked modifications.
The project-local inventory contains one compatible Qwen Image Edit transformer.
Other Qwen variants were not downloaded. Qwen and the conversion/companion model
cards declare Apache-2.0; ComfyUI is GPL-3.0 and its GGUF loader Apache-2.0.
The converter does not pin its original conversion toolchain; no paired BF16/Q4
quality comparison establishes whether observed defects come from quantization.
See [existing model audit](phase4b2-model-evaluation.md),
[upstream model card](https://huggingface.co/Qwen/Qwen-Image-Edit-2509) and
[conversion card](https://huggingface.co/QuantStack/Qwen-Image-Edit-2509-GGUF).
Current cards were checked during this phase; local execution retains older pins.

## Controlled family and edit boundary

[`recipes/qwen-pose-study.json`](../recipes/qwen-pose-study.json) fixes six prompts:
unchanged neutral, slight right lift, slight left lift, explanation, small wave,
and relaxed torso-open. All are meaningful in this source framing. The original
right forearm crosses the torso; the left arm hangs. Anatomical side wording is
explicitly related to image sides in the prompts; this is not a semantic label
given to the segmentation model.

Settings: seed 1729 independently for every pose, Euler/simple, shift 3, CFG 4,
40 sampling steps, denoise 1.0. Every edit starts from the same image; outputs
are never recursively fed into later poses. The follow-up controls change only
denoise to 0.6 and select neutral/right-lift/torso-open. They were chosen after
the first neutral control failed, not presented as a blinded experiment.

The original alpha is composited over white and the full canvas is resized to
528 × 1024 (long edge 1024, dimensions rounded to 16). This preserves framing
approximately, with slight aspect rounding, but cannot preserve native texture
detail or exact source RGBA. The original file is copied unchanged separately.
The pinned Edit Plus encoder additionally uses its own 384²-area vision encoding
and 1024²-area reference-latent resampling.

A broad body envelope is derived from the raster alpha bounding box: vertical
fractions .22–.88, horizontal expansion .18 of foreground width. There are no
Codel pixel coordinates, artwork IDs or PSD-derived masks in this algorithm.
The normalized envelope is an experimental user-configurable framing assumption,
not a universal body detector. It includes space for moved limbs, lower hair,
torso and part of the skirt. Its bottom boundary can expose a compositing seam.
That seam is an experimental wrapper artifact; style/proportion drift inside the
editable area is separately assessed in raw decodes.

Comfy applies a latent noise mask. Qwen is not claimed to be natively trained
for masked inpainting. Each raw RGB decode is retained; the protected composite
copies source RGB outside the mask exactly. Consequently the unchanged face in
composites is imposed by the wrapper, not independent identity preservation by
Qwen. There is no generated alpha: forcing the original silhouette would clip
new hands and falsely suggest preserved geometry. White pixels and silhouette
changes remain visible in review.

## Screening and exploratory analysis

Development review is image-hash-bound and records identity, clothing, hair,
line style, colors, hands, limbs, torso, framing and useful structure separately.
`accept-exploratory` permits analysis only. It does not grant user approval,
source ownership, runtime acceptance or anatomical correctness. Rejected images
remain visible in the gallery but cannot contribute semantic/voting proposals.

The opt-in analysis uses reusable diagnostics:

1. Same-grid RGB change above 24/255, exceeding the neutral control change by
   16/255. This locates candidate change, not corresponding surfaces. A failed
   neutral control makes this particularly confounded; the raw changes stay visible.
2. Existing local SAM-HQ 19-category parsing on matched image inputs. Its unsided
   `handwear` class does not supply shoulder/elbow/wrist joints or upper/forearm
   classes. Input hashes bind each inference result to its exact RGB image.
3. Connected components of predicted arms; image-space centroids and areas are
   proposals only. A hand-color hint uses the median predicted source-face RGB,
   restricted to predicted arms. It can fail under shading, gloves or skin drift.
4. Strongly changed source-arm pixels predicted as topwear in an accepted edit
   are marked possible torso exposure. No independent hidden torso reference
   exists; changes of semantic prediction alone cannot establish reconstruction.
5. Repeated same-grid torso proposals are counted across accepted edits. This
   is a hypothesis visualization, not confidence calibration: model hallucinations
   are correlated and torso deformation invalidates unregistered pixel voting.

No cross-pose dense correspondence, anatomical joint estimator or actual arm rig
is claimed. A future correspondence method needs explicit occlusion handling,
cycle consistency on unchanged regions, rejection of many-to-one matches and
independent evaluation. Pure color similarity or motion deltas cannot identify
an elbow. Geometric bounds can reject implausible proposals, but cannot verify
hidden anatomy. Repeated generation is not independent corroboration.

## Reproduction

Use fresh destinations. Preparation uses only the main CPU environment; inference
uses the existing isolated Qwen environment and requires host GPU access.

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --frozen
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --frozen --offline --project backends/inpainting/qwen-env
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b7a_poses.py prepare \
  --input runs/references/codel-combined-v1/source/original.png --output runs/NEW-pose-input
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen --offline --project backends/inpainting/qwen-env \
  python scripts/phase4b7a_poses.py generate --prepared runs/NEW-pose-input --output runs/NEW-qwen
```

For the lower-strength controls, add `--denoise 0.6 --poses neutral right-lift torso-open`
to preparation with a separate output, then generate from that directory. Both
preparation and generation retain exact effective settings, image hashes and
code hashes. Generation saves a source snapshot and per-pose timings/VRAM.
Fresh CUDA replay is not promised bitwise deterministic.

If a process is interrupted, retain its directory and use `generate --reuse
runs/PARTIAL` with the exact same prepared input and a fresh output. Completed
pose files, task parameters and preparation hashes are verified before copying;
incomplete poses restart. Reused timing belongs to the original producer and is
labelled separately. The first daemon interruption and its two completed outputs
remain preserved in this phase.

The source semantic baseline uses the unchanged separate worker:

```sh
backends/see-through/.venv/bin/python backends/see-through/worker.py \
  --input runs/NEW-pose-input/input.png --output runs/NEW-sam/source --sam
```

For each development-accepted auxiliary pose, run the same worker on its
`composite.png` into `runs/NEW-sam/POSE-ID`. Do not run rejected images through
the accepted-evidence path. The parser is the previously installed Apache-2.0
`24yearsold/l2d_sam_iter2` snapshot `0b0608310fb7a89e32ecd7397147a249540cf1e7`,
with source `df019de5129d6c4b406587a14c3501669441a783`, separate frozen environment,
strict checkpoint hashes and FP32 inference. No new parser weights are needed.

Generate the standalone static gallery after saving an exact-image development
review (see the retained `development-review.json` for its schema):

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b7a_analysis.py \
  --prepared runs/NEW-pose-input --generated runs/NEW-qwen \
  --review runs/NEW-development-review.json --sam-root runs/NEW-sam \
  --reference runs/references/codel-combined-v1/candidate/face-final/frames/full-neutral.png \
  --layers runs/references/codel-combined-v1/source/layers \
  --output runs/NEW-review
```

The gallery is plain local HTML with relative images; it needs no SillyTavern,
MCP editor, hosted inference, JavaScript dependencies or installation. Large
artifacts, downloaded source and weights stay ignored. No creation defaults change.

For the combined review, generate the primary/lower galleries into fresh
`runs/NEW-review/primary` and `runs/NEW-review/lower`, then collect their summary:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b7a_report.py \
  --root runs/NEW-review --primary runs/NEW-qwen --lower runs/NEW-qwen-low \
  --benchmark runs/NEW-review/benchmark-summary.json
python3 -m http.server 8794 --bind 127.0.0.1 --directory runs/NEW-review
```

Regression commands:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python -m unittest discover -s tests -v
node --test tests/test_rp_talk.mjs tests/test_mouth_invariant.cjs
```
