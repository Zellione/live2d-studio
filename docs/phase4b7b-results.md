# Phase 4B.7b — guided Qwen generation and human reviewer

**Implementation is ready for local human review. Articulation feasibility remains
unproven until useful candidates are manually selected and examined.** This phase
does not claim a solved arm rig, verified generated anatomy or production approval.

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
Calibration plus initial candidates are also in `runs/phase4b7b-review-gallery/`.

Single-reference 1024 calibration took approximately 80 seconds per image;
two-reference 1024/40-step cases about 131 seconds; the 1536/40-step calibration
about 168–170 seconds. The initial seeded batch took 170–250 seconds per image
on the shared workstation. First-study peak Torch allocated/reserved VRAM was
21.504/23.123 GiB. Exact per-task measurements and hashes are in the benchmark;
these are not whole-device peak or dedicated-machine throughput claims.

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
A superiority claim over single-image segmentation is still pending that review.

## Validation and remaining review

The release Python suite passes **176 tests**, including real process locking,
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

The next step is human selection in the local reviewer, followed by selected-only
anatomical/segmentation assessment. Retain failures, change a documented preset
when appropriate, and regenerate only unapproved poses. Stop before final arm
rigging or deployment.
