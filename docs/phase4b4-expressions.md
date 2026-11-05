# Phase 4B.4 — independent facial expressions

This is an explicit candidate workflow, starting from `65c34e4`. It does not change
`create` defaults, accepted projects, package pins or production SillyTavern.
[Results](phase4b4-results.md) · [benchmark](benchmarks/phase4b4.json).

## Diagnosis

`generic_rig.animation_recipe()` composes five expression channels. Confused and
Embarrassed both use `ParamBrowEmotion=.2`; their eye/mouth differences are small.
Angry uses `.7` eye openness and a small open mouth, so idle blinking can readily
make an individual screenshot look sleepy. Stopping motion is necessary to compare.

Live MCP inspection found separate semantic brow meshes, their individual warp
parents, the common brows/face/head ancestry, and pre-existing `ParamBrowLY` /
`ParamBrowRY` mesh keys at -1/0/1. The shared brow-emotion field lives on the
parents alongside 27 head/body keys. Independent eye openness, gaze, mouth-form,
head angles and breath also exist. No new parameter needs classifier support:
Cubism expression files address the new exported parameters directly.

Sara's brow source shapes are narrow brown arcs drawn across the bangs, higher
than the darker eyelid creases. Their appearance initially suggested a parsing
error; that interpretation was not established and no pixels were relabelled.
The source left brow has a downward-image-coordinate slope of about -0.343,
and the right +0.214. A small symmetric shear primarily straightens these
already inclined strokes. The first candidate moved them but did not convincingly
read as angry. This is why increasing a five-channel recipe value was insufficient.
Actual mesh topology, source bounds, outer margins, axes and full ancestry are
saved in each candidate's `authoring/expression-inspection.json`.

The source mouth is a smile with a central gap. Selecting its longest connected
dark component picked only one half and produced a slanted correction. That
failed candidate remains local. The final fit uses both dark source halves, a
bounded quadratic and sufficient horizontal support.

## Optional authoring

`emotion_authoring.py` binds meshes by source roles, imported names and actual
ancestry. Canvas offsets come from the validated layer manifest. It does not use
character names, pixel coordinates, opaque mesh IDs or fixture metadata.

- `ParamBrowLIncline` / `ParamBrowRIncline`: positive draws the brow inward and
  brings its inner end down. Inner/outer is determined from the brow's position
  relative to the mouth, independently of anatomical side naming. A source-slope
  compensation targets a modest inclination, retaining stroke thickness.
- `ParamBrowLRaise` / `ParamBrowRRaise`: independent whole-brow translation, bounded
  relative to its width. The existing height keys and parent deformations remain.
- `ParamMouthSkew`: a small relative asymmetric field on the inspected mouth parent,
  expanded across its existing axes, so the mouth assembly follows together.
- `ParamMouthDispleasure`: transforms the source-neutral and cavity alternatives
  from the measured source smile toward a shallow frown. It includes their existing
  opening keys. It does not create teeth, a tongue, or a new mouth image.
- `ParamBlush`: independent opacity on a generated transparent cheek tint.

The source-aware mouth correction currently requires the explicit neutral/cavity
alternatives of the reconstructed sparse-source mouth. Unsupported or ambiguous
inputs fail instead of silently pretending this is a universal expression system.
Source-to-mesh normalization uses imported margins and bounds; it remains an
approximation that requires rendered inspection.

| Pose | Mouth | Brows | Eyes / blush |
| --- | --- | --- | --- |
| Neutral | Original resting mouth | Original | Original, no blush |
| Angry | Closed shallow frown | Both inner ends lowered and drawn inward | .88/.88, no blush |
| Confused | Small uncertain opening, partial frown, asymmetric curve | One raised, the other slightly lowered | 1/.85, no blush |
| Embarrassed | Small shy smile | Gently raised, opposite inclination to angry | .82/.82, blush on |
| Happy | Existing recipe | Existing recipe | Existing recipe, no blush |
| Sad | Existing recipe and shared sad axis | Existing recipe | Existing recipe, no blush |
| Surprised | Existing recipe | Existing recipe | Existing recipe, no blush |

All new channels explicitly return to zero in Neutral and the four unaffected
poses. Expression eye values retain Multiply blending, allowing blink to reach
zero independently. Mouth opening remains an independent talk control. No emotion
file adds a head angle; head-zero distinction is evaluated directly.

## Blush and provenance

The deterministic Gaussian idea is adapted from Phase 3.1 `expressive.blush_png`;
its fixed Girl2 coordinates are not reused. Cheek centres come from the two eye
supports and mouth height. Radius scales with eye separation and eye width.
Sufficient opaque face interior is required; insufficient placement support skips
blush and records the reason. A distance-based fade prevents a hard face boundary,
and Gaussian alpha rounds to zero well before a rectangular image edge.

The tint has a maximum alpha of 64/255, uses its own `ParamBlush`, and inherits the
inspected face parent. Neutral opacity is zero. No original raster, observed mask
or model weight is altered. The generated PNG, checksum, inferred landmarks,
parent binding, CC0 procedural provenance and anatomical uncertainty are recorded.
It is a cosmetic cue, not a reconstruction of concealed anatomy.

## Comparison and runtime checks

The viewer's **Compare expressions** mode stops idle/talking, resets manual values
and transient blinks, restores Neutral, and waits before applying the selected
expression. It then waits for expression fade-in. Moving controls are disabled
while comparison mode is selected. Rapid comparison clicks cancel stale pending
selections. Turning the mode off restores the normal controls.

`phase4b4_expression_scenario.js` uses the installed Core/viewer and captures seven
matched stills, twelve blink/talk samples per expression, idle coexistence, rapid
switches and exact neutral returns. It records actual parameters, stable pixels,
head-zero values, timing and control state. `phase4b4_compare.py` makes identically
framed close-up and normal-size sheets; Neutral, Angry, Confused and Embarrassed
come first, followed by the other expressions. Pixel differences are diagnostics,
never an emotion-recognition score.

The unchanged Phase 4B.3 suite retains 401 rendered samples and the 72-sample
exported eye channel/visible-triangle audit. `probe_expressions.cjs` additionally
checks 756 combinations: seven expressions, twelve blink/talk values, neutral head
and all eight ±X/±Y/±Z combinations. It audits edited brow, mouth and blush triangles,
all drawable finite vertices/opacities, and exact Core neutral restoration. Native
invisible-key warnings and strict float32 excursions remain separate evidence.
These numerical checks cannot establish human emotion perception.

## Reproduce locally

Use fresh output directories. The helper verifies all predecessor stage inventories,
saves the current editor before opening a predecessor, and works through loopback
MCP. Tokens are accepted only from the supplied environment. Nothing downloads.

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --frozen
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b4_experiment.py \
  --baseline runs/phase4b3-sara-create-final --output runs/NEW-expression
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b4_render.py \
  --model runs/NEW-expression/export/runtime/Generated_artwork.model3.json \
  --output runs/NEW-expression/expressions
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b3_render.py \
  --model runs/NEW-expression/export/runtime/Generated_artwork.model3.json \
  --correspondence runs/NEW-expression/transition-correspondence.json \
  --output runs/NEW-expression/dense
node scripts/probe_expressions.cjs \
  .cache/phase3-st/data/default-user/extensions/Extension-Live2d/lib/live2dcubismcore.min.js \
  runs/NEW-expression/export/runtime/Generated_artwork.model3.json \
  runs/NEW-expression/authoring/expression-inspection.json
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python -m unittest discover -s tests -v
node tests/test_rp_talk.mjs
```

Run the same controlled renderer on the predecessor model, then pass those two
render directories and the predecessor facial `layers` directory to
`phase4b4_compare.py --before BEFORE --after AFTER --layers LAYERS --output NEW`.
Open a chosen candidate explicitly with `preview-live --model ...`; defaults remain
accepted models. Review all seven expressions at rest and while talking/blinking.
No user acceptance or automatic promotion is implied by a successful command.
