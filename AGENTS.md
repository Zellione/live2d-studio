# Local Codex instructions for live2d-studio

## Mission
Build an open-source, Linux-native workflow for turning one or more 2D character illustrations into a Live2D model **actually usable in SillyTavern's Live2D extension**, with minimal manual image editing. Read `docs/HANDOVER.md` before planning changes.

## Environment and coding conventions
- Target Arch Linux, Hyprland/Wayland with XWayland, RTX 5090 32 GB VRAM.
- Run through local Codex CLI so localhost MCP tools and GPU are accessible.
- Use Python with `uv` for project-specific environments and packages; do not install Python libraries system-wide with pip.
- Shell examples must be zsh-safe. Prefer `bash <<'BASH'` for multi-line commands. NEVER assign to shell variables named `path` or `PATH`.
- Prefer `vim` (or `sudo vim` for privileged files) when explaining manual file edits.
- Prefer `git --no-pager` and `systemctl --no-pager` for outputs.
- Do not require Photoshop, paid Cubism software, external hosted inference, or cloud image services.

## Safety, scope, and reproducibility
- Never overwrite original input artwork or the user's actual SillyTavern installation.
- Do not install unreviewed AUR packages, run arbitrary remote installer scripts, change GPU drivers, BIOS, global shell PATH, or other host settings without explicit approval.
- Avoid writing to system folders and user profile secrets. Keep downloads and generated files under the project or user-approved tool install locations.
- PSD2Live MCP must remain on loopback (`127.0.0.1`); prefer an access token when supported and never commit it.
- Inspect the version and license of every tool and model; pin versions and record provenance, including image asset rights.
- Never claim compatibility from documentation alone: test with the installed extension and save evidence (logs/screenshots, sanitized where necessary).
- Make small, reviewable changes with tests. Preserve intermediate PSDs, `.psd2live` project files, and export diagnostics.
- Do not change the upstream SillyTavern extension initially. If a compatibility adapter is necessary, isolate it, document why, and test against the upstream runtime.

## Milestone sequence
1. **Phase 0 (first assignment):** Inspect SillyTavern's loader and PSD2Live outputs; smoke-test one sample export with the actual installed extension. Analyze `.model.json` vs `.model3.json` and underlying runtime support rather than renaming files blindly. Produce `docs/compatibility.md` and a repeatable smoke-test recipe.
2. **Phase 1:** Establish PSD2Live MCP connection; enumerate operations, create/open a sample, inspect state, make a small reversible rig edit, export; record results.
3. **Phase 2:** Extract image parts, inpaint occluded regions, create layered PSD compatible with PSD2Live. Begin with frontal bust and limited features. Automate segmentation and visual QA; permit human checkpoint if needed, but do not require drawing/editing skill.
4. **Phase 3:** Generate a basic rig: idle, blink, eye gaze, mouth open/close, breathing, modest head rotation, key expressions.
5. **Phase 4:** Build, validate, package, and (only with approval) copy final model into SillyTavern's Live2D assets directory. Validate emotion triggers and text-talk behavior in SillyTavern.

## Acceptance tests
- An independently repeatable end-to-end smoke test succeeds in the installed SillyTavern Live2D extension.
- Output is portable within its model folder and includes all references/textures/metadata.
- Input illustrations remain unchanged; PSD and rig project sources are preserved.
- Tests cover required file references, supported runtime version, and expected parameter IDs.
- Record true limitations, visual artifacts, and required manual interventions; do not describe an approximation as a full rig.

## Working style
- For each phase, first summarize findings, proposed changes and test commands. Implement only that phase, test it, and provide a concise result with files changed and any blocking dependencies.
- Keep a decision log in `docs/decisions.md` as assumptions are validated.
- If a tool or MCP connection is missing, report the exact blocker and minimal setup needed instead of choosing a paid alternative.

## Phase 2 repository state
- Read `docs/phase2-results.md`, `docs/phase2-architecture.md` and `docs/artifact-policy.md`.
- Golden fixtures: `tests/fixtures/phase0/` and `tests/fixtures/phase1/final/`.
  Never regenerate these in place. Keep all new runs, diagnostics and exports in `runs/`.
- Use `uv sync --frozen` and `uv run --frozen python -m unittest discover -s tests -v`.
  Optional GPU probe: `uv run --frozen --extra gpu live2d-studio doctor`.
- Inference must only read raster inputs/configuration. Fixture metadata belongs
  exclusively to benchmark generation/evaluation; never import it into segmentation.
- Manifest v1: relative paths, hashes, source rights, observed/reconstructed masks,
  explicit missing/unknown regions. Scores are uncalibrated candidate indicators.
- The CPU flat-colour baseline passes the geometric benchmark; real anime parsing
  fails semantic acceptance. Phase 2.5 separately validates See-through GPU
  inference on the 5090; read its results before generalizing to other inputs.
- Keep MCP on loopback; tokens only from an explicitly provided environment.
  `mcp-check` is read-only. Never read profile secrets to close the live CLI auth gate.
- Phase 3 was the previous stopping point. Phase 4A was subsequently authorized;
  the current Phase 4A section below governs deployment scope.

## Phase 2.5 neural backend
- Read `docs/phase2-5-results.md` and `backends/see-through/README.md`.
- Never install worker dependencies into the main environment. Its separate
  pyproject/uv.lock and models.lock.json pin source, wheels and approved weights.
- `prepare --backend see-through` imports an offline worker bridge. It does not
  download weights or load Torch inside the baseline process.
- V2 generated alpha is fractional. Observed masks remain protected-original
  pixels; no inferred hidden mask may be described as independently known truth.
- XCF metadata and SAM predictions are not independent inference inputs/GT
  interchangeably. Only the reviewed XCF evaluation recipe supplies ground truth.
- Coverage, correct semantic assignment, reconstructed plausibility, import and
  rendered motion are separate gates. Girl2 passed a basic animation experiment;
  Wikipe-tan failed semantic quality. Retain both outcomes.

## Phase 2.6 source fidelity and quality
- Read `docs/phase2-6-results.md` and `docs/phase2-6-quality.md`. Frozen Phase 2.5
  measurements stay unchanged; compare against them, never relabel them current.
- `refine` reuses existing decomposition and optional source-matched SAM masks.
  Observed masks prove copied RGBA; semantic ownership can still be uncertain.
  A source sample must not appear in multiple observed layer masks.
- `readiness` and `review-poses` cannot grant production readiness from part names
  or moving vertices. Keep semantic, source, hidden, import, Core and visual gates
  separate. Test combined head/blink/mouth poses in an isolated runtime.
- `prepare-rig` guard bands remain experimental: Girl2 neutral equality passed,
  but new hair fragments made its export unacceptable. Prefer the contour-corrected
  source restoration without guards. Retain negative visual evidence.
- Final tested Girl2 is a limited prototype with remaining hair gaps and flat lids.
  Girl1/Wikipe-tan fail parsing; Boy1 fine beard/brow ownership is not rig-ready.
  Phase 3 was subsequently authorized for Girl2 only; see the current section below.

## Phase 3 Girl2 RP prototype
- Read `docs/phase3-results.md`, `docs/phase3-animation.md` and
  `docs/phase3-sillytavern.md`. Keep the accepted Phase 2.6 project immutable.
- `recipes/girl2-animation.json` is specific to the inspected Girl2 rig. No general
  character conversion or new image inference was implemented in this phase.
- Prefer `runs/phase3-final/` and the local `runs/phase3-review/` gallery. Rebuilds
  must use fresh directories. Rig/texture neutrality and RP lifecycle are separate gates.
- `sillytavern_settings.json` maps all 28 installed classifier labels. Actual
  message-handler tests use mocked network classification, not model inference.
- The optional adapter only patches a pinned, isolated `.cache/` ST copy. Never
  silently install it into production or claim upstream has the corrected behavior.
- Retain HTTP-fallback failure evidence and strict/raw opacity excursion counts;
  ST-caught listener errors are distinct from uncaught browser exceptions.
- Run Python regression tests plus `node tests/test_rp_talk.mjs`; actual RP browser
  tests cover messages, mapping, idle, interruption, reload, fallback and stale replies.
- Phase 3 authoring remains frozen. Phase 4A subsequently authorized isolated
  packaging/deployment tests only; see below.

## Phase 4A isolated packaging and rollback
- Read `docs/phase4a-results.md`, `docs/phase4a-deployment.md` and
  `docs/benchmarks/phase4a.json`. Accepted Phase 3 art/rig/runtime remain immutable.
- `package` uses `recipes/girl2-package.json`; do not silently repin accepted hashes.
  Runtime references, all seven expressions, two motions, mapping, actual pinned
  Core instantiation and reviewed sleeve/torso/neck mesh IDs must pass.
- `deploy`/`rollback` write only marked `.cache/phase4a-*` copies. Production writes
  remain unimplemented, even with `--execute`; never add an implicit override.
- Keep the disposable server stopped during changes. Existing models require explicit
  `--replace`; backups, write-ahead journals and rollback hashes stay in `runs/`.
  Never force through changed user files, damaged backups or unknown upstream hashes.
- CLI settings are read-only. Browser-created test state is preserved/reset separately;
  rollback restores deployment-owned files, not arbitrary later chats/settings.
- The adapter changes only pinned `live2d.js` plus `rp-talk.mjs`. No suitable complete
  companion hook was found in the inspected version; review again before upgrading.
- Framing is not anatomy. Preserve a full bilateral source inventory and distinguish
  source preservation, semantic ownership and animation. Missing source hands do
  not fail Girl2 portrait completeness; lost visible limbs must block acceptance.
  Synthetic mask checks are not independent real limb benchmark validation.
- Repeat with `scripts/phase4a_acceptance.py --run-id NEW_ID`; real message handlers
  use classifier network mocks, including before application startup. Keep the
  intentional upstream HTTP failure and all raw opacity excursion evidence.
- Run Python regression tests and `node tests/test_rp_talk.mjs`. No generated packages,
  snapshots, browser data or backups enter Git. Local review: `runs/phase4a-review-final/`.
- Stop after Phase 4A. No production installation, Phase 4B automation or training
  is authorized. Production requires separate explicit authorization and implementation.


## Phase 4A.1 production audit
- Read `docs/phase4a1-production-audit.md` before any production planning. Audit from
  `f1c7e39` was production-read-only; no production execution is authorized.
- `audit-production` may inspect code, Live2D asset trees and its restricted settings
  projection. Never dump/copy raw settings, read chats/cards/credentials, call production
  HTTP endpoints, or stop/restart services to complete this audit.
- Production expressions `api=2` is unsupported by the installed Live2D classifier
  path: upstream joy fallback, current adapter neutral fallback. Do not change the
  user's provider or promise full automatic emotions from package compatibility.
- Project ext4 and target Btrfs differ. The current installer remains isolated-only.
  Future target-side transactions need explicit authorization and implementation;
  preserve the document's controller-first order and durability/recovery requirements.
- No audit `--execute`, production override or retagging production as a test copy.
  Proposed production commands in the audit are unimplemented design contracts.
- Stop here pending explicit user authorization. No Phase 4B or training assignment.


## Phase 4A.2 target-filesystem transactions and classifier investigation
- Read `docs/phase4a2-results.md`, `docs/phase4a2-deployment.md` and
  `docs/phase4a2-classifier.md`. This assignment superseded the earlier audit stop
  only for implementation and disposable testing. Production remains disabled.
- New `target-deploy`/`target-rollback` accept only fixed dedicated test bases:
  `/home/zelli/tools/ai/live2d-studio-phase4a2-tests` and `.cache/phase4a2-tests`,
  with `RUN/instance` plus private sibling `RUN/transactions/ID`. Do not broaden
  allowlists or retag production. Old Phase 4A commands/restrictions stay unchanged.
- Cross-filesystem copies go into target-local private staging. Preserve exact pins,
  verify hashes/metadata, publish controller before patched extension; restore original
  extension before controller removal. Keep plans, backups and standalone helpers.
- Production writes still need separate authorization and a reviewed production-only
  binding. No actual model/API calls, provider changes, private chats, production
  service changes, Phase 4B work or training are authorized.
- ST's exported classifier cannot provide typed errors or fresh shared message results.
  The authorized blocker path retains the current adapter, neutral fallback and provider
  preferences. `lastExpression` exists but has no message identity or success flag.
  Never claim LLM integration from the synthetic exact-function experiment or local
  classifier network mocks. No global fetch override belongs in shipped adapter code.
- Run all Python tests and `node tests/test_rp_talk.mjs`; 15 new transaction tests
  additionally run on Btrfs with `PHASE4A2_TEST_BASE` set to the dedicated base.
  `scripts/phase4a2_acceptance.py --run-id NEW` runs isolated message/render/removal
  scenarios and recovery with `/data` hidden. Node source-contract audits stay synthetic.
- Local evidence: `runs/phase4a2-acceptance-v3`, `runs/phase4a2-audit`,
  `runs/phase4a2-review-final`. Preserve expected upstream HTTP failure, blocked LLM gate,
  raw opacity excursions, and existing portrait limitations. SIGKILL is not power loss.
- Stop after Phase 4A.2; report remaining production/classifier decisions.


## Phase 3.1 standalone preview and facial candidate
- Read `docs/phase3-1-results.md`, `docs/phase3-1-preview.md` and its benchmark.
  This explicit assignment reopened Girl2 facial authoring only; production remains disabled.
- `preview-live` uses a loopback asset allowlist, accepted Phase 3 by default and a
  version selector for `runs/phase3-1-final-v2/runtime/`. No settings writes or backend.
- Keep Phase 3 sources/runtime and original animation/package recipes immutable.
  New recipe: `recipes/girl2-expressive.json`; new builder: `scripts/build_phase3_1.py`.
- User accepted clearer expressions and the corrected sad eyebrows. Preserve the
  dedicated sad-brow axis, neutral equality, original artwork and rejected evidence.
- Repeat browser review with `scripts/phase3_1_acceptance.py` in fresh runs. Keep
  user visual review distinct from geometry/pixel tests and professional-quality claims.
- Stop after Phase 3.1. No production deployment, Phase 4B or training is authorized.

## Phase 4B reusable creation
- Explicit user authorization on 2026-11-03 supersedes the earlier Phase 4B stops
  for local reusable orchestration, generic authoring and independent benchmarks.
  Read `docs/phase4b-results.md` and `docs/phase4b-create.md` before continuing.
- `create` uses the separate pinned offline worker, hash-verified resumable stages
  and loopback MCP. Never turn cached masks or reviewed Girl2 IDs into universal
  semantic ground truth. No coding agent is a runtime dependency.
- Keep failed attempts and negative characters. A source-fidelity score, role name,
  moving vertex or valid MOC cannot grant semantic/visual acceptance. Do not weaken
  gates to obtain a passing independent benchmark. Review records must remain bound
  to exact evidence and identify development-agent review separately from user review.
- Accepted Phase 2.6/3/3.1 projects, Golden Fixtures and Girl2 package pins remain
  immutable. New profiles and operations derive targets from inspected semantics
  and ancestry. Source pixels and generated/procedural alternatives stay distinct.
- All inference, artwork, PSD/project/runtime, raw reports, browser profiles and
  downloads remain outside Git. Commit only code, configuration, tests, provenance
  definitions and concise results. Production deployment restrictions are unchanged.
- Stop after Phase 4B. No production installation or training is authorized.
