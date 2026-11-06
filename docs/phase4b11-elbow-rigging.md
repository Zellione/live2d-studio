# Reproducing the elbow experiment

This opt-in authoring path does not change ordinary creation or shoulder-only
fallbacks. It requires the local frozen frontal prototype, reviewed family and
source-matched geometry assessment. All outputs must be fresh ignored runs.

```sh
uv run --frozen python scripts/phase4b11_elbow.py \
  --output runs/NEW-right --author --overlap
uv run --frozen python scripts/phase4b11_elbow.py \
  --output runs/NEW-both --author --side left --overlap \
  --predecessor runs/NEW-right/rig/authoring
```

Each command verifies the Git-pinned frozen reference and family hashes. The
selected side must contain three distinct parts under one inspected owner, with
no unrelated children or existing independent mesh axes. Existing original
textures must survive archive comparison. Source-relative pivots and overlap
provenance are saved alongside the project. `--degrees` is bounded to 135;
120 is the evaluated diagnostic. `--method landmarks` reproduces the rejected
mesh-based comparison and must not be treated as the viable method.

Native rotation owns the forearm and hand under the existing shoulder deformer.
The parameter is `ParamArmRElbow` or `ParamArmLElbow`, 0..1, neutral 0. The fitted
pivot and scale are left unchanged; only native angle is keyed. The elbow clip
coordinates `ParamArmRightOpen`/`ParamArmLeftOpen` up to .15. Native rotation was
chosen from actual exported Core/render evidence, not from documentation alone.

The overlap generator copies a bounded elliptical region of the existing sleeve
into a new, explicitly source-derived concealed layer. It does not edit original
pixels or invoke a cloud/local model. The cap is parented to the inspected shoulder
and placed behind the upper sleeve. Its opacity is 0 at elbow=0 and 1 by .02.
Newly visible shape remains inferred and requires human review. Do not infer
approval for another side or character from Codel's right-patch approval.

```sh
uv run --frozen live2d-studio preview-live \
  --model runs/NEW-both/rig/exported/runtime/Generated_artwork.model3.json \
  --compare-model runs/references/codel-frontal-prototype-v1/runtime/Generated_artwork.model3.json \
  --port 8816 --no-open
uv run --frozen python scripts/phase4b10_render.py \
  --model runs/NEW-both/rig/exported/runtime/Generated_artwork.model3.json \
  --output runs/NEW-elbow-render --scenario phase4b11_elbow_scenario.js
uv run --frozen python scripts/phase4b11_report.py \
  --run runs/NEW-both --render runs/NEW-elbow-render \
  --output runs/NEW-review --live-port 8816
python3 -m http.server 8817 --bind 127.0.0.1 --directory runs/NEW-review
```

The viewer shows only parameters actually exported. Elbow sliders inspect gesture
progress, existing Reset returns to rest, and gesture buttons play the real clips.
Starting an arm clip releases manual arm overrides while retaining head controls.
No wrist control is exposed without a wrist parameter. The side-by-side model
shares expression/head inputs; unsupported elbow parameters do not alter the old
reference. No API, SillyTavern or coding agent is needed.

The landmark canvas saves bounded click proposals locally under the exact proposal
hash. Downloaded corrections are review material, not automatic approval or an
unvalidated rig input. Hidden artwork review and final animation review are
separate decisions.

```sh
uv run --frozen python -m unittest discover -s tests -v
node --test tests/test_rp_talk.mjs tests/test_mouth_invariant.cjs
uv run --frozen python scripts/phase4b10_validate.py \
  --run runs/NEW-both/rig --output runs/NEW-preservation \
  --correspondence runs/phase4b10-rig-v2/stages/project-1a5d3a27ee44/transition-correspondence.json
uv run --frozen python scripts/phase4b10_render.py \
  --model runs/NEW-both/rig/exported/runtime/Generated_artwork.model3.json \
  --output runs/NEW-shoulders --scenario phase4b11_shoulder_scenario.js
node scripts/probe_body.cjs \
  .cache/phase3-st/data/default-user/extensions/Extension-Live2d/lib/live2dcubismcore.min.js \
  runs/NEW-both/rig/exported/runtime/Generated_artwork.model3.json \
  runs/NEW-both/rig/authoring/body-inspection.json --elbows
```

The old fixed three-mesh shoulder check intentionally remains failed for the
additional invisible overlap mesh. Read both reports; do not erase the old failure
or call it a universal visual pass. The new scoped test separately checks visible
original mesh isolation and exact invisible-overlap count. All other historical
Core and browser gates remain unchanged. Preserve unsuccessful authoring attempts,
MCP transcripts and exported failures under their original run names.
