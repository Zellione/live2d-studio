# Handover to local Codex CLI

## Current state after Phase 2 (2026-11-02)

Read [Phase 2 results](phase2-results.md), [architecture](phase2-architecture.md)
and [artifact policy](artifact-policy.md) first. The original plan below is retained
as history; Phase 0/1 are complete and Phase 2's limited MVP is implemented.

- Cleanup commit `c5d6512` removes obsolete index entries while retaining local
  copies. Phase 0 and final Phase 1 golden fixtures remain unchanged.
- `uv run live2d-studio prepare/inspect/reconstruct/evaluate/build/mcp-check/doctor`
  provide local stages. Commands with arguments are in the architecture document.
- 33 automated tests and all three isolated ST browser scenarios passed.
- Synthetic: visible mask IoU 1.0, full-layer mean IoU 0.93646; original pixels
  unchanged. PSD2Live import/export and basic visible animation passed.
- Real licensed Wikipe-tan image: semantic acceptance failed; most foreground
  remains unknown, some candidate roles are wrong. Do not promote synthetic
  success to real-anime readiness. No neural image weights installed.
- PyTorch 2.9.0+cu128 arithmetic succeeds on RTX 5090; CPU image pipeline is the
  implemented backend. GPU model inference remains future work.
- Connected authenticated MCP succeeds; independent CLI still needs a local
  environment token. Do not read profile secrets. No production ST writes.
- Stop here. Next authorized work should improve semantic parsing and concealed
  contours using a licensed benchmark, before broader rig/production automation.

## User goal
The user wants to provide one or more illustrations of an anime/roleplay character and obtain a properly rigged Live2D avatar for SillyTavern's Live2D extension. They have no image-editing experience, use Arch Linux/Hyprland, and want to avoid paid software like Photoshop or Cubism Pro. Codex should orchestrate an automated, locally executed pipeline and use PSD2Live through MCP if reliable.

## Grounded starting points (verify at implementation time)
- PSD2Live: https://github.com/tsunehimatoi/psd2live – Linux tar.gz release, X11/GLX via XWayland, localhost MCP usually `http://127.0.0.1:23871/mcp`, Cubism-family `.moc3` and `.model3.json` export.
- SillyTavern extension: https://github.com/SillyTavern/Extension-Live2d – documentation currently describes `*.model.json` discovery. This may be a *real runtime compatibility issue*, not merely a filename convention.
- Official docs: https://docs.sillytavern.app/extensions/live2d/ – model installation and interaction settings.
- Codex CLI: https://github.com/openai/codex – local execution and MCP support.

## Design principles
- Prioritize actual SillyTavern rendering and expression switching over VTube Studio support.
- MVP: front-facing torso or bust, with blinking, eye tracking, mouth movement, gentle idle breathing and a few expressions. No initial requirement for complete full-body movement, precise phoneme lip sync, or face tracking.
- Separate image preparation, PSD creation, rigging/export, and SillyTavern deployment into independent stages with inspectable artifacts and automated QA.
- Use local image models where practical; do not choose/pull large model weights without checking licenses, requirements and user approval.

## Phase 0: compatibility gate – first Codex assignment
1. Identify the actual local SillyTavern installation and installed Live2D extension, versions/commits and the asset root; inspect rather than assume the path. If absent, record installation instructions without mutating existing installations.
2. Read extension source and bundled Live2D runtime dependencies. Determine model-format discovery and runtime support for Cubism model generations 2.x and 3+.
3. Inspect the latest installed PSD2Live export behavior. Prefer an upstream example PSD/project from its examples resources with clear permitted usage.
4. Produce a minimal full model export and a deterministic integrity validator for JSON references, case-sensitive filenames, textures, motions, expressions, and binary `.moc3` presence.
5. Load the exported model in the *actual SillyTavern extension* using a disposable fixture location; record the browser console output and successful or failed render. Do not modify upstream extension source or production assets without asking.
6. Write `docs/compatibility.md`: exact versions, supported/unsupported formats, reproduction steps, screenshots/log paths, and the next smallest viable change.

**Stop condition:** If a valid PSD2Live export is not loadable in SillyTavern, do not begin full image-segmentation work. Establish a verified adapter/runtime solution, or clearly explain that the goal is blocked.

## Phase 1: MCP proof of control
- Connect to the local PSD2Live MCP endpoint, using its own Settings > MCP configuration and appropriate authentication. Check `codex mcp list`.
- Start with `workspace_overview`, `workspace_inspect`; discover extra operations with `workspace_list_operations` and `workspace_call`.
- Use preview/dry run before atomic edits when supported, and verify edits survive save/reopen.
- Capture sample MCP requests/responses without leaking auth tokens.

## Phase 2: image-to-layers pipeline
- Import 1+ high-quality frontal character images; keep source unchanged.
- Proposed components (evaluate, don't assume): semantic segmentation, alpha matting, occlusion inpainting, transparency cleanup, standardized naming/ordering, layered PSD generation.
- Split visible parts: face base, hair front/back, eye whites/pupils/eyelids/brows, mouth shapes, neck, torso, accessories. Generate hidden pixels for deformation.
- Use `uv`, deterministic pipeline configs, previews/contact sheets and quality gates.
- Test generated PSD import and auto-rigging in PSD2Live before generalizing.

## Phase 3: rig MVP
- Parameter targets: blink, gaze, mouth open, breathing, subtle head angle, happy/sad/angry/surprised expression toggles; optional hair physics.
- Match *the actual SillyTavern extension's* supported parameter and expression mapping. Do not invent parameter ID support.
- Test extremes and in-between keyframes; reject tearing, seams, missing occluded pixels, or crushed eyelids.

## Phase 4: packaging and SillyTavern QA
- Export source PSD, editable project, runtime bundle and a concise manifest of tool versions/assets.
- Validate model loads, renders, idles, talks on text output, and responds to at least three expression triggers.
- Document any feature requiring the SillyTavern Classify extension or additional extension settings.
- Deploy to the user-selected SillyTavern assets path only with approval; back up any target conflict.

## Deliverables expected
- Reproducible CLI pipeline, tests, a local installation guide, a sample input test case with license provenance, a complete exported model bundle, source assets, QA renders, and a `docs/compatibility.md` report.

## First command to Codex
"Read AGENTS.md and docs/HANDOVER.md. Work on Phase 0 only. Verify the exact version/format compatibility of PSD2Live's .moc3/.model3.json output with my installed SillyTavern Live2D extension. Inspect existing versions and paths before editing anything. Implement only a reproducible compatibility smoke test and docs/compatibility.md. Stop and report if you need host installs, GUI access, or approval to alter SillyTavern."
