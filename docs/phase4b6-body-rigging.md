# Phase 4B.6 — optional body motion

`prepare-body` builds a **separate candidate** from an existing verified creation
run or one of its local authoring experiments. It reuses the editable project and
source layers; there is no inference, model download, training or deployment.
Existing creation defaults and accepted models remain unchanged.

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio prepare-body \
  --baseline runs/phase4b5-codel-full-first --output runs/NEW-body
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio preview-live \
  --model runs/NEW-body/export/runtime/Generated_artwork.model3.json \
  --compare-model runs/phase4b5-codel-full-first/stages/export-0547c939391c/runtime/Generated_artwork.model3.json \
  --port 8788 --no-open
```

The preview requires only the exported bundle and the already installed local
Cubism/PIXI libraries. It does not need SillyTavern running, an LLM, MCP, GPU
inference, or a coding agent. Restart idle to synchronize the two playback starts;
the original 12-second loop and new 16-second loop retain their own timelines.
Only exported motion groups appear as gestures. Head/body/hair switches and sliders
control real Cubism parameters, not canvas motion. The comparison uses equal model
scale; its responsive page layout does not animate the illustration.

## What the diagnosis established

Codel has separate face, ears, nose, facial-feature, front-hair, back-hair, neck,
topwear, bottomwear, legwear and one unsided handwear mesh. The last contains both
sleeved arms and both hands. Its 260,082 pixels form one connected alpha component.
The copied arm artwork has no generated backing; its ownership remains a parser
candidate, not independently verified anatomy.

The importer already creates a body XY parent, lean/proportion parent, body
rotation/breath parent, head rotation, head container, facial parents, and separate
hair-follow/physics parents. All face and hair children inherit head tilt. XY head
motion is much weaker in the hair than in the face: at X=12, baseline maximum
vertex displacements at the 570-pixel character framing are approximately 1.97 px
for the face, 1.20 px for front hair, and 0.25 px for back hair. The original idle
only reaches X=2, Y≈0.69, Z=1. Actual viewer capture confirms that it plays this
motion and executes physics; it is not merely changing controls without rendering.

Breathing already deforms visible upper-body geometry. At Breath=1, topwear and
attached sleeves move up to 6.56 rendered pixels, versus about 0.68 for bottomwear
and 0.41 for legwear. These are maximum vertex displacements, not perceived motion
scores. The existing neck/head overlap and rotation parent are retained. A rigid
fit to exported face vertices under Z=5 recovers the actual head pivot inside the
neck support, with approximately 0.00018 source-pixel residual. The benchmark
records its measured normalized position; no character coordinate enters authoring.

## Reusable authoring and honest limits

`src/live2d_studio/body_rig.py` finds mesh bindings through semantic layers and
actual ancestry. It requires one face, a common head XY parent for all discovered
head/face/hair parts, a head Z rotation and a body breathing parent. It rejects a
head ancestor that also owns torso or limb meshes. Missing/ambiguous bindings and
unbounded key expansion fail explicitly. Portraits with no visible hands work.

The edit adds a small shared translation to existing head-cage keys: 0.08 of cage
width over the full inspected X range and -0.04 of cage height over the full Y
range. The sign follows the importer's upward-positive head parameter in a
local downward-positive coordinate system. Existing facial perspective fields,
rotation pivot, neck attachment, body deformation, draw order and raster ownership
stay intact. All directly bound axes are enumerated; neutral keys are untouched.
This is a conservative 2D apparent turn, not a recovered three-dimensional skull.

Separate front/back pendulums and their pinned-root deformation fields are reused.
Output scales become 3.2 and 5.0 parameter units/radian, respectively; existing
lengths, damping, weights and normalization remain distinct. Exported physics3 is
used by the installed runtime. A release test moves the head, stops its inputs,
and measures delayed hair response and settling. No authored sine-wave hair
substitute is needed. Individual strands are not split without reliable evidence.

The 16-second idle uses different Bezier timing and pauses for X/Y/Z, body
compensation and breathing. Each curve has equal first/last values and horizontal
end tangents. Blinks have separate timing. Two 2.8-second motion groups provide a
small head nod and questioning head tilt. They contain no expression, mouth or
arm curves. The viewer preserves expressions when a motion starts and keeps
manual blinking and talk envelopes active. A short viewer blink can occur during
a gesture while the idle blink clip is interrupted. This gesture-time automatic
blink is a viewer behavior, not a second exported parallel motion track.

There is **no independent arm articulation**. Neither connected components nor
left/right role labels prove shoulder/elbow/wrist ownership. Codel lacks separate
upper-arm, forearm, hand and sleeve surfaces, reviewed joint landmarks, and hidden
pixels for the crossed-arm/torso intersections. Existing SAM handwear/topwear
classes do not supply those joint boundaries. No pixel cut or guessed joint is
introduced. Arms keep their shared body attachment, including breathing; this must
not be described as an arm gesture or a full-body rig. Optional limb preparation
currently produces an evidence inventory and explicit static fallback.

## Preservation and export

Source-stage inventories are verified before authoring. The builder saves the
current editor, opens the predecessor, records inspected hierarchy/recipe/motions,
and authors through loopback MCP. All archived raster asset hashes and decoded
source-layer RGBA must match the predecessor. A new PSD, editable project and
portable runtime are exported. Seven original expressions remain selected; the
new gesture references are checked with the normal bundle validator.

PSD2Live 3.6.7 leaves a dirty flag after saving these custom Bezier clips. The
builder first preserves and verifies the complete candidate archive, then checks
out the predecessor history node and independently opens the saved candidate for
export. It never uses `discard_unsaved`. Early failed save/reopen and motion-name
attempts remain local. This is a version-specific recoverable authoring workaround,
not permission to overwrite the accepted predecessor.

## Runtime evidence

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b6_render.py \
  --model runs/NEW-body/export/runtime/Generated_artwork.model3.json \
  --output runs/NEW-body/body-review
node scripts/probe_body.cjs \
  .cache/phase3-st/data/default-user/extensions/Extension-Live2d/lib/live2dcubismcore.min.js \
  runs/NEW-body/export/runtime/Generated_artwork.model3.json \
  runs/NEW-body/authoring/body-inspection.json > runs/NEW-body/core-body.json
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b3_render.py \
  --model runs/NEW-body/export/runtime/Generated_artwork.model3.json \
  --correspondence runs/phase4b5-codel-full-first/stages/project-8e223ef17e1b/transition-correspondence.json \
  --output runs/NEW-body/dense
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python -m unittest discover -s tests -v
node tests/test_rp_talk.mjs
```

Use the matching source project's transition correspondence; never substitute
another character's IDs. `phase4b6_regressions.py --output runs/NEW-regressions`
builds separate aligned Girl2/Sara candidates and retains a failing aggregate
status if any Core gate fails. The broad audit includes 481 combined synthetic
trajectory samples plus independent axes; browser tests separately play real
exported idle/gesture clips, expressions and physics. Both kinds of evidence matter.

Actual Core geometry, parameter traces, rendered silhouettes, and development/user
visual review remain separate gates. The broad probe retains the existing 1e-12
area-product threshold and exact neutral return. No failed lip geometry is waived
because it was inherited. Raw float opacity excursions and the existing eight-ULP
acceptance tolerance remain visible in reports. The standalone CDP suite tests
network isolation and reload with a pixel-identical neutral render.

The review gallery's WebM recordings retain measured intervals between continuous
browser samples. They are sampled-frame recordings, not every 60 Hz display frame.
All PNG frames, timestamps, PSDs, projects, runtime bundles, videos and failed
attempts stay under ignored `runs/`. Full final measurements and review limitations
are in [results](phase4b6-results.md) and [benchmark](benchmarks/phase4b6.json).
