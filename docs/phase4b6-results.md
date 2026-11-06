# Phase 4B.6 — body, head, hair and head gestures

Continued from `68e1d25`. **A separate Codel body-motion candidate is ready for
explicit user visual review.** It has a more visible coherent head, stronger
secondary hair response, a calm 16-second idle, breathing/body compensation, and
two head-only gestures. Arms remain on their shared body attachment. Nothing is
promoted or installed into production.

- Candidate: `runs/phase4b6-codel-v7/export/runtime/Generated_artwork.model3.json`.
- Editable project: `runs/phase4b6-codel-v7/authoring/character.psd2live`;
  corresponding PSD, exported project and diagnostics are in `export/`.
- [Interactive before/after viewer](http://127.0.0.1:8788/).
- [Local gallery and recordings](http://127.0.0.1:8791/), backed by
  `runs/phase4b6-review-release/index.html`.
- [Implementation/reproduction](phase4b6-body-rigging.md) and
  [benchmark](benchmarks/phase4b6.json).

## Diagnosis and measured change

The original model was not entirely unrigged. Its real head Z parent, body/breath
warps, separate front/back hair fields and physics3 all work in installed Cubism
Core 5.0.0. The viewer plays the exported idle correctly. Its head amplitudes are
small, and its XY face/hair response is uneven: the skull/hair barely follow the
facial turn. The implementation reuses those inspected ancestors and adds bounded
shared XY translation. It keeps the head pivot inside the original neck support.

At the viewer's 570-pixel whole-character framing, measured maximum displacement
of actual exported vertices is:

| Region / independent input | Original | Candidate |
| --- | ---: | ---: |
| Face, Head X ±12 | 1.97 px | 4.77 px |
| Front hair, Head X ±12 | 1.20 px | 4.01 px |
| Back hair, Head X ±12 | 0.25 px | 2.83 px |
| Face, Head Y ±8 | 2.11 px | 3.90 px |
| Front hair, Head Y ±8 | 0.62 px | 2.40 px |
| Back hair, Head Y ±8 | 0.21 px | 1.99 px |
| Face, Head Z ±5 | 7.31 px | 7.31 px |
| Face, complete idle capture | 3.41 px | 6.33 px |
| Topwear, complete idle capture | 2.63 px | 4.84 px |

The idle rows combine head, breathing and torso movement; they are not isolated
head-turn measurements or aesthetic scores. No CSS/canvas movement is used. The
head rotation fit recovers a pivot near normalized `(0.51529, 0.19756)` of the
source canvas and an actual -4.999999° Core-space rotation for Z=5, with a
0.000173-source-pixel maximum fit residual. Coordinates appear only in measured
evidence, not generic authoring code.

The 16-second idle has pauses, offset X/Y/Z timing, breathing and mild opposing
body movement. Hair uses the existing distinct Cubism pendulums with more visible
output gains. In the release test, front/back responses peak at approximately
0.353 / 0.442 on their ±1 channels after the head stops, then return to zero in
the final eight samples. Hair roots inherit head motion and the original pinned
fields; no new strands, textures or exaggerated continuous sway were introduced.

Separate 2.8-second `Nod` and `Question` groups move the head. The viewer preserves
expressions across motion starts, keeps talking/manual blinking active, and adds
a short automatic blink during a gesture while its idle blink clip is interrupted.
The gesture curves themselves contain no facial or limb channels. During both
recorded gestures, the selected mouth-expression value stays at 0.4 while mouth
opening varies and eyes still close. This is local text-talk simulation, not LLM
classification, phonemes or production SillyTavern integration.

## Arms and source preservation

Codel's crossed and hanging arms, hands and sleeves form one unsided handwear
component: 260,082 copied pixels, zero generated hidden pixels in that layer.
There are no reviewed shoulder/elbow/wrist partitions or concealed surfaces behind
the crossed arm and its torso/sleeve intersections. Existing SAM labels do not
supply that anatomical separation. The authoring report inventories the evidence
and uses an explicit static articulation fallback. Breathing may move this shared
attachment; it is **not independent arm or hand articulation**. No greeting hand
lift or shoulder-only shrug is claimed.

All 33 archived Codel artwork PNG hashes and all 20 imported source-layer RGBA
images are preserved. Candidate and original neutral renders are pixel-identical
at equal scale. The sealed Phase 4B.5 run verifies unchanged. Original artwork,
accepted Girl2/Sara projects, package pins and earlier failures remain immutable.
No See-through/SAM inference, new model download, training, production write or
host configuration change occurred.

## Separate test and visual outcomes

| Check | Codel | Girl2 regression | Sara regression |
| --- | --- | --- | --- |
| Broad actual Core, 496 independent/combined samples | Pass, 0 visible reversals | **Fail: 1,716 inherited lip reversals** | Pass, 0 visible reversals |
| Continuous body/idle/talk/gesture rendering | 476 final comparison frames, pass | 475 frames, pass | 475 frames, pass |
| Existing dense facial suite | 401 frames, pass | 401 frames, pass | 401 frames, pass |
| Existing eye-channel/triangle audit | 72 samples, pass | 72 samples, pass | 72 samples, pass |
| Exact neutral geometry/render return | Pass | Pass | Pass |
| User visual approval | Pending | Not requested/promoted | Not requested/promoted |

The body scenario measures actual vertices and rendered frames for independent
axes, complete idle, seven expressions with talking, gestures, hair settling,
control disabling and reload. The final Codel comparison records zero network
failures or external requests and a pixel-identical neutral after reload. Each
suite uses a fresh local server/browser profile, also exercising restart. Core
trajectory audits and real motion playback are distinct evidence; one cannot
replace the other.

**The aggregate portrait regression gate remains failed.** Girl2's upper and
lower generated lip meshes have the same 1,716 visible reversals in the predecessor
and candidate broad audits. They are not relabelled harmless or removed from the
sample set. Its eye audit and dense rendering pass separately. The runner returns
failure after collecting the independent render evidence.

Sara passes numeric geometry but retains significant source-boundary gaps in
combined poses. Its matched older/new dense suites have maximum enclosed-pixel
counts of 2,713 / 2,805. These are diagnostic counts, not anatomical accuracy or
visual acceptance. The new wider body suite reaches 3,362 enclosed pixels and
100 small-component pixels; it does not grant a clean portrait-body rig claim.
Both portrait candidates remain local diagnostics.

Codel's final sampled body poses reach 55 enclosed transparent pixels and three
small-component pixels. Close-ups identify the existing gap between a hair strand
and shoulder becoming enclosed as the head moves. The earlier baseline body suite
reached 46 enclosed pixels at a tilt. Selected Codel poses show no major new neck
tear, detached face/hair assembly, lost limb or broken clothing boundary. This is
a development assessment of selected frames, not exhaustive anatomical proof or
user acceptance of natural movement. The gallery retains close-ups and raw counts.

Inherited near-closed eye contours/shading, simplified lashes and plain mouth
cavity remain. Head X/Y are conservative 2D apparent movement, not a fully modeled
three-dimensional turn. Development review permits presenting this limited Codel
candidate for the user's assessment; it does not promote it.

All **142 Python tests**, **five JavaScript talk tests**, and **three existing
JavaScript source-contract audits** pass. Core/browser regressions above retain
the separate failed Girl2 gate. No threshold was relaxed. The existing eight-ULP
opacity policy remains: final Codel body capture records 1,125 strict excursions,
maximum 1.0000004768371582, with zero out-of-policy opacities or nonfinite vertices.

## Retained attempts and provenance

Early local failures include a sandboxed loopback/browser launch, a capture syntax
error, incorrect Bezier handle interpretation, a reserved generated-motion name,
and PSD2Live's dirty flag after saving custom clips. All diagnostic runs remain.
The v5 handle error and v6 vertical translation that partly cancelled the existing
nod are preserved; v7 fixes direction without changing neutral artwork. Reopening
saved projects uses verified archives and reversible history checkout, never
`discard_unsaved`. Earlier baseline scripts that captured full per-frame vertices
also remain; later reports keep compact displacement summaries.

Tools reuse existing pins: PSD2Live 3.6.7 (recorded GPL-3.0), installed proprietary
Cubism Core 5.0.0 with SHA-256
`942783587666a3a1bddea93afd349e26f798ed19dcd7a52449d0ae3322fcff7c`,
and the frozen uv environment. Existing FFmpeg n9.0.2 (GPL-3.0-or-later build)
encodes sampled browser frames into WebM using their measured intervals. No runtime
library is redistributed. Codel remains LisadiKaprio's CC BY 4.0 artwork; attribution
and source links appear in the gallery and existing provenance definition.

The evidence collector regenerates the local gallery from the preserved captures
and writes a benchmark summary. Use fresh destinations; `--measurements-only`
skips gallery media encoding:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/phase4b6_report.py \
  --output runs/phase4b6-review-rebuilt --benchmark runs/phase4b6-benchmark-rebuilt.json
```

Restart review in separate terminals:

```sh
python3 -m http.server 8791 --bind 127.0.0.1 --directory runs/phase4b6-review-release
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio preview-live \
  --model runs/phase4b6-codel-v7/export/runtime/Generated_artwork.model3.json \
  --compare-model runs/phase4b5-codel-full-first/stages/export-0547c939391c/runtime/Generated_artwork.model3.json \
  --port 8788 --no-open
```

Stop after Phase 4B.6. No production deployment or automatic visual acceptance.
