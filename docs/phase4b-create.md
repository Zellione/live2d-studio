# Create a local portrait

This command is a Python application. Codex is not involved at runtime. It needs
the already pinned See-through environment/checkpoints, a local PSD2Live application
with MCP enabled on `127.0.0.1`, and the installed viewer libraries. Nothing downloads
or installs itself. See [worker setup](../backends/see-through/README.md) and
[viewer dependencies](phase3-1-preview.md). The current automatic support is a
**limited frontal portrait**, with explicit semantic and visual review.
The independent Sara benchmark reaches this workflow's preview but fails visual
acceptance. This release does not yet establish a usable independent character;
see the [Phase 4B results](phase4b-results.md).

From an interactive zsh with `PSD2LIVE_MCP_TOKEN` explicitly exported:

```sh
uv sync --frozen
uv run --frozen live2d-studio mcp-check
uv run --frozen live2d-studio create \
  --input character.png --output runs/character \
  --rights 'Author; license; source URL'
```

Use a fresh output directory. Input files, accepted models and fixtures are never
overwritten. Transparent PNG portraits are the tested input class; PNG/WebP/JPEG
decoding is supported up to 4 megapixels but does not imply reliable background
removal or parsing. EXIF-rotated inputs require a separately normalized copy.
The GPU worker uses the existing separate environment and pinned offline weights.
It does not install Torch into the main environment or change host settings.

The command initially stops for semantic review or a failed quality gate. Exit
code 2 means a pending/blocked quality decision; exit 1 means an execution error.
Inspect the printed `layers/preview/index.html`, source/mask sheets and
`readiness-*/quality.json`. Review facial ownership, hidden face support, missing
or duplicated contours, original pixel preservation and all visible limbs.
Record left/right shoulders, upper arms, forearms, hands, legs and feet in notes:
preserved, absent in input, cropped, uncertain or incorrectly assigned. Do not
equate clothing layer names with correctly preserved anatomy.

```sh
uv run --frozen live2d-studio review-create --output runs/character \
  --stage semantic --decision accept --reviewer 'Your name' \
  --checks semantic_ownership,hidden_face,source_preservation,visible_limbs \
  --notes 'Describe the reviewed source, hidden regions, bilateral limbs and limits.'
```

Use `--decision reject --notes 'Reason'` to reject it. No painting is required.
Hard missing/unsupported facial geometry and source-preservation failures cannot
be overridden. A rejected or stale review cannot silently resume to rigging; keep
that run and create a new candidate. A record is tied to the exact quality report,
which in turn pins its layer manifest. Neither an agent review nor numerical
checks count as user visual approval.

Repeat the **same create command** to continue. It verifies completed artifacts,
skips inference, and builds the editable project, PSD, rig, expressions and runtime.
PSD2Live saves the previous editor into a fresh snapshot before switching. No
`discard_unsaved` operation is used. Concurrent creation stages serialize access
to the shared editor; avoid editing that workspace while a stage is running.

The exported model is instantiated with the actual local Cubism Core. A dedicated
headless browser renders independent blink/mouth/gaze/head controls, seven
head-locked expressions, combined poses, idle and exact reset. Logs, frames,
numeric warnings and a contact sheet are retained. Headless validation currently
requires `/opt/google/chrome/chrome`, Node and usable WebGL (SwiftShader is used).
The interactive viewer then opens on loopback; Ctrl+C stops it. `--no-preview`
performs the pipeline and validation without leaving a viewer server running.
`--extension DIR` selects installed libraries, and `--port NUMBER` changes the
interactive viewer port. These options never start a SillyTavern server.

Final acceptance is a separate explicit review:

```sh
uv run --frozen live2d-studio review-create --output runs/character \
  --stage visual --decision accept --reviewer 'Your name' \
  --checks blink,mouth,head_overlap,expressions,holes_contours,visible_limbs \
  --notes 'Describe reviewed poses, limb preservation and remaining artifacts.'
```

Until this review is accepted, the model remains a candidate. Reject it if animation
loses features, exposes major holes, duplicates lines or deforms limbs incorrectly.
Expressions need separate judgement with the head stationary. Numeric hole/component
counts are warnings, since legitimate hair gaps and eyelid folding also affect them.
Duplicate contours and natural-looking eyelids are not solved automatically.

`creation.json` records the current runtime path and every stage. To reopen just
the viewer, use `uv run --frozen live2d-studio preview-live --run runs/character`.
This verifies the current export's hashes before opening it. No MCP, GPU inference,
token or coding agent is needed to view an exported model. The model folder has
portable runtime references; PSD/project sources stay in the run.

## Repeating stages and tuning

`--until` accepts `ingest`, `inference`, `semantics`, `restore`, `readiness`,
`facial`, `project`, `rig`, `animation`, `export`, `validation`, `preview`.
Prerequisites are automatically checked/reused. Failed stages retry in fresh
directories; previous diagnostics are retained. Code/configuration changes invalidate
dependent checkpoints. Tampered outputs fail closed instead of silently rerunning.
Keep the external input unchanged so resume can verify its identity.

To repeat into a new run without GPU inference, use `--decomposition OLD/bridge`
and `--sam OLD/SAM_DIRECTORY`. Each cache must match the original source hash;
model revisions, bridge dimensions, masks and content hashes are validated. After
the first import the run owns its copies. A cache is never semantic ground truth.
For existing accepted experiments, the retained `runs/phase2-5-oga-neural/bridge`
and `runs/phase2-5-oga-sam` can replay Girl2.

The reusable configuration is `src/live2d_studio/portrait_profile.json`: normalized
mouth/brow curve fields and modest idle amplitudes. It contains no artwork hashes,
mesh IDs or canvas coordinates. The builder discovers actual role-to-mesh/deformer
bindings and enumerates their key axes. Ambiguous parents, missing parameters and
unbounded key expansion are errors. The inspected binding and generated recipe
are saved with each build; changing the profile requires renewed render review.

Facial preparation deliberately uses PSD2Live's procedural lid/lip generation and
relative mesh deformation. These are generated alternatives, not source pixels.
The original imported RGBA is verified inside the saved project archive. See-through
provides unvalidated candidate hidden surfaces; there is no independently known
hidden mask, teeth/tongue system or reconstructed eyelid skin. Optional blush is
omitted from this generic profile. These limitations remain visible in reports.

No deployment is part of `create`. Existing isolated-only deployment restrictions,
accepted Girl2 packaging pins and production settings remain unchanged.
