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
