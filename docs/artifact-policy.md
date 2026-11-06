# Artifact and Git policy

Code, pinned dependency metadata, tests, recipes and concise results belong in Git.
Generated runs belong under `runs/`, caches under `.cache/`, weights under `models/`
or `checkpoints/`, private source art under `assets/input/`. These directories are
ignored, including generated PNG textures, masks, previews, PSD, PSD2Live, MOC3,
CMO3, CAN3, model3/motion3/exp3 JSON, browser profiles/videos and diagnostics.
Export-family suffix rules also guard accidentally misplaced exports; explicit
exceptions preserve the curated `tests/fixtures/phase0/` and
`tests/fixtures/phase1/final/` golden fixtures. Do not force-add generated runs.
New golden fixtures require rights/provenance, review and passing regression tests.
The final Phase 1 fixture must never be silently regenerated in place.

`docs/evidence/` is local-only for future runs. Existing tracked Phase 0 evidence
is grandfathered as the compatibility record; Phase 1 results and numerical
measurements are summarized in `phase1-results.md`, with historical commit
`07f56b3` identifying their original raw evidence. Cleanup does not assert a new
browser run. Optional deliberately selected examples belong under `docs/examples/`.

The Phase 2 audit used `git ls-files`, references in scripts/tests/docs, and clean
`git status --short`. Tests require Phase 0 export, Phase 1 final runtime and the
art generator; no test requires the removed Phase 1 intermediate or raw evidence.
Removal uses `git rm --cached`: local originals, intermediate PSDs and diagnostics
survive. No history rewrite, forced push or change to another repository.

Never commit downloaded illustrations without redistribution rights, model weights,
credentials, auth headers, profile secrets or local secret-bearing configuration.
Use environment variables for MCP tokens; never print them. Runtime transcripts
are local diagnostics, not permission to capture HTTP authorization headers.
Record model revision, license, checksum, cache path and actual measured hardware
usage before promoting a model-backed result. Review `git diff --cached` before
committing. Do not use `git add -f` to bypass this policy.

Phase 2.5 adds `backends/see-through/` for its independent pyproject, uv lock,
model download manifest and worker code. Nested `.venv/` stays ignored. Source
checkouts remain under `.cache/`, model snapshots under `models/see-through/`,
licensed XCF inputs under `assets/references/`, and all inference/PSD/runtime/SAM
outputs under `runs/`. Compact benchmark numbers and recipes may be versioned
under `docs/benchmarks/`; raw GPU samples, masks and browser recordings may not.

Phase 4A packages, package manifests, deployment journals, verified backups,
quarantined files and disposable browser data remain under `runs/`. Isolated ST
copies/profiles remain under `.cache/`. The reviewed packaging policy and hashes
in `recipes/girl2-package.json`, automated scenarios, compact benchmark and results
are tracked; no generated runtime, copied upstream dependency or settings snapshot
is added to Git. Keep failed attempts and rollback evidence inspectable locally.


Phase 4A.2 additionally retains target-filesystem disposable instances, journals,
backups, quarantine and browser profiles under the explicitly authorized
`/home/zelli/tools/ai/live2d-studio-phase4a2-tests/` base, outside production and Git.
Project reports/contact sheets/logs stay in ignored `runs/phase4a2-*`; local unit
fixtures use `.cache/phase4a2-tests`. Only implementation, repeatable scenarios,
compact benchmark and documentation are committed. Do not copy target-side recovery
material into served asset trees or force-add generated package data.

Phase 4B.2 keeps model weights under `models/phase4b2`, downloaded inference source
under `.cache/phase4b2-*`, and worker environments in ignored nested `.venv` folders.
Raw/composited crops, generated/uncertain masks, model parity diagnostics, reviewed
image selections, failed download/runtime attempts, PSDs, projects and actual Core
comparison galleries remain in `runs/phase4b2-*`. Version only implementation,
licenses, frozen locks, generic recipes, tests and concise results/benchmark. The
quantized Qwen download approval does not authorize committing weights or changing
the user's ComfyUI installation. Preserve all rejected candidates locally.

Phase 4B.3 preserves all new projects, PSDs, exports, mesh inspections, native
warnings, failed attempts, dense frames and sampled recordings under
`runs/phase4b3-*`. Reused neural patches keep their producer hashes and masks;
no weights or new inference outputs are introduced. Commit only authoring,
validation/reproduction code, tests and concise results. Do not promote or delete
old rejected experiments because a later transition looks better.

Phase 4B.4 keeps fresh PSDs/projects/runtime bundles, generated cheek tint, source
geometry inspections, MCP transcripts, controlled/dense captures, comparison sheets,
recordings and development-review records in ignored `runs/phase4b4-*`. Commit only
optional authoring/viewer/review code, tests and concise documentation/benchmark.
Previous accepted and rejected runs remain immutable; user review is a separate gate.

Phase 4B.4.1 keeps mouth inspections, snapshots, fresh PSD/project/runtime exports,
all rejected iterations, comparison sheets, browser profiles and Core reports under
ignored `runs/phase4b4-1-*`. No raster artwork is regenerated. Commit optional mouth
and review code, regression tests, concise results/design and benchmark only. The
Phase 4B.4 candidate remains preserved despite the user's visual rejection.

Phase 4B.6 keeps body inspections, immutable predecessor inventories, editor recovery
snapshots, PSD/project/runtime exports, Core reports, continuous frames, browser
profiles and sampled WebM recordings under ignored `runs/phase4b6-*`. Source artwork,
model downloads and accepted benchmarks remain unchanged. Version only reusable
body/viewer code, validation/report scripts, tests, concise results and benchmark
summaries. Retain the failed motion-format/name/save attempts, earlier nod-direction
candidate, and Girl2's inherited lip-triangle failures. Neither a rendered movie
nor a development review records user approval.

Phase 4B.6.1 retains saved-project inspections, numerical isolation probes,
MOC-bound geometry contracts, optional composition stages, reverse-order and failed
candidates, face/body captures, recordings and whole-runtime-bound review records
under ignored `runs/phase4b6-1-*`. Original body/mouth references stay frozen.
Commit reusable composition and regression code, concise results and benchmark
summaries only. Model3 hashes alone do not identify referenced MOC/exp3 contents.

Phase 4B.6.2 freezes the reviewed combined Codel as
`runs/references/codel-combined-v1/`, with a separate user acceptance record and
full SHA-256 inventory. Files/directories are read-only (0444/0555); the Git-pinned
manifest hash provides integrity, not root-proof storage. Never overwrite or repin
v1. Future changes require a new reference ID and review. Commit only the small
`docs/references/codel-combined-v1.json`, tests and documentation. The 1,806 payload
files, original candidate, source artwork, reproduction runs and audit evidence
stay ignored. Historical failures and pending labels remain as recorded; the new
limited user review does not retroactively approve earlier candidates.

Phase 4B.7a retains canonical-source copies, Qwen auxiliary poses, raw decodes,
protected composites, masks, semantic predictions, code snapshots, rejected runs,
restart diagnostics and review galleries under ignored `runs/phase4b7a-*`.
Auxiliary poses are generated hypotheses, never observed anatomy or accepted rig
artwork. Commit only study scripts, prompt/config recipe, tests, concise documents
and the small benchmark. Model weights and source/runtime reference pins remain
unchanged. A screening decision is exact-image development review, not user approval.

Phase 4B.10 establishes `codel-frontal-master-v1` as synthetic primary artwork,
with the original retained only as identity/style reference. Keep both source
hashes and the older canonical/angled freezes unchanged. The separately reviewed
`runs/references/codel-frontal-prototype-v1` contains 203 read-only payload files;
its Git-pinned manifest and separate human runtime decision identify the accepted
limited prototype. Decomposition/backing approval alone cannot approve animation.
All matte derivatives, inferred backing, layered PSDs, editable projects, runtime
exports, browser profiles, images, clips and failed candidates stay in ignored
`runs/phase4b10-*`. Only code, tests, concise reports and small provenance/benchmark
JSON enter Git. Synthetic observed pixels mean copied master samples, not verified
anatomy. No production deployment or elbow/finger articulation is authorized.

Phase 4B.11 keeps native elbow projects, failed mesh-transform exports, source-derived
sleeve caps, joint hypotheses, local correction proposals, exact user reviews and
all Core/browser evidence under ignored `runs/phase4b11-*`. New hidden-shape samples
remain inferred even when their RGB is copied from the synthetic master. The user
accepted the bilateral candidate as a limited experiment; this does not overwrite
or promote over the frozen frontal prototype. Commit only authoring/review code,
small benchmarks, tests and concise documentation. Preserve historical failures.
