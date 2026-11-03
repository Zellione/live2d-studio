# Phase 4B.2 — local neural facial inpainting

Continued from `71ef58e`. **Retain deterministic reconstruction.** Local LaMa and
quantized Qwen Image Edit 2509 were executed on the RTX 5090. Qwen produced smoother
fully closed lashes in Sara stills, but dense actual-runtime blinking exposed a
doubled contour. No tested neural/hybrid candidate improved animation without a
visual regression. Every rendered candidate is rejected by development review;
none replaces accepted Sara/Girl2 artwork or receives user/production approval.

[Model investigation and exact provenance](phase4b2-model-evaluation.md),
[worker/CLI reproduction](../backends/inpainting/README.md),
[benchmark](benchmarks/phase4b2.json).
The local review entry point is `runs/phase4b2-review-release/index.html`.

## What ran

- **32 local crop tasks**: LaMa at native and 2× scale on Sara/Girl2; Qwen Q4_K_S
  with an FP8 vision/text encoder on both; two 40-step Sara conditioning controls;
  a small held-out skin patch on licensed Boy1 at native/rescaled resolution.
- **Five fresh editable PSD2Live projects**, with PSD, project, mesh/parameter
  inspections, MCP transcripts and Cubism exports: Sara LaMa, Sara Qwen eyes/mouth,
  Sara closed-eye hybrid, Girl2 LaMa and Girl2 Qwen. Original See-through/SAM outputs
  were reused; expensive decomposition was not rerun.
- **57 matched actual Core poses** per rendered model/baseline: independent eyes
  at 0/.25/.5/.75/1, mouth range, smile/frown, seven expressions, talking,
  head/gaze, combined poses and reset. Sara additionally has **122-frame** baseline,
  LaMa, Qwen and hybrid transition suites: ten talk samples per expression,
  expression fades, blink/mouth ramps in 0.1 increments and exact neutral returns.
- Main Python regressions and JavaScript talk tests pass. Exact test count and logs
  are recorded in the benchmark. The additional tests cover protected RGBA/alpha,
  missing/open-mouth feature fallback, review-bound hybrids, changed cache inputs,
  parameters/weights/masks, and a no-model-load deterministic fallback.

These are single-image experiments. Neither inference nor crop preparation reads
other expression sprites, XCF evaluation layers or benchmark truth. The Boy1 truth
image is kept separately for evaluation. All model inference is local/offline.
No system drivers, accepted model pins, training or production SillyTavern changed.

## Visual decisions by region

| Region | Result | Decision |
| --- | --- | --- |
| Concealed skin behind eyes | LaMa commonly reconstructs an eye. Qwen conditioned on the original open-eye crop also retains one. A 40-step control initialized with deterministic blank skin avoids that error but adds no established improvement over the existing fill. | Keep deterministic skin. The controlled reference matters; do not mislabel the first failure as a universal inability to remove eyes. |
| Fully closed lashes | Qwen draws smoother curved lashes on Sara. Girl2 gains inconsistent left/right lash density and changed line style. | Stills alone are insufficient; reject generalized use. |
| Intermediate closure | At **0.1 openness**, Sara's new curved lash and the shrinking source contour form a loop/double contour during crossfade. The quarter-step suite missed it. The hybrid has the same failure. | Reject both Sara neural selections. A future method needs contour/geometry correspondence during transitions, not just another attractive closed-eye PNG. |
| Half-lid artwork | Initial closed-eye-conditioned edit invents a larger open eye. The stronger 40-step open-eye-conditioned control produces a heavy dark lid/changed contour. | Reject; no intermediate raster was silently installed. Existing geometric half lids remain limited. |
| Mouth interior, corners and lip transition | Qwen shades the cavity and changes the apparent lip shape, but reduces visible opening in actual talking. LaMa makes the cavity pale. Preserved deterministic boundaries do not establish a better lip transition. | Keep original deterministic cavity/source contour. Already-open Girl2 mouth remains on its existing geometry-based branch. No teeth/tongue claim. |
| Small missing skin | Boy1 native-scale RGB MAE: deterministic **0**, LaMa **1.4704/255**, 197 removed pixels. This was a flat, source-owned patch. | No neural advantage. It is a synthetic removal test on real licensed artwork, not concealed-anatomy truth. |
| Hidden face exposed by head motion | Existing source/generated face support remains. New eye backing/closed patches were tested under combined head/blink/talk; they do not solve broader hidden geometry or hair gaps. | No improved hidden-face geometry claim; keep prior limitations and gates. |

Duplicate contours were assessed by development visual inspection of matched frames,
not by treating an edge/component count as an anatomical detector. The retained
`blink-ramp-9` frames show the decisive 0.1-openness defect. There is no blinded
professional-quality score or new user acceptance. All five formal rejection
records are bound to their exact runtime quality reports.

## Measurements and their limits

| Run group | Peak Torch allocated | Peak reserved | Batch wall time |
| --- | ---: | ---: | ---: |
| LaMa Sara, native / 2×, six crops each | 0.220 / 0.289 GiB | 0.244 / 0.434 GiB | 0.88 / 3.06 s |
| LaMa Girl2, native / 2×, four crops each | 0.307 / 0.643 GiB | 0.467 / 1.324 GiB | 0.84 / 1.10 s |
| Qwen Sara, five 20-step crops | 20.394 GiB | 21.881 GiB | 207.70 s |
| Qwen Girl2, three 20-step crops | 20.362 GiB | 21.857 GiB | 138.19 s |
| Qwen Sara controls, two 40-step crops | 20.394 GiB | 21.895 GiB | 160.93 s |

Qwen's successful 20-step tasks took approximately 35–44 seconds each. A sampled
`nvidia-smi` reading during inference was 25,053 MiB total GPU usage, including the
desktop; it is not a measured process peak. Torch measurements include allocations
from load and inference, with cumulative peaks per batch. Qwen had about 8.5 MiB
of residual allocations after explicit model unload; process exit releases the
remaining context. The workers do not remain running between batches.

The quantized path **does fit and run on the 32 GB 5090**. This finding does not
establish a 16 GB benchmark. Full precision, FP8-transformer, NVFP4 and INT4 variants
were investigated, but only Q4_K_S/FP8-encoder was executed; there is no paired
full-precision comparison to isolate quantization degradation. SDXL was inspected
but not downloaded/run. No extra model was added just to increase the comparison.

All 32 task composites preserve RGBA outside masks and alpha everywhere exactly.
Original facial source/layer/mask files are byte-identical to their corresponding
Phase 4B.1 baseline. Existing source-composite exact fractions remain **99.7713%**
for Sara and **99.8855%** for Girl2; these are not replaced with a false 100% rendered
fidelity claim. Every frozen Phase 4B.1 stage inventory and **41 accepted Phase
3/3.1 files** was revalidated unchanged. Replaying the hybrid with the final cache
implementation reproduces all its PNGs exactly.

The selected Qwen and hybrid neutral frames are byte-identical to their respective
baselines. LaMa's always-visible backing changes 2,594 Sara / 525 Girl2 neutral
pixels despite exact source-layer preservation. Final Sara hole counts stay at
102 neutral / 4,357 maximum, with at most 79 small detached pixels; Girl2 stays at
124 / 267 holes and four small detached pixels. These counts include legitimate
details and do not prove good eyes. All completed suites have zero nonfinite
geometry, out-of-tolerance opacity, external requests or resource failures.
Raw float32 opacity excursions are retained; the unchanged eight-ULP tolerance
is not relaxed to obtain a pass.

## Optional implementation and fallback

`create --reconstruction deterministic` remains the default and needs no new
environment or model. `neural` uses an explicit local configuration. `hybrid`
requires an image review that names selected features and pins input/mask/output
hashes; it blends only those interiors while preserving deterministic boundaries.
Review is character/evidence-specific, not a Sara-coordinate heuristic. An empty
review selection takes the deterministic fallback without loading a model.
There is **no recommended accepted neural selection** from this phase.

Models load only for requested inference and are unloaded afterwards. Verified
cached predictions can be replayed without GPU inference; original producer
measurements remain identified as reused. The source layers are immutable to the
neural stage. Generated alternatives carry masks, hashes and uncertain boundaries,
including generated skin in closed-lash patches. A review of still images cannot
bypass existing semantic/runtime/visual creation gates. No coding agent is needed
to prepare crops, infer, create a rig or open its standalone viewer.

## Rejected attempts and reproduction

Retain `runs/phase4b2-*` in full. Failures include sandbox CUDA/browser refusals,
the first Qwen VAE singleton-frame conversion failure (sampling had succeeded),
and a first Girl2 baseline run that failed a talking assertion. Its fresh repeat
passed; this is recorded as a timing-sensitive failure, not erased or hidden by
loosening the test. The Boy1 2× run has blacked-out-mask resampling contamination
(MAE 75.5956); it is excluded from the clean model comparison. Native replay
isolates that confound. LaMa's original TorchScript and safetensors implementation
match exactly on the verified parity crop, with all 989 tensors equal.

Run new experiments in fresh directories using the worker README and:

```sh
uv run --frozen python scripts/phase4b2_crops.py \
  --baseline runs/phase4b1-sara --output runs/NEW-lama --model lama --scale 1
uv run --frozen python scripts/phase4b2_crops.py \
  --baseline runs/phase4b1-sara --output runs/NEW-qwen-controls --model qwen --controlled
uv run --frozen python scripts/phase4b2_holdout.py \
  --layers runs/phase2-6-boy1-release --output runs/NEW-boy1-holdout
uv run --frozen python scripts/phase4b2_evidence.py \
  --output runs/NEW-phase4b2-review --benchmark runs/NEW-phase4b2-review/benchmark.json
```

The evidence collector references retained experiment paths, verifies artifacts
and tests, and produces the review gallery; it is not an inference dependency.
Its task reports preserve exact seeds, prompts, scales, step counts and model pins.
The controlled-crop preparation script reproduces the inspected input PNGs and
parameters exactly. Generated files/weights/PSDs/runtime/recordings remain outside
Git. Stop after Phase 4B.2; production restrictions and training prohibition remain.
