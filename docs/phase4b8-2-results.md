# Phase 4B.8.2 — Qwen 2509 Lightning acceleration

The pinned BF16 Lightning adapters work with the existing Q4_K_S GGUF transformer
and FP8 encoder. At 800 × 1536 with three references, the matched 8-step run took
**43.53 seconds end to end**, and the 4-step run **30.98 seconds**, versus **253.14
seconds** for the 40-step reference. Both Lightning images show a bent arm with a
present hand; the reference leaves both arms down. These are development-reviewed
synthetic outputs, not human-approved anatomy or accepted rig assets.

Started from validated HEAD `8316adfd88bfba37154d71c89c72b7300cd5094f` with a clean
working tree. No generation batch was running when the study began. All 1,854
inventoried historical files remain hash-identical, including the frozen combined
Codel snapshot, canonical selection and previous helper selections/results.
No existing presets, inference-worker hashes, model/environment locks, accepted
runtimes or production SillyTavern files were changed.

## Matched performance comparison

Same seed `2597810572262578`, source, guide, original identity reference, prompt,
negative prompt, output size and sampler family in every row. Euler/simple,
shift 3, denoise 1, source latents, silhouette guide, no mask or CFG normalization.
Only steps, CFG and LoRA selection/strength differ as specified below.

| Configuration | CFG | LoRA strength | Model load | Reference encoding | LoRA setup | Sampling | Decode | Image total | Process total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Quality, 40 steps, no LoRA | 4 | 0 | 10.91 | 1.68 | 0.00 | 236.33 | 0.84 | 239.29 | 253.14 |
| Balanced, 8-step Lightning | 1 | 1 | 11.38 | 1.63 | 0.41 | 25.55 | 0.85 | 28.92 | 43.53 |
| Fast, 4-step Lightning | 1 | 1 | 11.26 | 1.72 | 0.40 | 13.25 | 0.84 | 16.70 | 30.98 |
| Control, 8 steps, no LoRA | 1 | 0 | 11.01 | 1.73 | 0.00 | 24.63 | 0.84 | 27.72 | 41.43 |
| Control, 4 steps, no LoRA | 1 | 0 | 10.96 | 1.60 | 0.00 | 12.79 | 0.83 | 15.77 | 29.38 |

All times are seconds. Process speedups are **5.82×** and **8.17×**. Per-image
speedups excluding shared model construction are **8.27×** and **14.33×**. The
8/4-step comparison also changes CFG, as requested; these are configuration
speedups, not a measurement isolating the adapter's speed contribution.

Peak Torch allocation/reservation was 20.86/23.43 GiB for the quality reference
and 20.87/23.37 GiB for both Lightning runs. There was no OOM. These are allocator
peaks, not whole-board VRAM or total GPU memory including desktop applications.
CUDA synchronization bounds each stage. Model loading measures Qwen construction;
lazy device transfers and weight patch application occur within sampling, and
VAE transfers within decoding. Startup, latent initialization, input preparation,
image saving and unloading are also recorded in the raw reports. Process total
includes interpreter startup and shutdown. Each comparison uses a fresh process
with warm filesystem caches; n=1 per configuration provides no variance estimate.

All cases retained three `[1,16,1,177,92]` reference tensors and produced 800 × 1536
images. The new no-LoRA worker reproduces the historical Phase 4B.8.1 candidate 1
**byte-for-byte** at the same seed. This checks the refactored timing path without
claiming reproducibility across different hardware/library versions.

## Adapter compatibility and actual effect

Both files are pinned from `lightx2v/Qwen-Image-Lightning` revision
`d468c534b360e0754c6bf9e38ed49e1e09cd2e2a`. Public metadata declared Apache-2.0,
849,608,296 bytes per file and exact LFS SHA-256 values before download. Both local
files match. Only these two adapters were downloaded; base weights, encoder,
VAE, ComfyUI and GGUF extension remain unchanged. See the
[generation documentation](phase4b8-2-lightning.md) for full pins and commands.

The installed `LoraLoaderModelOnly` retains `GGUFModelPatcher` and applies all 720
expected weight patches from each adapter's 2,160 tensors. Missing weights,
wrong hashes, missing patches, unmapped keys and shape/merge failures raise errors;
there is no silent unpatched fallback. FP8 text encoding is unchanged because
the adapter is model-only. BF16 dequantization/patch arithmetic remains pinned.

Matched 8-step and 4-step **no-LoRA** controls isolate adapter presence at CFG 1.
Both show ghost/duplicated arms and severely damaged raised hands. The Lightning
images have continuous opaque arms and visible hands. Mean absolute RGB changes
are 5.09/255 and 7.00/255, affecting 73.94% and 85.19% of pixels respectively.
Those changes demonstrate that patches affect inference; they are not evidence
of correct hidden geometry. The control settings are diagnostic only, not presets.

## Visual tradeoffs

- **Quality:** face, hairstyle, outfit, palette and frontal framing remain close
  to the canonical base, but both arms stay down. This historical preset remains
  selectable; its name does not promise better gesture compliance.
- **Balanced:** recognizable character/style and clothing; clear anatomical right
  elbow bend (viewer left), continuous sleeve/wrist and present hand, opposite
  arm down. The hand points with an index finger and is higher than the requested
  relaxed chest-height placement. Folded-finger topology and shoulder anatomy
  still need review.
- **Fast:** similarly clear bent arm and hand, with slightly changed face/body
  proportions and simpler hand/cloth shading. It shares the pointing/high-hand
  departure. One seed is insufficient to establish a general quality ranking.

After this comparison, a separate reviewer run generated five fresh Balanced
candidates in **162.18 seconds** worker total, including one shared model load.
Per-image times: 28.61, 30.09, 29.65, 29.60 and 29.67 seconds. Every candidate
records three references and 720 patches; patches do not accumulate across tasks.
All five visibly bend the intended right forearm and retain the other arm down.
Hands vary between curled/pinching, pointing and open-palm forms; candidate 1 has
an awkward curled fingertip, and 3/4 introduce more skirt folds. The guide does
not yet fix finger pose or exact hand height. Faces, hair, outfit design and
frontal framing remain recognizable. This is better gesture visibility than the
previous five arms-down/missing-hand failures, not five guaranteed usable poses.

No image was automatically accepted, parsed with SAM, converted into verified
anatomy or applied to a rig. The other four target poses were not generated.

Final inspection added a guard against a same-named LoRA shadowing the pinned
file in ComfyUI's search paths. This does not change sampling. The compared
worker/helper snapshots and their hashes remain under the audit directory; the
initial five-image run remains intact at `runs/phase4b8-2-lightning-review`
(localhost 8802). Its producer pins were not rewritten. The final guarded worker
uses a fresh `runs/phase4b8-2-lightning-review-v2` run, served on 8804. Historical
runs remain reviewable; further generation requires the matching producer or a
fresh run. The final five-image batch took 161.52 seconds total; each image took
28.42–30.08 seconds. All five bend the correct arm; hands vary between curled
fingers and open palms above the target height. Candidate 3 shifts/widens the
torso and nearly clips the relaxed hand at the edge; candidate 5 has a small
patterned bottom-border artifact. Exact measurements are recorded separately
in the benchmark. These fresh seeds are distinct from the first batch's seeds.

## Review and validation

- Comparison gallery: <http://127.0.0.1:8803/>, `runs/phase4b8-2-review-final`.
- New standalone reviewer: <http://127.0.0.1:8804/>,
  `runs/phase4b8-2-lightning-review-v2`.
- Matched results and controls: `runs/phase4b8-2-comparison`.
- Model metadata, logs, preservation inventory and browser evidence:
  `runs/phase4b8-2-audit`, `runs/phase4b8-2-browser-*`.
- Machine-readable [benchmark](benchmarks/phase4b8-2.json).

206 Python tests pass, including nine new Lightning tests. Both JavaScript
regression files pass (5 RP talk and 3 mouth-invariant checks). The first Python
run had two sandbox socket-permission errors; the complete rerun with loopback
access passes. The failed logs are retained. Synthetic browser QA covers two
five-seed batches, rejection, approval locking, unsupported handling, history,
zoom, three-reference display and selected-only export. Real-browser read-only
QA verifies the five generated candidates and comparison dialog without creating
approval. Ordinary unit tests require no GPU or model downloads.

Recommendation: use **Balanced** for subsequent human-reviewed pose exploration,
**Fast** for quick trials, and retain **Quality** as the historical reference.
These are opt-in presets in a new run; existing reviewer catalogs are untouched.
Performance feasibility is positive. Human selection, more exact hand placement
and anatomical evaluation remain necessary before any later articulation work.
Stop after Phase 4B.8.2; no final rigging or production change was made.
