# Phase 2.5 — See-through evaluation

Work in progress, 2026-11-02. No neural quality result is claimed by this audit.
Phase 2 baseline and golden fixtures are retained. All inputs, checkpoints and
generated outputs remain local; production SillyTavern is out of scope.

## Audit and approved download plan

Official [source](https://github.com/shitagaki-lab/see-through/tree/df019de5129d6c4b406587a14c3501669441a783)
pinned to `df019de5129d6c4b406587a14c3501669441a783` (Apache-2.0).
Public Hub metadata, cards, LICENSE and NOTICE were fetched before downloading
weights. Exact filenames, sizes and LFS SHA-256 are in
`backends/see-through/models.lock.json`; raw audit is under `runs/phase2-5-audit/`.

| Snapshot | Immutable revision | Total download bytes |
| --- | --- | ---: |
| [LayerDiff V3](https://huggingface.co/layerdifforg/seethroughv0.0.2_layerdiff3d) | `4477e6ce529bc6a141732e1a55a4932176db3b89` | 10,159,649,987 |
| [Anime Marigold](https://huggingface.co/24yearsold/seethroughv0.0.1_marigold) | `4f4ffc46050b6feb764b628859968a26e76e6b6a` | 3,276,274,643 |
| [SAM-HQ 19-part parser](https://huggingface.co/24yearsold/l2d_sam_iter2) | `0b0608310fb7a89e32ecd7397147a249540cf1e7` | 1,294,783,156 |

Main pipeline: 13,435,924,630 bytes (12.51 GiB); all three: 14,730,707,786
bytes. Sizes include configuration/tokenizer/license files, not just tensors;
wire traffic/retries can differ. Plan 40 GiB free including the separate Python
environment, download cache and benchmark outputs (budget, not measured usage).
User explicitly approved **all three models** after receiving this plan.

The two diffusion snapshots inherit OpenRAIL++ use conditions. LayerDiff also
includes LayerDiffuse OpenRAIL-M and an MIT VAE; Apache-2.0 covers the authors'
contributions. Marigold inherits Stable Diffusion 2 restrictions. SAM-HQ weights
are Apache-2.0. See each pinned snapshot's LICENSE/NOTICE; the code license alone
does not describe the weight licenses. Model cards permit commercial use subject
to those conditions. This experiment redistributes neither weights nor artwork.

## Dependency and execution boundary

`backends/see-through/pyproject.toml` and its independent `uv.lock` specify a
Python 3.12 headless worker. Upstream pins Torch 2.8.0+cu128 / torchvision 0.23.0,
Diffusers 0.37.0, Transformers 5.0.0, HF Hub 1.7.2, NumPy 2.2.6 and Pillow 12.1.1.
These differ from Phase 2 and must not replace its environment. No conda, system
pip, kernel, driver or system CUDA change is required by the proposed path.
Qt/UI, training, detectron2, mmcv and SAM2 tiers are not imported by the main
inference path and are omitted. The semantic parser uses vendored SAM-HQ, not
the optional language-guided SAM2 package. Numerical/IO dependencies use their
BSD/MIT/Apache licenses; Torch CUDA wheels bundle separately licensed NVIDIA
runtime libraries. Exact transitive wheels/hashes are recorded by uv.

Upstream advertises BF16 at 1280px using approximately 12–16 GB VRAM; this is
**not yet a local measurement**. 32 GB looks sufficient for evaluation, not a
guarantee. Upstream keeps both pipelines in globals: merely running stages one
after another does not unload them. Our worker will release LayerDiff before
loading Marigold, run offline against local snapshots and measure both stages.

## Programmatic and output audit

`inference/scripts/inference_psd.py` calls `apply_layerdiff`, `apply_marigold`,
then `further_extr`. There is no editor interaction or SAM requirement. V3 uses
two diffusion passes (body, then cropped head), 23 final semantic categories;
the temporary `head` output is replaced by finer head layers. Inputs are padded
and resized to square; this transform must be retained for fair comparisons.
Model output is generated RGBA, not a protected-pixel inpainting operation.

`save_psd` creates 8-bit raster PSD layers with cropped offsets, semantic names,
per-pixel transparency and layer opacity 255. Depth median sorts back to front;
a second grayscale depth PSD and a JSON sidecar are produced. Median-depth
ordering is a heuristic, not independently validated drawing order. PNG alpha
and depth maps remain available before PSD conversion. Optimized PNGs can be
saved by running extraction without the PSD flag. No trusted observed/hidden
pixel provenance mask is emitted. Nose/mouth RGB is replaced with resized input
RGB during postprocessing, which does not prove correct semantics or geometry.

Optional `--tblr_split` splits connected components. Upstream `-r` means image
left and `-l` image right, opposite our manifest side labels. It may discard
smaller components or fail when contours connect; splitting is not a semantic
confidence score. V3 separates irides, eyewhite, eyelash and eyebrow, but lacks
separate pupils, eyelid skin, blink variants, mouth interior/closed variants and
validated concealed facial geometry. No rig acceptance follows from a PSD export.

## Licensed benchmark preparation

A: unchanged Kasuga Wikipe-tan from Phase 2 (CC BY-SA 3.0), same original hash.
B: [stevenburrow's CC0 portraits](https://opengameart.org/content/anime-girl-and-boy-portraits),
archive `allanime-11-28-2020.zip`, SHA-256
`616438aaf0bb1f5925b164486f351ee4a612952054de7d3b6900bf121f3a5c05`.
Downloaded into `assets/references/oga-portraits/`. Installed GIMP 3.2.6 loads
the XCF headlessly with a separate project-local profile. Source includes four
character groups; eyes and mouth are combined, so fine ocular ground truth
cannot be claimed from layer names alone. Extraction/evaluation remains pending.
