# Phase 4B.7b — local human pose review

The reviewer is a standalone Python/HTML application. It needs the project uv
environment and the already pinned local Qwen environment for generation. It
needs no SillyTavern, API provider, coding agent, PSD2Live or image editor.

## Open or resume

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/pose_reviewer.py serve \
  --run runs/phase4b7b-review --port 8795
```

Open <http://127.0.0.1:8795/>. Stopping/restarting the server preserves decisions,
images, old batches and seeds. The server binds only loopback. On a remote host,
use an explicitly configured SSH loopback tunnel; do not bind to all interfaces.

1. Choose a target pose and a named parameter preset. Inspect its source and guide.
2. Generate five candidates. Progressively completed images appear automatically.
3. Open any image for zoomed side-by-side inspection. Check face/hair, clothing,
   pose, hands, proportions and useful visible structure.
4. Accept one candidate, or flag problems and generate five more. An acceptance
   freezes only that pose. Rejected images and previous batches remain visible.
5. Mark a pose unsupported if no suitable result is achievable in this framing.
6. Save the reviewed pose set. Only accepted images are copied into the new
   `selections/ID/` directory. Pending, rejected and unsupported statuses are
   reported separately. Saving a partial set is permitted and clearly recorded.

Each normal batch reserves exactly five unique 52-bit seeds, with no reuse across
new batches. Its source, guide, prompt, negative prompt and configuration stay
fixed. Presets can differ between batches, but never inside a batch. Exact hashes,
seeds, timings and settings are visible in each candidate's metadata.

A failed/interrupted batch offers **Resume unfinished candidates**. Completed
images remain untouched; only unfinished reserved tasks rerun with their original
seeds in new retry directories. This is resuming the same five-candidate batch,
not a new random batch. Partially written/failed attempts remain available on disk.

## Create a separate experiment

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/pose_reviewer.py init \
  --input runs/references/codel-combined-v1/source/original.png \
  --output runs/NEW-pose-review --presets recipes/pose-review-presets.json \
  --rights 'LisadiKaprio; CC-BY-4.0; https://opengameart.org/content/codel-visual-novel-sprite'
```

To add a parameter or prompt comparison within the same review, write one bounded
configuration JSON and run:

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/pose_reviewer.py add-preset \
  --run runs/phase4b7b-review --name NEW-NAME --config runs/NEW-config.json
```

Existing preset names cannot be replaced. This explicit addition records old/new
catalog hashes and the new configuration; previous batches and approvals stay
unchanged. Direct in-place edits fail hash verification. Optional `prompt_suffix`
and `negative_prompt` strings are each limited to 2,000 characters and saved in
every task. Changing the producer code requires a fresh review run.

The shipped catalog provides four 1536-pixel choices: silhouette/40 steps,
skeleton/40 steps, skeleton/40 steps with denoise .8, and skeleton/20 steps.
All use CFG 4, shift 3, Euler/simple, source latents and no mask or CFG norm.
These are experimental choices, not accepted quality profiles; creation defaults
are unchanged. The neutral source is never regenerated.

CLI generation is also available (`generate --run RUN --pose right-lift --preset
NAME`). It uses the same reservation, locking and verification as the browser.
No automatic review/accept CLI exists. An accepted pose cannot be silently replaced;
use a new run for reconsideration.

## Persistence and boundaries

`review.json` records candidate IDs, settings, image hashes, human decisions and
append-only event history. Each `batches/ID/plan.json` fixes generation inputs;
`report.json`, individual `result.json` files and `worker.log` retain execution
evidence. The selected manifest includes exact approval/image bindings and marks
anatomical verification false and articulation usefulness unknown.

State writes use an atomic replace, fsync and a process lock. A per-run GPU flock
covers reservation and execution, is inherited by the worker, and rejects a
second batch even if another server/CLI process attempts it. Jobs are bounded to
five tasks, at most 60 steps and a one-hour process timeout. A server singleton
lock prevents two serving processes for the same run. Separate experiment runs
are not a global GPU scheduler; run independent calibration jobs sequentially.

The server exposes fixed UI files and registered, hash-checked image assets only.
It does not serve directory trees or arbitrary paths. Host/Origin checks, same-site
requests and an ephemeral CSRF token protect mutation endpoints; request bodies
are bounded. Tokens never enter disk state or Git. This is local single-user
review, not an authenticated multi-user service. Local disk owners can edit their
own files; this is not a tamper-proof signature system.

## Selected-only follow-up

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b7b_analyze_selected.py \
  --run runs/phase4b7b-review --selection SAVED_ID \
  --output runs/phase4b7b-review/diagnostics-NEW
```

This validates the saved selection and image hashes, then produces original /
selected / difference panels and an anatomical review checklist. Empty selections
are refused. Colour differences include pose displacement and repainting; they
are **not** measurements of recovered hidden anatomy. An anatomical inspection
must separately assess shoulders/elbows/wrists, sleeve boundaries, torso coverage,
side ownership, occlusion and cross-pose contradictions. No selected image is
applied to the frozen rig or treated as independently verified source pixels.

## Tests

Ordinary tests use synthetic fixtures and never require GPU inference. The browser
fixture is explicitly synthetic and uses a disposable run, separate from actual
human review. It exercises five-image generation, regeneration, rejection,
selection, history, comparison, zoom, unsupported state and selected-only save.
The fixture server must never be presented as the real Codel reviewer.

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python -m unittest discover -s tests -v
node tests/test_rp_talk.mjs
node tests/test_mouth_invariant.cjs
```

HTTP tests require permission to bind temporary loopback sockets. Browser QA uses
`scripts/cdp_smoke.mjs` and `scripts/phase4b7b_browser_scenario.js` against
`tests/pose_reviewer_fixture_server.py`, with a dedicated ignored browser profile.
Keep failed browser runs; test harness timing failures do not establish model
quality or human approval.
