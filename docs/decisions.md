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
- Enforce white/iris/lash depth order only for complete unambiguous per-eye role
  triplets. This fixes Sara's hidden iris without character coordinates and leaves
  Girl2's accepted restored layers unchanged. Preserve the raw imported order.
- Keep Sara's successful export and numeric runtime checks separate from its
  explicit visual rejection: ghosted closed-eye contours and insufficient mouth
  opening still block independent-character acceptance. Do not promote it merely
  because 32 poses render or all application tests pass.
- Retain Boy2 and both Hachi inputs as parser failures. Independent ground-truth
  masks remain evaluation-only; Sara has no independent semantic ground truth.

# Phase 4B.1 decisions (2026-11-03)

- Reconstruct ownership before rigging: Sara had static face-owned eye/mouth pixels,
  missing concealed skin and an independent partial-contour blink deformation.
  Source copying and neutral fidelity alone did not diagnose these causes.
- Keep skin/lash/interior alternatives separate with explicit provenance. Opaque
  backing changes runtime fractional-alpha compositing; report that separately
  from exact observed RGBA, rather than weakening the original source gate.
- Preserve source upper-lash colour/thickness in a generated closure and retain
  original open-eye details. A dark mouth cavity is an uncertain simple shape;
  no unsupported teeth/tongue or hidden reference tiles are inputs.
- Retain procedural mouth generation when substantial already-open source artwork
  exists. A failed Girl2 regression demonstrated that a universal replacement
  degraded its opening range. Sara's artifacts are unchanged by this branch.
- User accepted limited visual improvement of the exact Sara candidate gallery.
  Keep development geometry/head/limb checks separately attributed. No general
  image-to-Live2D, professional-quality or production acceptance is inferred.
- Assess additional models through pinned public metadata only. Neither a newer
  model nor an available local filename establishes a tested facial improvement.

# Phase 4B.2 decisions (2026-11-03)

- Test a small specialized safetensors LaMa first; investigate quantized Qwen
  before drawing VRAM conclusions. The separately approved 21.59 GB Q4_K_S/FP8
  set runs on the 5090 at about 20.4 GiB peak Torch allocation. Reuse the verified
  existing VAE. Full Qwen and untested FP8/NVFP4 variants are not downloaded.
- Keep optional inference in separate frozen uv environments and offline worker
  processes. Hash-check weights, source revisions, crop inputs and masks. Preserve
  source layers; hard-composite generated RGB only inside explicit masks.
- Use exact cached outputs for controlled neural/hybrid rig comparisons. Review
  names individual feature outputs and hashes. Empty selection means deterministic
  fallback with no model load; no character-name/coordinate tuning or universal
  promotion policy is introduced.
- Keep **deterministic as the default**. LaMa recreates/removes features incorrectly;
  Qwen's smoother Sara closed lashes produce duplicate contours during the 0.1
  blink crossfade. Its mouth edit reduces apparent opening. Girl2's generated
  lashes change style asymmetrically. All five rendered candidates are rejected.
- Dense transitions are a separate visual gate. Quarter-step poses, exact neutral
  equality, unchanged source ownership and finite geometry missed the decisive
  double-contour defect. Preserve both successful numerical checks and failures.
- Diagnose experimental confounds rather than assigning them to the model:
  native Boy1 holdout removes the rescaled black-boundary halo; original LaMa
  TorchScript/safetensors forward parity is exact; stronger Qwen conditioning
  avoids reconstructing an eye but does not establish better skin or half lids.
- Record developer review separately from user acceptance. No anatomical truth,
  quantization-only quality degradation, general conversion, production approval,
  training or driver change follows from this experiment. Stop after Phase 4B.2.

# Phase 4B.3 decisions (2026-11-03)

- Diagnose correspondence before adding artwork. The old .1-openness loop combines
  a .4-opacity flattened source with a .6-opacity stationary curved replacement.
  Shared head ancestry and valid meshes do not align those local curves.
- Derive landmarks from source roles, pixels and inspected mesh bounds/margins.
  Move the replacement along the same interpolated curve as the source. Keep the
  fully open source unchanged and the alternative completely invisible at opening.
- Preserve source-over coverage during handoff: complementary scalar opacities
  yield only .75 coverage at their midpoint. Hold the lower stroke opaque until
  the original white/lash can cover it. Explicitly hide the iris near closure.
- Keep the extreme source squash invisible until it unfolds. The actual Core
  audit found a visible reversal at .05 in an earlier Qwen candidate; final checks
  reject visible eye reversals at three head poses. Native invisible-key warnings
  are retained rather than relabelled as zero geometry issues.
- Copy sparse-mouth opening keys from the inspected full-open cavity, preserving
  horizontal span/centre and inherited expression/head motion. Keep the existing
  open-source branch for Girl2 and deterministic cavity artwork for Sara.
- Treat Sara's eliminated loop as a limited temporal improvement, not anatomical
  truth or universal neural acceptance. Girl2's neural lash style and the neural
  skin/cavity remain rejected selections. Default artwork stays deterministic;
  aligned motion is explicit pending character-specific review.
- Record 401-frame dense suites, parameter trajectories, exported channel checks,
  complete sequence sheets and sampled recordings. Frame-difference maxima are
  not uniformly reduced and are not an aesthetic score. No new user acceptance,
  model downloads/inference, training or production deployment. Stop after 4B.3.

## Phase 4B.4 — 2026-11-05

- Preserve `generic_rig.animation_recipe()` defaults and accepted projects. Add an
  explicit expression candidate from the hash-verified aligned Sara predecessor.
- Bind independent brow axes through inspected semantic meshes/parents. Compensate
  measured source inclination instead of increasing the shared brow-emotion value.
  Keep old height axes and Sad behavior. Do not relabel brow/eyelid art from uncertain
  visual interpretation.
- Fit both disconnected source mouth halves; retain the failed one-component fit.
  Generated cheek tint has its own opacity/provenance and inherits the face parent.
- Compare settled poses with neutral restoration and no idle/blink/talk/head noise.
  Retain 401-frame transition checks and add 756 exported expression combinations.
  Numerical success and development visual judgments do not close user acceptance.
- Keep all accepted art/runtime/package pins and rejected evidence. No automatic
  candidate promotion, production deployment, inference or training.

## Phase 4B.4.1 — mouth geometry takes precedence over earlier expression judgments

The user's manual review rejected Phase 4B.4 readability. Its development judgments
are not user acceptance. The optional follow-up changes all seven mouth recipes,
leaving non-mouth channels unchanged. Inspecting visible alternatives established
that the imported MouthForm axis is ineffective, negative parent curvature retains
the source smile, and the old Angry correction supplies a soft Sad-like frown.

Use separate rest-derived source/cavity mappings to the same target seam, independent
roundness/tension/width/skew and bounded opening. Preserve all PNG artwork. The first
copy-based implementation accumulated bends when equal forms were omitted; reject
it and author ordered reset/deform keys instead. The source seam has no opening
geometry. Validate visible cavity winding against its full-open surface and retain
the false-reference failure. No visible geometry/opacity gate is relaxed.

Expose mouth-only review with identical neutral non-mouth channels, pair sheets and
opening samples. Finite geometry, exact neutral/source preservation and distinct
configurations do not grant human emotion recognition. Candidate v4 remains pending
explicit user visual approval. Preserve accepted/rejected predecessors and stop at
Phase 4B.4.1 without production deployment, inference or training.

## Phase 4B.5 — technical generalization does not close visual acceptance

Freeze `7863b34`, original-framing Codel3.png and an unused secondary crop before
inference. Disclose numbered-PNG selection exposure; never claim a fully blinded
reference holdout or absence from training. Only one flat image enters creation.
Preserve the first run before extracting the PSD, and keep optional 4B.4/4B.4.1
scripts separate because they are not integrated into the creation CLI.

The original frame completes all twelve stages with no special rig instructions.
It preserves both hands, but a single unsided arm layer is not independent limb
articulation. The PSD's fused base and color/ink facial pairs support narrow ink
ownership and concealed-face checks, not universal semantic ground truth. Store
all evaluation coordinates in an explicitly evaluation-only definition.

Retain the optional mouth Core failure at 1.19e-7 versus 1e-7 even though no visible
triangles reverse. Do not weaken the gate based on a plausible rounding diagnosis.
High-resolution actual renders reveal overlapping near-closed eye contours and
residual shading, so development review rejects convincing animation. Numeric
success and almost perfect source copying are separate findings. User approval
is still pending; neither candidate is promoted. Stop after Phase 4B.5.

## Phase 4B.6 — coherent head motion, evidence-gated limbs

The user reopened local body/head/hair authoring and independent regressions from
`68e1d25`. Actual Codel Core and continuous viewer samples show working but tiny
XY/head/hair idle motion, not a missing parameter or an idle playback failure.
Bind the shared head ancestor by semantics and ancestry, add bounded normalized
translation, retain the inspected neck rotation pivot, and keep separate exported
hair pendulums. Correct vertical translation to agree with the importer's nod;
preserve the earlier cancelling-direction candidate and motion-format failures.

Use a 16-second paused/eased idle with independent breathing/blink timing. Export
only honest head-nod and questioning-tilt gestures. The merged Codel handwear
component has both arms/hands but lacks reviewed joints and hidden intersection
surfaces. Preserve source pixels and its shared body attachment; component count,
side labels and clothing are insufficient to authorize independent articulation.

Codel/Sara pass the broad combined Core audit; Girl2 retains 1,716 generated
lip-triangle reversals also present before the body edit. Keep that gate failed
while reporting independently passing dense facial/render tests. No threshold is
relaxed and no prototype is promoted. Source gaps which become enclosed during
motion retain numerical hole counts and close-up evidence; counters alone do not
establish missing anatomy. User visual approval remains a separate pending gate.

## 2026-11-06 — Phase 4B.6.1 expression/body composition

- User accepted Phase 4B.6 head/hair/breathing/gestures, but identified Confused's
  regression. Saved-project and exp3 inspection confirms that body authoring
  started from the original five-channel branch, not the improved mouth branch.
- Add optional resumable coordinated-mouth/body composition after existing base
  animation. Read saved expressions, preserve them through body authoring, check
  every exported channel/blend/fade, and retain the gesture groups. Defaults stay
  unchanged; duplicate authoring and legacy overwrite are refused.
- Keep approved body geometry and motion unchanged. Final Codel has exact matching
  physics/Idle/Nod/Question files and 481 poses with zero non-authored-region vertex
  difference. Confused stills exactly match the optional improved reference.
- Keep the historical strict seam failure. A separately supplied, MOC-bound
  geometry-independence contract enables a scale-aware eight-binary32-step bound,
  capped at .001 source pixel. Independent Codel/Sara and injected-deformation
  checks support this limited policy. It is not a proof of arbitrary Core rounding
  error or permission to waive genuine geometry failures; Girl2's 1,716 lip
  reversals remain failed. The old probe behavior persists without the contract.
- Present `runs/phase4b6-1-codel-v3` for explicit visual review. No automatic
  promotion, production deployment, inference, downloads or training.

## 2026-11-06 — Phase 4B.6.2 freeze reviewed combined Codel

- Record the user's “Das sieht soweit gut aus jetzt.” separately from automated
  and development review, bound to the whole runtime and editable project. Scope
  is the current combined facial/body animation; no professional, independent-arm,
  general conversion or production acceptance follows.
- Preserve the original candidate and create `codel-combined-v1` as a read-only,
  SHA-256-pinned local snapshot. Git stores a small identity manifest, documentation
  and regression tests; generated projects, PSDs, runtime and artwork stay ignored.
- Verify both autonomous entry points with existing source-matched inference caches.
  All 15 runtime-referenced files reproduce exactly; CAN3/CMO3 editor containers
  differ. No individual agent rig operations or new inference were needed.
- Keep coordinated mouths and calm body explicitly selectable, with aligned facial
  motion and deterministic reconstruction. Defaults and product code are unchanged.
  Keep historical Codel seam and Girl2 visible lip failures. Stop at the freeze.

## 2026-11-06 — Phase 4B.7a Qwen pose feasibility

- Reuse the locally pinned Q4_K_S/FP8 Qwen setup; no new weights or defaults.
  Only the frozen original flat Codel image enters generation. Retain raw decodes
  separately from protected composites; copied face pixels cannot prove model fidelity.
- Predefine six conservative poses. After the no-change control failed, compare
  three lower-strength controls with otherwise identical settings. Preserve all
  nine completed outputs and the interrupted/recovered execution history.
- Screen before semantic aggregation. Six stronger edits and one weaker lift
  are rejected; two source-like weaker near-copies are accepted only for coarse
  exploratory analysis. Neither exposes useful new structure. Actual source and
  accepted-image SAM results retain one substantial unsided arm component.
- Keep plausible stills, segmentation usefulness and reliable articulation as
  separate gates: 2 / 0 / 0 in this study. No arm rig or promotion follows.
- Recommend pose-guided, source-constrained generation research before arm
  authoring; current tests do not establish that all Qwen configurations fail.
  Preserve `codel-combined-v1`, historical failures, defaults and production.


## 2026-11-06 — Phase 4B.7b guided pose review

The old pose run used 1024/40-step inference, not the older facial 512/20 setup.
Keep that finding separate from the new high-resolution, multi-reference study.
Use the installed Image Edit Plus node with two checked reference latents and
source-relative guides. Keep the pinned Q4_K_S/FP8 stack; neither checkpoint
identity nor successful execution proves parity with an unavailable old workflow.

Human selection is mandatory for downstream auxiliary evidence. Five seeded
variants share one fixed prompt/guide/config; new batches reserve fresh seeds.
Accepted poses are immutable. Resume keeps completed images and only replays
unfinished tasks in fresh directories. Review/export remains standalone and
loopback-only. Generated pixels are never promoted to independently known anatomy.
Thirteen calibration cases expose remaining pose-control failures; feasibility
requires user-selected useful candidates, not merely better-looking still images.


### Phase 4B.7b human-selected follow-up

The user selected candidate 2 in the right-arm batch. Its image hash and saved
selection manifest were verified before inference. The unchanged SAM parser gives
one substantial arm component on the original and two on the approved auxiliary.
This supports a limited positive segmentation-feasibility conclusion. It does not
supply an upper-arm/forearm split, reliable joints, exact hidden clothing or a
validated pose family. Preserve the pose-compliance caveat: the approved image is
closer to uncrossed arms-down than an explicit arm lift. Do not regenerate the
approved pose, infer approval for the other candidates, or alter the frozen rig.


## 2026-11-06 — Phase 4B.8 canonical working bases

Canonicalization now precedes further helper-pose experiments. Keep it opt-in:
original angled artwork remains the identity/style authority, while a separately
human-approved frontal synthetic image may become the working geometry source.
Never silently replace existing creation inputs or accepted runtime bundles.

Reuse the reviewer’s fixed five-seed batches and guarded persistence. A canonical
approval creates a recoverable, hash-bound working snapshot with separate original
and synthetic files. Prepare future helpers only through an explicit command;
record all input roles and do not claim three-reference visual validation without
executing it. Preserve early mannequin-copy failures and all historical approvals.

- Phase 4B.8 user selected canonical candidate 4 (image `ab2a52ae…d78da3e`).
  The unchanged parser separates two substantial arm regions versus one merged
  source region. Treat this as support for canonical-first decomposition; retain
  synthetic anatomy uncertainty and test three-reference helpers in a later phase.

## Phase 4B.8.1 — separate reference processing from gesture compliance

- Preserve the approved canonical and use a new opt-in bent-forearm profile.
  Actual Qwen execution retains three reference tensors; missing third-reference
  evidence must fail, never trigger an implicit two-reference fallback.
- The user rejected all five initial candidates: four arms-down, one missing the
  raised hand. No approved helper means no new SAM analysis or rigging evidence.
- A matched two-reference control produces a bent arm with a present hand. Treat
  this as reference-family evidence for revised conditioning, not universal model
  limits or anatomical proof. It remains separate and unapproved.
- Keep skeletal deformation and discrete gesture variants as future alternatives;
  neither should begin before complete, reviewed gesture evidence exists.


## 2026-11-06 — Phase 4B.8.2 Lightning as an explicit option

Preserve historical inference hashes by introducing a separate timed worker and
adapter lock for fresh canonical helper runs. Use the installed model-only LoRA
loader with GGUF patch-count/shape checks; reject missing or partially applied
adapters. Keep all three references and retain Quality at 40 steps/CFG 4.

Actual matched tests support optional Balanced (8/CFG 1) and Fast (4/CFG 1):
43.53/30.98 seconds fresh-process time versus 253.14 seconds, with clearer bent
arms in this seed. Matched low-step no-LoRA controls fail with ghost limbs,
confirming adapter influence independently of the changed step/CFG family.
Five additional Balanced candidates take 162.18 seconds total. Their hand shapes
and height still vary; human selection and anatomical analysis remain separate.
No generated output is promoted, no previous selection is modified, and no
production rigging or deployment is authorized by this performance result.

## 2026-11-06 — Phase 4B.9 preserves exact accepted artwork; stops before rigging

Freeze only the four hash-bound human selections; leave the pending fifth pose
alone. Visual approval permits anatomical assessment, not joint or rig acceptance.
The user confirmed that the exact angled accepted artwork and rig must remain,
so a replacement frontal canonical body is outside this experiment's scope.

Selected-only SAM improves bilateral sleeve/hand evidence, but source-view cuts,
rotation pivots, occluded backing and helper-to-original attachment are unresolved.
The canonical raster registration exposes a shoulder seam and its intermediate
crossfades duplicate limbs. This rejects the tested compositor, not every hybrid.
Stop before PSD2Live authoring under the conditional anatomical gate. Prefer a
future discrete gesture after review of original-view cut lines and backing;
do not force continuous deformation from uncertain projected cloth-axis lengths.

Fresh regressions validate preservation of the unchanged accepted runtime only.
Keep the failed geometric hypotheses and probe; no promotion, further generation
or production change follows from the completed assessment.
