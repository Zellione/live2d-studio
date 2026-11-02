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
