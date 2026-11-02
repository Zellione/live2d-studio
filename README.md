# live2d-studio

A local, open-source-first pipeline that turns one or more character images into an animated Live2D avatar usable in the SillyTavern Live2D extension.

**Status:** Phase 0 compatibility and Phase 1 geometric face-rig tests passed in
an isolated copy of the installed SillyTavern extension: independent blink,
mouth opening, head X/Y/Z, three expressions and authored idle animation.
See [Phase 0](docs/compatibility.md) and [Phase 1 results/reproduction](docs/phase1-results.md).
The standalone MCP CLI still needs its local authentication token. Real artwork
segmentation, text-talk and emotion classification remain unvalidated.

## Constraints

- Linux (Arch + Hyprland/XWayland), no Photoshop or paid Cubism dependency.
- Prefer local inference on an RTX 5090; use `uv` for Python dependencies.
- Codex CLI runs locally, with a loopback-only PSD2Live MCP connection.
- Minimize manual image editing. Preserve originals and intermediate assets.
- Validate the final model in the *actual SillyTavern extension*, not just PSD2Live's preview.

## Next phase

Read [`AGENTS.md`](AGENTS.md), [`docs/HANDOVER.md`](docs/HANDOVER.md) and the phase
results before continuing. Phase 2 is proposed only; it has not been started.

## Project structure

- `docs/HANDOVER.md` – objective, phases, milestones, acceptance criteria
- `AGENTS.md` – instructions for local Codex agents
- `assets/input/` – user-supplied source images (ignored by Git)
- `assets/intermediate/` – generated segmentation, inpainting, PSDs (ignored by Git)
- `assets/output/` – generated Live2D bundles and previews (ignored by Git)
- `src/live2d_studio/` – future pipeline code
- `tests/` – test assets and automated checks
- `scripts/preflight.sh` – read-only check of host prerequisites
- `scripts/install-psd2live.sh` – SHA-256-verified Linux x64 release installer

## References

- https://github.com/tsunehimatoi/psd2live
- https://github.com/SillyTavern/Extension-Live2d
- https://docs.sillytavern.app/extensions/live2d/
- https://github.com/openai/codex
