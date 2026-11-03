# Standalone Girl2 preview

From the repository, run:

```sh
uv run --frozen live2d-studio preview-live
```

This opens `http://127.0.0.1:8768/` in your browser with the accepted Phase 3
Girl2 already loaded. Choose **Phase 3.1 · expression candidate** in the Version
menu to try the revised model, including the corrected sad eyebrows. No SillyTavern
server, onboarding, character, mapping, connection, classifier or editor is needed.
The original remains the default regression baseline.

Click any of the seven expressions. Idle runs initially; pause it for a stable
pose. Blink left/right independently, move the mouth/head sliders, or start talking.
Sliders override their corresponding pose channels until **Neutral / reset**.
Reset stops idle/talk and restores neutral with the expression fade. Pausing idle
also suspends physics, making comparisons repeatable; resuming restores it.
Talking blends into a simulated mouth envelope and back to the expression's rest.
It does not use audio, text, inference or phonemes. Parameters are available in a
collapsible panel; **Save image** downloads the actual transparent canvas.
Nothing is saved to character settings, browser storage or SillyTavern.

Close with Ctrl+C in the terminal. If the browser does not open, use the printed
URL. `--no-open` starts only the server; `--port 8778` chooses another loopback port.
For the revised model directly, without the version selector:

```sh
uv run --frozen live2d-studio preview-live \
  --model runs/phase3-1-final-v2/runtime/Generated_artwork.model3.json
```

## Local dependencies

Generated bundles are deliberately ignored by Git. The default baseline is
`runs/phase3-final/runtime/Generated_artwork.model3.json`; the optional candidate is
`runs/phase3-1-final-v2/runtime/Generated_artwork.model3.json`. A fresh clone needs
those locally retained artifacts, or a rebuild using the documented source inputs.
The viewer does not silently download artwork or reconstruct a missing model.

Libraries are read from the already installed, isolated local copy at
`.cache/phase3-st/data/default-user/extensions/Extension-Live2d/lib/`.
`--extension DIRECTORY` selects another existing directory containing `lib/`.
Core, legacy Live2D, PIXI and the Cubism bridge must be present. Runtime libraries
are not copied into Git. Missing libraries/model references produce actionable
terminal errors before the server starts; loading/WebGL failures appear in the UI.
A browser with working WebGL is required; automation used Chrome with SwiftShader.

The server binds only `127.0.0.1`, validates Host, and serves preloaded exact assets:
UI, configuration, four runtime scripts and the validated model references. It does
not serve a repository directory, settings, CMO3/CAN3, PSD, project archives or
unreferenced files. Traversal and escaping model references are rejected. No write
API or external network service is present; the page's CSP restricts connections
to its own origin. Selected files are captured at startup; restart after a rebuild.

## Rebuild the editable candidate

Keep the accepted Phase 3 source unchanged. Provide the PSD2Live MCP token explicitly
in the local environment if using the CLI builder; do not put it in a file/command
history or read it from a profile store. PSD2Live must listen on loopback.

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/build_phase3_1.py \
  --source runs/phase3-final/character.psd2live \
  --output runs/phase3-1-new-build
```

Use a fresh output directory. The builder checks the accepted source hash and the
reviewed `recipes/girl2-expressive.json`, snapshots the current editor, authors
geometry and a deterministic transparent blush layer, saves PSD/project, reopens
and exports. `src/live2d_studio/expressive.py` generates the recipe and cheek pixels.
The original `animation.py` and `girl2-animation.json` remain unchanged.

The connected authenticated MCP route was exercised. The equivalent CLI workflow
requires an explicitly provided token, absent in this session; it was not falsely
claimed as an authenticated CLI replay. No profile secrets were accessed.

## Repeat browser acceptance

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase3_1_acceptance.py \
  --output runs/phase3-1-new-review \
  --revised runs/phase3-1-final-v2/runtime/Generated_artwork.model3.json
```

This starts temporary loopback asset servers and a dedicated headless Chrome profile,
checks both models, captures faces/portrait poses/transitions, and stops its processes.
Use `--chrome PATH` or `--cdp-port PORT` if needed. No ST process is started.
Open the resulting `index.html` directly. `faces.png` uses identical framing with
X/Y/Z locked to zero; portrait images approximate 240-pixel-wide UI usage.
`transitions.gif` contains actual successive browser frames. These are review aids,
not emotion-recognition scores. Earlier failed runs remain under `runs/`.
