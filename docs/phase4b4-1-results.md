# Phase 4B.4.1 — mouth redesign candidate

Continued from `889faf1`. The user's rejection of Phase 4B.4 legibility is retained:
the old mouth system was insufficient, including its preserved Happy/Sad/Surprised
poses. This candidate replaces the competing mouth fields with coordinated
source-contour and cavity shapes. **It awaits explicit user visual review and is
not promoted.** No eyebrow/eye exaggeration or new raster artwork was used.

[Design, diagnosis and reproduction](phase4b4-1-mouth-design.md) ·
[benchmark](benchmarks/phase4b4-1.json).

- Mouth-only review: `runs/phase4b4-1-review-release/mouth-only.html`.
- Complete expressions: `runs/phase4b4-1-review-release/full-expressions.html`.
- All comparisons: `runs/phase4b4-1-review-release/index.html`.
- Editable candidate: `runs/phase4b4-1-sara-v4/authoring/character.psd2live`.
- Preserved PSD/project and Cubism bundle: `runs/phase4b4-1-sara-v4/export/`.

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio preview-live \
  --model runs/phase4b4-1-sara-v4/export/runtime/Generated_artwork.model3.json \
  --port 8785 --no-open
```

Select **Mouth only** to compare settled mouths with neutral eyes, brows, gaze,
head and blush. Uncheck it to inspect full expressions. Leave comparison mode to
try talking, blinking and head motion. Original models remain available unchanged.

## Development visual assessment

These are observations of the actual rendered candidate, not user acceptance or a
machine recognition score. The gallery exposes both successes and remaining limits.

| Pose | Mouth-only observation |
| --- | --- |
| Neutral | Original recognizable resting smile and centre gap retained exactly. |
| Happy | Fuller curved opening with visibly raised corners; much less like the old thin horizontal opening. The cavity is still a simple dark fill. |
| Sad | Closed soft frown with lowered corners; the baked smile is removed. |
| Angry | Tense, compressed, nearly horizontal seam. It avoids the rounded sorrowful frown used by the old Angry pose. |
| Confused | Small parted oval, in the same shape family as Surprised; no friendly smile or sad frown. Whether it reads specifically as questioning remains a user judgment. |
| Surprised | Larger vertical oval with no smiling curvature. |
| Embarrassed | Narrower closed asymmetric smile, distinct from Happy's open smile. Blush remains an additional cue; perceived shyness still requires user review. |

All seven mouths were inspected with head X/Y/Z zero and identical non-mouth
channels. Pair sheets isolate Happy/Sad, Sad/Angry, Confused/Surprised and
Happy/Embarrassed. The opening sheets show emotional shape from 0 through 1.
Talking returns to each expression's own rest, rather than resetting to neutral.

The first revised candidate still had a thin Happy and weak Embarrassed mouth.
A second refinement improved those rests, but opening-sheet inspection exposed
accumulated source-corner deformation in Sad near .05/.1. It was rejected and
corrected with independent rest-derived keys and no opening geometry on the source
seam. The corrected sheets show a continuous handoff without that doubled/splayed
contour. Earlier candidates and diagnostics remain in `runs/phase4b4-1-*`.

## Validation and preservation

- **137 Python tests and five JavaScript tests pass.**
- Dedicated final comparison: **213 captures**, all seven mouth-only/full poses,
  eight explicit opening levels, talking, blink/head combinations, rapid switching,
  exact returns, and actual mouth-only UI controls. Parameter bounds are checked
  throughout, including rapid fades.
- Sara and preserved Girl2 each pass the unchanged **401-frame** dense transition
  suite and **72-sample** exported eye-channel/visible-triangle audit.
- **819 exported Core samples** cover seven expressions at rest and twelve combined
  blink/talk levels, neutral head and all eight ±X/±Y/±Z combinations. Zero visible
  mouth-triangle reversals, nonfinite vertices or out-of-tolerance opacity;
  exact neutral geometry return. The source-seam opening-invariance check passes.
- The revised neutral render differs from Phase 4B.4 in **zero pixels**.
  All **33 archived PNG assets**, including source mouth, cavity, backing and blush,
  are byte-identical. All **18 imported source layers** pass decoded RGBA checks.
- **41 accepted Phase 3/3.1 files**, frozen Phase 4B.1/4B.2/4B.3 inventories, and the
  full Phase 4B.4 predecessor inventory verify unchanged. Girl2's MOC is unchanged.
  Golden fixtures, package pins, locks and neural inference code are unchanged.
- Dense maximum holes/detached-pixel counts remain **2,713/85 for Sara** and
  **146/3 for Girl2**, equal to the earlier maxima. These are diagnostics, not
  visual acceptance scores. Strict float32 opacity excursions remain recorded;
  the maximum is `1.0000004768371582` and the existing tolerance is unchanged.

The old `ParamMouthForm` -1/0/1 comparison changes zero pixels because it belongs
to hidden importer mouth meshes. The visible alternatives now use source-aware
curve, roundness, tension, width, skew and independent opening. No source image,
observed mask, model weight, production SillyTavern file or deployment rule changed.
No downloads, inference, training, system changes or new runtime dependency occurred.

## Limits and review gate

This remains a stylized low-resolution mouth with a source centre gap and a plain
cavity. It has no teeth, tongue, phonemes or reconstructed anatomy. Brow/eye style,
flat lashes, uncertain concealed skin and head/hair gaps remain. Wide talking
openings naturally reduce some distinctions; the bounded shape fields and emotional
rest persist. The tested sparse-source branch is not a universal character converter.

Rendered inspection supports presenting this candidate for review, but cannot
establish immediately recognizable emotions for the user. Inspect the mouth-only
comparisons first, then complete expressions and talking in the preview. No
automatic adoption or production deployment is authorized. Stop after Phase 4B.4.1.
