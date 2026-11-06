# Phase 4B.8.1 — canonical-based guided gestures

Three-reference inference and the reviewer work, but the initial configuration
failed the gesture-quality gate: the user rejected all five candidates. A matched
two-reference control produces a much clearer bent-arm gesture. This is evidence
for revising conditioning, not for starting final arm rigging. The study started
from clean local and remote HEAD `46717d4`.

## Preserved inputs and implementation

The approved canonical candidate remains
`ab2a52ae59af22435b1c2595cb7ced24fdcd4ed5056b16496b8d2b482d78da3e`;
its frozen manifest remains
`8d15231abbb8e648e1f1663abd16a7cdd5323296c1361f91c3115e31f2610725`.
The original is
`98589fb8750ccfc3664935985fc42810381b2e09f22e1ae8cf4cd6dd45d39a2d`.
All 1,812 pre/post-inventoried files across the accepted Codel snapshot, canonical
freeze and previous helper selections remain hash-identical. No canonical regeneration,
accepted-runtime replacement or production SillyTavern access occurs.

New run: `runs/phase4b8-1-gestures`; reviewer: <http://127.0.0.1:8800/>.
`init-from-canonical --gesture-profile chest-forearm-v1` preserves the existing
handoff while adding an explicit anatomical-right, chest-height bent-forearm guide.
Image1 is canonical geometry, image2 the guide, image3 the original for identity
and style. An arms-down redraw is not a successful gesture.

The reviewer shows all three reference roles and keeps approval, rejection,
regeneration, history and unsupported handling. Five fresh seeds are reserved per
batch; approved targets stay locked. Missing third-reference evidence is rejected.
The four other poses are prepared but not automatically generated. Selected-only
analysis now labels the canonical baseline distinctly from the original artwork.

See [generation and reproduction](phase4b8-1-gesture-generation.md) and
[benchmark](benchmarks/phase4b8-1.json). Generated artwork and logs remain ignored.

## Generation and compliance

Initial batch: `b-cff4858500e9424bbe4340f92e2e9335`, five unique seeds.
Preset `canonical-gesture-1536-40` matches the reviewed canonical numerical
settings: Q4_K_S transformer, FP8 encoder, 800 × 1536, 40 steps, CFG 4, shift 3,
Euler/simple, denoise 1, source latents, no mask/CFG normalization, silhouette
guide and empty negative prompt. No weights or dependencies were downloaded.

All five outputs retained three `[1,16,1,177,92]` reference tensors and completed
at 800 × 1536. Per-image times were 239.159, 240.501, 241.584, 240.091 and
240.483 seconds. Peak Torch allocation was 20.86 GiB and reservation 23.43 GiB;
these are allocator metrics, not whole-board VRAM usage.

| Candidate | Seed | Development screening |
|---|---:|---|
| 1 | 2597810572262578 | Both arms down; requested gesture absent |
| 2 | 528438402671782 | Both arms down; requested gesture absent |
| 3 | 3531224070097414 | Correct side bends, but raised hand is missing and shoulder contour is damaged |
| 4 | 2090140980387358 | Both arms down; requested gesture absent |
| 5 | 666969407125788 | Both arms down; requested gesture absent |

The batch preserves frontal identity/outfit reasonably well, but **zero of five**
meet the complete requested gesture in development screening. Candidate 3 proves
some guide influence, not a usable arm. Clean parsing of the four arms-down images
would not change this result. No new SAM inference was run on unselected images.

## Controlled two-reference comparison

A separate diagnostic reuses candidate 1's seed, canonical source, guide and all
numeric settings. It removes only image3 conditioning and its identity instruction.
Actual retained reference count is two, with two `[1,16,1,177,92]` tensors; runtime
172.034 seconds. This is an explicit reference-family comparison, not a silent
fallback and not a test isolating image removal from its associated text.

Unlike the three-reference result with this seed, the control shows a continuous
anatomical right shoulder/upper arm, a clearly bent elbow, rising forearm, wrist
and a present hand; the other arm stays down. It preserves frontal styling well.
The raised hand points with one finger and sits closer to shoulder height than
the requested relaxed chest-height placement. Finger topology, shoulder shape
and cross-pose geometry still require review. This diagnostic has not been
human-approved or parsed. Image and metadata remain under
`runs/phase4b8-1-two-reference-control`.

This pair suggests competition from the full original identity reference in the
tested setup. It does not establish a universal three-image limitation, a GGUF
compatibility defect or quantization degradation. The exact observed failure is
poor pose compliance despite successful three-image encoding and sampling.
The unchanged installed Qwen consumer processes all reference tensors; there is
no observed missing-input fallback or VRAM failure. A skeleton-guide control is
implemented for reproducibility but was not executed in this bounded study.

## Human review and semantic boundary

The user rejected candidates 1, 2, 4 and 5 for **wrong pose**, and candidate 3 for
**bad hands** in the real reviewer. The pose remains `rejected`, so the user can
request fresh batches; it was not automatically marked structurally unsupported.
The saved selected-set export is empty. **No new SAM inference or downstream
anatomical analysis was performed**, because no human-approved helper exists.
The previous canonical SAM result remains historical evidence, not a new gesture
success. Human decisions and all failed images are retained.

Local gallery: `runs/phase4b8-1-review-final`, including the original, canonical,
guide, five rejected candidates and explicit two-reference control. The interactive
reviewer remains at localhost 8800; the gallery is served at localhost 8801.

## Validation

The first full regression run passed 196 Python tests. Eight new gesture tests
cover exact input roles, preserved canonical data, missing/wrong reference
rejection, repeated five-seed batches, approval persistence and locking,
three-input interruption recovery, pinned guide directions and matched controls.
The final full regression run passed 197 tests, including the control test.

Both JavaScript regression files passed. Read-only real-browser QA verified the
complete five-image batch, all three reference roles and the comparison dialog;
it created no approval. The initial mouth-test command used a
nonexistent filename; the corrected `test_mouth_invariant.cjs` run is retained
separately. Synthetic browser QA passed three-reference display, ten fresh seeded
images across two batches, rejection, approval, unsupported handling, selected-only
save, zoom and comparison. An early synthetic worker briefly published incomplete
fixture metadata before adding reference fields; publishing the complete fixture
record atomically fixed that test-only race. Real inference already publishes
complete task records atomically. Failed diagnostics remain retained.

## Architecture and next decision

A compliant approved gesture could support bilateral contour proposals and local
shoulder/elbow/wrist investigation. SAM component counts alone do not supply these
joints or verify fingers, hidden clothing, depth or cross-pose correspondence.
The canonical baseline itself is synthetic. No new anatomical validity follows
from the previous canonical separation result.

Future skeletal deformation needs consistent geometry, reviewed joints and hidden
backing. Discrete gesture-layer variants may be a more practical first experiment
if the generated poses vary in proportions, but still need reviewed cut lines,
occlusion and transition tests. Neither strategy is implemented here.

Recommendation: defer final rigging. Next compare a less competing identity
reference or explicitly evaluate a five-seed canonical-plus-guide batch, keeping
the original as an identity review reference. The single two-reference diagnostic
must be repeated and human-reviewed before using it for segmentation. Any later
skeletal or discrete-layer experiment first needs complete, approved bent-arm and
hand evidence. No remaining pose was generated, no final rig was built, and no
accepted runtime or production installation was changed. Stop after Phase 4B.8.1.
