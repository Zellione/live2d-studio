# Phase 4B.3 — rig-aware facial transitions

Continued from `ca66737`. The optional aligned authoring method eliminates the
previous Qwen loop near **0.1 eye openness** in the inspected Sara comparison.
Deterministic lashes also remain visible through near-closure, and the sparse-source
mouth opens more evenly. These are limited candidate improvements, not new user
acceptance, anatomical truth or a production-quality conversion claim.

Validated implementation milestone: `f00b177`.

[Implementation and reproduction](phase4b3-transition-quality.md) ·
[benchmark](benchmarks/phase4b3.json).
Local review entry point: `runs/phase4b3-review-final/index.html`.

## Results by strategy

| Strategy | Sara assessment | Girl2 assessment |
| --- | --- | --- |
| Deterministic artwork, aligned motion | Better near-closed lash continuity and a more even cavity opening; open and neutral appearance preserved. | Improved near-closed lash visibility and reduced early iris ghost. Existing open-source mouth retained. |
| Existing Qwen closed lashes, aligned motion | The old separated loop is removed. Curved lashes can now be inspected through a complete transition; style and concealed-skin assumptions remain uncertain. Deterministic mouth retained. | Geometry alignment cannot fix the generated lashes' different density/style. Keep deterministic artwork as the conservative selection. |
| Deterministic contours with existing Qwen concealed skin | Temporal motion works, but the skin patch adds no established benefit and changes neutral shading. Reject the extra neural skin. | No forced neural-skin substitution. Deterministic regression remains independent. |
| Existing Qwen cavity | Shading still reduces the apparent mouth opening. Keep the deterministic cavity despite valid scaling. | Existing open-mouth branch is unchanged. |

Neural artwork is not promoted or automatically enabled. Deterministic remains the
artwork default; `--facial-motion aligned` explicitly enables the reviewed algorithm
for a new candidate. Legacy motion remains available and is the default pending
character-specific visual review. Accepted Phase 3/3.1 Girl2 and limited Phase 4B.1
Sara projects remain frozen.

## Evidence and limits

Each completed full suite renders 401 frames in the actual installed Cubism Core:
twelve dense opening values, complete closing/reopening cycles, seven expressions,
head/blink/talk combinations, authored idle blinks and exact neutral restoration.
Source/alternative keyforms, topology, draw order, clipping and parent ancestry are
retained with each editable MCP project. PSDs, project files, runtime exports,
contact sheets and short GIF recordings remain local.

The five final candidates each pass **401 rendered poses and 72 exported-Core
channel/triangle samples**. All 130 Python tests and five JavaScript tests pass.
Final deterministic and Qwen-eye neutral frames differ from their respective
baselines in **zero pixels**; the rejected skin-only candidate changes **933**.
Girl2's 36 mouth/smile/frown frames are byte-identical to its baseline in both
final eye candidates. The comparison collector revalidated 41 accepted Phase
3/3.1 files and every frozen Phase 4B.1 and rejected Phase 4B.2 stage inventory.

Maximum measured holes/detached pixels stay at **2,713/85 for Sara** and **146/3
for Girl2**, equal to their matched baseline maxima in this suite. All final
audits have zero visible eye-triangle reversals at the sampled poses, nonfinite
vertices and out-of-tolerance opacity. Native invisible-key fold/collapse warnings
are retained; this does not mean every hidden triangle is unflipped. Sara's
deterministic mouth-cycle maximum mean absolute frame change falls from 0.2016 to
0.1726 on the retained face crop. Eye metrics are mixed, so no universal numerical
smoothness or naturalness improvement is claimed.

The final benchmark distinguishes structural/numerical checks from development
visual assessment. It records source preservation, neutral differences, holes,
detached pixels, opacity excursions, actual parameter samples, Core channel audits
and temporal image-change metrics. Finite geometry or lower frame differences do
not establish natural movement. Existing head/hair limitations remain visible.
No blinded artist evaluation or new user approval was performed.

The original source rasters and frozen stage inventories are verified unchanged.
New rigging moves source samples at runtime; it does not claim pixel equality for
animated poses. Final deterministic/Qwen-eye neutral equality and the skin-only
neutral difference are measured separately in the benchmark. Previously pinned
model files, environments and accepted package pins are unchanged. This phase
performed no model downloads, neural inference, training or system changes.

## Retained negative experiments

All `runs/phase4b3-*` directories remain. Initial fits fragmented the deterministic
stroke and extrapolated a bent contour; holding overly squashed geometry caused a
near-disappearing lash at .15. Moving both curves fixed alignment, but a symmetric
alpha crossfade still lost contrast. An exported Core audit then found a small
visible reversed source triangle at .05 in a Qwen candidate. The final handoff
keeps that source hidden until it unfolds while the replacement remains visible.
Native warnings on invisible squashed geometry remain documented.

The failed static/default-key authoring attempt, initial output-directory misuse,
sandbox refusal, first browser pixel-read bug, and oversized CDP transfers are
preserved. Fresh runs correct these issues; no acceptance threshold or previous
result was rewritten. Girl2's neural style failure and the Qwen cavity/skin
rejections remain separate from the improved contour correspondence.

No production SillyTavern files were modified. Stop after Phase 4B.3.
