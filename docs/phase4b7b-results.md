# Phase 4B.7b — guided Qwen generation and human reviewer

**Limited positive result for auxiliary segmentation support:** the user selected
one candidate, and the same parser separates its visible arm regions better than
the original. Full joint recovery, cross-pose consistency and final articulation
remain unproven. No rig or generated anatomy was promoted.

Started from clean local `c56a59d50c5a473fd55e8c4435159a568290e5de` on main.
Remote main initially pointed to `6205158be49f3ab70894982ad73b5b9872f691c6`.
After the frozen-reference tests passed, the existing Phase 4B.7a commit was pushed
and remote main verified at `c56a59d`. No pre-existing uncommitted work was present.

## What changed

A separate opt-in Qwen worker now accepts a second pose-guide image, preserves
aspect ratio at 1024/1536 output long edges, and records the actual reference
latents and output dimensions. It reuses the pinned Q4_K_S transformer and FP8
encoder with no downloads. It does not modify the old facial worker or creation
defaults. The actual previous pose settings were 1024/40 steps, not 512/20.

The localhost reviewer supports the five requested gestures, five fresh seeds per
batch, persistent human accept/reject/unsupported decisions, old batch history,
zoomed side-by-side comparison, guarded regeneration and selected-only export.
An accepted pose remains unchanged while other poses are generated/reviewed.
Completed tasks survive interrupted jobs; unfinished tasks resume in new output
directories. A saved set records the exact approved hashes and reviewer decisions.

See [generation audit and reproduction](phase4b7b-generation.md),
[reviewer instructions](phase4b7b-reviewer.md) and
[small benchmark](benchmarks/phase4b7b.json).

## Calibration findings

The first study contains nine single-seed comparisons; the follow-up contains
four. These research cases are not five-candidate review batches. Seed 1729 is
held constant. Recorded plans specify the parent comparison and changed family.
All raw results remain under `runs/phase4b7b-calibration*`.

- Removing hard composition avoids the old pasted boundary seams, but permits
  unrelated repainting. The unmasked/short-text 1024 cases redraw the face and
  often change proportions.
- Image2 is retained by the installed GGUF pipeline, and guide representation
  changes the result. Several skeleton cases crop the head or put the desired
  arm behind the body. Successful conditioning is not successful pose control.
- At 1536, face/hair/style are substantially closer to the source in the inspected
  seed. Missing or hidden right arms remain a major failure. Silhouette guidance
  reveals a second hand and more clothing, but does not establish a useful elbow.
- Adding facial landmarks does not solve arm placement. Lower denoise .8 mostly
  restores the crossed-arm source pose, preserving its original occlusion.
- CFG normalization and empty initialization do not fix the 1024 framing failure
  in this seed. The study does not identify a universally optimal Qwen workflow.

These are development assessments, not user decisions. Generated clothing can
look plausible without being the original hidden fabric. A newly visible hand
can still have untrustworthy anatomy or belong to the wrong spatial arm path.
No calibration image was automatically admitted to the selected set.

## Initial review batch and performance

The initial right-arm batch contains exactly five fresh seeds at 800 × 1536,
silhouette guidance, 40 steps, CFG 4, shift 3, source latents, denoise 1 and no
mask/CFG normalization. This is a frozen experimental preset, not an optimality
claim. Other target poses are available for independent user-requested batches.
The original is the neutral reference; no neutral edit is generated.

The batch provides visibly different outcomes under one prompt/guide/settings:
some hide a hand, one retains a crossed arm, and two expose both hands and more
front clothing. None is automatically accepted. The reviewer is live at
<http://127.0.0.1:8795/> with persistent state in `runs/phase4b7b-review/`.
Calibration plus initial candidates are also in `runs/phase4b7b-review-gallery-assessed/`.

Single-reference 1024 calibration took approximately 80 seconds per image;
two-reference 1024/40-step cases about 131 seconds; the 1536/40-step calibration
about 168–170 seconds. The initial seeded batch took 170–250 seconds per image
on the shared workstation. First-study peak Torch allocated/reserved VRAM was
21.504/23.123 GiB. Exact per-task measurements and hashes are in the benchmark;
these are not whole-device peak or dedicated-machine throughput claims.

## Human-selected candidate and semantic follow-up

The user selected **candidate 2** in the right-arm slot and saved set
`34e5960402594190b38972b4797af192`. The exact candidate is
`b-941e0650b84f40bca2973fdfa66a2a1d-c2`, seed `1189768204161235`, image SHA-256
`f63a611c296c9e350c7dae04ce270f21b2a5d3b5da6f48c429363662aab079d5`.
The saved manifest hash is
`0ba3747ad564d8483cbb06d2cd44424c78840b9e7a9156fa73864b2f11a35850`.
This is a real human visual decision, separate from development assessment.
The other four candidates are unselected, not automatically rejected; the other
four pose slots remain pending. The approved pose cannot be regenerated.

Only this selected image and the original were passed through the existing pinned
SAM parser, on matching 800 × 1536 canvases. The parser is
`24yearsold/l2d_sam_iter2`, revision
`0b0608310fb7a89e32ecd7397147a249540cf1e7`, Apache-2.0, with unchanged worker/source
and checkpoint hashes. No extra weights were downloaded. These fresh measurements
do not replace the original frozen decomposition or Phase 4B.7a results.

| Input | Substantial arm-category components | Component areas, pixels |
|---|---:|---|
| Original, uniformly fitted | 1 | 121,013 |
| Human-selected auxiliary | 2 | 26,535 and 68,582 |

Components use four-neighbour connectivity and at least max(32 pixels, 5% of
that image's arm mask). Area values are not coverage comparisons: proportions and
pose differ. The mask overlays confirm the split corresponds to the two visible
sleeve/hand regions, not merely two fragments of one hand. However, much of the
character's **right upper arm is still occluded or unparsed**. SAM does not label
upper arm, elbow, forearm, wrist and hand separately.

- **Useful:** both hands/cuffs are visible at the sides; arm-to-arm contact is
  removed; front clothing covered by the original crossed forearm is illustrated.
  This supplies a useful additional segmentation view and plausible torso reference.
- **Still uncertain:** shoulder attachment, complete right upper-arm contour,
  elbow pivots, finger anatomy, cloth reconstruction and depth/draw-order ownership.
  The generated body is more frontal/slender, so direct pixel transfer is invalid.
- **Pose compliance:** the selected still is closer to uncrossed arms-down than a
  clear right-arm lift. Visual acceptance is not proof of guide accuracy.
- **Scope of the positive result:** one approved auxiliary view improves visible
  component separation over parsing the original alone. No fused multi-pose
  segmentation, stable joint correspondence or consistent pose family is demonstrated.

Review <http://127.0.0.1:8797/> (`runs/phase4b7b-review/selected-assessment-v1/index.html`): source/selected
SAM overlays, an unregistered difference panel, exact measurements and a separate
hash-bound development assessment. Only the selected image entered this analysis.
The original and selected set remain unchanged. Parser stage timings were about
2.22 s for the source and 2.12 s for the candidate, excluding worker startup.

## Evidence boundaries

| Level | Meaning in this phase |
|---|---|
| Visually plausible | Development screening or an explicitly recorded human visual decision |
| Anatomically plausible | Separate inspection of complete limb paths, joints, hands and occlusion |
| Useful articulation evidence | Source-relative/cross-pose structure that survives those checks |
| Verified source pixels | Immutable original artwork only; not the generated pose |

The frozen combined Codel reference retains its reviewed face/head/hair/breathing
behavior. Its original semantic decomposition still merges both arms/hands. The
new application does not alter either asset or relabel generated regions as known
anatomy. It can export selected-only comparison panels and difference diagnostics;
these do not automatically identify hidden regions or grant semantic ownership.
SAM or future anatomical decomposition must consume only a manually selected set.
The selected-only comparison above establishes a narrow component-separation
benefit. It does not establish general superiority or anatomical reconstruction.

## Validation and remaining review

The release Python suite passes **180 tests**, including real process locking,
HTTP guards, interruption recovery, immutable approvals/presets, hash tampering,
selected-only export/diagnostics and explicit preset additions. Both existing
JavaScript suites pass (5 talk tests, 3 mouth-invariant tests). Frozen reference
and existing semantic/Core/deployment gates remain intact.

Actual browser QA on synthetic images passed generation, five-more, rejection,
selection, unsupported handling, history, zoom/compare and selected-only save.
It made no external requests and had no uncaught errors or failed asset requests.
The first browser run exposed a rapid-click handling issue; later harness retries
fixed stale-element timing. Failed screenshots/logs remain in ignored runs.
Synthetic browser decisions are not Codel user approvals. A separate read-only
browser check loaded the real five-image batch and comparison dialog successfully.
Its only HTTP miss was the browser’s optional favicon request; no review asset
failed. The desktop screenshot is retained under `runs/phase4b7b-browser-real/`.

New source code, tests, presets and documentation are the only committed artifacts.
Generated artwork, model weights, reports, browser profiles, reviewer state and
selected sets remain ignored. No accepted Girl2/Sara/Codel asset, deployment gate,
production SillyTavern installation or creation default was changed.

The next step is a complementary manually approved pose exposing the obscured
upper arm/elbow, followed by generic sided-arm and cuff/hand proposals using only
the selected set. Retain failures and regenerate only unapproved poses. The current
helper demonstrates limited usefulness, not a final arm rig. Stop before rigging
or deployment.
