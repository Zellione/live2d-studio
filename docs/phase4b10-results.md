# Phase 4B.10 — frontal master and first independent arms

**The frontal canonical is now the primary character artwork, and the user accepted
the resulting limited frontal prototype.** The original angled illustration is
identity/style reference only. Its historical rig remains unchanged as an archive.
No production SillyTavern deployment occurred.

Started from clean local/remote `54ff23b2008642132ec4b91422dc5a0f4525529f`.
This assignment explicitly supersedes Phase 4B.9's requirement to keep the exact
angled rig as the target. It does not rewrite that phase's historical findings.

## Source authority and human review

Primary binding: [codel-frontal-master-v1](references/codel-frontal-master-v1.json).
The exact approved canonical image remains
`ab2a52ae59af22435b1c2595cb7ced24fdcd4ed5056b16496b8d2b482d78da3e`, candidate
`b-62c26625a6664a98810b8361cea4b371-c4`, seed `2801932010064774`.
`runs/phase4b10-master` preserves its original generation settings, prompt, guide
hash, producer/model pins, human approval and separate original identity image.
The new promotion manifest establishes artwork authority without changing the
older canonical manifest or calling synthetic pixels verified anatomy.

Three separate user decisions were recorded against exact evidence:

1. “Approve for limited rig experiment”: frontal matte, semantic decomposition,
   concealed facial skin and sleeve/torso backing.
2. “Approve the local brow repair”: revised local eyebrow backing after enlarged
   expression renders exposed stationary residual brow marks.
3. “Accept as a limited frontal prototype”: the repaired frontal rig's seven
   expressions, head behavior, two modest arm gestures, talking and neutral return.

The final runtime and editable project are frozen separately as
[codel-frontal-prototype-v1](references/codel-frontal-prototype-v1.json), with 203
payload files under `runs/references/codel-frontal-prototype-v1` and a hash-bound
human review. Acceptance excludes elbow/finger articulation, runtime wave/raised-
forearm poses, verified anatomy and production deployment.

## Identity/style and semantic foundation

Development comparison and the user's review find recognizable auburn hair with
side fringe, gray eyes, lavender turtleneck, brown skirt and dark tights. The
frontal face is rounder and more symmetric, and waist/skirt proportions differ
from the original. No embedding score or pixel equality is claimed as identity
proof. Both shoulders, sleeves and hands are visible; stylized overlapping fingers
remain synthetic artwork, not independently certified finger anatomy.

The opaque white backdrop is removed only in a tracked derivative matte by a
border-connected near-white mask. The selected master itself stays unchanged.
Retained RGBA samples remain exact. This avoids counting the illustration's white
background as missing character coverage. The first raw creation report correctly
failed foreground/silhouette gates on that opaque image and is retained.

The existing pinned offline See-through backend generated the frontal decomposition;
source-matched Phase 4B.9 SAM was reused. LayerDiff took 116.85 seconds, Marigold
14.75 seconds and PSD/bridge export 1.19 seconds; worker total 133.43 seconds.
Peak Torch allocation was 12,722,573,312 bytes. Model/source/environment locks
remain unchanged; no new weights or dependencies were installed.

The frontal preparation contains 25 semantic layers, including torso/topwear,
skirt, neck, face/head, front/back hair including side locks, upper-leg clothing,
paired facial components and six separate arm parts. Each arm has editable upper
sleeve, forearm and hand/cuff ownership. Neutral elbow locations remain hypotheses;
these partitions do not establish a validated bone skeleton or independently
rotating elbow textures.

Reassembled foreground preservation is **608,135 / 608,259 pixels (99.9796%)**,
with the same 0.999796 silhouette IoU. The existing 0.995 gates were not relaxed.
Remaining 124 samples and thin matte-edge fringes are retained as limitations.
“Observed” here means copied from the approved synthetic master, not the old
original or independently verified anatomy.

Existing generated backing is retained beneath overlaps and was explicitly
reviewed. The small shoulder motions did not require a new whole-body redraw,
Qwen pose batch or LaMa run. The local brow correction generates 3,519 skin
samples beneath the two brow patches and transfers 3,185 original master samples
to their moving layers. It preserves the prior neutral composite exactly. The
first narrower repair left faint tails and remains retained as a failed attempt.

## Recreated behavior and independent motion

Fresh editable project: `runs/phase4b10-arms-v3/authoring/character.psd2live`.
PSD and portable runtime: `runs/phase4b10-arms-v3/exported`.

The existing reusable authoring recreates seven expressions, coordinated mouth
shapes, head X/Y/Z, breathing, calm idle, Nod/Question and front/back hair follow-
through on the frontal artwork. It does not copy angled mesh coordinates or
force binary compatibility with the old runtime.

Each side's upper sleeve, forearm and hand share an inspected independent arm
owner. A smooth cubic horizontal field keeps its root and initial slope fixed
and moves the arm outward. All existing body/proportion combination keys receive
the same new axis, preserving neutral forms and body composition. It is a bounded
illustration deformation, not a measured anatomical shoulder rotation.

Two non-looping 3.2-second clips, `ArmRight` and `ArmLeft`, drive these independent
controls and return to rest. Actual isolated renders move exactly three meshes on
the intended side; torso, head and opposite arm remain fixed. Intermediate frames,
talking with a held head turn, and exact neutral restoration pass. The first
normalized arc was too subtle; it is retained separately from the clearer cubic
candidate. No displaced-image crossfade is used.

These are **modest outward shoulder gestures**, not the bent-forearm, explanatory
hand or wave illustrations in the helper set. Finger and elbow articulation are
not implemented. Larger motions would need additional joint/backing review.

## Frontal helper workflow

`runs/phase4b10-pose-review`, localhost 8808, uses canonical geometry as image1,
target guide as image2 and the original identity/style illustration as image3.
All four prior human approvals and their relevant batch histories are copied
exactly and stay locked. Their original reviewer run is unchanged. The new run
also retains prior used seeds, preventing accidental reuse on new batches.

Two independent pending targets, `right-aside-v2` and `left-aside-v2`, use a
24-degree outward upper-arm guide with a slight inward forearm bend. This is a
versioned, more distinct silhouette within the narrow framing; it does not claim
the earlier suggested 40–55-degree straight arm fits. The ineffective historical
13.42-degree guide and its failed generations remain in the old run. Five unique
candidates per batch, fresh regeneration, rejection, unsupported decisions,
resuming, selected-only exports and per-run GPU serialization use the existing
reviewer. No new helper images were generated or automatically approved here.

## Validation and review artifacts

- [Final gallery](http://127.0.0.1:8810/): actual animation loops, seven expression
  crops, primary/original comparison, selected helpers and decomposition.
- [Final live frontal rig](http://127.0.0.1:8812/): expressions, talking, body/hair
  controls, independent arm sliders and gesture buttons.
- [Frontal helper reviewer](http://127.0.0.1:8808/).
- [Approved backing correction](http://127.0.0.1:8807/v3/).
- [Workflow/reproduction](phase4b10-frontal-master.md) and
  [machine-readable benchmark](benchmarks/phase4b10.json).

All six final candidate gates pass: 819 mouth/expression Core poses, 496 body
Core poses, arm browser controls/clips, 401 dense facial frames, body/idle gestures
and facial/body coexistence. An additional Core run includes 101 arm/body/face
combinations (597 total samples), with zero nonfinite vertices, zero visible
triangle reversals and exact neutral restoration. High-resolution seven-expression
still comparisons pass separately. Historical absolute seam and raw opacity
reports remain visible under the unchanged structural/float32 policy.

All 226 Python tests and both JavaScript regression suites pass, with logs recorded
in the benchmark. A fresh preparation reproduces the final repaired facial manifest
exactly. No fixture, accepted historical runtime or deployment gate was weakened.

Retained failures include the raw opaque-background gate, a sandbox-denied editor
connection, a misplaced-module import, the overly subtle arc, the first arm
scenario's missing QA-summary fields, the narrow brow repair and a tiny synthetic
guide fixture outside the real guide's framing constraints, and a new test's
fixture-directory collision. Corrected runs remain
separate. Numeric passes did not grant acceptance; the final user review did.

Stop after this limited frontal prototype. The next phase can investigate reviewed
elbow/gesture-specific anatomy on this frontal foundation; the angled rig is no
longer the target. Production SillyTavern remains untouched.
