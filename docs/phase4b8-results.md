# Phase 4B.8 — canonical front-facing base

The user approved candidate 4 as a synthetic front-facing working base. Its exact
image and provenance are frozen separately from the original. Selected-only
segmentation yields two separated arm regions instead of the original merged
region: a useful improvement for later body decomposition, not solved articulation.

Continued from clean HEAD `ad8340a6a14fc17239484e80e4cd388af81119ed`.
The input remains the frozen original flat Codel image, SHA-256
`98589fb8750ccfc3664935985fc42810381b2e09f22e1ae8cf4cd6dd45d39a2d`.
The approved Phase 4B.7b helper is preserved and is not the canonicalization input.
A previously user-started left-arm batch was allowed to finish before the new
GPU run; those historical outputs remain in their original review run.

## Implementation

- Separate canonical workflow, symmetric frontal guide, frontal-neutral prompt,
  five unique seeds per batch, fixed saved settings and repeatable regeneration.
- Local reviewer at <http://127.0.0.1:8798/> supports comparison, approval,
  rejection, additional batches and marking canonicalization unsuccessful.
- Approval freezes exact original and selected synthetic payloads separately,
  with a human decision, provenance, hashes and a persisted manifest binding.
  Read-only snapshots are checked on reopening; interrupted freezes recover.
- Explicit `init-from-canonical` prepares a new helper run with canonical primary
  geometry and the original identity/style input. It launches no inference.
  Three-input helper execution is prepared but not GPU/visually evaluated here.
- Historical pose worker/guide files and producer pins remain unchanged. Original
  creation defaults, accepted runtimes and production SillyTavern remain untouched.

See [workflow and reproduction](phase4b8-canonicalization.md) and
[benchmark](benchmarks/phase4b8.json). All images, raw logs, reviewer state and
frozen working payloads remain under ignored `runs/` directories.

## Candidate generation and review

Current run: `runs/phase4b8-canonical`. Initial preset:
`frontal-silhouette-1536-40`, Qwen Image Edit 2509 Q4_K_S with the pinned FP8
encoder, 800 × 1536 output, 40 steps, CFG 4, shift 3, Euler/simple, denoise 1,
source latents, no mask/CFG normalization, original plus a frontal guide.
The model and environment locks are unchanged; no downloads were required.

All five candidates completed in 850.9 seconds of per-image inference time
(about 170 seconds each), with peak Torch allocation 20.50 GiB and reservation
22.86 GiB. These are allocator measurements, not total board memory usage.

| Candidate | Development screening | Remaining concerns |
|---|---|---|
| 1 | Unsuitable: mannequin copying | Severe identity, anatomy and outfit/style drift |
| 2 | Promising frontal illustration with separated arms | Missing upper legs; slimmer proportions and simplified hands |
| 3 | Unsuitable: rectangular torso and long neck | Missing skirt/legs; changed neckline, expression and proportions |
| 4 | Strongest candidate for human review | Synthetic hand anatomy, facial/proportion changes and hidden clothing remain uncertain |
| 5 | Unsuitable: mannequin proportions | Redesigned face/neckline, flat skirt and missing upper legs |

Candidate 4 exposes both sleeve silhouettes and the torso front, with visible
shoulders and hands and a similar upper-leg crop. All failures are retained;
unselected candidates are not relabelled as human-rejected.

## Human selection and usefulness

The user approved `b-62c26625a6664a98810b8361cea4b371-c4`, seed
`2801932010064774`, in the live reviewer. Selected image SHA-256:
`ab2a52ae59af22435b1c2595cb7ced24fdcd4ed5056b16496b8d2b482d78da3e`.
The automatic freeze manifest is
`runs/phase4b8-canonical/canonical/b-62c26625a6664a98810b8361cea4b371-c4/manifest.json`,
SHA-256 `8d15231abbb8e648e1f1663abd16a7cdd5323296c1361f91c3115e31f2610725`.
The original remains separately hash-bound. The approved selection was exported
for analysis as `9f1f3d4d08be46a2bddf4641c3efe66b`; the export is automated,
while the underlying image approval is the persisted human decision.

The unchanged local SAM backend analyzed only the original and approved base.
At the same 800 × 1536 canvas and threshold:

| Input | Substantial arm-category regions | Interpretation |
|---|---:|---|
| Original angled source | 1 (121,013 pixels) | Overlapping arms remain merged |
| Previously approved 4B.7b helper | 2 (26,535 / 68,582 pixels) | Earlier result; one upper arm remains occluded/unparsed |
| Approved canonical base | 2 (59,658 / 58,819 pixels) | Bilateral sleeve/hand silhouettes are more complete and separated |

These are uncalibrated connected-component proposals, not accuracy scores.
Components require at least max(32 pixels, 5% of the arm mask); left/right ordering
is image-space only. The canonical arm/torso mask overlap is 1,481 pixels versus
3,084 on the original, but neither value measures anatomical correctness.

The selected frontal view is better suited to **initial arm/body separation** than
the original: both shoulders, sleeve contours, wrists and hands are readable;
the torso front is no longer covered by the crossed forearm. This makes later
joint and draw-order investigation more practical. Sleeve/torso boundaries still
need review, and the parser does not separate upper arms, forearms or hands into
articulatable parts. Elbows, fingers, hidden clothing and depth remain synthetic
hypotheses. No independently verified source pixels are recovered by this redraw.
No multi-pose consistency experiment or new helper generation was performed.

Local gallery: `runs/phase4b8-review-final` (all candidates, guide and selected-only
overlays). Detailed parser evidence: `runs/phase4b8-canonical/selected-assessment-v1`.

## Validation and boundaries

The full Python regression run passed 189 tests, including nine canonical workflow
checks, plus both existing JavaScript suites. Synthetic browser QA passed the
canonical-only view, five-image generation, rejection, five-more, history,
comparison, approval, automatic freeze, export and approved-generation blocking.
Synthetic fixtures are never Codel user approvals. Exact logs/hashes and selected-only
measurements are recorded in the benchmark. The final 37-test reviewer subset
also passed with localhost sockets available; its sandbox-only attempt retained
two socket-permission errors. Real-browser checks confirmed the five-image batch
and comparison dialog without making an approval.

Recommended next step, in a separately authorized phase: use the frozen canonical
base as primary pose geometry and the unchanged original for identity/style,
then evaluate a small guided helper batch before attempting arm joints. The
three-reference inference route still needs an actual GPU/visual comparison.
Phase 4B.8 stops here: no helper inference, rig migration, final articulation or
production deployment was started.
