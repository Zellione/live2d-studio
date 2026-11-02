# Phase 2.5 — See-through evaluation

Completed 2026-11-02. **See-through works locally and produces a basic animated
CC0 portrait, but fails on the cropped Wikipe-tan input. Keep it opt-in, not the
unconditional default backend.** It is the strongest tested candidate for further
real-anime decomposition work; the deterministic baseline remains unchanged.
No custom training or production deployment was performed.

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

Direct license metadata was also inspected from the installed distributions:
Torch/torchvision and NumPy/SciPy use BSD-family terms; Pillow MIT-CMU; OpenCV and
the HF stack/Requests Apache-2.0; einops/PyYAML/psd-tools MIT; pycocotools FreeBSD;
tqdm MPL-2.0 AND MIT; Matplotlib its published license agreement. GIMP is the
already installed GPL tool. Full local dependency notices are retained in their
distributions; audit metadata is `runs/phase2-5-audit/dependency-licenses.json`.

Upstream advertises BF16 at 1280px using approximately 12–16 GB VRAM. Our actual
measurements below confirm operation on this RTX 5090. Upstream keeps both
pipelines in globals: merely running stages one after another does not unload
them. Our worker releases LayerDiff before loading Marigold and runs offline
against verified local snapshots. Upstream source remains unmodified. A restricted
sandbox hides CUDA; the explicitly allowed host GPU runs succeed.

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
character groups. Deeper inspection found inner-eye, outer-eye and mouth children
inside `EyesMouth`; ten visible Girl2 leaf layers were exported. Their visual
content was inspected before defining six coarse evaluation groups. `InnerEyes`
contains iris/pupil/highlights together; `OuterEyes2` combines whites, lines and
brows. No independent fine eyelid/pupil score is claimed.

Input `runs/phase2-5-oga-ground-truth/flat.png` is 1000×1000, SHA-256
`09011ad707e0325c345fdc39da23d9b1a1640c3327c1ba2dfe192001da736f41`.
It is composed from the visible leaves, respecting XCF offsets and clipping to
canvas. Compared with GIMP's group projection: alpha identical; 29 nontransparent
pixels differ by at most one RGB level, plus 24 irrelevant zero-alpha RGB pixels.
Neither XCF metadata nor ground-truth masks enter either inference backend.

## Measured hardware and reproducibility

Separate Python 3.12.14 environment, Torch 2.8.0+cu128, NVIDIA RTX 5090 sm_120;
the main project still uses its unchanged dependency lock. No system changes.
All three downloaded snapshots passed published LFS SHA-256 checks. Approximate
installed footprint: 7.0 GiB worker environment and 13.72 GiB model snapshots,
plus shared uv/cache and local outputs; hard links/cache reuse affect disk usage.

| Run | LayerDiff seconds | Marigold seconds | Total worker seconds | Peak Torch allocated / reserved |
| --- | ---: | ---: | ---: | --- |
| Wikipe-tan BF16 | 114.07 | 8.17 | 124.99 | 11.85 / 16.02 GiB |
| Girl2 BF16 | 103.39 | 8.14 | 113.06 | 11.85 / 16.02 GiB |

Resolution 1280, seed 42, 30 steps for each body/head pass; depth 768, 4 steps.
Marigold itself peaked at 5.95 GiB allocated / 6.70 GiB reserved. Whole-device
sampling at 500 ms reported 19,872 / 19,951 MiB and mean GPU utilization
80.64% / 86.83% (peak 100%). Whole-device values include unrelated GPU allocations;
Torch values are this process. Times include model loading, inference and export,
but exclude downloads, pre-run checksum checks and interpreter imports. These are
single runs, not statistical performance claims. CPU fallback remains the existing
deterministic backend; neural inference is CUDA-only.

A second Girl2 BF16 run produced **21/21 identical bridge files**, including all
19 layer PNGs, normalized source and decomposition metadata. Adapter manifests
are deterministic for identical inputs. This establishes repeatability on this
machine/configuration, not universal bitwise reproducibility across hardware.

## Image quality results

The native-size comparison uses alpha >127, image-side layer placement and
frontmost assigned candidate, excluding baseline `unknown` layers. Resized model
masks use nearest sampling. Composite RGB uses Lanczos back to native size, so
the differences include resampling. Coverage is **candidate assignment**, not
correct semantics. All neuronally generated pixels remain marked generated and
uncertain; no original-image passthrough conceals mistakes.

| Native input | Baseline candidate coverage | See-through candidate coverage | Baseline / See-through RGB MAE |
| --- | ---: | ---: | ---: |
| Wikipe-tan 440² | 22.33% | 76.71% | 0 / 52.02 |
| Girl2 1000² | 54.22% | 99.32% | 0.018 / 8.283 |

Wikipe-tan repeats Phase 2's 145,250 unknown pixels of 187,018 foreground pixels.
See-through produces 15 named layers, yet the face largely becomes a grey/brown
`back hair` surface, while `face` contains a forehead/bang-shaped fragment. The
headwear and some silhouette area disappear. Eyes/irides/eyelashes are recognizable,
but one ear-side split attaches to a tiny border artifact. **Reject as rig input.**
180,898/187,018 foreground composite pixels change. No independent GT exists, so
no Wikipe-tan IoU or semantic correctness percentage is reported.

Girl2 produces 19 layers. Hair, irides, whites, lashes, brows, mouth and face are
visually recognizable. The generated back hair and face extend behind foreground
parts; these are plausible candidate surfaces, not anatomically verified truth.
The visible upper chest is incorrectly baked into `topwear`; neck shading has a
hard seam. Some red hair ribbons disappear or change colour. 309,662/310,977
native foreground composite pixels change; the model does **not** preserve the
visible source exactly. A recognizable neutral composite is not pixel integrity.

Independent XCF evaluation, same six groups for both backends:

| Group | Baseline visible IoU | See-through visible IoU |
| --- | ---: | ---: |
| Hair and hair accessories | 0.0000 | 0.9766 |
| Face, ears, nose | 0.8917 | 0.9573 |
| Eyes and brows | 0.0000 | 0.9026 |
| Mouth | 0.6657 | 0.9078 |
| Neck / exposed upper chest | 0.7038 | **0.1376** |
| Clothing, including sleeves | 0.8587 | 0.8162 |
| Unweighted mean | **0.5200** | **0.7830** |

Visible coarse semantic accuracy: **168,627/310,930 (54.23%)** baseline versus
**279,003/310,930 (89.73%)** See-through. Missing/unmapped pixels: 142,303 versus
2,119. Background false positives: 157 versus 776. Pixel denominator differs
slightly from composite alpha because GT uses frontmost individual alpha >127.
Sleeves (`handwear`) are included in clothing after inspecting their content;
the earlier local `coarse-evaluation.json` excluded sleeves and is superseded by
`coarse-evaluation-reviewed.json`, without discarding the diagnostic history.
Full-layer mean IoU: 0.4961 versus 0.7060, comparing original authored shapes;
those shapes are **not complete hidden anatomy**, so this is not an inpainting
quality score. These results cover one licensed character, not a general dataset.

## Separate SAM experiment

Strict checkpoint loading succeeds without detectron2 or SAM2. FP32 SAM-HQ runs:
4.74 s Wikipe-tan / 2.04 s Girl2 including model construction/loading, peak
4.66 GiB allocated / 5.08 GiB reserved. Very few utilization samples were captured;
they do not characterize the short inference burst reliably.

Candidate foreground coverage: 80.43% / 98.03%; overlapping mask pixels:
417 / 5,187. Wikipe-tan's mouth becomes `neck`, upper hair becomes `topwear`,
with spurious `legwear`: high coverage again fails semantic acceptance.
Girl2 independent coarse per-class visible mean IoU is 0.7936; neck IoU 0.3716.
Masks overlap, so this is **not** exclusive-label accuracy and is not directly
the same ordered-label metric as the decomposition table. SAM supplies 19 coarse
classes, combined eyes and no hidden-pixel reconstruction. Its predictions were
not used as ground truth or fed back to the measured diffusion runs.

## PSD, adapter and actual animation experiment

The generated PSDs reopen as PSD v1, 8-bit RGB documents with transparent raster
layers and integer offsets. Layer opacity is 255 with normal blend modes. The
stored merged preview is RGB (opaque background); it must **not** be used to infer
layer transparency. Recomposition from layers produces RGBA. The psd-tools float
compositor and Pillow bridge composite differ at fractional edges (Girl2: 2,922
pixels change alpha >127 classification); the metric tables explicitly use the
bridge/Pillow path. This is retained in local PSD diagnostics, not hidden by
claiming identical rendering across applications.

Manifest v2 adds generated-alpha, full candidate semantic and uncertainty masks;
v1 remains supported. Verified-original `mask_path` stays empty for neural output.
Hidden-only provenance is unavailable: `hidden_reconstruction_status=unlocalized`,
not a fabricated inpaint mask. Model/source revisions and input transform are
retained. Unknown/uncovered foreground is saved separately. The adapter maps
semantics and character-side suffixes to PSD2Live image sides, preserves PSD order
and offsets, and rejects invalid references/blends/overflow without dropping parts.

The strict public `build` gate remains closed for unreviewed neural manifests.
For the explicitly requested Phase 2.5 experiment, the reviewed Girl2 artwork
request was sent through connected authenticated MCP, with fresh state each time:
Create → Save → PSD export → Reopen → Runtime export. No Phase 1 opaque IDs or
coordinates were reused. Import validation: **19 source layers, 21 imported
layers, 24 meshes, 28 deformers, 20 parameters**. Two lip layers and through-bangs
drawables are PSD2Live-generated. Export warning: draw order renumbered for the
generated front-hair-through-bangs subject; recorded in the local transcript.
Bundle references and Cubism Core 5.0.0 geometry validation pass.

Isolated actual installed SillyTavern/Extension run passes discovery, dropdown,
resource loads, controlled poses and reload. Zero control noise, no unexpected
model HTTP errors or uncaught JS exceptions. Changes against neutral:

| Pose | Changed canvas pixels |
| --- | ---: |
| Left / right eye closed | 1149 / 1574 |
| Both eyes half / fully closed | 1677 / 2723 |
| Mouth half / fully open | 314 / 624 |
| Head X −25 / +25 | 17548 / 17495 |
| Head Y −20 / +20 | 12246 / 12098 |
| Head Z −20 / +20 | 49677 / 49340 |

Frames and cropped pose sheet were visually inspected: actual closed eyelash
lines, contracting white/iris regions, visible half/open mouth and modest head
deformation. **A basic animated real-art prototype is demonstrated without manual
painting.** It uses PSD2Live's procedural eyelash/white deformation and lip shapes;
it does not prove See-through emits blink or lip-sync variants. At half blink,
lids are simplified/flat; the hard neck/chest colour boundary persists during
head motion; brows/lines through bangs alter the original style. Separate pupils,
eyelid skin, teeth/tongue and a richer mouth system remain absent. No text-talk,
emotion trigger, full pose-space quality or production readiness claim is made.
The 2D input mouth is open; the rig's default mouth is closed by design.

## Regression, recommendation and local evidence

40 automated tests pass (33 previous + 7 bridge tests), covering fractional
alpha, provenance/path/order/overwrite gates, deterministic manifests and refusal
to pretend generated pixels are original. Existing Phase 0/1 browser and Core
checks pass with unchanged goldens. Phase 0 turquoise pixels: 104,704 first,
104,703 reload. Phase 1: all controlled poses/expressions; idle Z span 11.2093°,
blink minimum near zero, sampled idle difference 19,855 pixels. These are new
measurements, not substitutions for historical values. The 137 copied/original
server/extension files match their pre-test hashes. Test processes are stopped.

**Recommendation:** retain See-through as an opt-in evaluated backend and the
leading candidate for suitable frontal/bust artwork. Do not make it the default
for arbitrary images yet: one of two inputs fails badly, visible source colours
change, neck semantics are unreliable, and no trusted inpainting mask exists.
Next work should focus on input suitability checks, visible-pixel preservation,
neck/chest separation, suppression of tiny split artifacts and explicit animation
quality gates. No custom segmentation training is justified by this evaluation.

Reproduction: [`backends/see-through/README.md`](../backends/see-through/README.md).
Download/audit milestone: `0ea8a6a`; validated integration: `1cfcf91`. Local-only evidence:

- `runs/phase2-5-audit/`: checkpoint/license audit, tests, comparison reports,
  exact replay and production isolation checks.
- `runs/phase2-5-{wikipe,oga}-neural/`: raw generated PNGs, depth maps, PSDs,
  PSD sidecars, bridge and timing/VRAM metrics. `oga-repeat/`: independent replay.
- `runs/phase2-5-{wikipe,oga}-layers/preview/index.html`: original/composite,
  candidate masks, generated overlay and layer contact sheets.
- `runs/phase2-5-{wikipe,oga}-sam-review/`: coarse parser masks/metrics/previews.
- `runs/phase2-5-oga-ground-truth/`: independent XCF extraction/composition.
- `runs/phase2-5-oga-build/`: editable project, PSD, runtime, import and Core proof.
- `runs/phase2-5-oga-browser/pose-review.png`: actual rendered animation poses.
- `runs/phase2-5-review/index.html`: consolidated original/baseline/neural/pose
  comparison. Compact numerical record is versioned in `docs/benchmarks/phase2-5.json`.

Independent MCP CLI authentication still requires a locally provided environment
token; this phase uses the connected MCP and never reads profile secrets.
**Stopped after Phase 2.5.** No production deployment or Phase 3 expansion.
