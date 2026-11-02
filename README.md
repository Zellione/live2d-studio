# live2d-studio

A local, open-source-first pipeline that turns one or more character images into an animated Live2D avatar usable in the SillyTavern Live2D extension.

**Status:** Phase 2 provides a reproducible local CLI for candidate RGBA layers,
segmentation/reconstruction masks, a versioned manifest and offline previews.
The geometric regression passes image → layers → PSD2Live → installed SillyTavern
extension, with visible blink, mouth and head movement. A licensed real anime test
exposes unreliable semantic parsing; this is **not a production anime converter**.

See [Phase 2 results](docs/phase2-results.md),
[architecture and commands](docs/phase2-architecture.md),
[artifact policy](docs/artifact-policy.md), [Phase 0](docs/compatibility.md) and
[Phase 1](docs/phase1-results.md). The standalone MCP CLI requires a locally supplied
token; the authenticated connected MCP route was exercised. Text-talk and emotion
classification remain unvalidated.

```bash
export UV_CACHE_DIR="$PWD/.cache/uv"
uv sync --frozen
uv run --frozen live2d-studio prepare --input character.png --output runs/character
uv run --frozen live2d-studio inspect --project runs/character
uv run --frozen python -m unittest discover -s tests -v
```

Open `runs/character/preview/index.html` to review all layers and warnings.
Outputs must be new directories. CPU processing requires no model downloads;
optional `uv sync --frozen --extra gpu` installs the pinned Torch/CUDA probe stack.

## Constraints

- Linux (Arch + Hyprland/XWayland), no Photoshop or paid Cubism dependency.
- Prefer local inference on an RTX 5090; use `uv` for Python dependencies.
- Codex CLI runs locally, with a loopback-only PSD2Live MCP connection.
- Minimize manual image editing. Preserve originals and intermediate assets.
- Validate the final model in the *actual SillyTavern extension*, not just PSD2Live's preview.

## Continuing work

Read [`AGENTS.md`](AGENTS.md), [`docs/HANDOVER.md`](docs/HANDOVER.md) and the phase
results before continuing. Phase 2 stops at the documented MVP; Phase 3 and
production deployment require a new assignment.

## Project structure

- `docs/HANDOVER.md` – objective, phases, milestones, acceptance criteria
- `AGENTS.md` – instructions for local Codex agents
- `assets/input/` – user-supplied source images (ignored by Git)
- `assets/intermediate/` – generated segmentation, inpainting, PSDs (ignored by Git)
- `assets/output/` – generated Live2D bundles and previews (ignored by Git)
- `src/live2d_studio/` – image stages, manifest validation, CLI and MCP transport
- `tests/` – test assets and automated checks
- `scripts/preflight.sh` – read-only check of host prerequisites
- `scripts/install-psd2live.sh` – SHA-256-verified Linux x64 release installer

## References

- https://github.com/tsunehimatoi/psd2live
- https://github.com/SillyTavern/Extension-Live2d
- https://docs.sillytavern.app/extensions/live2d/
- https://github.com/openai/codex
