# Optional Qwen Image Edit 2509 Lightning

This adds a separate timed worker and explicit `--lightning` initialization for
new canonical helper runs. The historical workers, base model lock, environment
and reviewer presets remain unchanged. All three image roles are required:
canonical geometry, target guide, original identity/style. There is no fallback
to two references. See [measured results](phase4b8-2-results.md).

## Provenance and local compatibility

The [official 2509 adapter directory](https://huggingface.co/lightx2v/Qwen-Image-Lightning/tree/d468c534b360e0754c6bf9e38ed49e1e09cd2e2a/Qwen-Image-Edit-2509)
and [model card](https://huggingface.co/lightx2v/Qwen-Image-Lightning/blob/d468c534b360e0754c6bf9e38ed49e1e09cd2e2a/README.md)
identify the Edit-2509-specific 4/8-step V1.0 BF16 weights, under the repository's
declared Apache-2.0 license. Exact revision, local paths, sizes and hashes live in
`backends/inpainting/lightning.lock.json`. Each file is 849,608,296 bytes:

| File | SHA-256 |
|---|---|
| Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors | `2a32ce938ec71db2b49a817b4844ae86995569518dea56ee0ddc209cbe8e1377` |
| Qwen-Image-Edit-2509-Lightning-8steps-V1.0-bf16.safetensors | `b5c48ba90d22294cc4e20ea4a347496e2136295ad438ff79ad4fe841f28d7f72` |

The [upstream examples](https://github.com/ModelTC/LightX2V-Qwen-Image-Lightning)
provide 40-step CFG 4 and 8/4-step CFG 1 comparisons. The displayed 4-step command
contains an 8-step filename typo; this implementation uses the actual **4-step**
file for Fast. Upstream also distinguishes ComfyUI and Diffusers behavior. We do
not assume workflow equivalence or universal optimality from those examples.

Unchanged local stack:

- ComfyUI 0.3.60, `b8730510db30c8858e1e5d8e126ef19eac395560`, GPL-3.0,
  `.cache/phase4b2-comfy`.
- ComfyUI-GGUF `6ea2651e7df66d7585f6ffee804b20e92fb38b8a`, Apache-2.0,
  `.cache/phase4b2-comfy-gguf`.
- QuantStack Qwen-Image-Edit-2509 Q4_K_S transformer, revision
  `84a3006979126011422eeeefe0c9485ddf431ef5`, Apache-2.0,
  `models/phase4b2/qwen/Qwen-Image-Edit-2509-Q4_K_S.gguf`.
- Comfy-Org Qwen-Image FP8 scaled Qwen2.5-VL 7B encoder and Qwen Image VAE,
  revision `1f12b17be14c89b026c51a91d67c32f84bb047bc`, Apache-2.0.
- Separate frozen `backends/inpainting/qwen-env` (Torch 2.8.0+cu128, Python 3.12).
  Exact base file hashes remain in `backends/inpainting/models.lock.json`.

`pose_lightning_worker.py` calls the installed `LoraLoaderModelOnly`, checks that
all 720 expected patches exist and that the patcher remains GGUF-aware. Its
strict logging handler turns unmapped/incompatible patch warnings into failures.
The resolved Comfy filename must also point to the exact pinned local file;
a same-named adapter in another search directory is rejected before loading.
The GGUF extension performs BF16 dequantization and patch arithmetic; the existing
`patch_on_device=None` is false-like, so CPU/offload-side patch placement is
preserved. Encoder weights are not LoRA-patched. Tests and matched real controls
show active adapter influence; checkpoint names alone would not establish this.

## Reproduction

Run from the repository root. Downloads are already present locally. If rebuilding
on a new machine, first inspect the pinned public Hub metadata and license, then
fetch only the two filenames below; do not install new base models implicitly:

```sh
HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HOME="$PWD/.cache/phase4b8-2-hf" hf download \
  lightx2v/Qwen-Image-Lightning \
  Qwen-Image-Edit-2509/Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors \
  Qwen-Image-Edit-2509/Qwen-Image-Edit-2509-Lightning-8steps-V1.0-bf16.safetensors \
  --revision d468c534b360e0754c6bf9e38ed49e1e09cd2e2a \
  --local-dir models/phase4b8-2/lightning
```

The worker verifies file size/SHA before expensive model loading. It never
downloads weights. For the exact matched study, choose a fresh output directory:

```sh
uv run --frozen python scripts/phase4b8_2_compare.py \
  --run runs/phase4b8-1-gestures \
  --batch b-cff4858500e9424bbe4340f92e2e9335 \
  --output runs/my-lightning-comparison --execute
uv run --frozen python scripts/phase4b8_2_report.py \
  --run runs/my-lightning-comparison --output runs/my-lightning-gallery
```

This creates five sequential cases: Quality, Lightning8, Lightning4, no-LoRA8 and
no-LoRA4. It holds the source review run's GPU lock, refuses existing output
folders, preserves all input hashes and uses the first saved seed/task. Omitting
`--execute` writes reproducible plans only. Reports include the actual new worker
hash alongside historical parent producer pins. The comparison script is intended
for this three-reference canonical helper workflow.

To create another independently reviewed five-candidate run:

```sh
uv run --frozen python scripts/pose_reviewer.py init-from-canonical \
  --canonical-run runs/phase4b8-canonical \
  --output runs/my-lightning-review \
  --presets recipes/lightning-gesture-presets.json \
  --gesture-profile chest-forearm-v1 --lightning
uv run --frozen python scripts/pose_reviewer.py generate \
  --run runs/my-lightning-review --pose right-lift --preset Balanced
uv run --frozen python scripts/pose_reviewer.py serve \
  --run runs/my-lightning-review --port 8804
```

Use a free port when the supplied reviewer is already running. To reopen the
existing five-candidate run, use only `serve --run runs/phase4b8-2-lightning-review-v2`.
The browser's **Generate five more** reserves five fresh seeds with one fixed
preset. **Accept** binds approval to the exact image hash and locks that pose.
**Finish review** exports only explicitly approved images. Pending poses are
not approved or marked unsupported automatically. Prior batches remain available.

| New preset | Steps | CFG | Adapter | Strength |
|---|---:|---:|---|---:|
| Balanced | 8 | 1 | 2509 Lightning 8-step V1.0 BF16 | 1 |
| Fast | 4 | 1 | 2509 Lightning 4-step V1.0 BF16 | 1 |
| Quality | 40 | 4 | none | 0 |

All use 1536px long edge (actual 800 × 1536), Euler/simple, shift 3, denoise 1,
source latent initialization, silhouette guide, no mask/CFG normalization and
empty negative prompt. `fit` preserves aspect ratio subject to the existing
multiple-of-32 rounding. The installed conditioning node internally resamples
references to its existing image area: retained latents are `[1,16,1,177,92]` for
each input. Neither reference resampling nor encoder behavior changed here.
Every task records settings, seed, exact prompt, reference/output hashes, adapter
revision/hash/strength/patch count, latent shapes and timing/memory stages.

The optional presets were added only after actual visual comparison. They are
not inserted into any historical run. Adding an adapter preset to an old worker
fails before mutating its catalog. New producer pins include the adapter lock,
loader helper and timed worker. Changed producers require a fresh run. Resume
retains the reserved seeds and settings and generates only unfinished candidates.
No concurrent GPU batch is allowed **within the same review run**; locking is not
a global GPU scheduler across independent runs. Do not start other GPU batches
while benchmarking. Reviewer loopback/Origin/CSRF/path guards are unchanged.

## Validation commands and limits

```sh
uv run --frozen python -m unittest discover -s tests -v
node tests/test_rp_talk.mjs
node tests/test_mouth_invariant.cjs
```

Synthetic reviewer browser testing uses
`tests/pose_reviewer_fixture_server.py --lightning` and the existing
`scripts/phase4b8_1_browser_scenario.js`; real-run inspection uses
`scripts/phase4b8_1_browser_readonly.js`. Neither approves real images.

This phase measures speed and visually screens candidates. It does not establish
correct hidden anatomy, exact fingers, production readiness or final arm rigging.
Codel artwork is by LisadiKaprio, CC-BY-4.0,
[original source](https://opengameart.org/content/codel-visual-novel-sprite).
Synthetic derivatives retain this provenance; the original and reviewed canonical
remain immutable. Generated images, raw logs, model weights and browser profiles
stay under ignored project directories.
