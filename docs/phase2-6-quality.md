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
