# Phase 4B.8.1 — canonical-based guided gestures

This phase exercises the existing local three-image route. It does not replace
any accepted runtime, regenerate the canonical base or authorize final arm rigging.
Only human-selected images may enter the semantic comparison.

## Inputs and coordinate convention

`init-from-canonical` verifies the approval-bound canonical snapshot and prepares
a fresh helper run. The inputs remain distinct:

| Slot | Input | Purpose |
|---|---|---|
| image1 | Frozen Phase 4B.8 candidate 4 | Synthetic frontal working geometry |
| image2 | Programmatic gesture guide | Requested arm placement |
| image3 | Original flat Codel illustration | Identity, outfit and artistic style |

Anatomical right is the character's right, appearing on the **viewer's left** in
this frontal view. The initial `right-lift` target is a raised right forearm,
elbow bent near waist height, hand approximately at chest height. The anatomical
left arm remains down. A clean arms-down redraw fails this target.

The opt-in `chest-forearm-v1` profile supplies explicit instructions and a bent-arm
guide. It derives scale from foreground bounds; coordinates are normalized framing
hypotheses for head-to-upper-leg images, not detected or verified anatomy. All
five candidates in a batch share the exact guide, prompt, settings and references.
Seeds vary rendering, not the requested gesture. The five prepared pose targets
have consistent anatomical side names; only the first target is generated initially.

The old `canonical_pose.py`, historical pose guides and both inference workers
remain byte-identical. Their previously frozen producer pins stay usable. The
new profile is separately hash-pinned in newly opted-in runs. Editing a profile
requires a fresh run; existing reviewed targets remain locked.

## Local reproduction

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/pose_reviewer.py init-from-canonical \
  --canonical-run runs/phase4b8-canonical --output runs/NEW-canonical-gestures \
  --presets recipes/canonical-gesture-presets.json --gesture-profile chest-forearm-v1
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/pose_reviewer.py serve \
  --run runs/NEW-canonical-gestures --port 8800
```

The live run is `runs/phase4b8-1-gestures`, reviewer <http://127.0.0.1:8800/>.
Its first batch uses the same numerical settings as the approved canonical preset:
1536-pixel long edge, 800 × 1536 canvas, 40 steps, CFG 4, shift 3, Euler/simple,
denoise 1, source latents, silhouette guide, no mask or CFG normalization, and an
empty negative prompt. Scaling is uniform with minimal white letterboxing.

Equivalent generation command:

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/pose_reviewer.py generate \
  --run runs/NEW-canonical-gestures --pose right-lift --preset canonical-gesture-1536-40
```

Five unique seeds are reserved atomically before inference. Repeating a batch
uses five fresh seeds and keeps the older images. Interrupted batches resume only
unfinished candidates with the original three inputs, prompt, settings and seeds.
The reviewer displays canonical, guide and original, supports full-size comparison,
rejection, selection, more batches, unsupported targets and selected-only export.
Per-run GPU locking also covers diagnostic controls and semantic analysis.

## Model and actual conditioning checks

No weights, nodes or environments were downloaded. The existing isolated Qwen
worker uses Q4_K_S transformer revision `84a3006979126011422eeeefe0c9485ddf431ef5`,
the FP8 `qwen_2.5_vl_7b_fp8_scaled.safetensors` encoder and Qwen VAE from revision
`1f12b17be14c89b026c51a91d67c32f84bb047bc`. Exact file hashes, licenses and local
paths remain in `backends/inpainting/models.lock.json` and the
[Phase 4B.7b audit](phase4b7b-generation.md). Headless ComfyUI/GGUF/Torch pins and
all original model files remain unchanged.

The installed `TextEncodeQwenImageEditPlus` iterates image1/image2/image3 in order,
resamples each for vision encoding and separately VAE-encodes each. The installed
Qwen `extra_conds` forwards all reference latents; its transformer iterates and
concatenates them. It does not select only the last image. The inspected tokenizer
does not impose a 1,024-token truncation boundary on this prompt.

The actual worker passes all three images to positive and negative encoding and
requires three positive reference latents before sampling. Per-image runtime
metadata records their count and shapes, identity/guide hashes, seed, prompt,
settings, image hash and Torch CUDA peaks. The saved plan additionally binds the
canonical source and model lock. Reviewer reconciliation rejects missing image3
hashes, counts other than three, or missing/malformed latent shapes. There is no
automatic two-reference fallback.

The first measured three-reference task retained three `[1,16,1,177,92]` tensors
and completed on the RTX 5090. This proves that the installed route can execute
three-image conditioning; it does not prove compliance with the requested gesture.
Internal vision inputs are approximately 277 × 532; VAE references 736 × 1416,
independent of the 800 × 1536 output canvas. These are resampled conditioning
images, not preserved source pixels.

## Controlled diagnosis

If outputs ignore the bend, `scripts/phase4b8_1_control.py` can reproduce the first
seed in a separate diagnostic directory. It never changes reviewer candidates or
selects the control image. Its explicit controls change one reference family:

- `two-references`: remove image3 and its textual identity instruction; retain
  canonical source, guide, seed and all numerical settings.
- `skeleton`: replace silhouette with the saved skeleton guide; retain all three
  image roles, seed, numerical settings and prompt.

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b8_1_control.py \
  --run runs/phase4b8-1-gestures --batch BATCH_ID \
  --output runs/NEW-conditioning-control --mode two-references --execute
```

A diagnostic is one matched case, explicitly separate from five-candidate review
batches. It requires an idle per-run GPU lock. Saved plans support exact-settings
replay into fresh directories; bit-exact GPU determinism is not claimed.
Do not infer a universal three-image model limitation from one conditioning control.

## Evaluation and future architecture

After human approval, export the selected set and run the pinned SAM comparison:

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b7b_selected_semantics.py \
  --run runs/phase4b8-1-gestures --selection SELECTION_ID \
  --output runs/phase4b8-1-gestures/selected-assessment-v1
```

The baseline is labelled **canonical synthetic base**, distinct from the original
identity reference. Differences include repainting, deformation and exposure;
they cannot measure verified hidden clothing. Disconnected arm masks do not
establish upper-arm/forearm/hand parts or shoulder/elbow/wrist landmarks. Visual
approval, gesture compliance, segmentation usefulness and anatomy verification
remain separate findings.

| Possible later strategy | What approved poses could supply | Evidence still needed |
|---|---|---|
| Skeletal mesh deformation | Bilateral mask proposals, sleeve contours and possible joint locations | Stable cross-pose correspondence, reviewed joints, hidden backing, deforming mesh and runtime tests |
| Discrete gesture-layer variants | Reviewed whole-arm or body variants for specific gestures | Compatible cut lines, torso coverage, draw order, transitions and face/torso alignment |

If geometry differs across poses, discrete variants may be easier to evaluate
first. Neither path makes generated anatomy true. No PSD2Live rig, gesture swap
runtime or accepted Codel migration is implemented in this phase.
