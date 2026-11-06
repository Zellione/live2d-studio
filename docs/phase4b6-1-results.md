# Phase 4B.6.1 — preserve improved expressions through body authoring

Subsequent review: the exact final candidate received limited user visual
acceptance and was frozen in [Phase 4B.6.2](phase4b6-2-results.md). The pending-review
statements below describe the original Phase 4B.6.1 result, preserved historically.

Continued from `e6b9d81`. **The combined Codel candidate restores the small,
parted Confused mouth while preserving the body motion the user approved.**
Surprised has a larger oval opening; Sad has a distinct downward contour.
The new complete candidate still requires explicit user visual review. Nothing
was promoted, and production SillyTavern was not modified.

- [Interactive before/after viewer](http://127.0.0.1:8792/) — Phase 4B.6 on the
  left, combined candidate on the right.
- [Controlled facial comparison and recording](http://127.0.0.1:8793/), backed by
  `runs/phase4b6-1-review/`.
- Candidate: `runs/phase4b6-1-codel-v3/`; `performance.json` identifies its editable
  project, source layers and portable runtime. The exported PSD is beside `runtime/`.
- [Numerical summary](benchmarks/phase4b6-1.json).

## Confirmed diagnosis

Read-only MCP inspection reopened the original Codel animation project, optional
mouth project, and Phase 4B.6 body project. Their saved expressions match their
exported exp3 files. The body experiment's ancestry goes directly to the sealed
Phase 4B.5 first run, not the optional expression/mouth branch.

| Confused control | Original / Phase 4B.6 | Improved mouth / combined |
| --- | ---: | ---: |
| Mouth curve | -0.25 | 0 |
| Rest opening | 0.05 | 0.35 |
| Roundness | Absent | 1 |
| Width | Absent | -0.25 |
| Skew | Absent | 0.08 |
| Brow emotion | 0.2 | 0 |
| Left/right independent brow incline | Absent | -0.3 / 0.15 |
| Left/right independent brow raise | Absent | 1 / -0.3 |

The old recipe has five channels. The improved recipe has fifteen, including
independent brows, roundness, tension, width, skew and a resettable blush channel.
Surprised shares roundness=1 and curve=0, with opening=0.85 and width/skew=0.
No head tilt is needed to distinguish the new Confused mouth from Sad.

The regression was a **branch-composition omission**, not the body authoring
operation overwriting improved channels. The old animation builder can nevertheless
replace expressions, so it now refuses that operation on an already coordinated
mouth project rather than silently restoring its five-channel defaults.

## Reusable composition and preservation

`prepare-performance` creates a separate, hash-verified resumable run from an
existing creation run or local authoring experiment. Features are independent:
`--mouths coordinated` and `--body-motion calm`; both default to `preserve`.
The same composition functions are available as optional flags on `create`, after
its ordinary semantic/facial/rig/animation stages and before export. Existing
creation defaults and semantic/visual review gates remain unchanged.

The optional mouth stage reads the **actual saved expressions**, discovers semantic
meshes and ancestors, installs the earlier independent emotion controls when
missing, and applies the existing seven coordinated mouth recipes. It does not
reconstruct the recipes from the legacy animation builder. Already coordinated
mouths must be preserved rather than applied twice. The body stage similarly
rejects duplicate body authoring and checks exact expression-entry preservation.
Export verifies every saved channel, blend and fade against the exp3 files and
retains authored Idle, Nod and Question groups.

The final candidate was built in one command from the sealed first run: improved
mouths first, then the unchanged Phase 4B.6 body authoring. A separate v2 experiment
applied mouths to the approved body project, providing the reverse-order check.
Neither requires combining character-specific projects or supplying opaque IDs.
Repeating the final command reuses verified stages without contacting MCP.

Preservation evidence:

- Physics3, the 16-second Idle, Nod and Question files are **byte-identical** to
  Phase 4B.6. No motion curve contains an added mouth channel.
- Across **481 matching actual-Core poses**, all 21 checked drawables outside the
  explicitly authored mouth/brow/blush surfaces have **zero coordinate difference**.
  This includes head/face, neck, front/back hair, torso, shared limbs and eye parts.
- Equal-scale neutral renders are pixel-identical. Both mouth-only and complete
  Confused renders differ from the earlier improved mouth reference in **zero pixels**.
- All **33 original archived PNGs** and **20 imported source-layer RGBA images**
  remain exact. The complete 35-image archive matches the earlier optional mouth
  reference: the two extra archive images belong to its procedural blush workflow.
  There is no new inference or painted mouth artwork.
- The sealed first-run inventory and the approved Phase 4B.6 inventory verify
  unchanged. Original inputs, accepted projects, package pins and fixtures remain
  preserved. Arms still have shared body attachment, not independent articulation.

The model3 reference document can have the same hash while its referenced MOC or
expressions change. Review records therefore bind the **whole runtime inventory**,
editable project and exact captured/Core evidence, not only the model3 hash.

## Numerical seam contract

The historical 819-sample Codel mouth report remains **failed** at its original
absolute `1e-7` check. Its observed maximum is `1.1920928955078125e-7` Core units,
about **0.000128508 source pixel**. No historical report or threshold was edited.

Fresh probes independently vary opening, eyes, both, and identical repeated inputs
at 101 samples per expression. Eye-only changes and repeated inputs give zero
seam movement. Opening changes produce deterministic float32-sized differences.
The saved seam has no opening geometry axis, and no geometric ancestor binds that
axis; only its opacity track does. Sara exhibits the same pattern at a smaller
coordinate scale. The exact internal proprietary Core arithmetic is unavailable,
so interpolation precision is the supported explanation, not a claim to have
inspected its implementation. No evidence of meaningful source-seam deformation
was found. Reauthoring in either order retains the small effect.

An attempted separate opacity Part was rejected by the installed editor
(`Unknown structure action: create`); the untouched failed trial remains local.
No unsupported structural operation is shipped.

The **new optional contract** requires all of the following:

1. Saved-project inspection proves that the seam and every geometric ancestor
   exclude mouth opening. The contract is bound to the exact exported MOC hash.
2. The exported seam varies by at most eight binary32 representable steps at its
   largest coordinate magnitude, additionally capped at **0.001 source pixel**.
3. Every existing finite-geometry, visible-triangle, opacity, parameter-range and
   exact-neutral check still passes. The old absolute result remains separately
   reported as `legacy_source_seam_absolute_invariant`, which is false for Codel.

This is an explicit scale-aware numerical allowance plus a structural contract,
not a universal theorem about Core error bounds. Without a bound inspection file,
the probe still enforces its old `1e-7` rule. The new contract passed **819 poses
and 63 expression/head groups each** on the original Codel mouth reference,
independent Sara reference and final combined Codel. Maximum measured seam changes
are 0.000128508 source pixel for Codel and 0.000009388 for Sara in these suites.
The denser isolated Sara sweep also retains its 0.000010953-pixel maximum.

Negative tests reject an opening dependency even when displacement is tiny,
reject injected 0.01-source-pixel movement across six coordinate scales, reject
nonfinite inputs, and enforce the physical pixel cap at coarse coordinates.
The finite precision allowance does not excuse animation deformation or grant
visual acceptance. The previous Girl2 **1,716 visible lip reversals remain failed**;
they are unrelated to this source-seam contract.

## Runtime and visual review

| Test | Final result |
| --- | --- |
| Full Python suite | 146 pass |
| JavaScript talk / numerical tests | 5 / 3 pass |
| Existing synthetic JavaScript source-contract audits | 3 pass |
| Mouth Core | 819 poses, zero visible reversals; new structural/scale contract passes |
| Broad body Core | 496 poses, pass |
| Body preservation comparison | 481 poses, exact checked vertices |
| Dense facial / eye audit | 401 frames / 72 samples, pass |
| Mouth expressions, openings, talk return and rapid changes | 213 frames, pass |
| Continuous body/idle/gesture suite | 476 frames, pass, exact neutral reload |
| Dedicated Confused coexistence / dense openings | 355 frames, pass, exact neutral reload |
| Controlled high-resolution face captures | 17 frames each for old, reference and new |
| Side-by-side mouth-only controls / reload | Pass |

Confused keeps roundness=1 and curve=0 through idle, hair dynamics, head movement,
Question and talking. It returns to opening=0.35 after talk stops. Rapid switches
restore the same settled expression; neutral clears the channels. Dense 0.01-step
opening samples cover Confused and Surprised. Other expressions retain their earlier
coordinated recipes. The viewer's mouth-only mode now neutralizes non-mouth controls
on **both** comparison models.

Raw strict opacity excursions remain in every applicable report, with a maximum
of `1.0000004768371582` and zero values outside the existing eight-ULP opacity
policy. That policy and all visible-triangle thresholds are unchanged.

Development inspection of the matched sheets shows a small parted Confused oval,
a larger Surprised opening and a distinct Sad contour. The gallery presents
mouth-only comparisons first, then complete expressions and all seven expressions.
The short moving-Confused recording retains measured browser sample intervals;
it does not claim to contain every native display refresh.

The plain cavity, inherited eye contours/shading, uncertain facial backing and
limited limb separation remain. This phase does not redesign them. Naturalness
and expression readability remain the user's visual decision.

## Reproduce

Use fresh output directories for new builds/captures. Reusing a completed
`prepare-performance` output verifies and resumes it. Local MCP is needed only
for authoring; the exported viewer needs no SillyTavern server, LLM or coding agent.

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio prepare-performance \
  --baseline runs/phase4b5-codel-full-first --output runs/NEW-performance \
  --mouths coordinated --body-motion calm
```

To revise an already authored body model while preserving it, use that run as
`--baseline` and omit `--body-motion calm`. `performance.json` records the paths.
Run `scripts/phase4b6_1_validate.py --help` for the repeatable Core/browser suite;
its `--body-reference` is the preserved Phase 4B.6 model, and `--correspondence`
is the matching source project's transition correspondence. Standalone controlled
captures use `phase4b6_1_render.py --mode face`; gallery collection uses
`phase4b6_1_report.py`. All outputs stay under ignored `runs/` directories.

Final viewer and gallery restart:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio preview-live \
  --model runs/phase4b6-1-codel-v3/stages/export-f30df9451395/runtime/Generated_artwork.model3.json \
  --compare-model runs/phase4b6-codel-v7/export/runtime/Generated_artwork.model3.json \
  --port 8792 --no-open
python3 -m http.server 8793 --bind 127.0.0.1 --directory runs/phase4b6-1-review
```

The initial face-capture summary omitted `control_noise_pixels`; its raw successful
captures and failed summaries remain. Fresh corrected captures pass. The first
combined v1 strict seam failure, v2 reverse-order evidence, unsupported Part trial,
and sandbox launch failures remain inspectable. The final suite's initial aggregate
failure on that report field is preserved alongside the corrected face/comparison
results; no failed report was relabelled.

Existing PSD2Live 3.6.7, Core 5.0.0, frozen uv dependencies and FFmpeg are reused
with the provenance/licenses recorded in Phase 4B.6. No downloads, inference,
training, system changes or production writes. **Stop after Phase 4B.6.1.**
