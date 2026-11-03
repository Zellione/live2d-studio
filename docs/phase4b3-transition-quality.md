# Phase 4B.3 — contour correspondence and temporal review

This phase changes optional rig authoring, using existing artwork and installed
PSD2Live/Cubism. It downloads no models and runs no image inference. See
[results](phase4b3-results.md) and the [benchmark](benchmarks/phase4b3.json).

## Diagnosed failure

Phase 4B.1 contracts each source eye about a relative horizontal pivot. White and
lash geometry have only 0/1 opening keys. The closed raster has no corresponding
motion: its curve stays in its original place. Both meshes inherit the eye parent,
so sharing head motion does not repair their different local closure curves.
At openness 0.1, the source opacity is 0.4 and replacement opacity 0.6. Qwen's
curved lash and the contracted original contour therefore describe a visible loop.

The installed artwork is above the face, below the original eye assembly. A Qwen
closed-eye PNG also contains generated skin, but that lower skin cannot erase an
original lash drawn over it. Changing draw order alone would conceal artwork
without matching the eye's motion. The iris is clipped by the white drawable;
mask opacity is not a reliable way to hide that iris, so it needs its own opacity
track. Original contour ownership and generated backing remain those of Phase 4B.1.

The sparse-source mouth has a related mismatch: an exact source seam is faded
against an independently scaled cavity. Its old geometry keys and seam handoff
make the early opening range uneven. Qwen changes RGB inside the cavity's existing
alpha support, so a nicer shaded cavity can look smaller despite valid geometry.
Geometry alone cannot establish that its brighter pixels are mouth interior.

## Optional aligned method

`src/live2d_studio/transition_authoring.py` derives both sides from semantic roles,
source pixels, inspected mesh topology and parent ancestry. It requires a fresh
supported 0/1 source-eye axis, an unambiguous source/alternative binding, a common
parent and an unclipped replacement below the source white/lash. Unsupported rigs
fail explicitly. It contains no character names, source hashes or absolute artwork
coordinates.

1. Find the connected upper source stroke using local luminance statistics and
   horizontal support. An already isolated deterministic lash uses its alpha;
   selecting only its darkest quantile had fragmented that stroke in an early run.
2. Convert raster landmarks into the inspected parent space using mesh bounds and
   the inspected outer margin. Resample both curves on common horizontal positions.
   Fit a bounded cubic displacement; unsupported overlap/degenerate bounds fail.
   This raster-to-mesh conversion is an approximation, not exact per-texel binding.
3. Squash the source at closure and displace its upper curve toward the target.
   The replacement follows the same interpolated upper curve as the source opens.
   It retains its stroke thickness while the source regains height. Both inherit
   the same existing head deformation. Their geometry is not frozen during a fade.
4. Keep the source lash invisible through 0.1, then raise it to full opacity at
   0.25. White and iris remain hidden through 0.15 and reach full opacity at 0.25.
   Keep the lower replacement opaque until 0.25, then retire it by 0.35. It is
   completely invisible at full opening. This avoids the 0.75 coverage produced
   by compositing two 0.5-alpha strokes. Fractional texture alpha remains fractional;
   the scalar coverage calculation is not a guarantee that all stroke pixels match.
5. Audit exported channels and triangle orientation in the installed Core. A
   visible eye reversal relative to the open pose fails the aligned pipeline.
   Squashed invisible source/white triangles can still have native-key warnings;
   those are retained. The earlier Qwen candidate had one visible source reversal
   at 0.05. Delaying its visibility removes that case without removing the closed
   replacement. This is distinct from claiming an anatomically correct eyelid.

The source eyelash/iris artwork and fully open geometry remain intact. Deformation
changes where source samples render; it does not paint over their original raster.
Generated texture provenance and uncertain boundaries remain attached to the
existing alternatives. The skin-only experiment additionally records its exact
reused mask and boundary blend. Render fidelity is measured separately.

## Mouth and fallback

For the sparse-source branch, opening keys are copied from the inspected fully
open cavity, then given positive vertical scales at 0/.05/.15/.25/.5/.75/1. The
horizontal span and centre remain fixed in the mouth parent's coordinates. The
exact source seam stays through .05 and retires by .15; the cavity rises smoothly
from invisible closure to full opacity by .15. Smile/frown and head motion remain
on the shared parent, and expression resting values stay unchanged. No teeth or
tongue are invented.

Already-open artwork retains the existing importer mouth branch. This is the
existing source-support strategy selector, not a Girl2-specific exception. The
Qwen cavity remains a rejected alternative; final eye candidates use deterministic
mouth artwork. Neural skin is evaluated independently and is not needed for
alignment. No neural artwork is automatically selected or promoted.

## Temporal gates and evidence

The standalone suite captures **401 actual Core frames** per completed run:

- Both eyes independently, together, mouth, smile and frown at
  0/.05/.10/.15/.20/.25/.35/.50/.65/.75/.90/1.
- Forty-one samples each for left, right, bilateral closing/reopening and mouth
  opening/closing, evaluated through actual Cubism keyform interpolation.
- Seven expressions, twelve combined head/blink/talk samples each, neutral returns,
  and 65 samples of authored idle blinking coexisting with simulated talking.

The parameter trajectories are scripted; the rendered model is the installed
runtime. The suite records actual parameter values and capture times, rather than
assuming each command was rendered. `transition_quality.py` checks dense values,
independent eyes, complete monotonic round trips and moving talk envelopes.
`probe_transitions.cjs` checks exported opacity and visible triangle reversals at
neutral and two combined head poses. Its area-product threshold is 1e-12 in Core
coordinates; near-zero area counts remain diagnostic. Native MCP geometry reports,
strict opacity excursions and the existing eight-ULP float tolerance are retained.

Frame differences, hole/component counts and finite geometry are numerical evidence.
They cannot identify a natural eyelid or distinguish every legitimate fold from a
bad contour. Developer visual decisions are separate records tied to quality-report
hashes. Galleries include every dense pose, GIF recordings and complete sequence
contact sheets. GIFs use nominal intervals; recorded capture times remain available.
Frame-change maxima are not uniformly lower, and are not an aesthetic score.

Large frame sets transfer from the dedicated browser in bounded chunks. Earlier
single-message CDP attempts exceeded the transport limit and are preserved. The
larger suite has a separate time budget; no geometry/visual threshold was relaxed.

## Reproduction

```sh
uv run --frozen live2d-studio create --input portrait.png --output runs/NEW \
  --rights 'Author; license; URL' --facial-motion aligned \
  --decomposition SOURCE_MATCHED_BRIDGE --sam SOURCE_MATCHED_SAM --no-preview
```

Existing semantic and visual review commands still apply. `legacy` remains the
facial-motion default; deterministic remains the artwork default. Aligned is an
explicit candidate option pending character-specific review, including for neural
artwork selected with the existing `--reconstruction` flags. The new authoring,
Core probe and dense scenario participate in stage invalidation. Do not resume an
accepted run after code changes; use a fresh directory.

```sh
uv run --frozen python scripts/phase4b3_experiment.py \
  --baseline runs/phase4b1-sara --output runs/NEW-create --pipeline
uv run --frozen python scripts/phase4b3_experiment.py \
  --baseline runs/phase4b2-sara-qwen-hybrid --output runs/NEW-qwen
uv run --frozen python scripts/phase4b3_render.py \
  --model runs/NEW-qwen/export/runtime/Generated_artwork.model3.json \
  --correspondence runs/NEW-qwen/authoring/transition-correspondence.json \
  --output runs/NEW-qwen/dense
uv run --frozen python -m unittest discover -s tests -v
node tests/test_rp_talk.mjs
```

The experiment helpers verify frozen stage inventories and save the existing editor
before opening a predecessor. The pipeline helper reuses semantic review only when
its report is byte-identical. All actual authoring goes through loopback MCP. No
coding agent is required at runtime. `phase4b3_quick.py` is a static diagnostic only;
it never replaces full temporal validation. No production deployment is involved.
