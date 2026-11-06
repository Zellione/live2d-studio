# Phase 4B.8 — canonical front-facing working bases

Canonicalization is an opt-in stage before helper poses. It proposes a synthetic
front-facing neutral working image from the original flat artwork. The original
remains the identity/style authority. Historical Codel, Girl2 and Sara references,
creation defaults and production deployment are unchanged.

## Review workflow

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/pose_reviewer.py init-canonical \
  --input runs/references/codel-combined-v1/source/original.png \
  --output runs/NEW-canonical --presets recipes/canonical-base-presets.json \
  --rights 'LisadiKaprio; CC-BY-4.0; https://opengameart.org/content/codel-visual-novel-sprite'
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/pose_reviewer.py serve \
  --run runs/NEW-canonical --port 8798
```

The current local run is `runs/phase4b8-canonical` at <http://127.0.0.1:8798/>.
Choose **Generate five candidates**, inspect full-size comparisons, then approve
one canonical base or reject weak candidates and request five more. Every new
batch has five fresh seeds. Older batches, decisions and settings remain available.
**Mark canonicalization unsuccessful** stops the attempt without creating a base.
Ordinary pose review remains a separate workflow.

Approval automatically freezes the exact selected image. **Save canonical
selection** additionally exports the reviewed selected set. Neither action starts
helper generation. If the new view changes identity or costume too much, do not
approve it just because it faces forward. Pixel-perfect preservation is not an
acceptance criterion for the synthetic image.

Equivalent bounded generation command:

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/pose_reviewer.py generate \
  --run runs/NEW-canonical --pose canonical --preset frontal-silhouette-1536-40
```

## Conditioning and reproducibility

The initial configuration uses the existing local Qwen Image Edit 2509 Q4_K_S
transformer and FP8 encoder, Euler/simple, shift 3, CFG 4, 40 steps, denoise 1,
source latent initialization and no edit mask or CFG normalization. The original
1078 × 2089 image is uniformly fitted on a white 800 × 1536 canvas. It is never
stretched, overwritten or replaced with the previously approved auxiliary pose.
The PSD is not an input.

Image1 is the original; image2 is a symmetric frontal placement guide. The guide
centres face/chest/hips, levels both shoulders and leaves the relaxed forearms
slightly apart. It is a programmatic framing hypothesis, not detected joints.
Transparent foreground bounds or a conservative white-background estimate set its
scale; this assumes head-to-upper-leg framing. It is not a general anatomical
normalizer. The prompt explicitly requests a straight-on face, chest and pelvis,
neutral expression, both visible shoulders, uncrossed arms and visible hands,
while retaining character identity, clothing design, hairstyle and illustration
style. It allows the pose-related reconstruction necessary for a frontal view.

`canonical_pose.py` contains the exact prompt/guide definition. Every saved plan
contains the full prompt, negative prompt, five seeds, frozen preset and input
hashes. The first preset's negative prompt is empty. Additional named presets
provide a skeleton guide or empty initialization; selecting one is an explicit
configuration change between batches, not random variation within a batch.

`backends/inpainting/pose_reference_worker.py` is a separate opt-in worker. It
retains the historical pose worker and guide files unchanged, preserving existing
producer pins. The same unchanged `models.lock.json` and isolated frozen Qwen uv
environment pin model revisions, weight hashes, ComfyUI and GGUF sources. See the
[Phase 4B.7b audit](phase4b7b-generation.md) for exact local paths, licenses and
internal vision/VAE reference resampling. Per-image reports record reference count,
shapes, settings, output dimensions, image hashes, time and Torch CUDA peaks.
No models, custom nodes or global packages were installed for this stage.

## Frozen working-reference contract

The selected payloads are copied into `RUN/canonical/CANDIDATE-ID/`:

- `original.png`: exact original bytes and original source rights/hash.
- `canonical.png`: exact human-selected generated image, explicitly synthetic.
- `manifest.json`: separate original/canonical hashes, human decision, seed,
  prompt, guide hash, settings, producer pins and limited acceptance scope.

Payloads and manifest are made read-only. `review.json` binds the manifest hash
to the persisted approval. Reopening verifies those bindings. An interrupted
freeze can be completed idempotently after the approval was saved; an orphan
folder without the persisted approval cannot be used as a working reference.
Changed payloads or conflicting manifests are rejected, not silently overwritten.
This is application-level immutability with hash verification, not root-proof
storage. The reference name is separate from the frozen accepted Codel runtime.

Review acceptance means “use this synthetic frontal working base.” It does not
prove reconstructed anatomy, joint positions, exact hidden clothing, general
conversion quality or production readiness.

## Explicit downstream preparation

After approval, a separate opt-in initialization can prepare a future helper run:

```zsh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/pose_reviewer.py init-from-canonical \
  --canonical-run runs/NEW-canonical --output runs/NEW-canonical-helpers \
  --presets recipes/pose-review-presets.json
```

This command verifies the approved freeze and copies its canonical image as the
primary geometry input and its original image as the identity/style reference.
It creates no candidate images and launches no GPU job. Future helper plans bind:

| Input | Role |
|---|---|
| Picture 1 | Approved synthetic canonical base; primary pose/geometry |
| Picture 2 | Desired helper pose guide built in the frontal frame |
| Picture 3 | Original artwork; identity, face, outfit and style |

All three hashes and the canonical provenance are retained in the plan. The
optional reference worker routes the original to `image3` and checks the actual
reference count. CPU tests verify preparation and input roles; three-image helper
inference and its visual fidelity are **not evaluated in Phase 4B.8**. No existing
creation run is migrated and no helper poses or final arm rig are generated here.

## Evaluation

Human review covers recognizability, outfit/style fidelity, front-facing
readability, visible shoulders, arm separation and neutral expression. Development
assessment must remain separate from that approval. The existing selected-only
comparison scripts may produce source/canonical overlays and SAM proposals after
approval. Components and generated pixels remain uncertain evidence, not joints.
Compare against the original and the earlier approved auxiliary as distinct
baselines; do not relabel old measurements or accept a merely symmetric redraw.

Run the Python regression suite, both existing JavaScript suites, and the synthetic
canonical browser scenario. GPU inference is not required for ordinary tests.
No final arm rigging, production deployment or automatic downstream migration is
part of this phase.
