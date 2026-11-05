# Phase 4B.5 — independent Codel benchmark

Continued from clean `7863b346d65c16942cb9a376d7b98119ce175a90`.
**The frozen creation CLI converted the original-framing Codel PNG into an
interactive Cubism candidate without character-specific rig operations. This is
technical execution success, not accepted general-purpose conversion.** User
visual acceptance is pending; development review rejects convincing animation
because near-closed eye contours/shading remain visibly defective. A separate candidate using the unchanged optional
expression/mouth scripts fails one existing strict exported-Core invariant.

[Protocol and reproduction](phase4b5-generalization.md) ·
[machine-readable benchmark](benchmarks/phase4b5.json) ·
[art provenance](../benchmarks/phase4b5-art.json).

Local review: `runs/phase4b5-review-final/index.html` (served at
`http://127.0.0.1:8790/`). First-run viewer: `http://127.0.0.1:8786/`.
Separate optional-mouth diagnostic viewer: `http://127.0.0.1:8787/`.
Servers must be running; restart commands are in the protocol document.

## What was tested

Codel Visual Novel Sprite by **LisadiKaprio**, CC BY 4.0 on
[OpenGameArt](https://opengameart.org/content/codel-visual-novel-sprite), also
published on [itch.io](https://lisadikaprio.itch.io/codel-visual-novel-sprite).
The verified ZIP contains one 1078 × 2089 PSD and twelve numbered PNGs, without
a bundled license text. Original artwork and archive remain outside Git.

Selected input: **Codel3.png**, neutral and unblushed, unmodified, SHA-256
`98589fb8750ccfc3664935985fc42810381b2e09f22e1ae8cf4cd6dd45d39a2d`.
The image shows the head, torso, both arms/hands, skirt and upper legs; its bottom
edge excludes lower legs and feet. “Original framing” does not mean a complete
full-body illustration or a fully articulated full-body rig.

The image fits the decoder's 4-megapixel limit, although the documented reliable
target class is a frontal portrait. The original framing was attempted first.
A crop `(180, 0, 900, 760)` was defined and hashed before inference but **not run**:
the original framing reached runtime. No portrait result is substituted for it.

The numbered names required input selection: Codel1, Codel2, Codel8 and Codel3
were viewed before inference, and pixel-difference bounds against Codel2 were
computed to identify its unblushed neutral counterpart. This is disclosed
selection exposure, **not a fully blinded expression holdout**. No tuning used
those images. The PSD remained unopened until the first run was sealed.
Only the selected flat PNG entered creation; no PSD components entered inference,
reconstruction or authoring. Model pretraining exposure is unknown.

## Distinct acceptance results

| Gate | Finding |
| --- | --- |
| Technical execution | All twelve creation stages completed; portable runtime, PSD and editable project exported. |
| Original pixels | Restored neutral: 911,627 / 911,631 foreground pixels exact (99.99956%); zero duplicated observed owners. |
| Semantics | Limited independent facial ink agreement; no whole-character semantic ground truth or accuracy claim. |
| Functional rig | First run passes 401 rendered frames and 72 eye-channel/visible-triangle samples. Optional mouth audit fails its strict seam invariant. |
| Convincing animation | Development-rejected: overlapping quarter-open eye contours and residual shading/fragments; user review remains independent. |
| User acceptance | **Pending; no model promoted.** |

The first run is `runs/phase4b5-codel-full-first/`. Its editable project and PSD
are in `stages/export-0547c939391c/`, with the portable model in `runtime/`.
All source layers, intermediate worker PSD, stages, diagnostics and the first
failed sandbox launch remain preserved. `runs/phase4b5-freeze/first-run-seal.json`
pins the first-run result before independent reference inspection.

The CLI stopped for its normal semantic review. A **development-agent** review
permitted runtime evaluation after inspecting source, layer artwork, face support
and bilateral limbs. It explicitly retained uncertain facial contours/skin,
inferred ears and the merged arm assignment. This review is neither user approval
nor independent semantic ground truth. No agent is a CLI runtime dependency;
the existing human review checkpoint remains part of the workflow.

## Optional mouths: preserved failure

At the starting commit, `create --facial-motion aligned` includes Phase 4B.1
facial reconstruction and Phase 4B.3 transitions. Phase 4B.4/4B.4.1 optional
authoring still lives in separate Python scripts. It would be misleading to say
the first CLI run included them automatically.

After sealing the first run, the **unchanged** generic scripts produced
`runs/phase4b5-codel-expressions/` and `runs/phase4b5-codel-mouths/`. No Codel
coordinates, opaque IDs, special recipe or reference artwork were supplied.
No source or model parameter was tuned after seeing the references.

The optional candidate passes its 401-frame dense suite, seven-expression and
mouth-only browser suite, and 72 eye geometry samples. Both dense suites have
maximum hole/detached-pixel diagnostics of **6 / 2** at the standard render
resolution; these are not quality scores. The extra high-resolution diagnostic
suite covers seven full/mouth-only expressions, eight mouth openings per emotion,
36 eye samples, all six ±head axes, eight combined poses and exact neutral return.

The **819-sample mouth Core audit fails**:
Embarrassed's source-seam vertices vary by `1.1920928955078125e-7`, exceeding
the existing `1e-7` tolerance. This is two float32 increments near the measured
coordinate, consistent with a precision-scale effect; it is not evidence of a
visible contour defect by itself. The original report remains failed. Recounting
its samples finds **zero visible mouth-triangle reversals**, zero nonfinite
vertices, zero out-of-tolerance opacities and an exact neutral geometry return.
No threshold was relaxed and no failed result was relabelled a pass.

The first and optional standard-resolution neutral renders are pixel-identical.
All 20 imported source layers remain exact in the optional editable archive;
that includes explicitly generated hidden pixels and is distinct from original
input fidelity. Blush is procedural, marked generated and not source artwork.

## Independent reference evidence

The PSD has 16 raster leaves: fused `Set2`, blush, and color/ink pairs in seven
numbered facial groups. It is **not** a pre-separated Live2D source. Neutral is
base + color1 + face1, without blush. Native-grid composition matches 98.34% of
foreground RGBA exactly; mean channel error is 0.01468, maximum 3. No registration
fit was applied. This small compositor difference is retained in the evaluation.

In manually reviewed evaluation-only regions, original neutral ink ownership is:

| Independent ink evidence | Assigned to intended role family |
| --- | ---: |
| Image-left brow | 202 / 202 |
| Image-right brow | 176 / 176 |
| Image-left eye | 968 / 969 |
| Image-right eye | 757 / 757 |
| Mouth contour | 110 / 110 |

These are **ink ownership recall**, not complete eye masks, fine iris/lash IoU or
whole-character semantic coverage. The fused base cannot establish independent
front/back hair, neck, clothing or limb segmentation. It does provide artist-drawn
skin beneath facial marks: 451 generated face samples under neutral ink differ
from that base by RGB MAE 18.31. This narrow discrepancy is evidence of uncertain
reconstruction, not independently verified anatomy or a global quality score.
356,353 of 916,843 copied samples retain semantic uncertainty flags.

Both shoulders, upper arms, forearms and hands are visibly retained. The crossed
arm/hand and hanging arm/hand share a **single unsided handwear layer**. Reviewed
native-grid limb regions are pixel-exact, but the region boxes are not independent
anatomical masks. Static preservation and independent limb articulation remain
different claims. Lower legs and feet are absent in the input.

## Comparison and costs

| Reference | Exact foreground after restoration | Animation/review status |
| --- | ---: | --- |
| Girl2 frozen Phase 4B.1 | 99.8855% | Existing limited prototype; simplified lids/hair limitations retained. |
| Sara frozen Phase 4B.1 | 99.7713% | Previously accepted limited facial improvement; newer mouth candidates remain separate. |
| Codel original framing | 99.99956% | First CLI technical pass; user visual review pending; optional mouth invariant failed. |

The historical Sara/Girl2 stage timings are cached replays and must not be
compared with fresh Codel GPU inference as a speed benchmark. Their independent
semantic evidence also differs; pixel preservation is not a ranking of quality.
Source-matched historical worker logs separately record Girl2 decomposition/SAM
at 113.06 / 2.04 s and Sara at 142.83 / 2.31 s. Both have the same 11.85 GiB
decomposition and 4.66 GiB SAM peak Torch allocation as Codel. These are historical
measurements at different image dimensions, not fresh controlled timing trials.

First Codel stage seconds: ingest **0.04**, inference **156.83**, semantics/SAM
**9.90**, restore **4.60**, readiness **0.18**, facial preparation **34.30**, project
**7.23**, rig **1.50**, animation **2.88**, export **1.59**, runtime validation
**66.78**. These exclude review pauses and the initial sandbox failure.
Worker LayerDiff itself took 136.75 s; depth 9.29 s; SAM 5.56 s.
Peak Torch allocation: decomposition **11.85 GiB**, SAM **4.66 GiB**.
Decomposition reserved peak was **16.02 GiB**; sampled whole-device peak was
**23,563 MiB**, which includes other processes and is not worker allocation.
See the benchmark for full stage and per-operation records.

## Development visual assessment and next step

The candidate retains the recognizable source and both hands. Independent blinks
close, open eyes return and the sampled head/talk combinations remain functional.
The first-run Happy, Confused and Embarrassed mouths are subtle; Sad and Angry
are similar. Optional shapes make Happy, round surprise and the smaller questioning
mouth more distinct, but intended emotion recognition is still a user judgment.
At quarter openness, both eyes have overlapping compressed contours and residual
shading/fragments around the opening. This is a **development visual rejection**
for convincing animation, despite the numerical passes. Closed lashes are flatter
and simpler than the artist's closed-eye variants; residual skin/lip shading and
the plain cavity limit style fidelity. The supplied
expressions include tears and gaze changes that this rig does not reconstruct.

The promising general-purpose next improvement is **style-aware facial backing
and lid/lip boundary reconstruction evaluated at dense transitions**, with the
artist base used only as evaluation evidence. The mouth precision failure also
needs a generic investigation across object scales and both existing references
before any change to authoring or validation. Full-body scope would separately
need reliable bilateral arm/hand ownership and articulation. None is implemented
or hidden by changing the framing in this phase.

Baseline **137 Python tests and five JavaScript tests passed**. Frozen pipeline
code/profile, locks, fixtures, accepted outputs and package pins verify unchanged.
New code is benchmark extraction/evaluation/reporting and diagnostic capture only.
Early diagnostic capture-report failures remain alongside the corrected attempts.
No new image models, training, host settings or production SillyTavern changes.
Stop after Phase 4B.5; explicit user visual acceptance remains outstanding.
