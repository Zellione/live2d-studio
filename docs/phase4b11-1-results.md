# Phase 4B.11.1 — reviewed elbow freeze and optional integration

The user-accepted bilateral elbow candidate is frozen as
[`codel-frontal-elbows-v1`](references/codel-frontal-elbows-v1.json). The optional
arm stage now plans, pauses for exact human review, authors native elbows,
exports and validates a separate model through the ordinary CLI. Creation
defaults remain unchanged. This is a reusable limited method with conservative
fallback, not general anatomical reconstruction or professional skeletal rigging.

Baseline: `e014179181b1921ef41d42466e42993c67013707`.

## Frozen reference

`runs/references/codel-frontal-elbows-v1` contains 224 read-only payload files:
the complete editable PSD2Live project, layered PSD, runtime, original frontal
layers/master provenance, both source-derived sleeve patches, joint proposals,
preservation diagnostics and exact user review. The small Git manifest pins the
full inventory and review hashes. Files are 0444 and directories 0555; this is
hash-verified preservation, not protection against an administrator rewriting disk.

The exact review says **“Accept as a limited elbow prototype”** and covers both
coordinated gestures and the left concealed overlap. Its SHA-256 is
`0ab6ccd934573c36d9c877a1cfd2607aecde23df70890ecb9bbcf03040cb6589`.
The earlier gap rejection and original experiment remain preserved. No earlier
reference is replaced, including the original angled Codel and frontal prototype.

All seven expressions, coordinated mouth behavior, head/body controls, hair
physics, breathing, idle, shoulder gestures and Nod/Question clips are retained.
The known neutral difference from the previous frontal reference is **880 pixels**,
maximum RGBA channel difference 170; over white the maximum RGB difference is
24.02. Exact restoration to this candidate's own neutral is a separate passing
condition. Do not describe the old and new neutral renders as pixel-identical.

## Reusable implementation

`arm_pipeline.py` inspects actual source support, hierarchy and neutral geometry.
It derives normalized cut-based joint hypotheses and local sleeve overlaps, then
requires human review. Exact frozen review reuse is explicit and contract-bound.
The stage preserves old clips and uses the existing native rotation method; it
does not use the historically failed distal-mesh deformation method.

Missing or ambiguous arm evidence keeps the input static/shoulder behavior. The
stage cannot infer safe anatomy from layer names, repair arbitrary segmentation,
or approve its own output. Codel remains the only real accepted character for
this elbow method. Synthetic fixtures exercise rejection and fallback behavior;
they do not demonstrate another character's visual quality.

The direct replay in `runs/phase4b11-1-replay` reproduces the accepted MOC,
texture atlas, expressions, physics and motion payloads exactly. CAN3/CMO3 editor
archives differ; the model JSON adds an inspected validation contract. The
performance integration is retained separately in `runs/phase4b11-1-performance`.
It matches all 23 non-editor runtime payloads and the complete FileReferences
object; its neutral capture differs from the accepted elbow capture by zero pixels.
All 17 pre-existing expression/physics/motion files remain exact. Repeating the
performance command resumes the same five arm stages without editor mutations.
The old merged-arm Codel reference produces an unchanged fallback, with no editor
or inference call.
Plan acceptance and final animation acceptance stay separate; newly exported
candidates are not automatically promoted.

## Validation and retained failures

The [benchmark](benchmarks/phase4b11-1.json) records commands, hashes and measured
results. Tests cover source-relative joint proposals, ambiguous/disconnected
parts, invalid owners, unrelated children, missing neutral keys, exact human
approval, tampering, rejection, preserved inputs, CLI defaults and resumed stages.
All **252 Python tests** and both JavaScript suites pass. The performance replay
passes **898 body/elbow Core samples**, **819 mouth samples**, **384 arm browser
frames** and **355 talk/head/idle coexistence frames**. Body/elbow and mouth probes
report zero visible triangle reversals. Raw float32 opacity excursions remain in
the reports; the inherited absolute mouth-seam test remains false while the
existing MOC-bound scale-aware contract passes. Neither threshold is changed.

The unchanged historical facial transition, mouth, head/body and coexistence
regressions pass. The old shoulder test still fails its fixed three-total-mesh
count because the invisible overlap is a fourth moving mesh. Its failure remains
separate. The new inspected contract additionally checks three visible original
meshes, one hidden cap, no unrelated movement, exact neutral return and reload.
Core checks retain visible-triangle and opacity gates, and browser scenarios cover
talking, head/hair movement, intermediate elbow positions, interrupted/repeated
gestures and fresh model instantiation.

The first validation inventory attempt failed on Chromium profile socket symlinks
after its numerical/browser checks passed. Profiles now stay in a separate ignored
diagnostic directory; symlink rejection was not weakened. The first full Python
run hit two sandbox-denied loopback socket tests; the host run is recorded
separately. Historical 8,983 visible mesh-transform reversals and all earlier
failed candidates remain failures.

See [commands and review workflow](phase4b11-1-autonomous-arms.md). No new image
inference, model downloads, wrist/finger authoring, system changes or production
SillyTavern writes occurred. Stop after Phase 4B.11.1. A subsequent phase should
evaluate another suitably separated character with its own joint/overlap and
animation review before considering any default change.

Local review: [frame gallery](http://127.0.0.1:8818/) and
[synchronized accepted/replayed elbow rigs](http://127.0.0.1:8817/). These inspect
the completed reproduction; they do not replace the original human review record.
