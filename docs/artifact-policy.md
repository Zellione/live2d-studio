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
