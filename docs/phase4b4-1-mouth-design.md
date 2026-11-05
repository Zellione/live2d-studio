# Phase 4B.4.1 — coordinated emotional mouth shapes

Continued from `889faf1`. The user rejected the Phase 4B.4 emotional readability:
Angry read as sad, Sad retained a smile, Happy looked blank, Confused looked neutral,
and Embarrassed needed a shy mouth. This phase revises **all seven mouth recipes**
in an optional fresh candidate. Existing eyebrows, eyes, blush, default creation,
accepted source projects, deployment restrictions and model weights are unchanged.

[Results](phase4b4-1-results.md) · [benchmark](benchmarks/phase4b4-1.json).

## What the old mouth actually did

Inspection uses the editable Phase 4B.4 Sara project, original raster support,
explicit `facial-mouth-source-neutral` and `facial-mouth-interior` layers, mesh
vertices, keyforms, opacity channels and complete inherited ancestry. Target IDs
are discovered from layer roles/names and parent relationships. Inspection records
and a source-art close-up remain in `runs/phase4b4-1-diagnosis/`.

The observed mouth is a **baked smile with a gap between its two contour halves**.
The generated cavity is a plain dark ellipse. They share the inspected mouth
parent, but have different original baselines. Treating them as the same curve
therefore does not produce a consistent visible shape.

| Previous control | Observed effect / limitation |
| --- | --- |
| `ParamMouthCurve` | A normalized curve on the broad mouth parent, alongside head/body keys. Positive bends toward a smile; negative mostly flattens the already smiling source. Negative is not an absolute frown. |
| `ParamMouthDispleasure` | Source-relative correction on both visible alternatives. Its soft downward-corner target was used for Angry, giving it the geometry needed for Sad. Applying the same displacement to a flat cavity and a smiling seam does not align their baselines. |
| `ParamMouthSkew` | Small shear on the parent; its effect on the tiny mouth was too weak for a distinct shy mouth. |
| `ParamMouthForm` | Binds the original importer mouth/lip meshes, whose rendering is disabled in this reconstructed branch. Controlled -1/0/1 renders change **zero pixels**. It does not control the visible alternatives. |
| `ParamMouthOpenY` | Opens a separate cavity and fades out the source seam. A resting expression could therefore lose its source contour before the cavity conveyed the intended emotion. |

The previous Happy used positive parent curvature and `.25` opening, but the
visible result was a thin, nearly horizontal dark opening. Sad used only the
negative parent curve at closure: it did not remove the baked smile. Angry used
the soft displeasure frown; Confused used a partial version plus a tiny opening,
leaving a near-neutral line. Surprised opened the wide ellipse, with no independent
roundness. Embarrassed mixed a subtle parent smile/skew and early cavity handoff,
leaving a neutral-like mouth. Neutral already preserved the recognizable source.
These diagnoses come from controlled rendered images, not parameter names or signs.

## Optional surface authoring

`mouth_authoring.py` requires exactly one source-neutral and one interior
alternative sharing the inspected mouth parent. It verifies their hashes and
records mesh topology, source support, margins and ancestry. Already-open source
mouths such as Girl2 are deliberately outside this branch; they are regression
inputs, not silently converted to Sara's strategy.

The source seam fit uses **both disconnected halves**. All distances are relative
to observed mouth width, height and centre, with inspected mesh margins. There are
no character-specific coordinates, opaque IDs, other spritesheet tiles or new
raster assets. The existing source, generated skin, cavity and blush PNGs remain
byte-identical in the editable archive.

The candidate collapses the old parent `ParamMouthCurve`, old parent skew and
mesh `ParamMouthDispleasure` at their neutral defaults. It reauthors curve/skew on
the visible surfaces and adds only controls supported by those surfaces:

- `ParamMouthCurve`: target corner elevation and curvature. Positive targets raised
  smile corners; negative explicitly replaces the baked smile with lowered sad
  corners. Zero retains the original source seam. It is no longer merely a bend
  added to an unknown resting contour.
- `ParamMouthRound`: straightens the resting baseline, narrows the assembly and
  increases the cavity's vertical aperture. Confused and Surprised share this
  geometry; opening and modest width adjustment distinguish their intensity.
- `ParamMouthTension`: replaces the soft curve with a nearly horizontal compressed
  seam and reduces aperture height. This separates Angry from Sad.
- `ParamMouthWidth`: independent positive width scaling on the common mouth parent,
  expanded over its existing head/body keys. Both alternatives stay together.
- `ParamMouthSkew`: source-width-relative shear on each visible mesh. It supports
  a small asymmetric smile without relying on head tilt.
- `ParamMouthOpenY`: independent opening, bounded to 0..1. It changes cavity height
  and the source/cavity handoff, not the emotional corner target.

Curvature/corner elevation are one supported field, rather than redundant controls.
Roundness couples the width/aperture changes needed for an oval; independent width
then permits a smaller shy or questioning mouth. `ParamMouthDispleasure` is removed
from this candidate. `ParamMouthForm` remains on the preserved hidden importer
meshes; it is not advertised as a visible control.

The source surface has 12 curve/round/tension combinations and no geometry-opening
axis. The cavity has those combinations at eight opening keys. Skew expands their
geometry to 36 and 288 forms respectively. Opacity remains a separate opening
channel. Each surface starts from its own original rest geometry and reaches the
**same intended seam**, rather than receiving the same displacement. The cavity's
positive vertical scale is bounded, including at full opening. A small hidden
minimum scale avoids exact zero-area closure; visibility is audited separately.

A first implementation copied equal forms before editing. The editor could omit
those redundant copies, allowing later keys to inherit already bent neighbours.
This produced excessive Sad corner movement near .05/.1 opening. The final method
resets each key to rest immediately before its deformation in an ordered atomic
edit. The source seam has no reason to bend again as openness changes, so it has
no geometry-opening axis at all. An exported Core invariant now checks this.

| Expression | Curve | Round | Tension | Skew | Rest opening | Width |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Neutral | 0 | 0 | 0 | 0 | 0 | 0 |
| Happy | 1 | 0 | 0 | 0 | .42 | .15 |
| Sad | -1 | 0 | 0 | 0 | 0 | 0 |
| Angry | 0 | 0 | 1 | 0 | 0 | .1 |
| Confused | 0 | 1 | 0 | .08 | .35 | -.25 |
| Surprised | 0 | 1 | 0 | 0 | .85 | 0 |
| Embarrassed | .5 | 0 | .1 | -.65 | 0 | -.7 |

These values describe the inspected final candidate; the rendered geometry drove
iteration. They are not universal emotion thresholds. All six mouth controls have
explicit values in every expression, including neutral reset. Non-mouth entries
are preserved from Phase 4B.4.

## Talking and review controls

Expression opening supplies the emotional rest. The viewer starts each frame from
parameter defaults, applies expression once, then blends toward its bounded talk
envelope. It does not keep adding the resting opening on successive frames. The
shape controls remain active throughout talking; stopping talk restores that
expression's resting mouth. The explicit opening slider can override 0..1 for
inspection. Surprised's full-open geometry stays a bounded oval.

**Mouth only** in the viewer enables controlled comparison and holds every
non-mouth parameter at its neutral default: eyes open, identical brows/gaze,
zero head motion and invisible blush. Leaving comparison disables isolation.
Normal preview controls and accepted-model defaults remain unchanged.

The dedicated scenario captures previous and revised mouths with identical framing,
idle/talk/blink stopped, neutral restoration and settled expressions. It includes
mouth-only and full-face stills, the eight requested opening samples, time-sampled
talking, return to each emotional rest, blink/head combinations and rapid switches.
The gallery includes normal-size and close-up sheets, and the four requested pairs.
Full expressions are displayed separately so brows/blush cannot conceal mouth issues.

Core validation uses the **visible full-open cavity** as its winding reference,
like the eye audit uses open-eye geometry. Using the invisible squashed cavity as
reference initially reported false reversals for the opened surface. Every visible
near-closed sample is still tested, and the failed reference report is retained.
No visible-triangle or opacity tolerance was relaxed. The existing eight-float32-ULP
opacity tolerance and strict excursion counts remain separate from visual review.

## Reproduce

Run through local Codex CLI with the existing loopback PSD2Live MCP service. Supply
its token only through the provided environment. All output directories must be fresh.
No network model download or image inference is involved.

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --frozen
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b4_1_experiment.py \
  --baseline runs/phase4b4-sara-v6 --output runs/NEW-mouth
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b4_1_render.py \
  --model runs/NEW-mouth/export/runtime/Generated_artwork.model3.json \
  --output runs/NEW-mouth/mouths-release
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b3_render.py \
  --model runs/NEW-mouth/export/runtime/Generated_artwork.model3.json \
  --correspondence runs/NEW-mouth/transition-correspondence.json \
  --output runs/NEW-mouth/dense
node scripts/probe_expressions.cjs \
  .cache/phase3-st/data/default-user/extensions/Extension-Live2d/lib/live2dcubismcore.min.js \
  runs/NEW-mouth/export/runtime/Generated_artwork.model3.json \
  runs/NEW-mouth/authoring/mouth-inspection.json \
  > runs/NEW-mouth/expression-core-rest.json
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python -m unittest discover -s tests -v
node tests/test_rp_talk.mjs
```

Run `phase4b4_1_render.py` on the preserved Phase 4B.4 model for `BEFORE`, then:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b4_1_compare.py \
  --before BEFORE --after runs/NEW-mouth/mouths-release \
  --layers runs/phase4b3-sara-create-final/stages/facial-6e27043a2bb7/layers \
  --output runs/NEW-mouth-review
```

`phase4b4_1_evidence.py --help` lists the inputs for collecting the benchmark,
including a fresh Girl2 dense regression, passing test logs and the comparison.
`phase4b4_1_inspect.py --output NEW.json` performs read-only inspection of the
currently loaded editor. PSD2Live version/license and installed Core provenance
remain recorded in the benchmark; no proprietary runtime is committed.

A successful command does not establish human emotion perception. User review of
the mouth-only gallery and complete expressions is the final visual gate.
