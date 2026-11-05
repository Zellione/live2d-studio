# Phase 4B.5 protocol and reproduction

Read [results](phase4b5-results.md), [creation contract](phase4b-create.md) and
[provenance](../benchmarks/phase4b5-art.json). This tests a previously unused
illustration from a different credited artist, not guaranteed absence from model
training. Selection exposure is disclosed; no reference-based tuning occurred.

## Freeze and isolation

`runs/phase4b5-freeze/freeze.json` records the clean starting HEAD, hashes of
tracked pipeline/scripts/profiles/locks/fixtures, defaults, selected options and
gate thresholds. `references.json` pins and verifies accepted Phase 3/3.1 and
frozen Girl2/Sara stages and later expression/mouth archives. Baseline commands:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --frozen
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python -m unittest discover -s tests -v
node tests/test_rp_talk.mjs
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio mcp-check
```

Default deterministic artwork stays unchanged. Aligned motion is explicitly
selected, not silently made the default. Hard gates remain 99.5% exact foreground
and silhouette, paired eye roles, face/mouth/neck, no unknown role, 75% face
support of eyes and 50% SAM face agreement, plus evidence-bound semantic and
visual reviews. Parser agreement is not independent truth. No gate was weakened.

Use the existing separate pinned worker environment and offline snapshots from
`backends/see-through/models.lock.json`. LayerDiff/depth use their recorded
OpenRAIL-family licenses; SAM is Apache-2.0. Source revision is
`df019de5129d6c4b406587a14c3501669441a783`. The worker verifies weights and source
before inference, with seed 42, BF16 LayerDiff, FP32 SAM and no network downloads.
Recorded versions: Torch 2.8.0+cu128, torchvision 0.23.0+cu128, diffusers 0.37.0,
transformers 5.0.0, psd-tools 1.14.2. PSD2Live remains 3.6.7 (GPL-3.0 recorded
in compatibility documentation); installed Core 5.0.0 is proprietary and is not
redistributed. Core SHA-256 is
`942783587666a3a1bddea93afd349e26f798ed19dcd7a52449d0ae3322fcff7c`.
No Python packages were installed system-wide and no new model was downloaded.

## Prepare the same single input

Download only the publisher-linked archive into a new ignored directory:

```sh
mkdir -p runs/NEW-codel-source
curl -fL --output 'runs/NEW-codel-source/Codel sprite.zip' \
  'https://opengameart.org/sites/default/files/Codel%20sprite.zip'
```

Compare its SHA-256 with `benchmarks/phase4b5-art.json`. Extract **only
Codel3.png** for generation; leave the PSD and other PNGs quarantined for
evaluation. This exact extraction does not decode any alternate expression:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python - <<'PY'
import hashlib, json
from pathlib import Path
from zipfile import ZipFile
p = Path('runs/NEW-codel-source')
provenance = json.loads(Path('benchmarks/phase4b5-art.json').read_text())
archive = p / 'Codel sprite.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest() == provenance['archive_sha256']
with ZipFile(archive) as z:
    data = z.read('Codel3.png')
assert hashlib.sha256(data).hexdigest() == provenance['selected_input']['sha256']
with (p / 'neutral.png').open('xb') as f:
    f.write(data)
PY
```

The saved publisher HTML hash, member inventory, archive hash, input hash,
attribution, original dimensions and predeclared crop are in the provenance and
local freeze. License is verified from the publisher, not invented from filenames.
Credit LisadiKaprio and link the source/CC BY 4.0 when sharing permitted derivatives;
identify modifications. The downloaded archive and originals are not Git artifacts.

## Run the frozen workflow

From the project root with local GPU and loopback MCP access, using only an
explicitly provided token environment when needed:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio create \
  --input runs/NEW-codel-source/neutral.png --output runs/NEW-codel \
  --rights 'Codel by LisadiKaprio; CC-BY-4.0; https://opengameart.org/content/codel-visual-novel-sprite; automated benchmark derivative' \
  --reconstruction deterministic --facial-motion aligned --no-preview
```

Exit 2 is expected at a review checkpoint, not execution failure. Inspect the
reported layers and readiness evidence, especially concealed face, eye contours,
both visible hands and the shared arm assignment. Record an honest review using
`review-create` as documented in the creation guide, then repeat the identical
command. Do not copy this benchmark's accepted development-review record to a
different evidence hash. Do not pass the gate if the new output is unacceptable.
The CLI verifies caches, authors generic rig/expressions, exports PSD/project/MOC,
instantiates installed Core and renders 401 frames when aligned motion is used.
No coding agent is needed to execute these commands.

The recorded first run preserves an initial sandbox CUDA denial and a same-input
retry. It then stopped for semantic review and resumed normally. The model and
all completed stages were sealed before PSD extraction. No pipeline code changed
between freeze and first export, and all corresponding hashes are rechecked by
the report collector. Raw logs, masks, projects and browser profiles remain local.

## Optional generic authoring, separate from the first result

These existing scripts are not integrated into `create`; do not describe them
as part of its default first run. They use inspected semantic roles/ancestry and
source-relative geometry, not benchmark annotations:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b4_experiment.py \
  --baseline runs/NEW-codel --output runs/NEW-codel-expressions
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b4_1_experiment.py \
  --baseline runs/NEW-codel-expressions --output runs/NEW-codel-mouths
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b3_render.py \
  --model runs/NEW-codel-mouths/export/runtime/Generated_artwork.model3.json \
  --correspondence runs/NEW-codel-mouths/transition-correspondence.json \
  --output runs/NEW-codel-mouths/dense
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b4_1_render.py \
  --model runs/NEW-codel-mouths/export/runtime/Generated_artwork.model3.json \
  --output runs/NEW-codel-mouths/mouth-review
node scripts/probe_expressions.cjs \
  .cache/phase3-st/data/default-user/extensions/Extension-Live2d/lib/live2dcubismcore.min.js \
  runs/NEW-codel-mouths/export/runtime/Generated_artwork.model3.json \
  runs/NEW-codel-mouths/authoring/mouth-inspection.json \
  > runs/NEW-codel-mouths/expression-core.json
```

The final command fails for this Codel candidate's strict seam invariant. Preserve
its nonzero status and report. Do not add epsilon, change scale or remove samples
to obtain a pass. The report collector recounts visible reversals from the retained
samples while retaining the failed top-level verdict.

## Independent evaluation and gallery

`scripts/phase4b5_references.py` requires a seal with the run location, per-file
hashes and archive hash; it refuses changed evidence. The actual seal is
`runs/phase4b5-freeze/first-run-seal.json`. Replaying extraction from this seal:

```sh
backends/see-through/.venv/bin/python scripts/phase4b5_references.py \
  --archive 'runs/phase4b5-source/Codel sprite.zip' \
  --seal runs/phase4b5-freeze/first-run-seal.json --output runs/NEW-reference-evaluation
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b5_evaluate.py \
  --run runs/phase4b5-codel-full-first --references runs/NEW-reference-evaluation \
  --definition benchmarks/phase4b5-evaluation.json \
  --output runs/NEW-reference-evaluation/independent-metrics.json
```

The evaluation definition has manually reviewed facial-ink/limb **evaluation
regions only**. These coordinates never enter any worker, facial preparation or
rig recipe. It records ink recall, exact unique copied pixels, uncertainty and
the narrow artist-base comparison. It refuses mismatched input hashes or grossly
misaligned neutral compositions. Whole-character semantic accuracy stays null.

`phase4b5_render.py --model MODEL --output NEW` adds 122 high-resolution captures
at 1800 × 1950 using the same model and framing. This is new rasterization, not
portrait inference or a resized image. Existing dense/Core thresholds are untouched.
Early report-schema errors remain in `details`, `details-v2` and first-detail
attempts; the final sets are `runs/phase4b5-first-details-v2` and
`runs/phase4b5-codel-mouths/details-v3`.

`scripts/phase4b5_report.py` collects this fixed benchmark's locally retained
paths, verifies the sealed first run, pipeline hashes and reference inventories,
and emits a standalone review directory plus concise JSON. Regenerate the final
collection into a fresh directory:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b5_report.py \
  --output runs/NEW-codel-review --benchmark runs/NEW-codel-benchmark.json
```

Reference expression grids are visual evidence, not exact emotion labels or a
recognition score. The original artist provides several tears/closed-eye variants,
not direct equivalents for every generated emotion. The frozen Girl2/Sara figures
are historical evidence at different input resolutions, with existing limitations.

## Open the delivered review

Run these in separate terminals; all servers bind loopback. The gallery serves
only selected review artifacts, not the entire runs tree or browser profiles.

```sh
python3 -m http.server 8790 --bind 127.0.0.1 --directory runs/phase4b5-review-final
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio preview-live \
  --run runs/phase4b5-codel-full-first --port 8786
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio preview-live \
  --model runs/phase4b5-codel-mouths/export/runtime/Generated_artwork.model3.json \
  --port 8787
```

Start with the mouth-only rows, then seven full expressions, blink/opening sheets,
combined head/talk sequences and whole-character limb views. The optional-mouth
viewer is explicitly diagnostic because its strict Core check failed. Do not
record visual acceptance on the user's behalf. No production deployment is part
of this phase.
