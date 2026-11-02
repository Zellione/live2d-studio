# Isolated See-through worker

Run all commands from the live2d-studio repository root. This environment is
independent of the main `.venv` and `uv.lock`. Code and weights are pinned in
`models.lock.json`; no UI or cloud inference is used. Audit/results:
[`docs/phase2-5-results.md`](../../docs/phase2-5-results.md).

```bash
export UV_CACHE_DIR="$PWD/.cache/uv"
git clone https://github.com/shitagaki-lab/see-through.git .cache/see-through/source
git -C .cache/see-through/source checkout df019de5129d6c4b406587a14c3501669441a783
uv sync --frozen --project backends/see-through
# Only after explicit approval of the documented 14.73 GB download:
python3 scripts/download_seethrough.py --approved

backends/see-through/.venv/bin/python backends/see-through/worker.py \
  --input assets/references/wikipe-tan/original.png \
  --output runs/wikipe-neural-new
uv run --frozen live2d-studio prepare --backend see-through \
  --input assets/references/wikipe-tan/original.png \
  --decomposition runs/wikipe-neural-new/bridge \
  --output runs/wikipe-layers-new \
  --rights 'Kasuga; CC-BY-SA-3.0; https://commons.wikimedia.org/wiki/File:Wikipe-tan_face.png; evaluation derivative'
uv run --frozen live2d-studio inspect --project runs/wikipe-layers-new
```

Choose fresh outputs. The worker verifies checkpoint hashes, rejects altered
upstream source and runs with HF offline mode. It records seed, package versions,
stage time, Torch allocated/reserved peak and sampled whole-device VRAM/utilization
(500 ms sampling; includes other processes). BF16 LayerDiff 1280px/30 steps and
Marigold 768px/4 steps are defaults. Models are unloaded between stages. Seeds
alone do not promise bitwise CUDA reproducibility. No training is performed.

For SAM, use the same worker with `--sam` and a fresh output. This is the separate
19-class visible-part experiment, run at upstream FP32; it does not replace the
BF16 decomposition or provide independent ground truth. Strict state loading
and `torch.load(weights_only=True)` are used.

## Benchmark B

Download the CC0 archive from the source linked in the report, verify its SHA-256,
extract only `AllAnime/NewAnime.xcf` into `assets/references/oga-portraits/`.
The original remains untouched. Installed GIMP 3 can export without a GUI:

```bash
GIMP3_DIRECTORY="$PWD/.cache/phase2-5-gimp" \
OGA_XCF="$PWD/assets/references/oga-portraits/NewAnime.xcf" \
OGA_OUTPUT="$PWD/runs/oga-raw-new" \
gimp-console --new-instance --no-data --no-fonts \
  --batch-interpreter=python-fu-eval \
  --batch='exec(open("scripts/export_oga_gimp.py").read())' --quit
uv run --frozen python scripts/prepare_oga_benchmark.py \
  --raw runs/oga-raw-new --output runs/oga-truth-new
```

Pass **only `flat.png`** to either backend, never XCF or benchmark metadata.
After inference/import, evaluate the same six coarse groups at native canvas size:

```bash
uv run --frozen python scripts/evaluate_oga.py \
  --project runs/oga-layers-new --truth runs/oga-truth-new \
  --output runs/oga-layers-new/coarse-evaluation.json
```

The mapping is based on visually inspected source layers. Hair includes ribbons;
face includes ears/nose; eyes include brows, whites and irides. Full-layer IoU
compares authored shapes, **not verified hidden anatomy**. Visible IoU uses the
same alpha threshold (>127), frontmost-layer assignment and nearest mask
resampling for both backends. Fine iris/eyelid metrics are deliberately omitted.

## Manifest v2 bridge

`worker.py` emits a small `bridge/decomposition.json` and the PSD's actual cropped
RGBA layers, order and offsets. The main project imports these without loading
Torch/psd-tools. `prepare --backend deterministic` remains the default and retains
the Phase 2 algorithm and v1 manifest.

V2 adds fractional `generated_mask_path`, full candidate `semantic_mask_path`
and binary `uncertain_mask_path`. `mask_path` remains the mask of **verified
unchanged observed pixels**, empty for this backend. `reconstructed_mask_path`
is empty and `hidden_reconstruction_status=unlocalized`: the model does not
provide an independently trustworthy hidden-only mask. Zero reconstructed count
therefore means **unknown localization**, not absence of inpainting. Every output
pixel is conservatively marked generated/uncertain. No original-image passthrough
is inserted to inflate coverage or composite similarity. Coverage is candidate
support; correct assignment requires independent evaluation.

V1 validation remains unchanged. Both versions map role/side/offset/order to
PSD2Live artwork requests. Upstream `-r` maps to image-left, `-l` to image-right.
The bridge rejects unsupported blends, invalid paths, unpinned provenance and
out-of-canvas placement; it never silently drops excess layers. Automatic build
is gated until animation-specific shapes and concealed geometry are reviewed.
