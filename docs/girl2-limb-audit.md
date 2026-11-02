# Girl2 visible-limb audit — 2026-11-02

**No visible arm artwork was lost.** Girl2 already has sleeve ends with no
forearms or hands in the original XCF. Both clothed shoulders/upper-arm silhouettes,
both short sleeves and the exposed collarbone/upper chest survive into Phase 3.
This is a source-incomplete upper-body portrait, not a complete anatomical rig.
No arms were generated and no accepted assets were changed. Phase 4 has not begun.

Local [comparison sheet](../runs/girl2-limb-audit-final/comparison.png),
[gallery](../runs/girl2-limb-audit-final/index.html),
[all XCF leaves](../runs/girl2-limb-audit-final/xcf-all-leaves.png) and
[measurements/hashes](../runs/girl2-limb-audit-final/audit.json).

## Findings across stages

| Stage | Shoulders, sleeves, arms and hands |
| --- | --- |
| Original CC0 `NewAnime.xcf / Girl2` | `G2 Shirt` contains torso and both sleeves; `G2 Neck` contains neck and exposed upper chest. No bare forearms/hands. |
| Flattened `phase2-5-oga-ground-truth/flat.png` | Same silhouette and visible parts; neither sleeve was cropped away. |
| See-through decomposition | Both sleeves extracted as `handwear-r/l`, torso as `topwear`. Generated appearance differs; upper chest initially misassigned to clothing. No arm/hand artwork disappears because none exists below the sleeves. |
| Refined manifest | `st-01-handwear-left` and `st-03-handwear-right` retain sleeves, `st-05-topwear-none` retains torso; source pixels restored and most chest ownership repaired. |
| Final Phase 3 export/render | `ArtMeshHandwearL/R` and `ArtMeshTopwear` remain in export metadata; both sleeves and shoulder contours are visibly present in the actual retained Core/ST neutral frame. |

Side names in our manifest mean **image-left/right**, not anatomical left/right.
The original XCF combines sleeves with the shirt, but the final model does **not**
put all sleeve pixels into `topwear`. `handwear` here means the sleeve/arm category,
not evidence of hands. Separate sleeve meshes do not imply elbow/wrist/finger rigging.

Fresh GIMP 3.2.6 inspection found 15 leaf layers: ten visible, five hidden
eye/mouth variants. Every leaf was exported for visual inspection, including
hidden variants. None contains additional arms/hands. There are **zero
nontransparent pixels outside the 1000×1000 canvas in any Girl2 leaf**.
The complete flattened foreground bounds are `[178,90,751,919)`; sleeve ends
terminate well inside that canvas, with transparent space below them. Thus
“the arms are simply outside the canvas” is not supported: no off-canvas arm
content exists in this XCF, and these are not canvas-edge amputations. The
artist's intent beyond the supplied artwork is unknown.

## Measured preservation and limits

Independent XCF visible ownership was evaluated with alpha >127, frontmost
layer wins. This excludes faint antialiased edge samples from these counts.

| Source region | Evaluated pixels | Exact refined RGBA | Missing alpha pixels |
| --- | ---: | ---: | ---: |
| Shirt, including both sleeves | 131,509 | 131,509 (100%) | 0 |
| Neck/upper chest | 32,769 | 32,769 (100%) | 0 |

Shirt ownership: 13,358 pixels in left `handwear`, 13,039 in right `handwear`,
105,106 in `topwear`, six in back hair. Neck ownership: 32,289 in `neck`,
454 in `topwear`, 26 in back hair. These residual semantic mistakes remain;
exact neutral pixels do not establish correct deformation ownership.
The XCF has no independently separated sleeve GT, so no sleeve-specific IoU is claimed.

The fresh XCF projection exactly matches the retained GIMP projection. The
previously documented flattening difference is only 29 visible pixels differing
by one RGB level plus 24 transparent-RGB differences; alpha is unchanged.
Refined release layers match the accepted v2 rig-input RGBA hashes. Original XCF,
source, accepted Phase 2.6 project, final Phase 3 PSD/project/runtime and inspected
manifests/layers were hashed before and after: unchanged.

The comparison uses the **existing** `phase3-final-expressions/neutral.png` from
the successful actual Core/ST test, not a newly run browser test. Its alpha bounds
are cropped and isotropically scaled for display; this is not a source-grid pixel
comparison. The runtime's resting mouth is closed, unlike the source mouth.
Existing hair gaps/flat eyelids remain outside this limb audit's conclusion.

## Would future visible arms be preserved?

**Not guaranteed by the current pipeline.** The bridge forwards every emitted
layer and rejects >32 layers instead of silently truncating. It supports
`handwear`, image-side labels and generated/observed masks. But:

- The pinned See-through taxonomy conflates arms/hands/sleeves in `handwear`.
  Its component splitter keeps two selected components; extra detached parts
  can be lost. Overlapping or crossed arms cannot be validated by image side alone.
- Refinement restores pixels only where a generated owner exists or within a
  small gap radius (0.3% of the short dimension). An independently visible arm
  omitted by the neural backend can remain unassigned; it is not recovered by
  source preservation. High whole-image fidelity can hide a small missing hand.
- The deterministic baseline retains unclassified pixels as `unknown`, but
  does not provide anatomical arm parsing. Current readiness gates emphasize
  face/eyes/neck and do not require evidence for originally visible limbs.
- No complete independently visible arm/hand benchmark or limb deformation
  acceptance exists. Girl2 cannot establish that capability.

Code inspected: `seethrough.semantics/import_decomposition`,
`refinement.refine`, `manifest.artwork_request`, `readiness.analyze`, and pinned
upstream `common/utils/inference_utils.py:part_lr_split/label_lr_split`.

## Recommendations for Phase 4 — proposed, not implemented

Use framing and anatomical completeness as **separate** attributes:

| Input framing | Expected review scope |
| --- | --- |
| Portrait/bust | Head, neck, shoulders; preserve any visible hand/arm even if optional for the framing. Girl2: upper-body/bust, supplied without forearms/hands. |
| Half-body | Torso to approximately waist/hips; inventory each visible shoulder, upper arm, elbow, forearm and hand independently. |
| Full-body | Head through feet; also inventory thighs, knees, lower legs and feet. Occlusion can still make individual parts unverifiable. |

Record each side/part as `visible`, `partially-visible`, `occluded`,
`canvas-truncated`, `not-depicted`, or `uncertain`, with reviewed source evidence.
Do not infer absence from missing parser labels, or infer full-body completeness
from image dimensions. Track anatomical side separately from image side.

For every originally visible limb, retain a source mask and track its unique
pixel ownership through decomposition, refinement, import, export and rendering.
Report per-limb unassigned/lost pixels, alpha recall, exact RGBA/colour error,
semantic ownership, connectivity and silhouette differences; use independent GT
IoU where available. Unresolved source pixels should remain inspectable candidates
and block acceptance, rather than being silently dropped or merged into a rig.
Check full-canvas crops before display framing. Review neutral and combined-motion
renders for sleeve detachment, disappearing hands and doubled contours. Keep
**preserved**, **semantically separated**, and **independently animatable** distinct.
Add licensed half/full-body tests with raised/crossed arms and detached hand
components before claiming limb support. Missing source anatomy must be reported,
not automatically invented or required for portrait acceptance.

## Reproduce without editing accepted assets

Run from the repository; choose fresh output/profile paths if these already exist:

```sh
XCF_AUDIT_INPUT="$PWD/assets/references/oga-portraits/NewAnime.xcf" \
XCF_AUDIT_OUTPUT="$PWD/runs/girl2-limb-audit-xcf" \
GIMP3_DIRECTORY="$PWD/.cache/girl2-limb-audit-gimp" \
gimp --new-instance --no-interface --no-data --no-fonts --no-splash \
  --batch-interpreter=python-fu-eval \
  --batch="exec(open('scripts/audit_xcf_parts.py').read())" --quit
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/audit_girl2_limbs.py \
  --xcf-raw runs/girl2-limb-audit-xcf --output runs/girl2-limb-audit-final
```

Uses the existing local stevenburrow CC0 source/provenance; no downloads or new
dependencies. GIMP emitted an unrelated missing optional `gjs` plug-in warning;
the Python batch succeeded and its projection matched independently retained evidence.
59 Python regression tests and five JS controller tests pass. No pipeline or
model changes; generated comparisons/raw exports stay ignored under `runs/`.
