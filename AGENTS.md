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

## Phase 4B.1 facial reconstruction
- Explicit user authorization reopens only generic facial artwork/rigging and
  local regression evaluation. Read docs/phase4b1-results.md and
  docs/phase4b1-facial-artwork.md. Orchestration and deployment gates remain intact.
- The user accepted limited Sara visual improvement in the exact gallery
  runs/phase4b1-review-candidate. Preserve runs/phase4b1-sara and its review record.
  This is not general-purpose conversion, anatomical truth or production approval.
- Single-image reconstruction never reads the other spritesheet tiles. Only the
  evaluation gallery reads them; any future multi-reference run must be separate.
- Source-observed pixels stay exact/unique; generated backing, closed lashes and
  mouth alternatives retain provenance/uncertainty. Runtime-neutral equality is
  separate and is not claimed for the reconstructed candidate.
- Preserve the failed early facial candidates and Girl2 open-mouth regression.
  Reuse validated inference; do not alter accepted Phase 3/3.1 or package pins.
- Stop after Phase 4B.1. No production deployment, new training or global changes.

## Phase 4B.2 local neural inpainting
- Explicit authorization reopened local model investigation/downloads and facial
  inpainting comparisons. Read docs/phase4b2-results.md,
  docs/phase4b2-model-evaluation.md and backends/inpainting/README.md.
- Keep deterministic reconstruction as default. All five rendered neural/hybrid
  candidates were rejected by development review. Smoother Qwen closed-eye stills
  produce a doubled contour near 0.1 openness; quarter-step poses miss this defect.
- LaMa and Qwen Q4_K_S/FP8-encoder execute in separate frozen uv environments.
  Preserve model/source pins, project-local caches and exact-image hybrid reviews.
  Cached predictions require matching parameters, model, input, mask and output
  hashes. Empty hybrid selection uses deterministic fallback without model loading.
- Source layers/masks remain immutable to inpainting; generated alternatives and
  uncertain boundary masks remain distinct. No anatomy, universal quality or
  quantization-degradation conclusion follows from the tested crops.
- Keep all failed attempts, including the confounded rescaled Boy1 holdout and
  failed first Girl2 baseline talking assertion. Native holdout and repeated
  browser evidence are separately labelled. No acceptance gate was weakened.
- Review: runs/phase4b2-review-release. Accepted Phase 4B.1/3/3.1 and package pins
  stay frozen. Run Python regressions and node tests/test_rp_talk.mjs.
- Stop after Phase 4B.2. No production deployment, training or system changes.

## Phase 4B.3 rig-aware transitions
- Read docs/phase4b3-results.md and docs/phase4b3-transition-quality.md.
  This phase used existing artwork only; no model downloads or inference.
- `--facial-motion aligned` is an explicit candidate option; legacy motion and
  deterministic artwork remain defaults. Semantic/visual review gates persist.
- Source-derived and replacement curves move together during closure. Preserve
  the opaque lower-stroke handoff and source visibility delay: earlier symmetric
  fades lost contrast, and an early Qwen source triangle reversed at .05.
- Require the dense 401-frame suite and exported Core channel/visible-triangle
  audit. Keep native warnings on invisible squashed keys separate from visible
  geometry, source preservation and natural-animation assessment.
- Sara's Qwen loop near .1 was eliminated in the inspected candidate. Girl2's
  neural lash-style mismatch, neural skin/cavity failures and every early rig
  remain local. No neural image or development review grants user approval.
- Keep accepted Phase 3/3.1/4B.1, model/package pins and rejected Phase 4B.2 runs
  frozen. Review: runs/phase4b3-review-final. No hardcoded character coordinates,
  opaque artwork IDs or source hashes belong in generic authoring.
- Stop after Phase 4B.3. No production deployment, training or system changes.

## Phase 4B.4 expression legibility
- Read docs/phase4b4-results.md and docs/phase4b4-expressions.md. Explicit authorization
  reopened optional generic facial expression authoring only; production stays disabled.
- Independent source-relative brow inclination/raise, mouth skew/displeasure and
  procedural blush are candidates. Existing defaults and accepted models stay frozen.
- Source brow slopes and both disconnected mouth halves matter. Preserve the failed
  small-shear and one-component-fit evidence. Do not interpret role names or ambiguous
  brow-over-bangs styling as independently verified anatomy.
- Compare with the viewer's still-expression mode; keep 149 controlled captures,
  the 401-frame transition suite and exported 72/756-sample geometry audits separate
  from visual legibility. Development review is not user approval.
- Candidate: runs/phase4b4-sara-v6. Review: runs/phase4b4-review-release.
  Blush has generated provenance, inferred landmarks, independent opacity and face
  ancestry. Neutral/Happy/Sad/Surprised behavior remains unchanged; Sad is still limited.
- Stop after Phase 4B.4. No production deployment, training, model or system changes.

## Phase 4B.4.1 mouth-specific expressions
- Read `docs/phase4b4-1-results.md` and `docs/phase4b4-1-mouth-design.md`.
  The user rejected Phase 4B.4 legibility; no previous development assessment grants
  user acceptance. New optional mouths revise all seven recipes, not brows/eyes.
- Candidate `runs/phase4b4-1-sara-v4`; mouth-only/full galleries in
  `runs/phase4b4-1-review-release`. User visual approval remains pending.
- Keep original source/cavity/backing/blush assets, all accepted models, package pins
  and rejected candidates immutable. No new inference or raster artwork was needed.
- Author each mouth key from rest, preserve the source seam without opening geometry,
  and use visible full-open cavity winding as reference. Keep failed accumulation
  and invisible-reference diagnostics. Do not weaken visible-triangle/opacity gates.
- Mouth-only comparisons neutralize every non-mouth parameter. Shape/opening bounds,
  emotional talk return, exact neutral pixels and source preservation are separate
  from perceived emotion. Retain 401-frame/72-sample and 819-sample Core checks.
- Stop after Phase 4B.4.1. No production deployment, training or system changes.

## Phase 4B.5 independent Codel benchmark
- Read `docs/phase4b5-results.md` and `docs/phase4b5-generalization.md`.
  Explicit authorization covered local benchmark inference and evaluation only.
- Preserve the sealed `runs/phase4b5-codel-full-first` and all accepted references.
  Only original neutral Codel3.png entered creation; PSD/reference annotations
  are evaluation-only. Keep input-selection exposure and crop-not-run disclosure.
- All twelve first-run stages completed without character-specific rig operations.
  Source restoration and limited facial ink scores do not establish anatomy or
  visual acceptance. Both arms/hands share an unsided layer; no full-body rig claim.
- Optional unchanged expression/mouth scripts produced a separate candidate.
  Its 819-sample Core audit fails Embarrassed source-seam invariance by 1.19e-7
  against 1e-7. Do not relax that threshold or discard the failed report.
- Development visual review rejects quarter-open eye contours/shading fragments
  despite passing dense numerical checks. User acceptance remains pending.
  Gallery: `runs/phase4b5-review-final`. Preserve all intermediate/report failures.
- Stop after Phase 4B.5. No production deployment, new training or host changes.


## Phase 4B.6 body/head/hair candidate
- Explicit user authorization reopened local reusable body/head/hair authoring and
  regressions from `68e1d25`. Read `docs/phase4b6-results.md` and
  `docs/phase4b6-body-rigging.md`. Production remains disabled.
- `prepare-body` builds separate candidates from verified creation/experiment
  ancestry. Discover common head/face/hair parents; never use character IDs or
  coordinates as generic bindings. Preserve neutral keys, artwork and draw order.
- Candidate `runs/phase4b6-codel-v7`; comparison/gallery
  `runs/phase4b6-review-release`. User visual review remains pending. No promotion.
- Arms/hands remain one unsided component with no reviewed joints/hidden backing.
  Shared breathing/body motion is not independent articulation. Head nod and
  questioning tilt are the only new gestures; no hand lift or shoulder-only shrug.
- Retain 496-sample Core, 401-frame facial and continuous body/reload evidence.
  Girl2's 1,716 inherited lip reversals keep its broad gate FAILED. Sara's numeric
  passes do not close source-boundary visual gaps. Preserve all negative evidence.
- PSD2Live custom Bezier saves can retain a dirty flag: verify/save the full candidate
  archive, checkout the predecessor history, reopen for export. Never discard work.
- Keep frozen Codel/accepted models/package pins unchanged. No inference/downloads
  needed. Run Python and JS regressions; stop after Phase 4B.6 without deployment,
  training or host changes.

## Phase 4B.6.1 expression/body composition
- Read `docs/phase4b6-1-results.md`. User accepted Phase 4B.6 head/hair/breathing/
  gesture behavior; preserve it. Final combined expressions still await review.
- `prepare-performance` composes optional coordinated mouths then calm body motion;
  both options default to preserve. `create` exposes the same optional composition.
  Read actual saved expression entries; never regenerate them from the legacy
  five-channel recipe after coordinated authoring. Check exported channels/fades.
- Candidate `runs/phase4b6-1-codel-v3`; gallery `runs/phase4b6-1-review`.
  Confused round=1/open=.35, Surprised round=1/open=.85. Settled Confused matches
  the earlier improved mouth reference exactly; body/physics clips stay exact.
- Historical `1e-7` seam failure stays failed. New scale-aware verification requires
  an exact-MOC-bound saved geometry contract, no opening geometry dependencies,
  eight float32 steps at mesh scale AND a .001 source-pixel cap. Without the
  contract, the probe retains the original strict rule. Keep raw legacy results,
  precision probes, negative controls and Girl2's inherited 1,716 lip reversals.
- Preserve failed Part-creation experiment, v1/v2 candidates and the first missing
  face-summary field. User review is distinct from numerical/development review.
- Whole runtime hashes identify the candidate; model3 alone may be unchanged.
  No inference/downloads/training/system changes or production work. Stop after
  Phase 4B.6.1; no automatic promotion.

## Phase 4B.6.2 reviewed combined Codel reference
- Read `docs/phase4b6-2-results.md` and `docs/references/codel-combined-v1.json`.
  The user's “Das sieht soweit gut aus jetzt.” grants limited visual acceptance
  of the exact combined candidate, not professional/full-body/production acceptance.
- Preserve `runs/phase4b6-1-codel-v3` and the read-only snapshot
  `runs/references/codel-combined-v1`. Never repin or regenerate this reference
  in place. Its 1,806 payload hashes and separate user review are manifest-bound.
- Fresh autonomous `create` and `prepare-performance` reproduced all 15 referenced
  runtime files exactly. Editor CAN3/CMO3 archives differ. Use deterministic
  reconstruction, aligned facial motion, coordinated mouths and calm body options;
  creation defaults remain unchanged. Other characters need their own reviews.
- Run `tests/test_reviewed_codel.py` with the Python suite. Local artifact checks
  skip when the ignored snapshot is absent; metadata/default checks always run.
  Retain old Codel seam failure and Girl2's 1,716 lip reversals as failures.
- Only docs, tests and small manifests enter Git. No inference, training, production
  access or default changes. Stop after Phase 4B.6.2.

## Phase 4B.7a auxiliary pose feasibility
- Read `docs/phase4b7a-results.md` and `docs/phase4b7a-qwen-feasibility.md`.
  This assignment authorized local Qwen pose experiments only; no final arm rig.
- Nine completed images use the original frozen flat Codel image, existing
  Q4_K_S/FP8 weights and separate worker environment. No PSD/reference tiles enter
  generation. Default creation behavior and `codel-combined-v1` remain frozen.
- Six stronger edits and the weaker lift fail screening. Two weaker near-copies
  pass coarse consistency but add no useful structure; actual semantic analysis
  retains one substantial unsided arm component. No articulation success claim.
- Review: `runs/phase4b7a-review-release`. Protected face equality is imposed by
  the mask; raw outputs, clipping/seam limitations and all failures remain visible.
  Generated poses/region proposals are uncertain auxiliary inference, never GT.
- Preserve the interrupted first batch, verified recovery and lower-strength
  controls. No model downloads, training, production or default changes occurred.
  Stop after Phase 4B.7a; future pose-conditioning/arm authoring needs new scope.


## Phase 4B.7b guided auxiliary pose reviewer
- Explicit user authorization covers local Qwen calibration, a standalone human
  reviewer and selected-only feasibility analysis. Read docs/phase4b7b-results.md,
  docs/phase4b7b-generation.md and docs/phase4b7b-reviewer.md.
- Keep the frozen original and all accepted references immutable. New Qwen pose
  work is separate from the facial worker and creation defaults; no production work.
- Exactly five fresh seeds per new batch. Preserve fixed prompts/configs/guides,
  model/input/output hashes, failed attempts and all reviewer history. Accepted
  poses must not regenerate. Resume only unfinished reserved tasks in new folders.
- Only real human decisions may approve Codel auxiliary poses. Synthetic browser
  fixtures and development calibration screening are not user approval. Selected
  images remain inferred artwork, not verified anatomy or production rig assets.
- Review server stays loopback-only with fixed assets, guarded mutations and
  per-run process/GPU locks. No unrelated workflow/settings/credential inspection.
- Run Python regressions, both JS suites and synthetic reviewer browser checks.
  Stop after Phase 4B.7b; no final arm rigging, promotion or deployment.


## Phase 4B.8 canonical front-facing base
- Explicit user authorization covers an opt-in canonicalization stage before
  further helper generation or arm rigging. Read docs/phase4b8-results.md and
  docs/phase4b8-canonicalization.md. Existing production/default restrictions stay.
- Use the original flat artwork plus a frontal guide; retain five seeded batches,
  exact metadata and rejected outputs. Only human selection may freeze a base.
- A canonical base is synthetic working geometry. Preserve the original as the
  identity/style source, all historical references and the approved 4B.7b helper.
- Freeze separate original/canonical payloads with approval and hashes. Reject
  changed evidence; recover interrupted freezes without silently replacing files.
- Future helper preparation is explicit and must bind canonical primary geometry
  separately from original identity/style. No new helper inference, automatic
  downstream migration, final arm rigging or production deployment in this phase.
- Run Python/JS regressions and canonical reviewer checks; synthetic test approvals
  never grant real image acceptance. Stop after Phase 4B.8.

## Phase 4B.8.1 canonical-based guided gestures
- Explicit authorization reopens three-reference helper generation only. Read
  docs/phase4b8-1-results.md and docs/phase4b8-1-gesture-generation.md.
- Keep the approved canonical, original, prior selections and accepted runtimes
  immutable. Use init-from-canonical with an explicit opt-in gesture profile.
- image1 is synthetic canonical geometry, image2 the desired guide, image3 the
  original identity/style reference. Require actual three-reference evidence;
  two-reference controls must be explicit, separate and never silent fallback.
- The first target bends the anatomical right elbow (viewer left), forearm up,
  hand at chest height. Arms-down images fail compliance, regardless of parsing.
- Human approval, gesture compliance, segmentation and verified anatomy are
  separate. Parse selected images only; never use raw differences as hidden truth.
- Other poses remain independently reviewed. No automatic all-pose generation,
  final arm rigging, accepted-runtime replacement or production deployment.


## Phase 4B.8.2 optional Lightning acceleration
- Read docs/phase4b8-2-results.md and docs/phase4b8-2-lightning.md. The 2509-specific
  8/4-step BF16 adapters are pinned separately in lightning.lock.json; do not
  change historical workers, model locks, presets or approved selections.
- Use explicit `init-from-canonical --lightning` for fresh canonical helper runs.
  Keep all three references. Require complete model-only GGUF patches and exact
  adapter/input/output hashes; never silently ignore missing/incompatible LoRA.
- Balanced/Fast/Quality are optional, compared presets. Quality keeps 40 steps;
  no-LoRA low-step controls are failures, not replacement presets. Stage timings
  include lazy transfers; Torch peaks are not whole-board VRAM measurements.
- Five new Balanced candidates bend the intended arm, with variable fingers and
  hand height. None is automatically approved. No SAM or rigging follows from
  speed, visual plausibility, patch counts or pixel differences alone.
- Keep user reviewer on localhost 8804, comparison gallery on 8803. Run Python
  and both JS suites. Stop after performance/quality evaluation; no production,
  final arm rigging, retraining or unrelated system changes.

## Phase 4B.9 selected-family anatomy assessment
- Read docs/phase4b9-results.md and docs/phase4b9-arm-assessment.md. Four helpers
  have explicit hash-bound human approvals; the fifth remains pending and is not
  required. Preserve the selected-only export and runs/phase4b9-family.
- The user explicitly requires keeping the exact accepted artwork and rig.
  Canonical/helper images are synthetic evidence, not replacement permission.
- SAM bilateral masks and heuristic shoulder/cuff/elbow proposals do not certify
  joints, fingers, hidden backing or a fixed-length skeleton. Keep uncertain
  straight elbows and the 2.77× right projected-forearm discrepancy explicit.
- The canonical raster swap/crossfade fails attachment and intermediate-frame
  quality. No PSD2Live project or new gesture runtime was authored. Prefer future
  discrete gestures only after original-view arm cuts, attachment and backing review.
- Keep all failed landmark/probe evidence, old guide and accepted references.
  The 215 Python tests, both JS suites and fresh Core/browser runs preserve the
  old rig; they do not validate arm motion. No validation thresholds changed.
- Review at localhost 8805; unchanged accepted live rig at 8806. Stop for visual
  review before further articulation. No new generation or production changes.


## Phase 4B.10 frontal master is now the primary target
- The user's corrected goal supersedes Phase 4B.9's exact-angled-rig constraint.
  Read docs/phase4b10-results.md and docs/phase4b10-frontal-master.md.
  codel-frontal-master-v1 is the approved synthetic primary artwork. Original
  angled artwork is identity/style reference only; its accepted rig stays archived.
- Preserve the exact canonical freeze and historical manifests. New promotion
  metadata distinguishes source authority, uncertain anatomy and runtime approval.
- Frontal layers separate both upper sleeves, forearms and hands. Human review
  approved the initial matte/backing and then the local brow-backing repair.
  Pixel-exact neutral copying from a synthetic master is not original anatomy.
- Four existing helper approvals remain locked in the fresh frontal reviewer.
  New aside guides are separate versioned 24-degree targets constrained by framing;
  neither guide is generated or approved automatically. Do not edit historical runs.
- First arm gestures use independent root-pinned shoulder fields, not helper-image
  crossfades. No elbow/finger articulation or raised-forearm/wave runtime claim.
  Preserve original body/head/mouth regression thresholds and all failed attempts.
- The user separately accepted the exact repaired runtime as a limited frontal
  prototype. Preserve `codel-frontal-prototype-v1` and its 203 frozen payloads.
  Acceptance excludes elbow/finger articulation, wave/raised-forearm runtime and
  deployment. Production SillyTavern remains untouched. Stop after Phase 4B.10.
