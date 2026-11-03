# Generic facial artwork preparation

Phase 4B.1 extends the existing facial stage. It reads the reviewed native-grid
restoration, never the artist's other expression tiles or benchmark masks. It
runs with Python, NumPy, Pillow and SciPy already pinned in the main environment.
No inference/checkpoint installation or manual painting is required.

## Ownership and concealed skin

The builder requires exactly one face and mouth, and one white/iris/lash triplet
per side. Each eye's support is the union of its semantic layers. A small relative
margin covers antialiasing and shifted contours. Only source pixels owned by the
face or that feature are eligible; hair, brows, nose and unrelated parts are not
silently relabelled. Face-owned samples within the eye support transfer to the
moving eye assembly, retaining exact RGBA and unique observed ownership.

For a sparse closed mouth, a bounded rectangle spans disconnected contour pieces.
A local skin estimate and colour residual identify nearby mouth ink. The contour
and its immediate skin edge transfer from face to mouth. The original mouth input
and all other source files remain unchanged in their predecessor stages.

Nearby source-owned face samples provide the skin palette. Dark contour outliers
are excluded relative to that local distribution. A bounded Jacobi harmonic fill
interpolates concealed skin from these samples. Fewer than twelve usable samples,
missing roles, unsupported normalization or an unsupported connected lash fail
explicitly. The result is a plausible candidate, not known anatomy.

Concealed skin is separate transparent artwork with small overlap beyond the cut
boundary. Exact coincident raster edges produced visible cracks after separate
meshes were triangulated and texture-filtered; overlap fixes those cracks. Original
face RGB is used on the overlap where available. The importer places the backing
above the face and below moving features, with the inspected face parent.

The observed-layer neutral composite still passes the unchanged 99.5% source gate.
Runtime backing is opaque, including behind original alpha 254. Thus the final
render is **not byte-identical** to the old runtime or source. The separate runtime
comparison records this effect; observed-source copying is not presented as final
render equality. Every generated alternative records its hash, provenance and
unvalidated hidden-surface status. Its alpha defines generated support. A separate
exact-source neutral mouth alternative is marked as copied source artwork.

## Independent blinking

PSD2Live's generated meshes own blink keys. The inspected per-eye axes must be the
supported 0/1 opening axis; an unfamiliar rig is refused. The builder copies the
open geometry to the closed key, then contracts the complete surface toward a
relative lid line. It inherits the existing head and gaze rig. Both sides receive
independent controls, and open iris/pupil/lash artwork remains intact.

A separate closed-lash raster comes from the strongest connected dark upper-lash
component. Colour and per-column stroke thickness come from the input. The pixels
are projected onto a shallow relative curve with fractional alpha deposition.
There is no fixed skin colour or character coordinate. An insufficient connected
upper lash is an explicit failure. The variant inherits the inspected eye parent.

Over the final quarter of closure, this variant replaces the contracted open
assembly. White and iris opacity also reach zero: Cubism clipping does not make
an iris disappear merely because its mask drawable's opacity is zero. Intermediate
states combine ordinary geometry interpolation with this narrow crossfade. They
remain stylized; this is not a reconstructed three-dimensional eyelid or a learned
anatomical model. No feature is merely hidden without replacement skin/lash artwork.

## Mouth strategy

Sparse closed-source mouths receive an exact-source neutral contour variant and
a separate dark cavity. The cavity width, centre and colour derive from the source
mouth support and darkest local contour samples. Its height is a modest relative
assumption, explicitly uncertain. There are no invented teeth, tongue or highlights.

The cavity gets real mesh opening keys at 0, .25, .5, .75 and 1, plus opacity at
closure. The source contour fades into it over the first quarter of opening.
Both inherit the inspected mouth deformer, including smile/frown and head motion.
The unreliable procedural mouth/lip drawables remain archived but have zero
render opacity in this branch; explicit source and interior assets replace them.
Their original source is not deleted or painted over.

Already-open artwork is different. A mouth with height/width at least .32 and
observed occupancy at least .4 retains the existing PSD2Live mouth treatment.
This is a conservative geometric strategy selector, not an anatomical classifier.
Girl2 exposed this requirement: forcing the sparse closed-mouth replacement onto
its already-open source inverted the apparent opening range. That failed candidate
is retained, and the corrected branch is separately rendered. Neither strategy
can skip final visual review.

## Reproduction and review

The normal application entry point remains:

    uv run --frozen live2d-studio create --input character.png \
      --output runs/NEW-character --rights 'Author; license; source URL'

Follow the semantic and visual review commands in [the creation guide](phase4b-create.md).
After semantic review, facial output contains a new layers manifest, exact-source
masks, generated/uncertain masks, alternatives, reconstruction report and preview.
Project output records discovered bindings, installed artwork and blink edits.
Existing cache validation, stage locks, failed-attempt retention and hard gates
remain intact. No production deployment action was added.

For Sara, use the retained flat input at assets/references/phase4b-sara/portrait.png
and reuse the bridge and SAM directory named in runs/phase4b-sara/creation.json.
Do not resume a frozen accepted run after source-code changes: create a fresh run
with those validated caches. Changed reconstruction/authoring code invalidates its
stages and requires a fresh visual review; it does not rerun validated inference.
The later open-mouth regression fix reproduces Sara's facial artifacts byte-for-byte.

Open the reviewed, frozen candidate without authoring or inference:

    uv run --frozen live2d-studio preview-live --run runs/phase4b1-sara

The viewer verifies exported file hashes. Accepted Phase 3 and 3.1 remain available
through their previous preview paths. The new pipeline does not replace their pins.

Repeat the actual browser suite against any supported existing export:

    uv run --frozen python scripts/phase4b1_render.py \
      --model MODEL.model3.json --output runs/NEW-facial-render

Add --transitions for time-sampled talking during all seven expressions, expression
fades and control ramps. The normal 57-frame suite covers quarter-step left/right
blinks and mouth opening, isolated smile/frown, independent head/gaze, seven
head-locked expressions, talking, combined head/blink/mouth and exact reset.
The current installed Core/PIXI/bridge and dedicated local Chrome are used.

Build a comparison from fresh matched render evidence:

    uv run --frozen python scripts/phase4b1_compare.py \
      --baseline runs/phase4b1-sara-baseline --candidate runs/phase4b1-sara \
      --output runs/NEW-comparison --benchmark runs/NEW-comparison/benchmark.json

This evaluator alone reads Sara's spritesheet as an independent visual reference.
No multi-reference reconstruction experiment was performed. Its artist-drawn happy
mouth and closed-eye curvature remain richer than the generated alternatives.
