# Phase 4B.11 — independent elbows and concealed sleeve overlap

The native Cubism rotation-deformer experiment bends each elbow independently,
raises its hand toward chest height and returns to rest. The user accepted it as a limited elbow prototype. It remains an experimental
candidate, not a promoted reference. The user's rejection of the first separating
elbow led to a local sleeve-overlap repair. The exact right overlap was explicitly
approved **for continued validation**, not final animation acceptance.

Baseline: `009824853de7b5b9e52ec8908da10c896f9ed6a6`. Original artwork,
`codel-frontal-master-v1`, `codel-frontal-prototype-v1`, the historical angled rig
and production SillyTavern remain unchanged. No models, dependencies or drivers
were installed; no neural inference or whole-character redraw was performed.

## Actual hierarchy and evidence

The accepted project has three source meshes per side beneath each shoulder warp.
The shoulder parameters are `ParamArmRightOpen` and `ParamArmLeftOpen`; body,
breathing and proportion axes are inherited through their existing ancestors.
The meshes have no independent elbow axes. Their upper/forearm and forearm/hand
textures meet at flat cuts with **zero overlap rows**. Separate layer names did
not establish usable elbow joints or concealed joint caps.

The four reviewed helper poses and neutral canonical are hash-verified through
`runs/phase4b9-family`. Existing contour hypotheses remain uncertain; the earlier
2.77× right projected-forearm discrepancy is not repaired or called anatomical
truth. The diagnostic uses the median sleeve support at the actual cut as a
reproducible pivot hypothesis, normalized to the source canvas. Both sides are
inspected separately. Shoulder points remain sleeve surface anchors, not measured
skeletal pivots. The local gallery allows click-based landmark proposals, saves
them in this browser under the evidence hash and downloads them as JSON. It does
not silently alter the rig or infer approval from corrections.

## Method comparison and repair

1. Distal mesh keyforms under the existing shoulder parent failed. Raising the
   draw order exposed distorted sleeve/hand shapes, and the 697-sample combined
   Core audit recorded **8,983 visible triangle reversals**. This is retained as
   a failed method even though isolated mathematical affine tests pass. The parent
   mapping/export is not equivalent to an unconstrained pixel-space rotation.
2. Native `canvas_rotation` places a shared forearm/hand rotation beneath the
   existing shoulder owner, preserves the fitted rest pose, and keys its angle.
   It avoids that distortion. Upper-arm geometry stays unchanged under elbow-only
   input. The hand and cuff follow the same transform without individual finger
   deformation or a separate wrist axis.
3. The initial draw order put the raised hand behind the torso, then behind the
   skirt. Explicit depth slots above both garments fixed this in fresh candidates.
4. The user reported: “Elbow is desintigrating while moving, we need more overlap
   there.” A small elliptical patch derived from the existing sleeve now covers
   the exposed joint gap. It sits behind the original upper sleeve and forearm,
   inherits shoulder movement, and is invisible at zero elbow input. Its hidden
   shape is inferred and its duplicated samples are **not observed ownership**.
   All original texture assets remain unchanged.
5. The user approved the exact right patch with “Approve this overlap for continued
   validation.” The left patch is derived separately from that side's actual sleeve
   width, cut and geometry. The user subsequently accepted the left overlap and both coordinated gestures
   with “Accept as a limited elbow prototype.” This exact final review is bound
   to the runtime payloads, project, joint proposal and overlap hashes.

Native elbow travel is 120 degrees in this experiment, not a validated biological
range. Four-second Cubism clips use horizontal Bezier tangents and coordinate the
elbow with 15% of the existing shoulder control. They write only their own elbow
and shoulder channels. The existing seven expressions, mouth system, physics,
head/body controls and original shoulder gestures are preserved.

No image crossfade or replacement helper pose is used. A hybrid helper-artwork
approach remains possible, but would need registration and reviewed seams; the
older naive crossfade failure is retained. A separate wrist rotation is deferred
because the cuff cut has no independently reviewed overlap. It is not shown as
an available viewer control.

## Validation scope and limitations

The benchmark records the exact final results and logs. The bilateral Core audit
samples 898 poses, including 402 elbow/shoulder/head/body combinations. Browser
scenarios inspect 10/25/50/75/90/100% positions, dense rise/return, actual clips,
talking, moving head/breathing/hair, repeated starts, interruption, held elbows
with Nod/Question and fresh model instantiation. Exact candidate-neutral return
is distinct from equality to the earlier reference render.

The first native one-arm neutral differs from the previous reference capture in
368 pixels (maximum channel delta 37, mean absolute channel delta 0.001152).
Original raster assets are exact; fitted hierarchy/depth changes do not establish
byte-identical rendering to the older reference. This discrepancy is retained,
not hidden behind an exact-neutral-return claim. The final bilateral neutral
differs in 880 pixels, maximum RGBA delta 170, mean absolute channel delta
0.003656; compositing over white yields maximum RGB delta 24.02 and mean
0.002377. No byte-identical match to the older reference render is claimed.

The unchanged Phase 4B.10 shoulder scenario expects exactly three moving meshes.
It fails once an invisible fourth overlap mesh inherits shoulder movement. Its
failure remains recorded. The separate Phase 4B.11 shoulder scenario requires
exactly three **visible original** arm meshes, plus exactly one invisible overlap
on a side with an elbow. It retains the torso/head/opposite-arm isolation and exact
neutral-return checks. No numerical triangle/opacity or facial gate is relaxed.

Sleeve shape and folds are still a limited 2D illustration approximation. New
joint shading is not independently reconstructed anatomy. The user explicitly accepted the combined animation as a limited prototype.
This does not certify anatomy or promote it over the frozen frontal reference.

## Local review and reproduction

- Final candidate: `runs/phase4b11-bilateral-v2/rig` (editable project and runtime).
- Right-only repaired predecessor: `runs/phase4b11-overlap-v2/rig`.
- Historical failure gallery: <http://127.0.0.1:8813/>.
- Approved right-overlap review: <http://127.0.0.1:8813/overlap/>.
- [Final gallery](http://127.0.0.1:8813/final/) and
  [live before/after viewer](http://127.0.0.1:8816/).
- [Benchmark](benchmarks/phase4b11.json) records 382 final elbow browser frames,
  the 898-sample Core pass, scoped shoulder checks and retained historical count failure.
- All 233 Python tests and both JavaScript regression suites pass. All 17
  pre-existing expression, physics and motion payloads remain byte-identical.
- [Commands and design](phase4b11-elbow-rigging.md).

Stop after Phase 4B.11 with that explicit limited visual acceptance. No deployment or reference
replacement is included.
