# live2d-studio

A local, open-source-first pipeline that turns one or more character images into an animated Live2D avatar usable in the SillyTavern Live2D extension.

**Status:** Phase 4A packages the accepted Girl2 prototype reproducibly and deploys/removes
it through a recoverable CLI restricted to disposable SillyTavern copies.
Production deployment is disabled. Real message, expression, lifecycle and rollback
tests pass with the optional pinned adapter; upstream classifier-fallback failure
remains documented.

Read [Phase 4A results](docs/phase4a-results.md) and the
[deployment/recovery guide](docs/phase4a-deployment.md). Run the complete isolated
scenario with a fresh name:

```sh
export UV_CACHE_DIR="$PWD/.cache/uv"
uv run --frozen python scripts/phase4a_acceptance.py --run-id my-new-run
```

Accepted editable sources remain in `runs/phase3-final/`. Tested package:
`runs/phase4a-acceptance-v4/girl2/`; local visual review: `runs/phase4a-review-final/index.html`.
[Phase 3 animation](docs/phase3-animation.md) supplies seven expressions, independent
blinks and text-driven talking. No audio lipsync or classifier-model inference is claimed.
Girl2 passes portrait completeness despite absent source forearms/hands; this does
not validate general limb preservation or an anatomically complete rig.

Source preservation from [Phase 2.6](docs/phase2-6-results.md) remains intact:
99.89% exact visible RGBA in the refined layers, unchanged texture and runtime
neutral. Hair gaps are reduced; simplified lids and subtle expression shapes remain.
This is a character-specific prototype, **not a production anime converter**.

The deterministic baseline remains the default; see [architecture/commands](docs/phase2-architecture.md),
[artifact policy](docs/artifact-policy.md), [Phase 0](docs/compatibility.md),
[Phase 1](docs/phase1-results.md) and [source replay](backends/see-through/README.md).
Standalone MCP authoring needs a locally supplied token. The connected authenticated
MCP route was exercised without reading profile secrets.

## Phase 2.5: evaluated neural backend

See-through now runs locally in a separate pinned uv environment. One CC0 bust
produced a basic animated PSD2Live/SillyTavern prototype; the cropped Wikipe-tan
case failed semantic quality. The deterministic backend remains the default.
Read [results and limitations](docs/phase2-5-results.md) and the
[worker/reproduction guide](backends/see-through/README.md).

After running the isolated worker, import its output with
`uv run live2d-studio prepare --backend see-through --input IMAGE --decomposition BRIDGE_DIRECTORY --output NEW_DIRECTORY --rights RIGHTS`.
The v2 manifest distinguishes generated, uncertain and verified-original pixels;
a neural PSD alone is not a rig acceptance result. Model downloads require the
reviewed size/license/revision plan; generated artwork and exports remain local.

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
results before continuing. Work stops after Phase 4A. Production deployment needs
separate explicit authorization and implementation. Phase 4B image-to-model automation
and any training require a new assignment.

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
