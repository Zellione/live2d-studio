# Phase 2.6 — source fidelity and rigging readiness

Completed 2026-11-02. **Source-preserving postprocessing substantially improves
Girl2, with an actual animated prototype and explicitly limited visual acceptance.**
It does not turn See-through into a generally reliable anime parser. Girl1 and
Wikipe-tan are rejected; Boy1 preserves appearance but lacks acceptable fine part
ownership for rigging. No character is production-ready. Phase 3 was not started.

## Frozen reference and implementation

Starting commit `a29f050`; all Phase 2.5 coverage, composite and independent Girl2
metrics were recomputed **exactly**, before pipeline changes. Historical
`docs/benchmarks/phase2-5.json`, both golden fixture directories, baseline algorithm,
main dependency lock, isolated neural lock, upstream source and model checkpoints
are unchanged. Baseline evidence: `runs/phase2-6-audit/baseline.json`.

First milestone `dfcc02c` introduced independently replayable restoration and
neck repair after 46 tests. Validated milestone `b8a5032` adds contour correction,
expanded runtime QA and the explicitly rejected guard experiment after 51 tests.
The final code adds these CLI stages:

- `refine`: native-grid backprojection, unique source ownership, connected
  neck/chest skin repair, nearby facial contour reassignment, structural rejection
  and small-component flags. No GT or new inference enters this stage.
- `readiness`: paired-part inventory, missing geometry and procedural alternatives;
  it never grants aesthetic acceptance or sets `rig_ready`.
- `prepare-rig`: **experimental**, separately marked hidden guard bands; its
  measured hair regression means it is not recommended for this character.
- `review-poses`: actual renderer diagnostics and a local, consistently cropped
  21-pose sheet. Numerical findings remain separate from visual judgement.

See [quality contract](phase2-6-quality.md) and
[reproduction commands](../backends/see-through/README.md). No package installation,
new weights, host changes, manual painting or hosted image service was needed.

## Pixel provenance and restoration

Generated layers are backprojected from recorded center padding to the unchanged
source raster. The frontmost >127 alpha candidate supplies a unique ownership
label; very close silhouette gaps can inherit a nearby label. At each owned
location, only that layer receives exact source RGBA. Higher layers are cleared;
generated geometry below an opaque owner remains. Fractional source alpha is
preserved without duplicate lower-layer opacity. No original-image overlay exists.

Manifest v2 remains compatible. Observed masks prove exact source copying;
semantic ownership remains a candidate. SAM agreement is supporting evidence,
not independent truth. Disagreement, changed ownership and generated pixels retain
uncertainty. Validation rejects duplicate source ownership and altered observed
RGBA. Original bytes/hash, parent manifest hash, SAM mask hashes and configuration
are retained. Native-grid replays reproduce all four final manifests exactly.

Neck repair samples frequent bright colours from agreed face/neck regions, then
extends connected source skin into clothing within relative anatomical bounds.
Enclosed small line-art gaps travel with the skin. It reads neither character
coordinates nor XCF masks. The bright-palette assumption limits darker/complex
artwork; it is not a universal skin detector.

**Actual motion exposed a defect in the first restoration:** dark source eye and
mouth outlines just outside generated masks remained on the face, causing doubled
lines during blinking/closing. The correction moves nearby source ink into the
appropriate moving white/lash/brow/mouth/nose candidate, without duplicating it.
This is bounded local geometry/contrast inference, not an invented original shape.
Initial and corrected rendered evidence are both retained.

## Measured image quality

Native resolution, source alpha >127, identical independent coarse evaluation
mapping. Coverage counts candidates, not correct ownership. RGB MAE uses 0–255
channels; before values include back-resampling the 1280px model output.

| Input | Candidate coverage before → after | RGB MAE before → after | Exact visible RGBA after | Mean visible IoU before → after |
| --- | --- | --- | --- | --- |
| Girl2 | 99.32% → 99.89% | 8.283 → **0.055** | **99.89%** | 0.7830 → **0.9667** |
| Boy1 | 99.22% → 99.87% | 13.387 → **0.081** | **99.87%** | 0.9100 → **0.9237** |
| Girl1 | 91.94% → 93.20% | 34.484 → 15.654 | 93.20% | 0.5868 → **0.5826** |
| Wikipe-tan | 76.71% → 77.16% | 52.020 → 35.060 | 77.16% | No independent GT |

Before restoration, exact visible RGBA was only 0.42% Girl2, 0.44% Boy1,
0.28% Girl1 and 3.27% Wikipe-tan. Exact copied pixels do not establish semantics.
Girl2 preserves 99.70% of measured source edge pixels exactly; silhouette IoU
0.998855, canvas alpha MAE 0.0941. These are image metrics, not an animation score.
356 foreground pixels remain unsupported rather than being assigned arbitrarily.

Girl2 independent visible class IoU:

| Class | Phase 2.5 | Final |
| --- | ---: | ---: |
| Hair/accessories | 0.9766 | 0.9884 |
| Face/ears/nose | 0.9573 | 0.9689 |
| Eyes/brows | 0.9026 | 0.9488 |
| Mouth | 0.9078 | 0.9169 |
| Neck/exposed chest | **0.1376** | **0.9809** |
| Clothing/sleeves | 0.8162 | 0.9960 |

Coarse semantic accuracy: Girl2 **89.73% → 99.32%**, Boy1 **97.58% → 98.28%**,
Girl1 **81.46% → 82.39%**. Full authored-layer scores are retained in JSON, but
those shapes are not independent hidden-anatomy truth.

Ablation on Girl2: source preservation alone mean IoU 0.7851; adding neck repair
0.9544; adding nearby ink ownership 0.9667. The neck operation reassigns 27,757
source pixels; the contour operation another 457. Neutral RGB stays identical
across those ownership changes, showing why a composite metric misses rig defects.

Girl1's mean IoU decreases despite higher aggregate accuracy: mouth IoU drops
0.3813 → 0.3261. The badly positioned generated mouth/neck boundary, native
resampling and source silhouette clipping reduce its predicted mouth support;
restoring colours cannot repair the underlying wrong geometry. Other coarse
classes improve slightly. The character remains rejected; no threshold was relaxed.

## Expanded benchmarks and crop experiment

[stevenburrow's CC0 collection](https://opengameart.org/content/anime-girl-and-boy-portraits)
was rechecked. Two additional illustrations, Girl1 and Boy1, come from the existing
local XCF archive; no further download or redistribution was needed. Girl1 has
multiple bangs/ponytails, Boy1 short blond hair and a beard. They are additional
characters **from the same artist**, not evidence of broad style generalization.
`benchmarks/oga-*.json` pins source hashes and reviewed coarse layer mappings.

GIMP exports visible leaves without changing the XCF. Compositions versus GIMP
projection differ at 18 nontransparent pixels for Girl1, 11 for Boy1; alpha differs
at 0 / 2 pixels. Most raw differences are irrelevant RGB under zero alpha.
Separate extraction replays reproduce input hashes. Only flattened PNGs enter
inference. Beard is explicitly grouped with hair for coarse evaluation; irides,
whites/brows and mouth variants cannot receive independent fine scores from the
combined authored layers. Initial local benchmark labels incorrectly said Girl2;
corrected replay metadata and committed definitions identify each actual group.

Wikipe-tan gets a reversible 440→660 transparent padding experiment (110px each
edge), preserving the original bytes and transform record. Existing pinned BF16
models still assign facial regions to back hair; face support under eyes is zero.
Restored coverage reaches 91.76% on the padded canvas, but semantics remain
rejected. Padding addresses scale/context, not missing anatomy or tilt. Rotation
was not tested; neither crop nor orientation is established as the sole cause.

## Actual runtime and visual review

Recommended artifact: `runs/phase2-6-oga-v2-build/`, corresponding exactly to
`runs/phase2-6-oga-release/layer_manifest.json`. Connected MCP:
Create → Save → PSD → Reopen → Runtime. Fresh IDs/state, no Phase 1 coordinates.
19 source layers become 21 imported layers, 24 meshes, 28 deformers and 20
parameters. PSD2Live warns about generated through-bangs draw-order normalization.
Bundle checks and actual Cubism Core 5.0.0 basic geometry checks pass.

The new isolated ST/installed-extension harness measures **21 poses**: neutral,
six eye/mouth states, X/Y/Z ±15°, and eight combinations of head movement with
blink, half blink/mouth, open mouth and wink. Neutral provides all three zero
angles. Same harness and camera controls replay the unmodified Phase 2.5 export.
Both complete resource/load/reload checks with zero control noise, no unexpected
HTTP failures or uncaught JS exceptions. Two initial diagnostic runs stalled
because the new geometry probe referenced the destroyed Core after reload; the
probe was corrected, with failed logs retained. Runtime renders are real, not mocks.

Visual inspection of the original, initial restoration, corrected restoration and
combined pose sheets confirms restored red ribbons, source eye details/colours,
neck/chest shading and removed stationary duplicate eye/mouth contours. Blink and
mouth still use PSD2Live procedural shapes; no independent skin eyelid, pupil,
teeth/tongue or phoneme system was fabricated. Intermediate lids remain flat;
brows through bangs change style. Thin hair transition gaps remain under combined
motion. The restored original has sharper/noisier ink than the smoothed neural
output; large colour-gradient counts cannot be treated as automatic defects.

| Actual 21-pose diagnostic | Phase 2.5 | Corrected restoration | Experimental guards |
| --- | ---: | ---: | ---: |
| Maximum enclosed transparency pixels | 292 | 502 | 405 |
| Maximum small detached-component pixels | 1 | 3 | **42** |
| Maximum triangle orientation changes | 30 | 24 | 24 |
| Nonfinite vertices / invalid opacity | 0 | 0 | 0 |
| Triangles expanding >10× | 0 | 0 | 0 |

Counts include legitimate hair gaps and intended blink folds. They are warnings,
not quality thresholds. Hole overlays locate the thin forehead/ponytail/face-edge
gaps; the higher hole count is a **measured remaining regression**, not concealed
by better RGB. The 6,028 generated guard pixels leave neutral RGBA unchanged and
reduce some holes, but introduce visible detached hair tips: **reject this export**.
`prepare-rig` remains opt-in experimental; it does not run inside `refine` or build.

## Separate acceptance gates

| Character | Semantics | Source fidelity | Hidden geometry | Import/Core | Visual animation |
| --- | --- | --- | --- | --- | --- |
| Girl2 | Accepted for six coarse groups | Accepted with small fringe omissions | Reviewed, incomplete | Accepted | Limited prototype accepted; high-quality gate unmet |
| Boy1 | Coarse improvement; fine beard/brow ownership rejected | Accepted with small fringe omissions | Insufficient support | Not attempted | Not tested |
| Girl1 | Rejected face/chest/iris geometry | Incomplete | Rejected | Not attempted | Not tested |
| Wikipe-tan | Rejected, including padded test | Incomplete | Rejected | Not attempted | Not tested |

Thus the phase demonstrates measurable fidelity/readiness improvement and a full
real-art technical pipeline. It does **not** satisfy an unrestricted natural-
animation quality gate. Ordinary neural `build` remains closed; experiments use
the explicitly requested connected MCP route after review. No production deployment.
`rig_import.animation_tested=false` describes import validation only. The separately
recorded isolated browser runs do test actual animation; neither record supersedes
the other's scope.

## Performance, regression and next steps

Postprocessing takes about 0.94–1.95 seconds on CPU for these single runs. No neural
rerun was needed for original Girl2/Wikipe-tan. Only Girl1, Boy1 and padded
Wikipe-tan used new BF16 inference: 116.53 / 116.97 / 116.13 seconds, peak Torch
allocation **11.85 GiB**, reservation 16.02 GiB. Separate SAM runs take 2.13 / 2.07 /
2.38 seconds with 4.66 GiB allocated. Whole-device samples/timings are local;
compact records retain the actual values, not a speed guarantee.

51 tests pass, including exact/unique source provenance, hidden preservation,
wrong-SAM-source rejection, deterministic replay, disconnected skin exclusion,
contour transfer, guard neutrality and QA warnings. Synthetic Phase 2 metrics
remain unchanged; isolated Phase 0/1 browser regressions pass. 137 original/copy
ST/extension file pairs match their recorded hashes. Golden fixtures and historical
Phase 2.5 records are unchanged. All generated artifacts remain ignored.

No manual image editing was used. Visual acceptance still requires inspection;
a failed face parser cannot be corrected just by source copying. Before Phase 3,
priorities are reliable concealed face support, fine beard/brow/eyelid separation,
original-art-aligned occlusion boundaries and rig-aware underlap that does not
change mesh silhouettes. Broader independent artwork/style coverage is also needed.
Do not promote See-through to an unconditional default or train a custom model on
this evidence. **Stopped after Phase 2.6.**

Local review: `runs/phase2-6-review/index.html`. Recommended pose sheet:
`runs/phase2-6-oga-v2-review/poses.png`. All initial/rejected attempts, raw model
outputs, source/GT layers, masks, PSDs/projects, runtime bundles and transcripts
remain under `runs/phase2-6-*`. Concise numerical evidence:
[`benchmarks/phase2-6.json`](benchmarks/phase2-6.json).
