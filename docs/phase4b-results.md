# Phase 4B — reusable creation, independent visual acceptance blocked

Continued from 53ad920 with explicit authorization on 2026-11-03. **The local
application and generic authoring are implemented. Full Phase 4B acceptance is
not met:** Sara reaches an interactive preview without manually authored rig
operations, but its eyes/mouth fail visual review. Do not call it a usable finished
independent character. Production remains untouched and disabled.

Milestone 9581432 implements the first validated orchestration/authoring path.
The following milestone adds eye-order constraints, generic configuration, archive
fidelity, verified preview selection, independent benchmarks and rejection evidence.
See the [creation guide](phase4b-create.md), [benchmark](benchmarks/phase4b.json)
and local gallery at runs/phase4b-review-final/index.html.

## Application and runtime independence

    uv run --frozen live2d-studio create \
      --input character.png --output runs/character --rights 'Author; license; source'

Python orchestrates ingestion, offline See-through/SAM, semantic import, original
pixel restoration, readiness/review, procedural facial preparation, PSD2Live project
creation, generic rig authoring, expressions/idle, Cubism export, installed
Core/browser validation and preview. No coding agent is required at runtime.
PSD2Live remains a local authoring dependency; exported models/viewing need neither
MCP nor inference.

Each stage owns a fresh directory and content-hash checkpoint in creation.json.
Resume verifies outputs and skips completed stages. Changed source/rights require
a new run; code/profile changes invalidate relevant stages. Failures survive and
retry separately. Per-run locks prevent competing writers; authoring stages also
serialize shared-editor access. Current editor work is saved in a fresh snapshot,
never discarded. This is application recovery, not a power-loss durability claim.

Existing bridges/SAM masks can be reused after source/integrity validation.
Completed runs own their cache copies. A token-free sandbox replay of all twelve
Sara stages, omitting the earlier external SAM path, leaves every stage record
unchanged and preserves rejected-visual. GPU inference is not repeated to resume.

The user explicitly exported the MCP token through their zsh environment.
Standalone CLI authoring was exercised, not a connected-agent-tool replay. No token
value or profile secret store was inspected/logged. No new dependency/model
download, driver/system-CUDA change, training or hosted image processing occurred.

## Generic authoring and facial work

The builder inspects layer roles/sides, mesh ancestry, deformers, parameters and
actual key axes. Mouth/brow targets come from those associations. Ambiguous parents,
missing parameters and excessive key expansion are refused. The reusable
portrait_profile.json contains normalized curve strengths and modest idle
amplitudes, with no artwork hashes, opaque mesh IDs or canvas coordinates.
Recipes and inspected bindings are saved for each character.

Smile/frown and brow emotion use relative curve fields over all inspected
combination keys. Seven expressions and a twelve-second idle with blink/breathing
are authored against inspected ranges. Imported head/gaze/mouth/blink behavior uses
PSD2Live's procedural generator. Defaults are inspected and removed only in the new
project before adding expressions, avoiding case-insensitive name conflicts.

Sara exposed a depth-order defect: the left white was above the iris, so source
pupil pixels belonged to the white. The new semantic_order.py enforces white →
iris → lash within complete, unambiguous eye triplets; other slots remain unchanged.
Left iris observed ownership increases 49 → 350 pixels; right iris has 366.
Raw and initial restored results are retained. Girl2 order is already correct;
all 19 restored layer records still match accepted Phase 2.6 exactly. Neutral
source preservation alone did not reveal this ownership bug.

Facial artwork investigation remains **partial**:

- Procedural eyelash/white contraction and generated lips/interior are available,
  preserved in editable sources and exercised in real renders.
- Relative smile/frown and brow deformation work technically without repainting.
- Hidden face surfaces remain generated candidates, not independently known anatomy.
- No convincing generic eyelid-skin/intermediate-lid raster generator was completed.
  No teeth/tongue or phoneme system was invented.
- Optional blush is omitted; Girl2-specific cheek coordinates are not reused.
  The facial stage emits a plan; PSD2Live generates procedural alternatives during
  project creation.
- The available pinned LayerDiff/SAM models were tested on new inputs and fail some
  small mouths/face ownership. Source copying cannot repair missing artwork or
  disentangle every baked contour. No unreviewed model was downloaded.

Imported RGBA is checked against decoded PNG assets inside the saved project.
Archive assets remain unchanged through export preparation. This proves imported
layer preservation, including marked inferred pixels; original illustration
preservation remains a separate metric.

## Quality and independent benchmarks

Hard semantic gates check paired eye parts, face/mouth/neck, concealed eye support,
source/SAM consistency and at least 99.5% exact foreground/silhouette agreement.
These are conservative candidate rules, not calibrated semantic guarantees.
Hash-bound reviewer records are still required; hard failures cannot be approved
through the CLI. Visual review separately covers blink, mouth, head overlap,
head-locked expressions, holes/detached pieces/duplicate contours and visible limbs.

Clothing roles do not prove anatomy. Bilateral limb identification still requires
source review; no general automatic limb detector or verified hidden-anatomy
system is claimed. Explicit rejection is supported without manual painting.

| Input | Exact source foreground | Result |
| --- | ---: | --- |
| Girl2 regression | 99.886% | Fresh generic runtime passes; limited prototype, user visual review pending |
| Boy1 historical negative | 99.872% | Beard/brow rejection retained; no rig |
| Girl1 historical negative | 93.199% | Semantic/source gate blocks |
| Wikipe-tan historical negative | 77.159% | Face/neck/source gate blocks |
| Boy2, new CC0 portrait | 30.468% | Missing face/support; blocks before rigging |
| Hachi full body, independent artist | 99.112% | Missing mouth/face disagreement; blocks |
| Hachi recorded bust crop | 60.594% | Missing mouth/lost coverage; blocks |
| Sara, independent artist | 99.771% | Full CLI authoring/runtime; **visually rejected** |

XCF ground truth remains evaluation-only. Six-group mean visible IoU:
Girl2 **0.966665**, Girl1 **0.582639**, Boy1 **0.923733**, Boy2 **0.329776**.
Boy2's authored leaf composition differs from GIMP's cached projection; the defined
input is that retained leaf composition. Beard is a coarse hair group; these masks
cannot certify fine brow/eyelid ownership.

HachiStudio offers Hachi under CC0. Its full input is preserved, and the separate
crop explicitly excludes lower limbs without claiming to preserve them. Sara is
the neutral tile of RPG Action/ZeNeRIA29's CC-BY 3.0 portrait sheet. Attribution,
download/input hashes, crop/padding and alpha-only handling are pinned in
benchmarks/phase4b-art.json. Original sheets remain intact. Both crops reproduce
byte-for-byte using scripts/prepare_phase4b_art.py.

Sara's other expression tiles never enter inference. Independent part masks are
unavailable: no Sara semantic IoU or verified hidden-face score is invented.
Head ornament, braid, shoulders and upper arms survive; forearms, hands and lower
body are absent from the selected source tile. Hachi/Sara add artist variety, but
neither establishes accepted generalization. Two other downloaded portraits were
screened out before inference (large badge; patterned background and wink);
their provenance/screening decisions are retained.

## Actual runtime and visual rejection

Girl2 and Sara each pass 32 rendered poses using installed Core 5.0.0, PIXI 6.5.2
and Cubism bridge 0.4.0 in the standalone viewer. Checks cover independent eyes,
half/full mouth, gaze, X/Y/Z, seven head-locked expressions, talking, combined poses,
authored idle and exact neutral reset. Both have zero unexpected resource failures,
external requests, nonfinite vertices or opacity violations beyond the existing
eight-ULP tolerance. Strict opacity excursions remain recorded: **152 Girl2 /
214 Sara**; maxima 1.0000004768 / 1.0000001192. Sampling counts depend on timing.

Maximum enclosed transparency / small detached pixels: **262 / 4 Girl2**,
**4644 / 85 Sara**. These include legitimate details and are warning counts,
not aesthetic thresholds. Inspection of Sara's actual sheet found extra contours
when eyes close and barely visible mouth opening. Its CLI record is rejected-visual
despite passing numeric tests. Import/moving vertices do not prove usable animation.

Girl2 remains a limited regression prototype with simple lids and hair gaps. It
does not replace accepted Phase 3.1. Development-agent reviews are explicitly
labelled; no new user visual acceptance is asserted. Runtime testing used the
actual installed libraries in the standalone viewer, not production SillyTavern.
No fresh production emotion/provider integration is claimed. Dedicated validation
servers/browsers stop afterward.

## Verification, reproduction and remaining work

112 Python tests pass, including recovery/cache tampering, hash-bound reviews,
arbitrary target IDs, complete key enumeration, semantic ordering, exact archived
RGBA and current-export preview. Five existing JavaScript talk tests pass.
Deployment/transaction regressions remain in the Python suite; dedicated Btrfs
acceptance was not repeated because deployment code did not change.
Golden Fixtures, worker/model locks, accepted models and packaging pins are unchanged.

Repeat cached regressions and gallery generation with fresh output names:

    uv run --frozen python scripts/phase4b_benchmarks.py --output runs/NEW-regressions
    uv run --frozen python scripts/phase4b_summary.py \
      --output runs/NEW-gallery --benchmark runs/NEW-benchmark.json

See the creation guide for review/resume and source definitions for acquisition;
there are no implicit downloads. Final evidence: runs/phase4b-girl2-final,
runs/phase4b-sara, runs/phase4b-regression-eye-order, runs/phase4b-review-final.
Earlier/failing attempts, worker outputs, masks, PSDs and projects survive.

The remaining blocker is generic facial decomposition/artwork: remove baked
contours without losing source pixels, produce credible concealed skin/closed
and intermediate lids, and align a visible mouth interior to the illustration.
A usable independent character must then pass a new visual review. The present
work is not complete Phase 4B acceptance or solved general image-to-Live2D
conversion. No production installation or training was performed.
