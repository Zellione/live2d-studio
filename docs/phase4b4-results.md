# Phase 4B.4 — emotion legibility candidate

Continued from `65c34e4`. Sara now has a fresh expression candidate with independently
inclined/raised brows, a source-aware displeased mouth, an asymmetric questioning
pose, and an independent procedural cheek tint. Development inspection finds the
three revised configurations more distinct at zero head angles. **User visual
acceptance remains pending; no candidate is promoted.**

[Authoring and reproduction](phase4b4-expressions.md) ·
[benchmark](benchmarks/phase4b4.json).
Local comparison: `runs/phase4b4-review-release/index.html`.
Editable candidate: `runs/phase4b4-sara-v6/authoring/character.psd2live`.
Exported PSD/project/runtime: `runs/phase4b4-sara-v6/export/`.

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio preview-live \
  --model runs/phase4b4-sara-v6/export/runtime/Generated_artwork.model3.json
```

Select **Compare expressions** to pause idle/talking and compare settled expressions
without blinking or head motion. Normal controls remain available when it is off.
The gallery contains matched close-up and normal-size sheets, with Neutral, Angry,
Confused and Embarrassed first. Full temporal comparison and sampled recordings
remain in `runs/phase4b4-review-final/transitions/`.

## Visual findings

| Expression | Development assessment at head X/Y/Z = 0 |
| --- | --- |
| Angry | Clearer mild displeasure: closed shallow frown, inner brow ends lowered/inward, eyes normally open. High brows over bangs limit forceful anger. |
| Confused | One raised brow, the other slightly lowered, asymmetric eye apertures and uncertain near-flat mouth. The friendly smile is removed. |
| Embarrassed | Softer eyes/brows, small shy smile and subtle cheek tint. Distinct from the frowning poses; Happy remains its closest comparison. |
| Neutral | Original friendly resting smile retained. It is not an affectless source face. |
| Happy | Existing open smile retained; no observed regression. |
| Sad | Existing behavior preserved. The source smile still weakens sadness; no broader Sad redesign is claimed. |
| Surprised | Existing large mouth opening preserved; no observed regression. |

These are development-agent judgments, tied to exact quality/gallery hashes in the
review record. There is no human recognition study or machine emotion score.
Character identity appears retained in the inspected stills and combined poses;
that does not establish professional animation quality or general conversion.
Blink/talk controls and neutral restoration are tested separately from legibility.

## Runtime and preservation

- **134 Python tests and 5 JavaScript tests pass.**
- Final controlled suite: **149 captures**, seven settled expressions, dense eye /
  mouth values in each, idle coexistence, rapid switching, comparison-button races,
  cancellation with Neutral/reset, and exact neutral returns.
- Sara and the preserved Girl2 each pass **401 rendered temporal samples** and
  **72 exported eye-channel/visible-triangle samples** from Phase 4B.3.
- Additional exported-Core audit: **756 expression/blink/talk/head combinations**,
  with zero visible reversals in edited brow, mouth and blush meshes, zero nonfinite
  vertices, zero out-of-tolerance opacity, and exact neutral geometry restoration.
- Strict float32 opacity excursions remain in raw reports; the existing eight-ULP
  tolerance is unchanged. Maximum sampled opacity is `1.0000004768371582`.
- Maximum hole/detached-pixel counts remain **2,713/85 for Sara** and **146/3 for
  Girl2**. These are diagnostic counts, not aesthetic acceptance thresholds.
- All **18 imported Sara source layers** remain exact in the editable archive.
  No observed masks or original rasters are changed. The generated tint is a separate
  provenance-bearing layer, invisible at neutral and attached to the face parent.
- Neutral, Happy, Sad and Surprised each differ from the matched predecessor in
  **one rendered pixel** after export. Their expression behavior is preserved;
  blanket runtime-byte/pixel equality is not claimed. Neutral return within the
  candidate is exact.
- **41 accepted Phase 3/3.1 reference hashes** and frozen Phase 4B.1 / Phase 4B.2 /
  Sara Phase 4B.3 stage inventories verify unchanged. Girl2's MOC is unchanged.
  Golden fixtures, accepted recipes, environment/model locks and deployment pins
  remain unchanged.

The actual installed Core 5.0.0 and PSD2Live 3.6.7 are used. Their recorded licenses
and Sara's CC-BY-3.0 attribution are retained in the benchmark/provenance references.
No new dependency, model download, image inference, training, system change or
production SillyTavern write occurred. The local browser suites make no classifier
or model-provider requests.

## Retained limitations and failed attempts

The first new candidate moved the brow strokes but remained insufficiently distinct.
A first mouth fit selected only one disconnected contour half and produced a slant;
the final fit uses bilateral support and bounded curvature. Initial source-offset,
existing-key and sandbox failures remain local. An inefficient canvas equality loop
timed out; the corrected harness reads once per comparison, with no gate weakened.
The initial gallery path typo and earlier render outputs remain available.

Sara's upper brow artwork is stylized over the bangs; the lower dark curves resemble
lid creases. A transient interpretation that the upper arcs were misparsed hair was
not established, and no semantic reassignment was made. Limited brow visibility,
simplified mouth cavity/lashes, existing hair gaps and uncertain concealed backing
remain. Blush placement is inferred from reviewed feature supports, not anatomical
truth. The optional mouth correction currently requires explicit reconstructed
neutral/cavity alternatives; unsupported inputs fail rather than being forced.

New code is in `emotion_authoring.py`, the optional experiment/render/comparison/
evidence helpers, the exported expression probe, and the viewer comparison control.
The generic five-channel default recipe remains available unchanged. Accepted Sara,
Girl2, model weights and package versions are preserved. Review the candidate before
any decision to adopt it. Stop after Phase 4B.4; no production deployment.
