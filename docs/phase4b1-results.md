# Phase 4B.1 — source-aware facial reconstruction

Continued from 3e120c8. **Sara has a visibly improved single-image facial candidate.**
The user reviewed the before/after gallery and explicitly selected **“Accept limited
visual improvement.”** This is acceptance of the limited eyes/mouth/expression
improvement, not professional quality, anatomical ground truth, general-purpose
conversion or production deployment. Development checks of head poses, components
and source limbs are identified separately in the immutable review record.

The accepted local run is runs/phase4b1-sara. Open it with:

    uv run --frozen live2d-studio preview-live --run runs/phase4b1-sara

[Implementation and reproduction](phase4b1-facial-artwork.md),
[benchmark](benchmarks/phase4b1.json). The final local comparison is
runs/phase4b1-review-complete/index.html; the exact gallery reviewed by the user is
runs/phase4b1-review-candidate/index.html. Earlier failed candidates remain intact.

## Diagnosed causes

| Defect | Evidence and cause | Treatment |
| --- | --- | --- |
| Ghost eye contours | Restored face contained pale eye-shaped remnants and holes; source-owned face pixels remained within moving feature support. | Transfer 440 left / 428 right source samples to the eye assembly; remove static ownership and add separately marked concealed skin. |
| Residual lower contour during closure | After ownership repair, the imported blink geometry still left the lower outline near its resting position. The defect appears with one eye parameter and no expression/head motion. | Contract the full source surface; use a generated closed lash, retaining original colour/thickness, over the final closure interval. |
| Missing lid skin and cut-boundary cracks | Source alpha is mostly 254, and earlier restoration cannot retain opaque generated backing beneath fractional source pixels. Independently triangulated coincident cut edges also leave seams. | Local source-colour interpolation, explicit generated backing, overlapping mesh borders; retain separate runtime fidelity measurements. |
| Nearly invisible mouth | Original restored mouth owned only 27 pixels in two disconnected fragments. Much of the contour was stationary face artwork. | Transfer 110 additional source samples, preserve a complete neutral contour and generate a modest visible cavity. |
| Pale lip artifacts after transfer | PSD2Live procedural lip generation interpreted skin-bearing contour patches poorly in the first reconstruction candidate. | Replace those drawables' rendering with explicit neutral/interior variants; preserve source assets and editable rig. |
| Existing eye order | Phase 4B already corrected white/iris/lash order. | Preserve that fix; no new character-specific reorder or coordinates. |
| Expressions | Defects occurred in independent blink/mouth controls before expression composition. | Preserve generic expression/head architecture; new facial meshes inherit inspected parents and existing smile/frown. |

The current local See-through output, restored layers, saved project inspections,
MCP transcripts and actual browser frames support these distinctions. The face
sheets and failed renders are in runs/phase4b1-diagnosis and the retained stage
history. No inference rerun was necessary.

## Implemented application change

The existing facial stage now emits reproducible prepared artwork instead of only
a plan. New modules facial_artwork.py and facial_authoring.py use semantic masks,
local source colour, connected lash components and inspected rig ancestry. They
contain no Sara/Girl2 hashes, canvas coordinates, opaque asset IDs or skin palette.
Generated alternatives carry hashes, source/generation distinctions and uncertainty.

The standalone CLI installs real editable raster layers, writes actual mesh keys,
authors expressions/motion, exports MOC3 and validates in the standalone viewer.
Codex remains a development agent, not a runtime dependency. Existing semantic and
visual gates, locks, stage manifests, cache integrity and deployment restrictions
remain in place. Source inputs, earlier accepted projects and package recipes are
not modified. No painting, GPU inference, model weights, host settings, production
SillyTavern or cloud image processing was required for this phase.

A Girl2 regression caught an important limitation: applying the sparse closed-source
mouth variant to its already-open artwork made its opening range worse. The final
strategy retains PSD2Live's existing mouth treatment for substantial tall source
mouths. That decision derives from relative geometry/observed occupancy, not the
character name. Sara's facial output remains byte-identical after this branch fix.
The accepted Sara run stays frozen; future code changes are not silently applied.

## Rendered evidence and acceptance limits

A fresh baseline run of the preserved Phase 4B Sara export and the candidate each
render **57 matched poses**. This includes openness 0/.25/.5/.75/1 for both eyes
and the mouth; smile/frown; all seven expressions with the head locked; talking;
head/gaze controls; combined head/blink/mouth poses; and neutral restoration.
Additional time-sampled talking/fade/ramp evidence uses the same frozen candidate.
That separate run contains 122 captures, varying mouth envelopes during all seven
expressions and exact returns to neutral. Geometry/opacity remain within the
unchanged validity tolerance; 17 strict float32 opacity excursions are retained.

| Measurement, matched 57-pose suite | Phase 4B | Phase 4B.1 Sara |
| --- | ---: | ---: |
| Original observed-layer exact foreground | 99.7713% | 99.7713% |
| Neutral enclosed transparent pixels | 413 | 102 |
| Maximum enclosed transparent pixels | 4644 | 4357 |
| Maximum small detached pixels | 85 | 79 |
| Nonfinite geometry / opacity beyond existing tolerance | 0 / 0 | 0 / 0 |
| External requests / resource failures | 0 / 0 | 0 / 0 |
| Strict opacity excursions | 208 | 184 |

The float32 maximum is 1.0000001192 for both matched runs. Raw excursions are kept;
the existing eight-ULP tolerance is unchanged. Counts depend on sampling time.
Hole/component counts include legitimate hair/details and are warnings, not visual
acceptance thresholds. Existing head/hair limitations remain visible.

Original-source mask fidelity and final compositing are different measurements.
The new neutral render differs from the old one in 13,417 pixels, with mean absolute
RGBA difference 0.2410/255 over the full canvas. New opaque hidden backing changes
fractional-alpha compositing, mesh edges and mouth treatment. Neither runtime-neutral
byte equality nor preservation of every final rendered pixel is claimed. Original
input files and observed RGBA remain exact and uniquely owned in the manifest.

The user accepted the visible improvement after inspecting the gallery. Closed
eyes now have a coherent source-derived lash and skin, and opening produces a
visible mouth. The interior remains a simple dark cavity; intermediate lids and
expression transitions are stylized. No teeth/tongue, verified concealed anatomy,
phonemes or full-body reconstruction is claimed. The source's other expression
tiles were evaluation references only. No multi-reference experiment is included.

## Local model assessment

The deterministic repair addresses identified ownership/deformation failures; a
larger image model would not by itself fix incorrect rig keys or draw order.
A local inpainting/editing model could plausibly improve shaded eyelid skin,
closed-lash curvature and lip transitions. This is an inference from capabilities,
**not a demonstrated improvement on Sara**. Neither candidate was downloaded/run.
Public revision/license/file-size metadata was inspected with hf-cli, using no token.

- [SDXL inpainting 0.1](https://huggingface.co/diffusers/stable-diffusion-xl-1.0-inpainting-0.1):
  revision 115134f363124c53c7d878647567d04daf26e41e, OpenRAIL++ license; selected FP16
  UNet, two text encoders and VAE total 6,938,041,649 bytes. Its documented pipeline
  supports masked 1024px inpainting. The 32 GB GPU is a plausible target with room
  beyond weight storage, but actual activation memory, speed and fidelity are
  unmeasured. Use a separate pinned environment and preserve source outside the mask.
- [Qwen Image Edit 2509](https://huggingface.co/Qwen/Qwen-Image-Edit-2509):
  revision d3968ef930e841f4c73640fb8afa3b306a78167e, Apache-2.0; BF16 transformer,
  text encoder and VAE safetensors total 57,699,249,798 bytes. Transformer weights
  alone exceed 32 GB, so the documented full-resident setup is unsuitable here.
  CPU offload or separately reviewed quantization would be needed; no 5090 fit or
  pixel-preserving alpha output is promised. Its multi-image capability must remain
  separately labelled if used in a future experiment.

Existing pinned LayerDiff/SAM weights remain unchanged. Other ComfyUI model files
were not loaded: filename presence alone does not establish revision/license or
suitability. No new download is needed to reproduce the delivered deterministic path.

## Verification and preserved references

**117 Python tests and 5 JavaScript talk tests pass.** The five new facial tests cover fractional and opaque source preservation, unique
ownership, replay, translated geometry, nonstandard skin colour, insufficient
samples/lash evidence and retention of already-open mouth artwork. Full Python
regressions and existing JavaScript talking tests are run after implementation;
final logs and additional runtime evidence are recorded in the benchmark.

Cached Girl1, Boy1, Boy2 and Wikipe-tan negative cases remain rejected/blocked with
unchanged semantic/source metrics. Hachi failures are retained unchanged. Fresh
Girl2 candidates are isolated in runs/phase4b1-girl2; the failed mouth experiment is
retained in its history. Accepted Phase 3/3.1, Golden Fixtures and package pins
remain immutable and are not replaced by the regression candidate.
The corrected Girl2 candidate passes 57 actual rendered poses, with zero nonfinite
vertices or out-of-tolerance opacity, maximum 267 enclosed transparent pixels and
4 small detached pixels. This is development regression evidence, not new user
approval of Girl2 artwork. All 41 recorded editable/runtime reference-file hashes
from the accepted Phase 3 and Phase 3.1 pins were verified unchanged.

Rebuild the complete local gallery and supplementary evidence after the render runs:

    uv run --frozen python scripts/phase4b1_compare.py \
      --output runs/NEW-gallery --benchmark runs/NEW-gallery/benchmark.json
    uv run --frozen python scripts/phase4b1_evidence.py \
      --gallery runs/NEW-gallery --benchmark runs/NEW-gallery/benchmark.json

The supplementary collector verifies accepted reference hashes and reads the
retained passing test logs; it does not infer test success from motion metrics.

The code, tests, model/art provenance and concise report are versioned. Generated
artwork, browser data, PSDs, projects, runtime exports and raw evidence remain
outside Git. Stop after Phase 4B.1; no production deployment or training is included.
