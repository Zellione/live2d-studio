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
- Phase 3 is the current stopping point. Do not begin Phase 4, custom training
  or production copying without a new user assignment.

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
- Stop after Phase 3. No Phase 4, training or production deployment is authorized.
