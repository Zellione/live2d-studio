# Decisions

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
