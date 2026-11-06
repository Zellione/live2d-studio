# Phase 4B.7a — Qwen auxiliary pose feasibility

Continued from `6205158`. **No demonstrated improvement in arm/body articulation
readiness with the tested local configuration.** Qwen can change the pose, but
the stronger edits lose required source consistency. Lower strength preserves
the illustration more closely while leaving its original arm occlusion intact.
This is a bounded negative feasibility result, not proof that all Qwen-based
pose expansion is impossible.

[Protocol, exact model pins and reproduction](phase4b7a-qwen-feasibility.md) ·
[benchmark](benchmarks/phase4b7a.json).

Local review: `runs/phase4b7a-review-release/index.html`, served at
[127.0.0.1:8794](http://127.0.0.1:8794/). It includes all nine generated images,
source comparisons, raw decodes, protected composites, change overlays,
accepted/rejected decisions, semantic proposals, frozen arm-layer comparison and
a capture of the reviewed combined runtime. No SillyTavern setup is needed.

## What ran

- The same unmodified, hash-verified Codel3 image as `codel-combined-v1` was the
  only generation reference. No layered PSD or other character tiles entered
  inference. Source: LisadiKaprio, CC BY 4.0, original 1078 × 2089 framing.
- Existing local **Qwen Image Edit 2509 Q4_K_S**, separate **FP8 Qwen2.5-VL-7B
  encoder**, Qwen VAE, pinned headless ComfyUI/GGUF backend, RTX 5090. No weights
  were downloaded; installed Qwen language models are not compatible substitutes.
- Six required poses at denoise **1.0**: neutral copy, right lift, left lift,
  explanation, small wave and torso-open. No requested pose needed replacement.
- Three follow-up controls at denoise **0.6**: neutral, right lift and torso-open.
  These changed only strength and pose subset, with the same seed/prompts/mask.
  They were selected after the first neutral failed, not a blinded holdout.
- All use the same 528 × 1024 RGB source composite over white, seed 1729, CFG 4,
  Euler/simple, shift 3, 40 sampling steps, and a raster-derived broad body mask.
  The original full-resolution RGBA stays unchanged separately. There is no
  generated alpha or native-resolution detail claim.
- The existing 19-category SAM-HQ parser ran on the matching source RGB and the
  **two** outputs passing limited consistency screening. Rejected outputs were
  excluded from semantic proposals and reconstruction voting.

## Separate gates and per-pose findings

“Accepted” below means development acceptance for coarse exploratory image
analysis only. It is not user acceptance of new artwork or approval for a rig.

| Pose / strength | Screening | New information / limitation |
| --- | --- | --- |
| Neutral / 1.0 | Reject | Alters crossing, sleeve attachment and torso despite no-change instruction. Failed consistency baseline. |
| Right lift / 1.0 | Reject | Uncrosses both arms and adds a hole/exposed skin in the left sleeve. Apparent bilateral gaps cannot be trusted. |
| Left lift / 1.0 | Reject | Changes the opposite arm, sleeve and torso. Easier-looking silhouettes do not preserve the source. |
| Explanation / 1.0 | Reject | Lowers both arms instead of making the requested palm-up gesture; redraws clothing and proportions. |
| Small wave / 1.0 | Reject | Gesture and elbow bend are readable, but raised fingers are malformed/clipped; lower hair and torso drift. |
| Torso-open / 1.0 | Reject | Suggests an open front but changes neck/collar, shoulder width, bust/waist and truncates hands. |
| Neutral / 0.6 | Accept, consistency control only | Source-like pose/costume; crossed-hand fingers still change. No additional structure. |
| Right lift / 0.6 | Reject | Arm remains crossed; palm disappears behind the opposite sleeve and cloth wrinkles change. No useful separation. |
| Torso-open / 0.6 | Accept, near-copy only | Visually consistent, but retains the original crossing and hanging arm. The requested opening did not happen. |

**Nine unique completed images: two coarse-consistent near-copies, zero
segmentation-helpful accepted pose edits, zero reliable articulation examples.**
The stronger wave is a readable gesture, but not a consistent accepted derivative.
These distinctions prevent a nice-looking or clearly posed image from passing
the actual question about source-compatible structural evidence.

The face is protected by the composite mask. Zero outside-mask changes is an
implementation guarantee, **not** proof of Qwen identity preservation. Raw
decodes are available beside composites. The rectangular body envelope causes
visible skirt seams and clips some displaced fingers/hands; those are wrapper
limitations. Major torso, clothing and lower-hair repainting inside the editable
region remains a separate failure. No failure is attributed to quantization alone.

## Segmentation and articulation usefulness

The frozen decomposition still contains one unsided `handwear` layer with
**260,082 observed pixels and zero generated hidden pixels**. It includes both
arms/hands; its name does not establish anatomical ownership. The reviewed
runtime supplies accepted facial/head/hair/breathing behavior but no independent
arm channels or new views of concealed body regions. Nothing was changed in it.

At the matched 528 × 1024 analysis grid:

| Image | Substantial arm components | Largest predicted arm component | Possible newly exposed torso pixels |
| --- | ---: | ---: | ---: |
| Source | 1 | 53,333 | 0 |
| Accepted neutral / 0.6 | 1 | 53,066 | 0 |
| Accepted torso-open / 0.6 | 1 | 53,200 | 0 |

“Substantial” means at least 5% of predicted arm area and at least 32 pixels.
Source also has a 56-pixel fragment; it is not a second anatomical arm. Counts
are parser diagnostics, not semantic accuracy or independent ground truth.
Raw component bounds, overlap counts and input-bound parser reports remain local.

- **Left/right ownership:** neither accepted image breaks the large connected
  arm component. No reliable cross-pose side correspondence is gained.
- **Upper arm/forearm/hand and shoulder/elbow:** the parser does not represent
  these joints/subclasses. Accepted poses retain the original sleeve/arm overlap.
  No new joint evidence or validated geometry is available.
- **Hands:** color hints inside predicted arms locate the already visible hand
  areas, with additional small fragments. The two main source hints have
  5,938 / 3,645 pixels; neutral has 6,054 / 1,861, torso-open 5,999 / 3,535.
  Neutral's changed fingers reduce the second hint, rather than demonstrating
  better recovery. These are color-component sizes, not hand-mask IoU or fingers.
- **Hidden torso/clothing:** accepted images produce zero candidate arm-to-topwear
  exposure pixels under the recorded delta/semantic rule. Rejected open-front
  images invent clothing but cannot establish its source-compatible shape.
- **Front/back layering:** the same visible crossing remains in accepted outputs.
  New ordering in rejected outputs is not reliable evidence about the canonical
  image. No hidden backside or disocclusion truth is supplied.

The prototype evaluates generic same-grid deltas, semantic transitions, connected
components, skin-color hints and repeated exposure proposals. It exports only
diagnostics; no PSD, arm layer replacement, mesh or gesture rig was built. There
is one accepted non-neutral voting input, zero candidate torso exposure and zero
repeated exposure pixels. Empty evidence is not a successful reconstruction.

The full-strength neutral control changes editable RGB by mean **37.21/255**;
the lower-strength neutral is **4.03/255**. These are photometric differences,
not identity scores. Subtracting a failed neutral control is confounded, so primary
delta overlays serve only to show what changed; they do not rescue rejected poses.

## Runtime, memory and reproducibility

| Pose | Denoise 1.0 seconds | Denoise 0.6 seconds |
| --- | ---: | ---: |
| Neutral | 92.10 | 80.06 |
| Right lift | 79.81 | 79.50 |
| Left lift | 81.34 | — |
| Explanation | 79.42 | — |
| Wave | 79.59 | — |
| Torso-open | 80.00 | 79.55 |

Peak Torch allocated VRAM is **21.442 GiB**; peak reserved is **23.127 GiB**.
These are measured per-task peaks, not a sampled whole-device peak. Other GPU
processes are excluded. Model loading/hash verification was 17.19 seconds in the
first process, 10.90 seconds after recovery and 10.94 seconds for the controls.
Timings include conditioning, sampling, decode and artifact writes, exclude
user/development review, and are not a 16 GB or other-quantization benchmark.
The three SAM operations took 2.00–2.08 seconds each, peak allocated **4.662 GiB**.

The tool server restarted after two completed primary poses. Both were
hash-verified and copied to a fresh recovery run; the interrupted left-lift
restarted. `runs/phase4b7a-qwen-v1` retains its partial report unchanged, and
`runs/phase4b7a-audit/interruption.json` explains its historical “running” status.
Recovered records identify reused timings and the original producer report.
A mistyped control-launch flag failed before inference; its stderr remains
beside the successful retry. No generated rejection was deleted or silently rerun
until it passed.

## Preservation, checks and recommended next step

- The full Python suite passes **156 tests**. The final four pose-study tests and
  six frozen-reference tests pass after the last helper changes. Both JS suites
  (`test_rp_talk.mjs`, `test_mouth_invariant.cjs`) pass.
- Before/after reference tests verify the immutable manifest and **1,806 payload
  files**, original candidate, source, limited acceptance and historical failures.
  An additional **1,275 sealed first-run files** verify unchanged.
- Original artwork, reference manifest/runtime, package/model pins, existing
  creation defaults and production SillyTavern remain unchanged. No training,
  model downloads, deployment or host setting changes occurred.
- New code is confined to the opt-in study scripts, recipe, tests and reports.
  Large artifacts and images stay in ignored `runs/` directories.

**Do not start final arm rigging from these outputs.** The next useful experiment
would keep the same local model and test explicit pose/keypoint guidance plus an
edit envelope that accommodates the complete hand while protecting source
clothing/head boundaries. Evaluate a no-change control and one genuinely small
arm separation at adequate hand resolution before expanding the family. Require
a consistent changed pose and stable cross-pose ownership/occlusion evidence
before any rigging work. No claim is made that this next approach will succeed.

This result is limited to one character, one seed, Q4_K_S, 528 × 1024 output and
two denoising strengths. No full-precision comparison, larger-resolution study,
pose-conditioned generation or multi-character validation was performed.
Stop after Phase 4B.7a. Nothing is promoted; user review remains separate.
