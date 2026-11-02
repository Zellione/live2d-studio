# Phase 3 — Girl2 expressions and roleplay integration

Completed 2026-11-02, starting from `addd895`. **Girl2 now supports visibly distinct
stylized expressions, blinking, subtle idle and actual message-driven talking in
an isolated SillyTavern instance.** Complete RP acceptance uses an optional,
explicitly isolated extension adapter. The unmodified upstream path remains
available and its demonstrated failure is documented. No production deployment.

## Deliverables and reproducibility

- Editable project: `runs/phase3-final/character.psd2live`.
- Matching layered PSD: `runs/phase3-final/character.psd`.
- Complete portable runtime, expression/motion assets and mapping preset:
  `runs/phase3-final/runtime/`. Unpackaged editor export: `export/` beside it.
- Local visual review: `runs/phase3-review/index.html`; full controlled pose sheet:
  `runs/phase3-final-expression-review/poses.png`.
- Reproducible authoring: `scripts/build_phase3.py`,
  `recipes/girl2-animation.json`, [animation guide](phase3-animation.md).
- Actual integration procedure and optional patch:
  [SillyTavern report](phase3-sillytavern.md).
- Concise measurements: [benchmark JSON](benchmarks/phase3.json).

The 51-test baseline, bundle validation, actual Core probe and previous 21-pose
browser test were reproduced before authoring. Current editor state was preserved
in a separate snapshot. All working/export directories are new; no accepted export
or golden fixture was overwritten. Authoring and the full replay use authenticated
connected MCP. The separate CLI still needs an explicitly supplied local token;
no profile secrets were read.

The full 59-operation recipe was replayed from the accepted Phase 2.6 project,
then saved, PSD-exported, reopened and runtime-exported. All runtime-consumed
files, expressions, motions and portable settings match the preceding tested
build byte-for-byte. 21/23 packaged files match across full authoring replay;
CMO3/CAN3 editor containers differ. A separate packaging-only repeat matches 23/23.
Do not mistake these distinctions for universal archive reproducibility.

Milestones: `4a7b4e0` animation recipe; `bd76462` actual RP tests/isolated fixes.
No neural inference, additional models, dependencies, system changes or manual
painting were needed. Browser tests use installed Core 5.0.0 and software WebGL;
no new GPU inference/runtime performance claim is made.

## Expressions, eyes and mouth

Seven authored expressions: neutral, happy, sad, angry, surprised, confused,
embarrassed. A new `ParamBrowMood` axis changes brow inclination at all existing
head/lean combinations. Existing brow height, mouth form, eye openness and small
head offsets supply the remaining channels. The first brow direction looked wrong
in rendered frames and was reversed before acceptance; failed previews are retained.

Expressions use additive parameters and multiplicative eye openness, 0.45 s fades.
Neutral restores zero offsets and identity eye factors. Happy and surprise have
intentional small resting-mouth offsets, 0.1 and 0.3; neutral closes fully. Blinking
reaches zero with every expression active; talking still changes mouth opening.
No blush, teeth, tongue, skin eyelid or anatomically unsupported alternate raster
was invented. Happy/surprise are relatively subtle; embarrassment is a shy tilted,
lowered-eye pose rather than a detailed blushing expression.

Actual changed pixels against controlled neutral: happy 1,563; sad 1,493;
angry 1,892; surprise 690; confused 20,380; embarrassed 20,388. The last two include
head tilt, so their larger counts do **not** establish stronger facial expression.
Visual face crops were reviewed separately. Neutral restoration changes zero pixels.

The controlled review includes 42 frame labels: expressions and combinations,
independent left/right closure, eyes/mouth at 0/.25/.5/.75/1, individual X/Y/Z ±15°,
combined head/blink/mouth stress poses and neutral restoration. Some neutral states
are intentionally repeated; this is not a claim of 42 unique anatomical poses.
Core geometry remains finite and eye deformation remains independently addressable.

Lid/corner tuning and temporal blink timing were evaluated. Intermediate lids remain
flat/simplified; the tuning does not replace missing skin-lid art. Existing procedural
mouth shapes remain preferable to inventing unsupported lip/teeth artwork. The new
text-talk adapter uses smooth frame-aligned curves, not phoneme or audio analysis.

## Source preservation and hair

The original 99.89% visible-RGBA preservation is inherited from unchanged refined
layers, not re-estimated from browser frames. The runtime texture SHA-256 is
unchanged, the exported layered PSD is byte-identical to Phase 2.6, and the controlled
neutral browser RGBA is exactly identical to the Phase 2.6 reference. Runtime
resting mouth is closed by rig design; the source illustration's mouth is open.

Hair motion now follows head roll more closely with lower sway/curl/perspective.
No generated guard pixels or new hidden-anatomy claims. Matching stress-pose maximum
enclosed transparency decreases **502→349 pixels**; maximum small detached-component
pixels remains **3**. Gaps are reduced, not eliminated. Actual comparison frames
show no new floating tips or duplicate source outlines; source contour ownership
from Phase 2.6 remains intact. Existing legitimate hair gaps contribute to counts.

## Actual SillyTavern RP results

Installed ST `8172dcd0`, extension `d1801d36`, PSD2Live 3.6.7. The actual ST chat
render/event path triggers `index.js` → classifier fetch → mapping/expression and
`playMessage` → `playTalk`. Messages are synthetic assistant test replies. Only
classifier network responses are mocked; no classifier-model inference is claimed.

- All seven emotion categories resolve to the expected expression; applied brow/
  mouth-form values are checked after blending, with actual rendered changes.
  The preset maps all 28 installed labels, including aliases such as amusement→happy.
- Short/long messages produce mouth movement and recover to the appropriate rest.
  The neutral post-talk sample has mouth value zero. Actual mouth/lip geometry
  determines a canvas ROI, where successive talk frames visibly change; detailed
  counts and the final ROI are retained in the benchmark JSON.
- Idle contains gentle head/body/breath curves and occasional/double blinks. The
  authored ±2° X range is retained with the optional adapter. Talking, sad/happy/
  angry transitions and blinking coexist. Nod finishes and Idle resumes.
- Interruption, reload during talking and character change release old talk sessions;
  new messages work after returning. A delayed old joy classification cannot
  replace the newer anger expression or restart obsolete speech.
- Offline, HTTP-503 and unknown-label handling restore a neutral fallback through
  the optional adapter. The HTTP failure and delayed-response cases are tested;
  unknown-label behavior is the same guarded mapping fallback, not a separate
  classifier-inference experiment.

The unmodified extension can render/talk, but HTTP failure leaves an undefined
mapping and produces caught listener errors. Its runtime also adds fixed-amplitude
head movement beyond the authored idle. These are demonstrated reasons for the
optional isolated adapter. It additionally improves talk smoothness and uses the
runtime's expression-preservation setting for explicit motions. `force_loop=false`
and `force_animation=false` avoid unwanted repeated motions/model reloads.

## Separate acceptance gates and limitations

| Gate | Result |
| --- | --- |
| Semantic correctness | Inherited Girl2 coarse acceptance; no new parsing claim |
| Original-art preservation | Accepted: unchanged source layers, texture, PSD and runtime neutral |
| Hidden geometry | Reviewed but incomplete; residual hair/face gaps |
| PSD2Live import/export | Accepted, saved/reopened final project and portable bundle |
| Runtime geometry | Accepted; finite geometry, independent eyes, valid parameter ranges |
| Visual animation | Limited RP prototype accepted; flat lids and subtle shapes remain |
| RP integration | Accepted with optional isolated adapter and mocked classifier responses |
| Production readiness | Not granted; production installation unchanged |

Dynamic Cubism interpolation occasionally reports opacity a few float32 ULPs above
1. Strict raw excursion counts/min/max remain in evidence; invalid numeric opacity
uses an eight-float32-ULP precision tolerance. This changes no rendered values,
geometry limits or aesthetic thresholds. Phase 0/1 tests retain their original checks.
The first diagnostic runs and upstream caught-error failure remain locally available.

59 Python regression tests and five JavaScript controller tests pass. Actual
Phase-0/1 browser goldens pass against a separate unmodified extension copy. Golden
fixtures, earlier benchmark JSON, deterministic baseline, dependency/model locks
and original Girl2 inputs are unchanged. 137 original production code hashes match
their pre-test snapshot. Isolated test servers/browser were stopped; the saved
final editor project remains open. All artifacts/transcripts remain ignored under `runs/`.

No manual image editing was required; visual judgement is still necessary. Further
work should address real lid skin, concealed hair/face support, stronger expressive
mouth geometry and upstreaming the small lifecycle fixes. Do not generalize this
Girl2 recipe to arbitrary characters or call it professional VTuber quality.
**Stopped after Phase 3; no Phase 4, custom training or production automation.**
