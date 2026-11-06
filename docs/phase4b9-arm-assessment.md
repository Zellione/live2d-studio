# Selected-family arm evidence: reproducible workflow

This workflow freezes existing human decisions, parses only the selected family
and produces uncertain anatomical proposals. It never calls Qwen, approves a pose,
changes a saved guide or authors an accepted rig. See [results](phase4b9-results.md)
and the [benchmark](benchmarks/phase4b9.json).

## Freeze and provenance

`pose_family.freeze` checks the current reviewer, exact candidate hashes, human
accept events, candidate decisions and canonical provenance. An existing matching
selected export is reused. `--export-if-missing` creates a selected-only export
without changing the underlying approvals. Output must be a fresh ignored run.
Pending/unsupported/rejected poses do not enter the family; no fifth pose is required.

Each payload is copied and made read-only. `family.json` identifies source roles,
configurations, prompts, guides, seeds and approvals. Its hash is pinned in the
phase benchmark. Read-only file permissions are not root-proof signing. Downstream
loading checks paths, payload hashes, original/canonical separation, approval
bindings and equality with the selected export. Generic inference never receives
annotations, PSD layers or benchmark metadata as image ground truth.

```sh
uv run --frozen python scripts/phase4b9_assess.py freeze \
  --run runs/phase4b8-2-lightning-review-v2 \
  --output runs/my-arm-family --export-if-missing
uv run --frozen python scripts/phase4b9_assess.py infer \
  --family runs/my-arm-family --output runs/my-arm-sam
uv run --frozen python scripts/phase4b9_geometry.py \
  --family runs/my-arm-family --sam runs/my-arm-sam \
  --output runs/my-arm-geometry
uv run --frozen python scripts/phase4b9_hybrid_probe.py \
  --family runs/my-arm-family --geometry runs/my-arm-geometry \
  --output runs/my-arm-probe
uv run --frozen python scripts/phase4b9_reference.py \
  --family runs/my-arm-family --output runs/my-arm-reference-audit
uv run --frozen python scripts/phase4b9_report.py \
  --family runs/my-arm-family --geometry runs/my-arm-geometry \
  --probe runs/my-arm-probe --audit runs/my-arm-reference-audit \
  --output runs/my-arm-review
python3 -m http.server 8805 --bind 127.0.0.1 --directory runs/my-arm-review
```

Choose a free port while the supplied gallery is running. Existing directories
are never regenerated in place. `infer` takes the original review run's GPU lock
and invokes the pinned offline See-through worker with `--sam` sequentially for
canonical neutral and the selected helpers. It is not a global GPU scheduler.
The worker verifies local source/checkpoint pins and input hashes. Ordinary tests
use synthetic fixtures and never require GPU inference or downloads.

## Heuristics and uncertainty

1. Validate each SAM `input_sha256`, mask grid and frozen family binding. Keep
   independent overlapping `handwear`, `topwear` and `face` masks explicit.
2. Keep substantial four-connected arm-category regions. Require two regions for
   bilateral proposals. Interpret viewer-left/right as anatomical right/left only
   for the inspected frontal, non-mirrored case. This is an assumption to review.
3. Find upper sleeve surfaces adjacent to the torso. Topmost arm pixels alone
   are invalid when a hand is raised. Surface anchors are not shoulder pivots.
4. Use face colour as a skin hint and torso colour as a cloth hint. Locate a
   connected hand candidate and cuff interface. Similar skin/cloth chroma is
   explicitly rejected. Dark outlines, finger gaps, accessories and varied
   materials can still defeat this heuristic; it never validates fingers.
5. Compute an interior distance-weighted sleeve path on a four-pixel grid and
   fit a two-segment projection. Near-straight paths produce a broad unresolved
   elbow range. A touching upper/forearm can shortcut that path; a separate
   distance-weighted sleeve-lobe hypothesis retains the alternative and disagreement.
6. Split sleeve pixels by proximity to the two proposed segments and isolate the
   skin-colour hand candidate. These are exploratory masks, not rig-ready parts.
   Joint overlap textures, separation seams and draw order are still unreviewed.
7. Compare projected segment lengths normalized by each SAM torso height. Exclude
   unresolved straight-arm fits from the bent-view consistency ratios. These
   ratios cannot distinguish projection, cloth thickness, mask errors and redraw.

No raw difference image is used as proof of newly exposed clothing or correct
hidden geometry. The original is the only independent source artwork; every
canonical/helper pixel remains a synthetic inference artifact. Yellow inspection
radii are heuristic, not probabilities. The first three failed landmark approaches
are kept in `runs/phase4b9-geometry-v1` through `v3`; `v4` supplied the raster probe.
`runs/phase4b9-geometry-final` retains the same numerical hypotheses with explicit
algorithm hashing and the appropriate uncertainty radii in its overlays.

## What the hybrid diagnostic does and does not test

The diagnostic registers only a selected arm onto the canonical reference using
one uniform torso-height scale and shoulder translation. It removes the old arm
support to white **as an explicit unresolved-backing diagnostic**, inserts the new
arm and renders 21 fade samples. It saves both arm cutouts, endpoint images,
removed-support visualization, per-frame exactness checks and an animated WebP.

The visible shoulder hole and old outline residues are actual failures of this
simple extraction/registration. The translucent old/new arms are a failure of
ordinary crossfade for widely separated poses. Exact neutral return and unchanged
pixels outside the arm union are separate observations. No result is labelled a
PSD2Live gesture, verified torso reconstruction or accepted-rig replacement.
A future hard swap, better mask cut or source-view reconstruction could address
some failures; those alternatives still need an appropriate original attachment.

`phase4b9_reference.py` independently verifies the frozen accepted project hash,
reads its existing unsided-arm inspection and verifies historical original-image
SAM against the Git-pinned Phase 4B.8 benchmark. It also measures the saved fifth
guide without editing it. This is read-only evaluation, not neural conditioning.

## Preserving the accepted behavior

Run the existing validators against the immutable accepted runtime:

```sh
uv run --frozen python -m unittest discover -s tests -v
node tests/test_rp_talk.mjs
node tests/test_mouth_invariant.cjs
uv run --frozen python scripts/phase4b9_regressions.py \
  --output runs/my-arm-preservation-regressions
uv run --frozen live2d-studio preview-live \
  --model runs/references/codel-combined-v1/candidate/stages/export-f30df9451395/runtime/Generated_artwork.model3.json \
  --port 8806 --no-open
```

The regression script verifies the reference manifest/runtime hashes, runs the
unchanged 496-body/819-mouth Core probes and the dense face, body and coexistence
browser suites using pinned local Core libraries. Fresh isolated browser profiles
and all diagnostics stay in the new output run. It writes no editor, source or
production files. If the ignored reference/model caches are missing, restore
those exact local artifacts; do not regenerate or repin the accepted reference.

The current result is a reproducible assessment with a blocked rig gate. Before
an experimental arm rig, review a source-view bilateral cut, the arm's shoulder
and elbow attachment, and the hidden backing exposed by that motion. Preserve
the exact accepted face/head/artwork as the user requested. No additional fifth
pose, final articulation or deployment is authorized by this report.
