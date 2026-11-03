# Phase 3.1 — standalone preview and clearer Girl2 expressions

Continued from `257582f`, 2026-11-03. **A single command opens a real interactive
Cubism preview.** Girl2 has a separately saved facial candidate with a clear smile,
frown, stronger surprised mouth and subtle cheek blush. The user reviewed the
comparison as more recognizable, rejected the initial sad eyebrows as angry-looking,
and approved the corrected sad shape: “Yes, this reads as sad.”

The accepted Phase 3 source/runtime, historical recipes, packaging pins and benchmark
JSON remain unchanged. Production SillyTavern, its settings and services were not
used or modified. No Phase 4B, deployment or training was performed.

## Use and artifacts

Run `uv run --frozen live2d-studio preview-live`, then choose the Phase 3.1 candidate
in the Version selector. The accepted Phase 3 remains the automatic default.
See [preview/rebuild instructions](phase3-1-preview.md).

- Final editable candidate: `runs/phase3-1-final-v2/character.psd2live` and
  `character.psd`; unmodified editor export in `export/`, portable runtime in `runtime/`.
- Final matched gallery: `runs/phase3-1-review-corrected/index.html`, with face crops,
  portrait-size comparisons, combined blink/talk/head poses and a transition GIF.
- Explicit sad correction: `runs/phase3-1-sad-v2-browser/sad-correction.png`.
- Earlier reviewed version: `runs/phase3-1-review-complete/`; rejected versions,
  transcripts, screenshots and test logs remain in `runs/phase3-1-*`.
- New code: `preview_live.py`, packaged `preview_ui/`, `expressive.py`,
  `scripts/build_phase3_1.py`, browser scenario/acceptance scripts and preview tests.
- Recipe: `recipes/girl2-expressive.json`. Measurements: [benchmark](benchmarks/phase3-1.json).

## What changed visually

The original recipe's mouth-form offsets barely changed the resting contour.
New `ParamMouthCurve` forms bend the existing mouth/lip assembly into a smile or
frown, preserving independent mouth opening. `ParamMouthRound` narrows and lengthens
the open surprised mouth. These are edits to actual editable deformers, exported
into MOC3; the viewer contains no facial artwork substitute.

The first attempt used the wrong curve axis, moving the mouth sideways; it was
rejected. The corrected vertical field produced the reviewed smile and frown.
Happy uses a moderate open smile; sad/angry have visible downturned contours;
surprise uses substantially more opening. Confused retains an asymmetric brow/eye
pose and small tilt. Embarrassed combines a gentle smile, lowered eyes and blush.

User review caught an inherited directional error: the old sad brow axis steepened
the source eyebrows toward the nose. A large counter-rotation stretched their
appearance and was also rejected. The retained `ParamBrowSad` instead raises the
inner ends with a vertical deformation field, preserving brow width. It has its own
axis so the other six reviewed expressions keep their shapes. The source-neutral
brows are unchanged. Head/lean combinations receive explicit authored keys.

The blush is a reproducible original Gaussian tint at two inspected cheek positions,
RGB (229,100,111), maximum alpha 70/255, transparent elsewhere. It was imported,
registered at native canvas coordinates and added as an editable source layer through
MCP. Its mesh inherits head movement, draws just above the face and has an independent
`ParamBlush` opacity track: zero at neutral, one only for embarrassed. No source pixels
are painted over or duplicated as replacement facial contours. Provenance is saved
beside the build; the procedural artwork is CC0-1.0. No image model/cloud service used.

## Validation and limits

Both baseline and revised models run in the actual locally installed Core 5.0.0,
PIXI 6.5.2 / bridge 0.4.0, with continuous rendering. Automated UI checks cover all
seven expressions, mouth and X/Y/Z geometry, independent blinks, talking during
every expression, idle, manual overrides during idle, intermediate expression fades,
rapid changes, combined stress poses and exact neutral restoration. Network evidence
shows only local assets and no backend/classifier calls. Full-frame neutral comparison
with Phase 3 is byte-identical. Original archived artwork assets remain unchanged;
this does not remeasure the historical 99.89% source-preservation result.

The initial talk envelope used a maximum against resting opening, which could freeze
surprise; it now blends to a varying envelope and back. Residual physics initially
prevented exact reset; paused idle now suspends physics for deterministic manual poses.
The server and UI are read-only and serve a closed allowlist. Unit tests do not need
proprietary libraries or ignored runtime artifacts; actual rendering tests do.

Python regression tests, the existing five JS talk tests, the three synthetic Node
source audits, and all 15 target-transaction tests on the dedicated Btrfs test base
pass. Source-contract audits remain synthetic. Actual browser scenarios and raw
opacity excursions are recorded separately in the benchmark; tiny float32 excursions
are retained, with the existing eight-ULP validity tolerance, not silently clamped.
The existing Phase 0–4A.2 Python suite is preserved; historical ST browser results
were not relabeled as fresh runs. The new candidate was tested in the standalone
installed runtime, not a production ST session.

The earlier full replay reproduced every runtime-consumed file; only CMO3/CAN3
containers differed. The corrected final recipe was again authored from the accepted
Phase 3 project, saved/reopened and exported. Seven expression names, two authored
motions, mapping and portable references remain compatible in structure. The old
Phase 4A package command deliberately still pins Phase 3 and will not silently promote
this candidate. No new production package acceptance is claimed.

Visual improvement is user-reviewed, not a professional-quality or blinded seven-label
recognition result. Confused is still less emphatic than smile/frown/surprise. Eyes
cannot open beyond their authored source-neutral shape; lids remain flat, the mouth
has simplified/faint lip edges, and existing hair gaps remain. No teeth/tongue or
skin-lid anatomy was invented. These source/rig limits remain explicit. Stopped after
Phase 3.1; production remains disabled.
