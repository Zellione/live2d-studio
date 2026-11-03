# Decisions

## 2026-11-02 — Girl2 source-limb audit after Phase 3

- Full XCF inspection confirms source-absent forearms/hands, not dropped limbs.
  Both sleeves survive as image-left/right `handwear` and runtime meshes.
- Preserve the accepted model. Do not generate anatomical completion during audit.
- [Audit](girl2-limb-audit.md) records exact shirt/chest preservation, residual
  ownership errors and a reproducible local comparison. Framing and visible-limb
  preservation gates are future recommendations, not implemented Phase 4 work.

## 2026-11-02 — Phase 0 compatibility gate

- Installed source, not the `.model.json` wording in documentation, determines
  discovery: the installed server accepts `.model3.json`; do not rename it.
- Keep upstream extension and production SillyTavern data untouched.
- Use an original geometric fixture to remove third-party artwork/model rights
  uncertainty. Preserve PNG, PSD, editable archive, export and diagnostics.
- Validate integrity, native Core loading, browser rendering and actual ST
  integration separately. Core success cannot promote the end-to-end gate.
- Installed Core 5.0.0 loads this PSD2Live 3.6.7 MOC-version-5 export. No runtime
  adapter justified yet. Parameter presence is not proof of a working rig.
- Stop before GUI/isolated ST setup pending permission as requested in HANDOVER.
  Do not begin segmentation, broader MCP rig-edit validation or character rigging.

## 2026-11-02 — Authorized isolated browser acceptance

- User approved the isolated ST/browser test. Copied code and dependencies to
  `.cache/phase0-st`; used fresh data/config and browser profile, loopback only.
  No production user data copied and no extension/runtime modifications.
- Actual extension discovery, model dropdown, loading, software WebGL rendering,
  reload, parameter mapping and expression/motion file loading pass. Evidence:
  `docs/evidence/phase0/st-browser/` and `isolation.json`.
- Optional settings-file 404 and aborted preview idle-request are retained as
  limitations, not misreported as missing required model resources.
- Geometric-fixture compatibility gate passed. Visible facial rig quality,
  text-talk, emotion classification and hardware rendering remain untested.
- No adapter required for the verified versions. Stay within Phase 0.

## 2026-11-02 — Phase 1 rig validation, explicitly authorized

- Phase 0 committed as `fed38dc`. User expanded Phase 1 to include a visibly
  animatable test rig; this supersedes the original narrow MCP-only milestone.
- Use deterministic original raster shapes and semantic layer roles. PSD2Live
  generates meshes, deformers and standard movement; author custom Mood shapes,
  expressions and idle exclusively through MCP, never by patching rig files.
- Preserve original/intermediate fixtures; `tests/fixtures/phase1/final/` is the
  accepted version. Parameter IDs, changed Core geometry and changed browser
  pixels are three separate gates. Pixel tests use the actual ST-owned model.
- Correct brow direction after visual review. Use Multiply for expression eye
  entries and Add for mouth; neutral does not overwrite blink/talk channels.
- Complete keys must include all directly bound axes. Author mood at all 27
  existing head/lean combinations per brow. Do not infer full visual quality
  from the local geometry safety gate.
- Connected authenticated MCP replay succeeds. Standalone HTTP CLI receives
  401 without PSD2LIVE_MCP_TOKEN; do not read profile secrets or claim that CLI
  path was end-to-end validated. Token must be supplied locally for that path.
- Extension/runtime/production installation remain unchanged (137 code files
  compared). Phase 2 is a proposal only; no model weights downloaded.

## 2026-11-02 — Phase 2 artifact cleanup

- Explicit user authorization supersedes retaining intermediate Phase 1 artifacts in Git.
  Remove only index entries; retain local copies, final golden fixture and Phase 0 bundle.
- Preserve historical Phase 1 measurements in its report, traceable to `07f56b3`.
  Raw transcripts/frames are local-only; future runs use `runs/`.
- No golden fixture regeneration or production SillyTavern changes.

## 2026-11-02 — Phase 2 image stages and evidence

- Choose a deterministic CPU flat-colour baseline before model downloads. SAM 2.1
  is promptable segmentation, not an anime semantic parser; SDXL inpainting is
  not validated for preserving anime identity. Neither checkpoint was downloaded.
- Keep recognition, extraction, hidden-pixel reconstruction, editor import and
  actual animation as separate gates. Unknown pixels remain explicit; generated
  alternate shapes never count as recognized source regions.
- Flatten only simultaneously visible Phase 1 parts. Remove alternate closed-eye
  and closed-mouth forms from the flat benchmark. Source metadata is confined to
  `benchmark.py`, and an inference test hides it before a repeat run.
- Fill enclosed holes and bounded white-eye row gaps using original nearby colour.
  Do not invent missing outer neck/eye contours. Full-layer IoU reflects these gaps.
- Reuse only the Phase 1 MCP protocol and PSD2Live semantic roles, not its opaque
  project IDs/deformer geometry/Mood recipe. The generated baseline has 20 parameters.
- User authorized searching for a licensed real test image. Use Kasuga's CC-BY-SA-3.0
  Wikipe-tan PNG locally with attribution and SHA-256; no artwork committed. Real
  parsing fails acceptance despite an exact neutral composite; build is refused.
- Install Torch 2.9.0+cu128 only as an optional project extra. RTX 5090 arithmetic
  passes outside the sandbox; no GPU image-inference result is claimed.
- Shared MCP transport rejects non-loopback/credential URLs, redirects and proxies.
  Dummy-token JSON/SSE/session/error tests pass. Live CLI still returns 401 without
  user-supplied environment token; connected authenticated MCP completes export.
- Fresh `.cache/phase2-st` hosts Phase 0/1/2 browser runs; all pass. Original 137
  server/extension file hashes remain unchanged. Phase 1 final fixture unchanged.
- Stop after this Phase 2 MVP. Improving real-art parsing is necessary before a
  useful general-purpose character pipeline; no Phase 3 or deployment started.

## Phase 2.5 — Evaluate an existing neural decomposition backend (2026-11-02)

- Pin See-through `df019de5` and three publicly licensed checkpoint snapshots
  before downloading; user approved the 14,730,707,786-byte plan. Preserve all
  weight notices and checksums locally. No system stack changes.
- Isolate Python 3.12 / Torch 2.8/cu128 from the working Phase 2 environment;
  omit GUI/training/detectron2/mmcv/SAM2 tiers from the headless inference worker.
- Keep baseline behavior/defaults. Add a process/file boundary and manifest v2
  rather than calling neural output protected source pixels. Mark all model
  pixels generated/uncertain; hidden-only provenance remains unlocalized.
- Use independent CC0 Girl2 XCF layers for coarse evaluation; no GT enters
  inference. SAM is a separate prediction experiment, never a reference label.
- Retain See-through as opt-in: strong improvement on the frontal/bust case,
  major failure on cropped Wikipe-tan; no unconditional default promotion.
- Missing source blink/mouth variants do not establish impossibility: the
  explicit connected-MCP experiment demonstrates PSD2Live procedural fallback
  animation. Retain strict ordinary build gates and report that narrow success
  separately from high-quality rig acceptance.
- Full results, actual timing/VRAM, visual failures and repeatability evidence:
  [Phase 2.5](phase2-5-results.md). Stop here; no training or production deployment.

## Phase 2.6 — Preserve source ownership and judge actual motion (2026-11-02)

- Freeze/recompute Phase 2.5 metrics before changes. Keep baseline, golden assets,
  upstream/model pins and both dependency locks unchanged.
- Restore native source samples to one deformable layer each. Exact source
  provenance and uncertain semantic ownership are separate properties.
- Repair connected skin from face/neck agreement and source colours, never XCF
  GT or fixed benchmark coordinates. GT remains evaluation-only.
- Actual blinking exposed static source outlines on the face. Nearby ink transfer
  fixes this; lower neutral RGB error alone would have missed the regression.
- Evaluate four images, including two additional CC0 characters from the same XCF.
  Reject face/back-hair failures even when colour restoration looks recognizable.
- Keep guard-band filling experimental and reject its Girl2 export: neutral
  equality and fewer holes did not justify new visible hair fragments.
- Retain six separate quality gates, 21-pose actual runtime evidence and a limited
  prototype acceptance. Hair gaps and flat lids still block unrestricted quality.
- No new weights, training, manual painting or production ST changes. Stop at 2.6;
  [results](phase2-6-results.md) record improvements and measured regressions.

## Phase 3 — Character-specific animation and actual RP lifecycle (2026-11-02)

- User authorized Girl2 animation/RP work; preserve Phase 2.6 and stop before Phase 4.
- Author all expressions, brow shapes and motion curves through MCP; replay from the
  accepted project. Keep source rasters/texture and neutral runtime exact.
- Reverse the first brow inclination after actual visual review. Seven expressions
  use Multiply eyes / Add mouth and mood, preserving independent blink/talk.
- Select only authored Idle/Nod in the packaged model references. Builtin motion
  export suppression did not remove those files; do not rely on disabled flags alone.
- Prefer restrained hair tuning over inferred guard pixels. Neutral equality plus
  full pose review accepts reduced gaps; simplified eyelids remain a limitation.
- Prove message delivery through ST events with network-mocked classification.
  Never describe the mock as model inference or text-talk as TTS synchronization.
- Upstream HTTP 503 caused a caught event-listener TypeError. Retain negative evidence,
  broaden QA to caught errors, and isolate the pinned optional adapter under `.cache/`.
- Adapter handles classifier failure/stale messages, frame-aligned smooth mouth,
  reload cleanup and runtime-added head oscillation. Do not deploy it into production.
- Raw float32 opacity overshoots up to a few ULPs are retained. Classify invalid numeric
  opacity separately beyond eight float32 ULPs; no geometric/aesthetic threshold relaxed.
- Separate RP acceptance from source, semantic, hidden, import, Core and visual gates.
  Full runtime replay is exact; editable CMO3/CAN3 container bytes are not.
- 59 Python + five JS tests, actual RP/pose QA and old golden browser regressions pass.
  Stop after Phase 3; all generated projects, frames and transcripts remain ignored.


## Phase 4A — Reproducible packages and reversible isolated deployment (2026-11-02)

- User explicitly authorized Phase 4A from `a106c5f`, not production deployment or
  Phase 4B. Freeze accepted Phase 3 sources and all historical benchmark reports.
- Package only referenced runtime files, mapping and provenance. Pin the complete
  accepted input, probe actual Core and require reviewed sleeve/torso/neck drawables.
  No renamed model formats, runtime-library redistribution or new image generation.
- Restrict writes to marked independent `.cache/phase4a-*` copies. Reject links,
  traversal, incompatible hashes and existing destinations unless explicitly replaced.
- Use verified backups, fsynced write-ahead journals and atomic renames. Preserve
  interrupted transaction state for rollback; refuse modified installed files or
  corrupt backups. Test actual child-process death as well as injected failures.
- Keep user settings outside deployment ownership. Preserve/reset disposable browser
  fixtures separately, then verify exact data-file restoration. Do not imply that
  uninstall deletes later user chats or reverts deliberate settings changes.
- Inspect actual ST event exports and private extension state. No adequate complete
  companion hook exists in these pinned versions; retain the one-file optional patch
  and separate talk controller. Journal both changed files and restore original bytes.
- Implement explicit source inventory and independent-mask structural checks. Girl2
  clothed upper-arm/sleeve preservation permits portrait acceptance; absent source
  forearms/hands do not require generation. No general limb benchmark claim.
- Fresh browser tests exposed startup classification outside the old mock. Retain
  that failed attempt; install the Phase 4A startup mock before navigation, preserving
  explicit HTTP/offline/race injection through real message handlers.
- Upstream and adapter discovery, mapping, talk, idle, switching and reload tested;
  retain upstream HTTP fallback failure. Adapter RP suite, Phase 0/1 regressions and
  post-uninstall asset discovery pass. No real classifier inference or audio lipsync.
- Exact neutral canvas equality and visual review retain Phase 3's limited prototype
  acceptance. All 730 production hashes unchanged. Stop after Phase 4A; see
  [results](phase4a-results.md) for evidence and remaining production/Phase 4B work.


## Phase 4A.1 — Read-only production audit (2026-11-02)

- User authorized an audit from `f1c7e39`, explicitly excluding production changes,
  service actions, chats and credentials. Add only a read-only audit CLI and tests.
- Match all 11 compatibility pins and 729 prior public code hashes; probe actual
  Core again. Preserve Phase 4A browser evidence as inherited, not a new session.
- Project `/data` ext4 and production `/home` Btrfs differ. Design a private
  target-filesystem transaction sidecar outside served paths and both Git trees.
  Existing project-local same-filesystem/isolated restrictions stay unchanged.
- Identify production requirements beyond Phase 4A: publish the controller before
  patched imports; flush nested directories and both rename parents; retain durable
  target-side recovery when the project filesystem is unavailable. No installer added.
- Stream only allowed settings fields and reduce model/character records to counts.
  No saved Live2D models/settings exist, but the existing expression provider is LLM
  (`api=2`). Exact-source synthetic tests prove joy/neutral fallback without classifier
  calls. Package/Core compatibility does not establish production emotion inference.
- Preserve the provider and all existing settings. Exact-source preset tests confirm
  new entries initialize while existing/partial entries remain untouched. A later
  activation must use an approved per-key delta, never wholesale settings replacement.
- [Audit](phase4a1-production-audit.md) records 17 model-file creations, optional one
  controller creation/one extension replacement/one backup, paths/hashes, transaction
  scaffolding and recovery. Proposed installation commands are explicitly unimplemented.
- 82 Python + five JS controller regressions and two source-behavior audits pass.
  Stop and request explicit authorization before implementation/deployment, classifier
  changes, real production validation or service maintenance. Phase 4B remains unassigned.


## 2026-11-02 — Phase 4A.2 target-local transactions and classifier blocker

- Keep Phase 4A installer unchanged. A separate disposable-only engine uses private
  staging/backups/journals on the target filesystem, verified ownership/mode/mtime/
  xattrs, no-replace model/controller publication and atomic extension replacement.
  Recovery restores the original extension first. No production authorization switch.
- Real Btrfs tests validate different-device copying and target-local renames. A
  stdlib-only helper runs with `/data` hidden; retain target-side recovery material.
  SIGKILL/journal tests and simulated ENOSPC do not certify arbitrary power loss.
- Do not directly import ST getExpressionLabel into Live2D yet: its successful fallback
  emotion and failure return values are indistinguishable, its full prompt uses context,
  and it has no shared request/result identity. Exported lastExpression lacks message
  identity and can represent manual/old state. A wrapper cannot reliably deduplicate
  against the sprite worker or promise neutral errors without broader changes.
- Use the user's explicit blocker option: retain the pinned two-file adapter and
  neutral fallback, preserve provider 2, document a future shared result API instead
  of a second classifier/global fetch override/preference mutation. Mock labels are
  contract evidence, not real inference or an accepted LLM-to-Live2D integration.
- Keep technical runtime, visual prototype, classifier and production readiness gates
  separate. Any production binding, activation, maintenance or real API call requires
  new explicit scope. No Phase 4B or training work was started.

## 2026-11-03 — Phase 3.1 standalone preview and facial revision

- User explicitly reopened Girl2 authoring from `257582f` for a standalone viewer
  and clearer faces. Production deployment, Phase 4B and training remain excluded.
- Keep the accepted Phase 3 recipe, editable sources, runtime and Phase 4A package
  pins unchanged. The default preview loads that baseline; a version selector exposes
  the separate `runs/phase3-1-final-v2/` candidate without setup or persistent state.
- Apply manual controls immediately before Core geometry update; reset parameter
  defaults before motion evaluation. Pause physics with idle for repeatable manual
  poses. Talking blends to its envelope rather than taking a maximum with resting
  mouth opening, which had frozen the surprised mouth.
- Use the existing mouth/lip meshes for curved and rounded forms. Add only an
  original deterministic native-alpha blush layer, registered/imported through MCP,
  hidden by its own neutral opacity key. Preserve original archive assets.
- User accepted increased recognizability but rejected initial sad eyebrows as angry.
  A large reverse rotation distorted brow width. A dedicated vertical-deformation
  `ParamBrowSad` raises the inner ends and leaves other expressions intact. The user
  reviewed the corrected pose and said it reads as sad. Keep failed versions locally.
- Pixel differences and finite geometry do not establish emotional recognition.
  Record user-reviewed limited improvement separately from runtime tests. No blinded
  recognition, professional-quality, candidate production/ST-session or phoneme claim.
# Phase 4B decisions (2026-11-03)

- Explicit user authorization reopens reusable creation and independent benchmarks;
  production bindings, deployments, settings and services remain out of scope.
- Reuse the pinned offline worker and source restoration. Validate every cached
  artifact before reuse; never silently redo costly inference or overwrite failures.
- Semantic review and visual review are separate, hash-bound records. Hard parser
  failures cannot be overridden by review. Development-agent review is labelled as
  such and is never represented as user acceptance.
- Resolve rig targets through layer roles and mesh ancestry. Standard parameter IDs
  are a runtime contract; Girl2 object IDs, geometry and hashes are not a template.
- Keep procedural eyelid/mouth limitations visible. No invented teeth/tongue,
  arbitrary new hidden anatomy, production promotion or cloud image processing.
