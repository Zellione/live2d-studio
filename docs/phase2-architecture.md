# Phase 2 architecture and reproducibility

Phase 2 is a working **flat-colour baseline**, not a general anime part parser.
The modules deliberately separate recognition, extraction, reconstruction, editor
import and runtime acceptance. A successful neutral composite proves none of the
later semantic/animation gates. No production installation is automated.

## Actual stages

1. `pipeline.prepare`: decode PNG/WebP/JPEG, apply EXIF orientation to a separate
   normalized copy, retain original bytes and SHA-256, reject existing output.
   CPU MVP limit: 4,194,304 pixels. No input resizing or original modification.
2. `segmentation`: preserve alpha; for opaque input, flood only a nearly uniform
   border-connected background (95% border agreement, channel tolerance 12).
   Quantize RGB into 16-value bins, examine 48 most common bins, up to four
   components per bin and 96 total. Overflow remains `unknown`. Infer a warm
   face candidate, paired white eyes and nearby dark iris/lid/brow candidates,
   nose/mouth/neck/clothing using relative geometry. No fixed image coordinates,
   fixture colour table, source-layer metadata or model weights are read.
3. `reconstruction`: fill enclosed holes only when their area is at most 25% of
   observed support. Eye-white rows additionally fill between observed white
   endpoints, with at most 100% additional area. Nearest observed pixel provides
   the fill colour. No extension of unobserved outer contours. Original visible
   RGBA values remain exact. Alternate closed eyes are translated detected lids;
   the closed mouth is a narrow strip sampled from the detected mouth. These
   alternates are **generated**, not recognized; their masks mark every pixel as
   reconstructed and they are excluded from the default composite.
4. `manifest`: crop each RGBA layer and both masks to its bounds; persist content
   hashes, source/provenance, placement and increasing Z order. Validate modes,
   dimensions, alpha union, paths/symlinks, hashes and visible original pixels.
5. `preview`: offline HTML with original/composite, coloured visible masks,
   reconstruction overlay and labelled contact sheet. Warnings and attribution
   are included. No external resources or image-editing software required.
6. `mcp`: convert the manifest to `project_create_artwork`. Inspect fresh project
   state before each mutation; never discard unsaved editor work. Wait for jobs,
   record local diagnostics, verify imported names/roles/sides, mesh/deformer
   counts and basic parameter IDs. Save source project, export PSD, reopen and
   export runtime. Reuse the Phase 0 bundle validator. Never replay Phase 1
   opaque IDs, geometry coordinates or Mood edits against an unknown character.

The build gate rejects missing expected roles or an `unknown` layer. All detected
roles still need visual review: a false semantic assignment can pass a structural
gate. Standard Cubism parameter IDs describe the generated runtime contract;
deformer/layer IDs are inspected, not copied from the golden fixture.

## Manifest v1 contract

`layer_manifest.json` is deterministic for identical decoded input, rights text
and pinned algorithm/dependency versions. No timestamp, absolute path, random ID
or timing is embedded. Run-dependent measurements live in `metrics.json`.

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer 1; unknown versions rejected |
| `canvas` | Integer width/height, top-left origin, pixel units |
| `sources[]` | Original relative path/hash, normalized path/hash, rights string, stable source ID |
| `layers[].id` / `name` | Stable role/side ID and readable name; unique within project |
| `role` / `side` | PSD2Live role enum; left/right refer to image sides as in Phase 1 |
| `z_order` | Strictly increasing back-to-front order; adapter preserves this array order |
| `x,y,width,height` | Cropped raster placement/dimensions inside the canvas |
| `rgba_path` | Straight-alpha RGBA PNG, RGB zero where alpha is zero |
| `mask_path` | L PNG of observed pixels, preserving fractional input alpha |
| `reconstructed_mask_path` | Binary L PNG of filled/generated pixels; disjoint from observed mask |
| `sha256` | Digest for each layer/mask file |
| `source_id`, `provenance` | Link to original and versioned algorithms |
| `confidence`, `quality_status` | Uncalibrated candidate score 0.5 or unresolved/generated 0; never a probability claim |
| `default_visible` | Excludes mutually exclusive generated closed-eye/mouth variants from preview |
| `reconstructed_pixels` | Count of marked pixels, not an aesthetic score |
| `missing_regions`, `warnings` | Explicit gaps and review requirements |

The source list reserves multi-reference architecture; v1 rejects more than one
source because fusion is not implemented. Adding a backend means replacing the
`segment(rgba)` stage, returning `Region` records, then passing the same independent
extraction/validation gates. Ground truth is never an inference argument.

## Installation and commands

Python 3.13.15, `uv.lock` and exact direct versions are committed. Use project caches:

```bash
export UV_CACHE_DIR="$PWD/.cache/uv"
export HF_HOME="$PWD/.cache/huggingface"
export TORCH_HOME="$PWD/.cache/torch"
uv sync --frozen
uv run --frozen live2d-studio flatten-fixture \
  --art tests/fixtures/phase1/final/art --output runs/example-ground-truth
uv run --frozen live2d-studio prepare \
  --input runs/example-ground-truth/flat.png --output runs/example-layers \
  --rights original-repository-artwork
uv run --frozen live2d-studio inspect --project runs/example-layers
uv run --frozen live2d-studio evaluate \
  --project runs/example-layers --ground-truth runs/example-ground-truth
uv run --frozen live2d-studio reconstruct \
  --project runs/example-layers --output runs/example-reconstruction
uv run --frozen python -m unittest discover -s tests -v
```

Open `runs/example-layers/preview/index.html` locally. For another full run choose
a fresh output. `reconstruct` reuses saved visible masks without rerunning semantic
analysis, writes a fresh project, and accepts `--max-fill-fraction` (0..1; eye-white
row filling retains its separate 100% cap). This is bounded fill, not diffusion.
Image functions are independently callable; `inspect` and `evaluate` are read-only.
Failed runs remain available for diagnosis and must not be silently overwritten.

Optional CUDA probe (large CUDA **library** download, no model weights):

```bash
uv sync --frozen --extra gpu
uv run --frozen --extra gpu live2d-studio doctor
```

Torch is pinned to 2.9.0 from the explicit cu128 index; the lock includes hashes
and CUDA library versions. `doctor` selects a 5090 when present, executes and
synchronizes a matrix multiply, records compute capability/time/peak allocated
VRAM, then releases tensors. Restricted sandboxes can hide the GPU. CPU baseline
works without Torch; image processing has no GPU inference backend yet. A future
model backend should load segmentation and inpainting sequentially, batch 1,
unload each model before the next and record real allocation metrics. This policy
is not a claim that those model workers have been implemented.

Standalone MCP, with token entered locally and never supplied to chat:

```bash
bash <<'BASH'
read -r -s -p 'PSD2Live MCP token: ' PSD2LIVE_MCP_TOKEN </dev/tty
export PSD2LIVE_MCP_TOKEN
export UV_CACHE_DIR="$PWD/.cache/uv"
uv run --frozen live2d-studio mcp-check
uv run --frozen live2d-studio build \
  --project runs/example-layers --output runs/example-build
unset PSD2LIVE_MCP_TOKEN
BASH
```

Endpoint defaults to `http://127.0.0.1:23871/mcp`. Other hosts, URL credentials,
query tokens, proxies and redirects are rejected. `mcp-check` is read-only. The
connected MCP path was exercised; the authenticated standalone CLI still needs
an environment-supplied token. Dummy-credential transport tests do not close that
live authentication gate. `scripts/build_phase1.py` uses this same transport.

## Model assessment (2026-11-02)

No neural image model was installed or downloaded. Repository/model-card review
does not establish anime quality or actual GPU memory usage.

| Candidate | License/version and size | Suitability and decision |
| --- | --- | --- |
| SAM 2.1 Hiera tiny / large | Apache-2.0 checkpoints; 38.9M / 224.4M parameters, roughly 156 / 898 MB FP32 parameter storage; actual runtime VRAM unmeasured | Promptable segmentation, not semantic anime part parsing. Test only after reliable semantic prompts exist; not selected for this baseline. |
| SkyTNT anime-segmentation (ISNet etc.) | Repository Apache-2.0; no checkpoint/revision selected | Foreground extraction is useful for complex backgrounds, but does not solve iris/lid/hair-part assignment. Check exact weight provenance before adoption. |
| SDXL Inpainting 0.1 | OpenRAIL++; reviewed HF metadata reports 2,567,478,084 F32 parameters (~10.27 GB for that weight set, not total pipeline/VRAM) | Masked 1024px inpainting; model card focuses on photorealism. Anime identity/contour preservation unproven. Not selected without a licensed test benchmark and masked-pixel acceptance criteria. |
| Deterministic components + nearest continuation | Project algorithms 0.2.0; no weights | Selected: cheap, inspectable, deterministic, adequate only for controlled flat colours. Actual limits measured in results. |

Primary sources: [SAM2 code/model licensing and benchmark table](https://github.com/facebookresearch/sam2),
[Anime Segmentation](https://github.com/SkyTNT/anime-segmentation),
[SDXL Inpainting model card](https://huggingface.co/diffusers/stable-diffusion-xl-1.0-inpainting-0.1).
Parameter storage above is arithmetic, **not measured VRAM**. Before any future
weight download, pin repository revision and checkpoint digest, review its exact
license, size and intended benchmark. No model revision is claimed as installed.
Blackwell/cu128 support was introduced in [PyTorch 2.7](https://pytorch.org/blog/pytorch-2-7/);
this project independently tested its pinned 2.9.0 wheel on the actual device.

Installed direct packages: Pillow 12.0.0 (MIT-CMU), NumPy 2.3.4 and SciPy 1.16.3
(BSD-3-Clause, wheels also contain third-party notices), optional Torch 2.9.0+cu128
(BSD-3-Clause; bundled NVIDIA libraries have their own proprietary terms), pytest
8.4.2 (MIT), build-only Hatchling 1.27.0 (MIT). Python is PSF-licensed. Exact
transitive versions/hashes are in `uv.lock`; no system pip, driver or CUDA changes.

## Real-art test interface

`prepare --input LOCAL_FILE --rights 'author; license; source URL; allowed use'`
uses the same stages as the synthetic benchmark. `evaluate` accepts independent
full-canvas L masks via `ground_truth.json` (`layers: [{id,path,visible_path}]`).
Real artwork without validated masks receives no invented IoU score.

The tested image is [Wikipe-tan face by Kasuga](https://commons.wikimedia.org/wiki/File:Wikipe-tan_face.png),
licensed under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/),
440×440 PNG, SHA-256 `6035d94f0d446f87558fea4af285a014a5bc4b517eb605a1b6a2f4c88da35df1`.
The original is unchanged under `assets/references/wikipe-tan/`; derived layers
are local under `runs/phase2-wikipe-tan-release/`. No foreign image is committed.
It is a cropped, tilted face, not an ideal frontal bust; no layer ground truth
was available. Attribution, license URL and transformation notice accompany the
local provenance JSON and project rights field. Any redistribution of derived
images must retain attribution and applicable ShareAlike terms.

Re-download to a new local destination, verify SHA-256, then run the same CLI:

```bash
mkdir -p assets/references/wikipe-tan-repeat
curl --fail --location \
  --output assets/references/wikipe-tan-repeat/original.png \
  https://upload.wikimedia.org/wikipedia/commons/d/db/Wikipe-tan_face.png
sha256sum assets/references/wikipe-tan-repeat/original.png
uv run --frozen live2d-studio prepare \
  --input assets/references/wikipe-tan-repeat/original.png \
  --output runs/wikipe-tan-repeat \
  --rights 'Kasuga; CC-BY-SA-3.0; https://commons.wikimedia.org/wiki/File:Wikipe-tan_face.png; derived candidate layers'
```

A further licensed source with layered XCF exists: [stevenburrow's CC0 portraits](https://opengameart.org/content/anime-girl-and-boy-portraits).
It was identified, not downloaded/evaluated; no claim of validated ground truth.
