# Phase 2.6 quality contract

A source pixel is attributable by its unchanged native-grid RGBA value and unique
layer owner. This proves **copy provenance**, not anatomical ownership. Semantic
ownership remains a parser candidate, independently evaluated against XCF where
available. Generated and uncertain masks are orthogonal to source provenance.

`refine` inverts the recorded padding/resize into the original raster grid. The
frontmost alpha >127 candidate owns a source pixel. Very close missing silhouette
pixels (0.3% of the smaller dimension) can inherit a nearest owner; all such
changes remain uncertain. Each copied source sample belongs to exactly one layer.
Generated geometry is retained beneath other opaque source owners; layers above
the selected owner are cleared there. Outside the known silhouette and beneath
fractional source-alpha edges, generated pixels are clipped. No flattened overlay
is added. This can truncate speculative hidden extensions and needs motion QA.

Neck repair uses parser-agreed visible face/neck as a palette, relative face
bounds and connected skin extension into clothing. It does not read benchmark
masks or fixed character coordinates. Small enclosed ink holes are included;
ambiguous/disconnected areas remain unchanged. The bright-palette assumption
limits applicability to these inputs and is not a universal skin classifier.
SAM predictions are supporting evidence, never ground truth.

Reports distinguish six gates: semantic decomposition, source preservation,
hidden reconstruction, PSD2Live import, runtime geometry and visual animation.
A structural check can reject, but cannot automatically accept aesthetics.
`readiness` inventories paired eyes, procedural rig alternatives and missing
structures; it never sets `rig_ready`. Existing procedural blink/mouth is preferred
for the reviewed experiment. No unsupported mouth/eyelid anatomy is invented.

`rig_import.animation_tested=false` in Phase 2.5 is the scope of import validation.
The later isolated browser tests did test animation. Both records are correct;
import validation must never overwrite a separate runtime/visual result.

Near-feature source ink is a separate refinement: only dark pixels currently on
face/ears can transfer to nearby eye whites, lashes, brows, nose or mouth. Search
radius is at most 0.6% of image size and 15% of feature width. Far-away ink and skin
stay in place. This fixed the actual doubled lower-eye/mouth contours seen in the
first restoration rig; the original failed frames remain local.

Small relative components and tiny border components are retained and flagged
for uncertain review, not discarded. Source EXIF orientations not handled by the
pinned worker are rejected rather than silently misregistered. The refinement is
not a general background-removal or pose-estimation stage.

`prepare-rig` generates small nearest-interior-colour underlaps for face, neck,
back hair and clothing, only where a higher opaque layer already covers the
pixels. Radius 0.6% of canvas dimension, at most 10% of base support area. Newly
filled pixels are marked in reconstructed/generated/uncertain masks; the neural
model's other hidden-only provenance remains unlocalized. It must leave the neutral
composite exactly unchanged. Its Girl2 experiment is **visually rejected** because
of new detached hair fragments, despite reducing some holes. Never promote it
through a neutral-image metric alone.

Actual browser QA records 21 poses (neutral, six eye/mouth states, six ±15° head
poses, eight combined poses), plus control repeat and reload. Core nonfinite
vertices and out-of-range opacity are invalid. Triangle flips/collapse/expansion,
alpha holes, disconnected components and sharp colour steps are diagnostics;
closed eyelids can intentionally collapse/fold triangles. Duplicated contours,
identity, natural lid shape and plausible hidden anatomy require visual inspection.

The recommended Girl2 export passes numeric/runtime/import gates and limited
prototype motion review. The high-quality visual gate remains unmet because of
thin hair gaps and simplified lids. No report grants production readiness.
