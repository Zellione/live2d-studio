# Phase 4B.11.1 — optional reviewed arm authoring

`--arms native-elbows` adds a resumable extension to `create` and
`prepare-performance`. Both retain `--arms preserve` as their default. The same
extension is available directly through `prepare-arms`. It uses the installed
PSD2Live MCP editor, Cubism Core and standalone viewer; no coding agent, model
inference or network classification is part of execution.

## Readiness and limits

The first implementation supports the inspected three-part, arms-down layout:
one upper sleeve, forearm and hand/cuff mesh per anatomical side, beneath separate
shoulder warp owners. It requires source-matched raster assets, substantial opaque
support, contiguous cuts, plausible projected segment ratios, finite complete
neutral mesh data, existing neutral shoulder keys and no unrelated children or
direct arm mesh axes. Existing mouth/body/composition inspection contracts must
also be available for export and regression validation.

Semantic labels alone cannot pass these checks. Missing parts, unsupported cuts,
ambiguous hierarchy or absent prerequisites produce `shoulder-only-fallback`:
the input model and existing static/shoulder behavior remain unchanged. The stage
does not invent missing segmentation or silently create shoulder rigging. The
current single-image parser often lacks these prerequisites; enabling this option
does not make it a general articulated-character converter.

Pivot proposals use median opaque sleeve support at the actual forearm cut,
normalized to the source canvas. Each side is assessed independently. These are
attachment hypotheses, not measured skeletal joints. A small elliptical sleeve
cap reuses local source samples, stays beneath the existing sleeve, and becomes
visible only during bending. Its hidden shape and duplicated pixels retain
generated provenance. No neural inpainting occurs.

Every supported new plan stops at `needs-arm-review`. Review covers the exact
source project, layers, proposed pivots, 120-degree experimental travel, 15%
shoulder coordination and both overlap images. The range is bounded, not a claim
about biological joint limits. Rejected plans stay rejected. A changed source,
overlap image, plan or implementation invalidates resume/review evidence.

## Plan, inspect, review and resume

Run from the repository with the pinned environment and loopback PSD2Live MCP.
Use a fresh ignored output. Example using the frozen shoulder-only reference:

```sh
uv sync --frozen
uv run --frozen live2d-studio prepare-arms \
  --authoring runs/references/codel-frontal-prototype-v1/authoring \
  --layers runs/references/codel-frontal-prototype-v1/layers \
  --model runs/references/codel-frontal-prototype-v1/runtime/Generated_artwork.model3.json \
  --output runs/my-elbow-run
```

The result prints the exact plan directory. Open its `index.html`, `joints.png`,
`plan.json` and two overlap images locally. Substitute that directory below;
record acceptance only after a human has inspected it:

```sh
uv run --frozen live2d-studio review-arms \
  --plan runs/my-elbow-run/stages/arm-plan-PRINTED_ID \
  --decision accept --reviewer 'Your name' \
  --notes 'Reviewed these joint hypotheses, overlap pixels and limited range'
```

Use `--decision reject` for an unsuitable plan. The decision file cannot be
overwritten. Rerun the original `prepare-arms` command to continue. Successful
stages resume without repeating editor mutations; failed attempts and their logs
remain separate. Inputs are hash-checked, a per-run lock prevents duplicate jobs,
and the existing global editor lock serializes PSD2Live mutations.

An explicit `--arm-review-reference` may reuse an existing frozen human review
only if its source project, layer manifest, both joint coordinates, travel,
shoulder coordination and overlap hashes match the proposed contract exactly.
It cannot transfer Codel approval to another character or override a rejection.
The reference's complete payload inventory is verified first.

The validated performance integration is reproducible with a fresh output:

```sh
uv run --frozen live2d-studio prepare-performance \
  --baseline runs/references/codel-frontal-prototype-v1 \
  --output runs/my-reviewed-elbow-replay \
  --arms native-elbows \
  --arm-review-reference docs/references/codel-frontal-elbows-v1.json
```

`create ... --arms native-elbows` invokes the same stage after the ordinary
source, semantic, facial, export and runtime gates. Existing defaults and earlier
review gates remain intact. `prepare-performance` retains its baseline export and
records the extension in `optional-arms.json`; its `arms/arm-result.json` identifies
the resulting project, runtime, authorization and validation. Select that result
explicitly for later work. No downstream reference is automatically repointed.

## Authoring and validation

Native rotation deformers share the inspected forearm and hand meshes below each
unchanged shoulder owner. Upper-arm geometry does not receive the elbow axis.
The authoring code creates `ParamArmRElbow` and `ParamArmLElbow`, bounded four-second
Bezier gestures, concealed overlap opacity keys and explicit clothing draw order.
The hand follows the forearm; no wrist/finger axis is exposed. Source artwork stays
exact. Existing expression, physics and motion payloads must remain byte-identical.

Each output runs actual installed Core mouth and body/elbow probes plus continuous
browser arm and talk/head/idle coexistence scenarios. The runtime's inspected mesh
contract identifies exactly which two meshes may move with an elbow, which three
original meshes visibly move with a shoulder and which additional hidden cap may
inherit it. Unrelated movement, invalid geometry, failed neutral restoration or
failed temporal behavior blocks completion. Strict raw opacity excursions remain
recorded separately under the existing float32 rules. No threshold is relaxed.

`arm-result.json` and the CLI result provide a `preview-live --model ...
--compare-model ...` command. `create` also opens the comparison when preview is
enabled. The viewer already exposes supported shoulder/elbow controls, gesture
progress, talking/head/idle controls, interruption and neutral reset. Final
animation acceptance remains separate from plan approval and numerical validation.
The endpoint does not grant production deployment.

## Regression commands

```sh
uv run --frozen python -m unittest discover -s tests -v
node tests/test_rp_talk.mjs
node tests/test_mouth_invariant.cjs
```

The tests use synthetic fixtures for readiness, review and resume orchestration.
Local freeze integrity tests skip when the deliberately untracked reference is
absent. Actual editor/Core/browser replay is a separate local integration test;
ordinary unit tests do not need GPU inference.

The phase-specific freeze recipe is `scripts/phase4b11_1_freeze.py`. It verifies
the original human review and refuses an existing reference destination; never
rerun it to repin a frozen reference. Generate a fresh local evidence gallery from
the validated performance run with:

```sh
uv run --frozen python scripts/phase4b11_1_report.py \
  --run runs/phase4b11-1-performance --gallery runs/my-elbow-evidence-gallery
```

This report recipe verifies the frozen references and retains the phase's raw
Core/browser and test-log hashes in the small benchmark. It creates a new gallery
and updates `docs/benchmarks/phase4b11-1.json`; it does not edit any source artwork.
