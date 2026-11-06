# Frontal master workflow

The primary source is now the approved frontal synthetic artwork. The original
angled illustration remains an identity/style/outfit reference. Keep their hashes
and roles separate. The accepted historical angled runtime is archived unchanged.
See [results](phase4b10-results.md), [master binding](references/codel-frontal-master-v1.json)
and [limited runtime reference](references/codel-frontal-prototype-v1.json).

## Local inputs and source promotion

Use the existing project uv environment, separate pinned See-through/Qwen workers
and loopback PSD2Live. No download, hosted model, Photoshop or SillyTavern server
is needed. Large outputs stay under ignored `runs/`. Source artwork is Codel by
LisadiKaprio, CC-BY-4.0; canonical/helper images are synthetic derivatives.

A new primary-source manifest preserves the canonical approval, seed/configuration,
producer hashes and original reference. Promotion never rewrites the old freeze.
For a new already reviewed canonical/family, use fresh paths:

```sh
uv run --frozen python scripts/phase4b10_master.py promote \
  --canonical-run runs/phase4b8-canonical --family runs/phase4b9-family \
  --output runs/NEW-master
```

The shipped binding uses `runs/phase4b10-master`. Do not promote or regenerate it
again merely to replay downstream work. `load` verifies payload hashes, canonical
approval/role relationships and selected-family integrity before creation.

## Inference, matte and reviewed decomposition

```sh
uv run --frozen python scripts/phase4b10_master.py create \
  --master runs/phase4b10-master --output runs/NEW-inference \
  --sam runs/phase4b9-sam/canonical --until readiness
uv run --frozen python scripts/phase4b10_master.py prepare \
  --master runs/phase4b10-master --inference-run runs/NEW-inference \
  --geometry runs/phase4b9-geometry-final --repair-brows \
  --output runs/NEW-prepared
```

`create` performs the existing raw inference/semantic/restoration stages with the
canonical image. Its raw readiness report can block on the opaque backdrop;
**do not override that report**. `prepare` verifies its cached stage inventories,
creates a distinct native matte and derives a new layer manifest/quality report.
It uses the unchanged foreground/semantic thresholds on the explicit character
matte. Reuse `runs/phase4b10-frontal-base` as `--inference-run` to avoid another
GPU run. Reproduction without inference passed for both initial and repaired
facial manifests.

The matte removes only border-connected pixels whose RGB minimum is at least 225
and channel range at most 25; retained RGBA is exact. This conservative rule is
for the inspected near-white backdrop, not arbitrary background removal. Inspect
fine hair, hands and any light edge before approving another character.

Arm partitions are native-grid sleeve/cuff hypotheses. Both upper/forearm/hand
sets remain separate editable layers; whole-arm motion shares one parent per side.
The near-straight neutral does not identify a trustworthy elbow pivot. Front/back
hair layers include the visible side locks. No synthetic hidden surface becomes
verified anatomy through a role label or source-copy score.

`--repair-brows` creates a separate facial candidate with local harmonic skin
beneath expanded eyebrow strips. Neutral source samples move to the brow layers,
while generated backing remains uncertain. It makes no global face/art redesign.
It is optional outside this reviewed frontal recipe; old creation defaults stay
unchanged. The first narrow repair and earlier face candidate remain available.

Preparation writes `review/evidence.json`. Inspect the layer preview, reconstructed
surfaces, source/neutral and face regions before recording a human decision:

```sh
uv run --frozen python scripts/phase4b10_master.py review \
  --folder runs/NEW-prepared/review --decision accept --reviewer 'Your name' \
  --notes 'Reviewed matte, bilateral parts, source preservation and uncertain backing for a limited rig experiment.'
```

Use `reject` when unsuitable. Reviews require unchanged evidence, a reviewer and
notes; they do not grant runtime approval. Existing decisions cannot be overwritten.
The actual user approvals for this phase remain in `runs/phase4b10-source-review`
and its `v3` subdirectory. Never copy those approvals to changed artwork.

## Build and inspect the frontal rig

```sh
uv run --frozen python scripts/phase4b10_build.py \
  --master runs/phase4b10-master --facial runs/NEW-prepared/facial \
  --review runs/NEW-prepared/review --output runs/NEW-rig
```

This verifies the human review and builds resumable project, facial rig, animation,
coordinated mouth and calm body stages. The final printed authoring directory is
the predecessor for arm authoring. PSD2Live must be available on 127.0.0.1:23871;
if it requires a token, supply `PSD2LIVE_MCP_TOKEN` explicitly in the environment.
No profile secrets are read. Current editor work is saved before switching projects.

```sh
uv run --frozen python scripts/phase4b10_arms.py \
  --predecessor runs/NEW-rig/stages/BODY-STAGE/authoring \
  --layers runs/NEW-prepared/facial/layers --output runs/NEW-arms --amount 1
uv run --frozen live2d-studio preview-live \
  --model runs/NEW-arms/exported/runtime/Generated_artwork.model3.json \
  --port 8812 --no-open
```

Replace `BODY-STAGE` with the printed stage. `--amount` is a normalized field
amplitude, **not a physical shoulder angle**. The default horizontal cubic controls
are `[0,0,-.12,-.4]` on anatomical right and the opposite sign on left, normalized
to each inspected arm cage. The zero root/initial slope preserves attachment;
interior and endpoint quality must still be rendered. Existing body axes receive
all their combination keys. No unrelated layer may share the selected arm owner.

Arm gestures are 3.2-second shoulder sweeps with a hold and return to zero. They
preserve all three part cuts through a shared parent and do not articulate elbows,
fingers or replace arm pixels with a helper still. The ordinary body/talk/head/
hair machinery remains separate. Final visual approval must bind the full runtime
file set and editable project, not just model3 JSON.

## Frontal five-candidate helper reviewer

```sh
uv run --frozen python scripts/phase4b10_master.py helpers \
  --master runs/phase4b10-master --output runs/NEW-helper-review \
  --presets recipes/lightning-gesture-presets.json
uv run --frozen python scripts/pose_reviewer.py serve \
  --run runs/NEW-helper-review --port 8808
```

Initialization verifies the frozen family and prior decisions, retains selected
poses and their batch history, and records their origin. It generates nothing.
The original is image3 only; canonical master is image1 and the pose guide image2.
The four approved poses remain locked. Independent pending aside targets have
separate versioned guides. The old fifth guide/run is untouched.

Use Generate five more for exactly five fresh seeds. Rejection, reasons, unsupported
status, history, zoom, resume, selected-only export, loopback/path/CSRF guards and
per-run GPU locking are inherited unchanged. A new fresh run is required to replace
an already approved pose. Helpers are visually approved evidence, not rig truth.

## Validation and local artifacts

```sh
uv run --frozen python -m unittest discover -s tests -v
node --test tests/test_rp_talk.mjs tests/test_mouth_invariant.cjs
uv run --frozen python scripts/phase4b10_validate.py \
  --run runs/NEW-arms --output runs/NEW-validation \
  --correspondence runs/NEW-rig/stages/PROJECT-STAGE/transition-correspondence.json
```

The validation script retains all failed Core/browser gates. `probe_body.cjs`
also supports `--arms` to add 101 combined arm/body/face samples; its default
historical suite is unchanged. `phase4b10_render.py --scenario
phase4b6_1_face_scenario.js` supplies high-resolution expression comparisons.
`phase4b10_report.py --help` lists inputs for the standalone actual-render gallery.

Final accepted candidate is `runs/phase4b10-arms-v3`. Its source layers are
`runs/phase4b10-facial-v3/layers`; final checks are in
`runs/phase4b10-validation-final`, `runs/phase4b10-face-final` and the audit directory.
The frozen limited reference contains a portable runtime, PSD, editable project,
layer provenance and user review. Keep these local artifacts and all negative
iterations. Do not deploy to production or extend articulation in this phase.
