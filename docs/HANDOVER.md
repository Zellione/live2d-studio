# Handover to local Codex CLI

## Current Phase 4B.7b — local human pose review (2026-11-06)

Read [results](phase4b7b-results.md), [generation audit](phase4b7b-generation.md),
[reviewer guide](phase4b7b-reviewer.md) and [benchmark](benchmarks/phase4b7b.json).
Phase 4B.7a commit `c56a59d` was validated and pushed before implementation.

- New standalone reviewer: `scripts/pose_reviewer.py`, local run
  `runs/phase4b7b-review`, loopback port 8795. It uses the existing pinned local
  Qwen Q4_K_S/FP8 encoder; no model downloads or default changes.
- Fixed five-candidate seeded batches, image2 skeleton/silhouette guidance,
  aspect-preserving 1024/1536 output support, immutable history and resumable jobs.
  Accepted poses are frozen; only human-selected images enter exported sets.
- Thirteen controlled calibration cases retain important failures: cropped heads,
  hidden/missing arms, face/proportion drift and .8-denoise near-copies. Larger
  output improves inspected identity/style but does not guarantee pose compliance.
- **Feasibility remains pending human selection and anatomical review.** Never
  turn synthetic browser test approvals or development calibration notes into
  Codel user approval. Selected-only diagnostics are difference panels, not GT.
- Preserve `codel-combined-v1`, accepted Girl2/Sara, the original flat source,
  old negative evidence, model pins and deployment/semantic validation gates.
  Stop before final arm rigging or production deployment.


## Current state after Phase 4B.7a (2026-11-06)

Read [results](phase4b7a-results.md), [protocol](phase4b7a-qwen-feasibility.md) and
[benchmark](benchmarks/phase4b7a.json). Continued from `6205158` for local pose
feasibility only. **No demonstrated arm/body articulation benefit.**

- Existing Qwen 2509 Q4_K_S + FP8 encoder generated six standard poses at strength
  1.0 and three controls at .6. No downloads. All stronger outputs fail consistency;
  two weaker near-copies pass coarse screening but preserve the original occlusion.
- Three fresh SAM runs (source/two screened outputs) retain one substantial unsided
  arm component and yield zero candidate torso exposure. No reliable new joints,
  hand views, side correspondence or articulation evidence. No rig was built.
- Gallery: `runs/phase4b7a-review-release/` (loopback 8794). All nine images, raw
  decodes/composites, change overlays and accepted/rejected decisions are retained.
  Face equality is imposed by a mask; clipping/seams are wrapper limitations.
- Peak allocated/reserved VRAM 21.442/23.127 GiB; ~79–92 s per pose. Preserve the
  interrupted primary batch, verified recovery and the pre-inference flag failure.
- 156 Python tests and both JS suites pass; final pose/reference checks pass.
  Frozen reference/payload and 1,275 sealed first-run files remain unchanged.
- Next work would need stronger pose constraints and suitable hand/mask coverage
  before arm rigging. This bounded negative result is not a universal Qwen claim.
  Defaults, accepted models, production and model locks stay frozen. Stop here.

## Current state after Phase 4B.6.2 (2026-11-06)

Read [freeze results](phase4b6-2-results.md) and the immutable
[Codel reference identity](references/codel-combined-v1.json).

- User said “Das sieht soweit gut aus jetzt.” This is limited visual acceptance
  of the exact Phase 4B.6.1 combined Codel; not professional/full-body/production
  acceptance. New `user-review.json` is separate from unchanged automated reports.
- Original `runs/phase4b6-1-codel-v3` stays unchanged. Read-only snapshot:
  `runs/references/codel-combined-v1`, with 1,806 payload hashes and full manifest
  pinned by SHA-256 in Git. Do not repin/rebuild in place; use a new reference ID.
- Fresh `create` with existing bridge/SAM and `prepare-performance` both reproduce
  all 15 runtime-referenced files exactly. Extra CAN3/CMO3 containers differ;
  editor archive byte identity is not claimed. No individual agent rig operations,
  model inference or downloads. Semantic/visual checkpoints remain intact.
- Configuration: deterministic reconstruction, aligned facial motion, coordinated
  mouths, calm body. Mouth/body defaults remain preserve; no default or product
  code changes. Other characters still need their own reviews.
- Fresh 819-pose mouth and 496-pose body Core checks pass; fresh create passes
  401 browser frames and 72 eye samples. Existing exact body, mouth-only/full,
  idle/gesture/coexistence and neutral-reload evidence is pinned in the snapshot.
- 2,863 historical reference files and the sealed Codel first run verify unchanged.
  Old Codel absolute seam and Girl2 1,716 lip reversals remain failed, not waived.
- `tests/test_reviewed_codel.py` verifies metadata/defaults, local sealed contents,
  expression/physics/motion channels and tamper detection. Local artifact tests
  skip without the untracked snapshot. No production access or deployment.
- Stop after freezing Phase 4B.6.2. Future revisions require separate work.


## Current state after Phase 4B.6.1 (2026-11-06)

Read [results](phase4b6-1-results.md) and [benchmark](benchmarks/phase4b6-1.json).
User accepted Phase 4B.6 body motion; its final model remains frozen. The new
combined candidate restores improved mouth expressions and awaits visual review.

- Candidate `runs/phase4b6-1-codel-v3`; `performance.json` records editable/runtime
  paths. Viewer 8792 compares against the approved body model; gallery 8793 serves
  `runs/phase4b6-1-review` with mouth-only/full comparisons and moving Confused.
- `prepare-performance --mouths coordinated --body-motion calm` composes both in
  one resumable workflow. Same optional flags on `create`; defaults unchanged.
  Applying mouths to an existing body run instead uses body-motion `preserve`.
- All saved expression channels survive later body authoring and export. Confused
  has roundness=1/open=.35; Surprised open=.85. Both Confused still comparisons
  match the improved reference exactly; neutral matches approved body exactly.
- Physics/Idle/Nod/Question are byte-identical. 481 matching Core poses show zero
  change in the 21 checked non-authored drawables. All 33 old archive PNGs and 20
  source layers stay exact; complete artwork matches the optional mouth reference.
- 146 Python, five talk and three numerical JS tests pass, plus three synthetic
  JS source audits. Final candidate passes 819 mouth/496 body Core poses, 401
  dense frames/72 eye samples, 213 mouth, 476 body and 355 coexistence frames.
- Old Codel strict seam failure remains. New optional MOC-bound geometry contract
  adds explicit scale-aware float32 bounds plus a .001 source-pixel cap; Codel and
  Sara benchmarks/negative tests pass. No contract means the old strict check.
  Girl2's 1,716 lip reversals remain failed; no unrelated quality claim.
- Retain all failed attempts, first face-summary failure, reverse-order candidate,
  raw opacity excursions and exact runtime review hashes. No automatic promotion
  or production deployment. Stop after Phase 4B.6.1.


## Current state after Phase 4B.6 (2026-11-06)

Continued from `68e1d25`. Read [results](phase4b6-results.md),
[body authoring](phase4b6-body-rigging.md) and [benchmark](benchmarks/phase4b6.json).

- New optional `prepare-body` reuses verified source/project stages, inspects shared
  ancestry, adds coherent head XY motion, increases existing hair-physics response,
  and exports a 16-second idle plus two head-only gestures. No inference/downloads.
- Codel candidate: `runs/phase4b6-codel-v7`; original neutral/source assets stay exact.
  Both arms remain one unsided component with a shared body attachment. No arm/hand
  articulation or full-body claim. Missing joints/hidden intersections are explicit.
- Viewer supports head/body/hair controls, actual available gestures and equal-scale
  synchronized comparison. Local viewer 8788; gallery/recordings 8791 from
  `runs/phase4b6-review-release`. User visual approval remains pending.
- Codel passes 496 Core samples, 476 final body/comparison frames, 401 facial frames,
  72 eye-channel samples and exact reset/reload. Sara passes numerical Core/render
  gates but retains source-boundary gaps. Girl2's 1,716 inherited lip reversals
  remain a failed broad Core gate; both portrait dense suites pass independently.
- 142 Python tests, five JS talk tests and three source-contract audits pass.
  No threshold change, no promotion, production ST untouched. Retain raw opacity
  excursions, all earlier candidates, dirty-save/motion-format failures and v6's
  partly cancelling nod. Saved candidate/history checkout avoids discard_unsaved.
- Stop after Phase 4B.6. No production deployment, training or host changes.


## Current state after Phase 4B.5 (2026-11-05)

Continued from clean `7863b34`. Read [results](phase4b5-results.md),
[protocol](phase4b5-generalization.md) and [benchmark](benchmarks/phase4b5.json).

- LisadiKaprio's CC BY 4.0 Codel3.png, original 1078 × 2089 framing, completed
  all twelve frozen creation stages without character-specific rig operations.
  Archive/provenance verified; only the selected flat image entered generation.
- `runs/phase4b5-codel-full-first` is sealed before PSD evaluation. Source
  restoration is 99.99956% exact, unique observed owners; both hands retained.
  Both arms share one unsided layer. No complete full-body articulation claim.
- First/optional candidates pass 401-frame and 72-eye-sample suites. Separate
  unchanged 4B.4/4B.4.1 scripts produce `runs/phase4b5-codel-mouths`; its 819-sample
  mouth audit FAILS source-seam invariance in Embarrassed (1.19e-7 vs 1e-7).
  Zero visible reversals do not erase that failure. No tolerance changed.
- High-resolution review rejects convincing animation: overlapping quarter-open
  eye contours and residual shading/fragments; flat closed lashes. Strong source
  and facial ink scores do not imply visual quality. User acceptance is pending.
- PSD has a fused base and seven color/ink facial groups, not full semantic truth.
  Evaluation-only annotations never enter authoring. Four PNGs were exposed while
  selecting neutral; no reference-driven tuning, no training-holdout claim.
- Review `runs/phase4b5-review-final/index.html`; viewers 8786 (sealed first run)
  and 8787 (optional-mouth diagnostic candidate), gallery 8790 when running.
- Pipeline/defaults/locks/accepted references unchanged; new code only evaluates
  and presents evidence. 137 Python and five JS baseline tests pass. Preserve
  sandbox and early diagnostic-report failures. No models/training/production work.
- Stop after Phase 4B.5. Do not promote either model on the user's behalf.

## Current state after Phase 4B.4.1 (2026-11-05)

Continued from `889faf1`. Read [results](phase4b4-1-results.md),
[mouth design](phase4b4-1-mouth-design.md) and [benchmark](benchmarks/phase4b4-1.json).

- User rejected Phase 4B.4 emotional readability. All seven mouth recipes now have
  an optional coordinated contour/cavity candidate; brows/eyes/blush unchanged.
- Candidate `runs/phase4b4-1-sara-v4/export/runtime/Generated_artwork.model3.json`.
  Review `runs/phase4b4-1-review-release/mouth-only.html` first, then
  `full-expressions.html`. New viewer **Mouth only** control isolates facial shape.
- 137 Python and five JS tests pass; 213 dedicated captures, Sara/Girl2 401-frame
  suites, 72-sample eye audits and 819 mouth/expression Core samples pass.
- Neutral render exactly matches Phase 4B.4; all 33 archived artwork PNGs and 18
  source layers preserved. Earlier accepted/rejected models and pins remain frozen.
- Keep rejected v2/v3 and the early-opening corner accumulation evidence. Author
  each key from rest; source seam has no opening geometry axis. Visible full-open
  cavity supplies the winding reference, never an invisible squashed key.
- Plain cavity, source gap and existing facial/hair limitations remain. Explicit
  user visual acceptance is pending; no default change or automatic promotion.
- Stop after Phase 4B.4.1. No production deployment, inference, training or host changes.

## Historical state after Phase 4B.4 (2026-11-05)

Continued from `65c34e4`. Read [results](phase4b4-results.md),
[expression method](phase4b4-expressions.md) and [benchmark](benchmarks/phase4b4.json).

- Optional source-relative independent brows, mouth skew/displeasure and generated
  cheek tint make Sara's three revised poses more distinct in development review.
  Explicit user visual acceptance is pending; no promotion or default change.
- Candidate `runs/phase4b4-sara-v6/export/runtime/Generated_artwork.model3.json`;
  matched gallery `runs/phase4b4-review-release/index.html`. Use the viewer's
  **Compare expressions** mode for settled head-zero poses with idle/talking paused.
- 134 Python tests, five JS tests, 149 controlled captures, 401-frame Sara/Girl2
  temporal suites and exported 72/756-sample audits pass. Keep raw opacity excursions.
- Preserve source brow orientation, both disconnected mouth halves, source RGBA,
  generated-artwork provenance and rejected candidates. No role-name/anatomy inference.
- Accepted Sara/Girl2, golden fixtures, package/model pins and earlier failures remain
  frozen. Sad's weak source-smile reading, simplified cavity/lashes and hair gaps remain.
- Stop after Phase 4B.4. No production deployment, inference, training or system changes.

## Historical state after Phase 4B.3 (2026-11-03)

Continued from `ca66737`. Read [results](phase4b3-results.md),
[transition method](phase4b3-transition-quality.md) and
[benchmark](benchmarks/phase4b3.json). No new inference or model downloads.

- `create --facial-motion aligned` adds source-derived shared closure curves,
  coordinated source-over opacity, explicit iris hiding and a more even sparse
  mouth opening. `legacy` remains default pending character-specific review;
  deterministic remains the default artwork. No agent at runtime.
- The separated Qwen loop at Sara openness .1 is eliminated in the final candidate.
  The replacement moves with the source curve; a static crossfade is insufficient.
  Do not restore the earlier fragmented-landmark, disappearing-lash or contrast-dip
  versions. Keep all rejected `runs/phase4b3-*` attempts.
- Dense validation captures 401 actual Core frames. Exported channel/triangle
  audits cover twelve opening values on each side at three head poses. Visible
  eye reversals fail; invisible squashed-key warnings remain in reports.
- Girl2 independently exercises the same algorithm and retains its original
  open-mouth branch. Neural lash-style regression is not repaired by geometry.
  Qwen skin/cavity remain rejected selections; no automatic neural promotion.
- Local review: `runs/phase4b3-review-final/index.html`. Development assessments
  are distinct from user approval. Accepted Sara, Girl2, package pins and earlier
  neural failures remain immutable. Run Python regressions and JS talk tests.
- Stop after Phase 4B.3. No production deployment, training or system changes.

## Current state after Phase 4B.2 (2026-11-03)

Continued from `71ef58e`. Read [results](phase4b2-results.md),
[model investigation](phase4b2-model-evaluation.md) and
[benchmark](benchmarks/phase4b2.json). **Keep deterministic reconstruction.**
No tested neural candidate improved facial animation without a visual regression.

- Optional isolated LaMa and quantized Qwen workers now run through `create`
  (`deterministic`, `neural`, exact-image-reviewed `hybrid`). No agent at runtime;
  no inference/download in the default path. Separate frozen uv environments.
- 32 crop tasks used the actual 5090. Qwen Q4_K_S + FP8 encoder fits: peak Torch
  allocation about 20.4 GiB. FP8/NVFP4/GGUF alternatives were investigated; full
  Qwen was not downloaded. The matching existing VAE was hash-verified and reused.
- Five fresh editable MCP rigs and actual 57-pose comparisons retain failures.
  Four Sara 122-frame transition suites expose the decisive double contour near
  0.1 eye openness. Smoother fully closed stills did not survive animation review.
  Qwen mouth aperture and Girl2 lash-style regressions are also rejected.
- Source RGBA/masks and frozen Sara/Girl2/Phase 3/3.1 inventories remain unchanged.
  New generated pixels and uncertain boundaries are separately tracked. No model
  output is anatomical truth; other expression tiles remain evaluation-only.
- Local review: `runs/phase4b2-review-release/index.html`. Every rendered candidate
  has a development rejection record; no new user visual approval or promotion.
  Accepted Phase 4B.1 Sara and earlier Girl2 previews remain the defaults.
- Stop after Phase 4B.2. No production deployment, training or system changes.

## Current state after Phase 4B.1 (2026-11-03)

Continued from 3e120c8. Read [results](phase4b1-results.md),
[implementation](phase4b1-facial-artwork.md) and [benchmark](benchmarks/phase4b1.json).
The user accepted **limited visual improvement** for independent single-image Sara.
The exact reviewed gallery is runs/phase4b1-review-candidate; final comparison is
runs/phase4b1-review-complete. This does not establish general-purpose conversion.

- The facial stage now reconstructs source ownership, concealed skin, source-derived
  closed lashes and a simple mouth cavity through reusable Python/MCP authoring.
- Open the frozen reviewed model with preview-live --run runs/phase4b1-sara.
  Preserve it; changed code invalidates creation stages and requires new review.
- Matched 57-pose baseline/candidate renders and separate time-sampled transitions
  exercise the installed Core/viewer. Original inference is reused throughout.
- Girl2 exposed an already-open-source mouth case; the generic geometry selector
  retains its existing procedural treatment. Failed candidates remain in history.
- Accepted Phase 3/3.1 and all deployment restrictions remain unchanged. Additional
  image models were assessed from metadata only, without new weights or inference.
- Stop after Phase 4B.1. No production deployment or training.

## Current state after Phase 4B implementation milestones (2026-11-03)

Continued from `53ad920` with explicit authorization for reusable local creation.
Read [results](phase4b-results.md), [usage](phase4b-create.md) and
[benchmark](benchmarks/phase4b.json). **Independent usable-character acceptance is
not met.** Production remains disabled; no training was performed.

- `create` orchestrates twelve resumable stages with verified cache reuse, source
  restoration, semantic/visual review, local MCP authoring/export and actual Core/
  browser validation. No coding agent is a runtime component. `preview-live --run`
  opens a verified current creation export without MCP/inference.
- Generic target selection uses imported roles, mesh ancestry and inspected axes.
  Profile curves contain no Girl2 IDs/coordinates. Per-eye white/iris/lash ordering
  fixes a real Sara depth-order defect and is a no-op for accepted Girl2 layers.
- Fresh Girl2 and independent Sara projects/PSDs/runtime complete automatically;
  32 real poses each pass control/load checks. Sara is **visually rejected** for
  remaining closed-eye contours and inadequate mouth opening. Do not promote it.
- Boy2 and full/cropped Hachi fail semantic/source gates. Girl1/Wikipe-tan remain
  blocked, Boy1's fine beard/brow rejection is retained. XCF truth stays evaluation-only.
- Accepted Phase 2.6/3/3.1 models/recipes remain unchanged.
  `runs/phase4b-review-final/index.html` contains outcomes, layers and pose sheets.
  New artwork provenance is pinned in `benchmarks/phase4b-art.json`.
- Remaining work: generic contour ownership, concealed facial skin, intermediate
  lids and aligned open-mouth artwork, then an actually accepted independent rig.
  No production installation, deployment safety change or training is authorized.

## Current state after Phase 3.1 (2026-11-03)

Continued from `257582f` with explicit user authorization to improve Girl2 expressions
and add a standalone viewer. Read [results](phase3-1-results.md),
[preview/rebuild instructions](phase3-1-preview.md) and [benchmark](benchmarks/phase3-1.json).

- `uv run --frozen live2d-studio preview-live` opens accepted Girl2 immediately;
  select Phase 3.1 in the Version menu for the revised candidate. No ST/backend,
  onboarding, classifier, model picker or persistent settings. Loopback allowlist only.
- Final candidate: `runs/phase3-1-final-v2/character.psd2live`, matching PSD and runtime.
  Final gallery: `runs/phase3-1-review-corrected/index.html`.
- Clearer smile/frown/surprise and deterministic blush. User reviewed them as more
  recognizable, rejected initial sad eyebrows, then approved the corrected sad pose.
  Dedicated `ParamBrowSad` preserves the other expressions. Keep rejected evidence.
- Full neutral render is identical to Phase 3; all 19 archived source assets retained
  byte-for-byte. Original Phase 3 sources/runtime, recipe and packaging pins unchanged.
- 103 Python tests, five JS talk tests, 15 Btrfs transaction tests and three synthetic
  Node audits pass. Standalone browser checks pass for both models, including fades,
  independent blink, talking, idle, manual overrides, stress and exact neutral reset.
- Existing flat lids, hair gaps and simple lip edges remain. User-reviewed limited
  improvement is not professional rigging or blinded seven-emotion recognition.
- No production ST/settings/service activity, deployment, Phase 4B or training.
  Stopped after Phase 3.1. Production bindings/classifier decisions remain as below.


## Historical state after Phase 4A.2 (2026-11-02)

Started from `b53c3eb`. Read [results](phase4a2-results.md),
[target transactions](phase4a2-deployment.md), [classifier blocker](phase4a2-classifier.md)
and [benchmark](benchmarks/phase4a2.json). Production unchanged and disabled.

- `target-deploy` / `target-rollback` implement target-local private staging, verified
  copies/metadata, controller-first publication, durable journal and stdlib-only recovery.
  Only dedicated disposable bases are accepted; old Phase 4A restrictions unchanged.
- Real ext4 device 66305 → Btrfs device 48 staging and atomic publication pass.
  Both actual browser copies rolled back with `/data` hidden using bubblewrap.
  Original extension metadata/hashes and existing assets restored; later browser-created
  settings survive rollback. Post-removal actual asset discovery passes for both.
- 97 Python tests, five JS controller tests, three Node source behavior audits pass.
  The 15 new transaction tests also pass on actual Btrfs, including SIGKILL at all
  six served rename boundaries and sixteen install/rollback journal replacements.
  Low-space/ENOSPC is simulated; no destructive full-disk or power-loss claim.
- Eleven fresh browser scenarios: ten pass, upstream HTTP fallback is intentionally
  negative. Seven expressions, talking/idle/blink, lifecycle and stale reply checks pass.
  Neutral canvas is byte-identical to Phase 3; visual prototype limitations remain.
- **No LLM integration shipped.** Exact ST export tests show untyped fallback errors,
  duplicate identical calls and contextual full-prompt semantics. Exported lastExpression
  has no message identity/error status. Current provider 2 remains unchanged: upstream
  happy fallback, adapter neutral fallback, zero classifier requests. The user explicitly
  permitted this blocker outcome. Real inference is untested and unauthorized.
- Production pins/Core and all 729 public baseline files still match; projected
  settings/metadata and Live2D inventories unchanged. No credentials/chats accessed.
- Evidence: `runs/phase4a2-acceptance-v3/`, `runs/phase4a2-audit/`,
  `runs/phase4a2-review-final/index.html`; Btrfs transactions retained outside production.
- Next requires explicit production scope (including model-only/adapter, neutral/manual
  emotion acceptance or a broader shared classifier API, character activation and
  maintenance). Production path binding is still unimplemented; never loosen the test
  allowlist as a shortcut. Stop here; Phase 4B remains unassigned.


## Historical state after Phase 4A.1 read-only audit (2026-11-02)

Read [production audit and concrete plan](phase4a1-production-audit.md).
Started from `f1c7e39`; no production files/settings, services, package or adapter
were changed. No production browser/API session, chat or credential-store access.

- Installed ST/extension revisions, all 11 compatibility pins and 729 public code
  hashes match Phase 4A. Actual installed Core 5.0.0 accepts Girl2 MOC v5/24 drawables.
- No global or character-specific Live2D assets, saved model mappings or Live2D
  preferences. Proposed destination: `data/default-user/assets/live2d/girl2-phase3-portrait-v1`.
- **Production expressions API is 2 (LLM).** This Live2D revision falls back to joy
  (Girl2 happy); the existing adapter falls back to neutral. Neither calls the LLM
  classifier. Preserve the preference; full automatic-emotion readiness is blocked.
- `/data` ext4 and `/home` Btrfs are different filesystems. Production transaction
  staging/backups/journal must live in a private sidecar on the target filesystem.
  The plan also requires controller-first publication and stronger directory fsync.
- `audit-production` is read-only, projects settings without copying secrets/custom
  fields, and writes reports exclusively to new project `runs/` files. Local detailed
  report: `runs/phase4a1-audit/report-complete.json`. Proposed adapter bytes stay in that run.
- 82 Python + five JS controller tests and two exact-source synthetic behavior audits
  pass. Existing deployment/rollback/adapter implementations and restrictions unchanged.
- Future production command examples are explicitly proposed interfaces, not currently
  implemented commands. Do not use an isolated marker or ad-hoc copy as a bypass.
- Stop after the audit. Await explicit authorization for transaction implementation,
  model-only versus optional adapter, maintenance/character activation, and any separate
  classifier/provider changes or real production validation. Phase 4B remains unassigned.

## Historical state after Phase 4A (2026-11-02)

Read [results](phase4a-results.md), [deployment/recovery](phase4a-deployment.md) and
[benchmark](benchmarks/phase4a.json). Started from `a106c5f`; Phase 3 sources unchanged.

- Reproducible 17-file runtime package: `runs/phase4a-acceptance-v4/girl2/`.
  Recipe pins accepted files, CC0 rights, versions, Core, mapping and limitations.
- `package`, `deploy --dry-run/--execute`, `rollback --dry-run/--execute` implemented.
  Only marked independent `.cache/phase4a-*` copies are writable targets.
  Existing outputs fail; model replacement requires `--replace` and verified backups.
- Journaled install/recovery tests cover process death, interrupted rename boundaries,
  partial failures, changed user assets, corrupt backups, links and production refusal.
  Settings never written by CLI. Preserve journals; rollback rejects later user edits.
- Optional exact-hash patch remains necessary for complete tested RP behavior; no
  sufficient supported companion hook found. Original extension restored exactly.
- Full upstream/adapter isolated browser acceptance and post-uninstall discovery pass
  with the upstream HTTP fallback intentionally failing. Classification mocked before
  startup and at actual event fetch; no classifier inference or audio synchronization.
- 75 Python tests + five JS tests; Phase 0/1 browser goldens pass. All 730 production
  hashes unchanged, including model assets/settings where present. No production writes.
- Girl2 portrait completeness passes reviewed clothed-shoulder/sleeve preservation;
  absent source hands are explicit. General limb preservation remains unvalidated.
- Local gallery: `runs/phase4a-review-final/index.html`; full evidence and restoration records:
  `runs/phase4a-acceptance-v4/`. Neutral canvas equals Phase 3 exactly; flat lids,
  residual hair gaps and body-following-only sleeves remain. Servers/browser stopped.
- Stop here. Production deployment requires separate explicit authorization, a scoped
  production implementation and current-version revalidation. Phase 4B automation and
  independent real limb benchmarks are future assignments; no training authorized.

## Post-Phase 3 limb audit

Read [Girl2 limb audit](girl2-limb-audit.md). Both sleeves survive as left/right
`handwear`; the XCF itself contains no forearms/hands, including hidden/off-canvas
leaves. Shirt and neck evaluated visible pixels are exactly preserved. The local
comparison is `runs/girl2-limb-audit-final/index.html`. Future limb preservation
is not guaranteed; framing and per-limb checks are recommendations only.
Accepted models unchanged; this audit preceded the subsequently authorized Phase 4A.

## Historical state after Phase 3 (2026-11-02)

Read [results](phase3-results.md), [authoring](phase3-animation.md) and
[isolated RP tests](phase3-sillytavern.md).

- Girl2 has seven expressions, a new brow inclination axis, independent eyes,
  authored 16-second subtle idle/blinks and a short Nod. Source texture and neutral
  runtime are unchanged. No new raster pixels, models or dependencies.
- Accepted local deliverables: `runs/phase3-final/character.psd2live`, matching PSD
  and packaged `runtime/`. Local visual gallery: `runs/phase3-review/index.html`.
- Hair tuning reduces maximum stress-pose hole pixels 502→349 without more small
  fragments. Flat intermediate eyelids and residual hair gaps remain.
- Real ST assistant-message events trigger talking and all seven mapped expressions.
  Classification responses are mocked at the network boundary; no inference claim.
- Full RP acceptance needs the optional isolated adapter: neutral classification
  fallback, stale-response protection, smooth frame-aligned text-talk and suppression
  of additional runtime head/breath oscillation. Production extension untouched.
- Negative upstream HTTP-fallback test retained; caught EventEmitter errors are
  now included in browser QA. `force_loop` and `force_animation` must remain off.
- Complete recipe replay matches all runtime-consumed files exactly. Extra CMO3/
  CAN3 editor containers differ; no blanket archive-byte reproducibility claim.
- 59 Python tests + five JS controller tests; unchanged Phase 0/1 browser goldens
  pass. All 137 recorded production file hashes unchanged. Models/locks and earlier
  benchmark reports unchanged. Final project saved/reopened in editor; isolated
  test servers and browser stopped.
- Stop after Phase 3. No production installation, training or Phase 4 work.

## Historical state after Phase 2.6 (2026-11-02)

Read [Phase 2.6 results](phase2-6-results.md), [quality contract](phase2-6-quality.md)
and the [replay guide](../backends/see-through/README.md).

- Historical Phase 2.5 metrics reproduced exactly before changes and left intact.
- `refine` restores each source sample once, preserving generated hidden surfaces;
  uncertainty remains separate from copy provenance. Main/neural locks unchanged.
- Girl2 visible RGB MAE 8.283 → 0.055, 99.89% exact pixels; neck IoU 0.1376 →
  0.9809, six-class mean 0.7830 → 0.9667. No GT enters inference/refinement.
- Actual motion caught doubled contours in the first attempt. Bounded nearby ink
  ownership fixes them. Final recommended project: `runs/phase2-6-oga-v2-build/`;
  replay-identical layers: `runs/phase2-6-oga-release/`.
- 21 single/combined poses pass actual isolated ST/Core checks; limited prototype
  review accepted, unrestricted quality gate unmet (hair gaps, flat lids).
- Guard-band `prepare-rig` experiment is visually rejected: fewer holes but new
  detached hair fragments. Do not promote this optional experiment automatically.
- Added CC0 Girl1/Boy1 from existing XCF; same artist, limited style variety.
  Girl1 and Wikipe-tan rejected; Boy1 fine beard/brow ownership blocks rig acceptance.
  Padding did not solve Wikipe-tan. All failures remain in local evidence.
- 51 tests; synthetic visible IoU 1.0/full 0.9364596; Phase 0/1 browser regressions
  pass. Four exact manifest replays. Golden fixtures, models and production ST
  unchanged. Test server/browser stopped; editor reopened recommended saved rig.
- Stop after Phase 2.6. Next work requires new authorization; no production copying,
  Phase 3 expansion or custom training has been started.

## Historical state after Phase 2.5 (2026-11-02)

Read [Phase 2.5 results](phase2-5-results.md) and the
[isolated worker guide](../backends/see-through/README.md).

- See-through source and all three approved model snapshots pinned; verified
  checkpoint hashes, independent Python 3.12 / Torch 2.8.0+cu128 uv environment.
- Full BF16 decomposition runs on RTX 5090; sequential model unloading,
  approximately 113–125 s per tested image, peak 11.85 GiB Torch allocation.
- `prepare --backend see-through --decomposition ...` imports worker output into
  manifest v2; default deterministic backend and v1 goldens are retained.
- Girl2 CC0 XCF benchmark: six-group visible mean IoU 0.7830 versus baseline
  0.5200; 89.73% versus 54.23% visible coarse semantic accuracy. Neck/chest weak.
- Cropped Wikipe-tan fails visual/semantic quality despite higher coverage.
- Girl2 experimental MCP import/export and isolated actual ST blink/mouth/head
  poses passed. Basic animation uses PSD2Live-generated shapes, not complete
  animation parts from See-through. No general production-quality claim.
- 40 unit/regression tests, prior Phase 0/1 browser tests and actual Core checks
  pass; 21/21 repeated neural bridge files byte-identical on this setup.
- Keep neural build gated by default. Missing source variants do not mean no
  experimental motion is possible; actual evidence must be reviewed separately.
- No original input, golden fixture, system stack or production ST changes.
  Local evidence under `runs/phase2-5-*`; test server/browser stopped.
- Stop after Phase 2.5. No custom training, Phase 3 or production deployment.

## Historical handover after Phase 2 (2026-11-02)

Read [Phase 2 results](phase2-results.md), [architecture](phase2-architecture.md)
and [artifact policy](artifact-policy.md) first. The original plan below is retained
as history; Phase 0/1 are complete and Phase 2's limited MVP is implemented.

- Cleanup commit `c5d6512` removes obsolete index entries while retaining local
  copies. Phase 0 and final Phase 1 golden fixtures remain unchanged.
- `uv run live2d-studio prepare/inspect/reconstruct/evaluate/build/mcp-check/doctor`
  provide local stages. Commands with arguments are in the architecture document.
- 33 automated tests and all three isolated ST browser scenarios passed.
- Synthetic: visible mask IoU 1.0, full-layer mean IoU 0.93646; original pixels
  unchanged. PSD2Live import/export and basic visible animation passed.
- Real licensed Wikipe-tan image: semantic acceptance failed; most foreground
  remains unknown, some candidate roles are wrong. Do not promote synthetic
  success to real-anime readiness. No neural image weights installed.
- PyTorch 2.9.0+cu128 arithmetic succeeds on RTX 5090; CPU image pipeline is the
  implemented backend. GPU model inference remains future work.
- Connected authenticated MCP succeeds; independent CLI still needs a local
  environment token. Do not read profile secrets. No production ST writes.
- Stop here. Next authorized work should improve semantic parsing and concealed
  contours using a licensed benchmark, before broader rig/production automation.

## User goal
The user wants to provide one or more illustrations of an anime/roleplay character and obtain a properly rigged Live2D avatar for SillyTavern's Live2D extension. They have no image-editing experience, use Arch Linux/Hyprland, and want to avoid paid software like Photoshop or Cubism Pro. Codex should orchestrate an automated, locally executed pipeline and use PSD2Live through MCP if reliable.

## Grounded starting points (verify at implementation time)
- PSD2Live: https://github.com/tsunehimatoi/psd2live – Linux tar.gz release, X11/GLX via XWayland, localhost MCP usually `http://127.0.0.1:23871/mcp`, Cubism-family `.moc3` and `.model3.json` export.
- SillyTavern extension: https://github.com/SillyTavern/Extension-Live2d – documentation currently describes `*.model.json` discovery. This may be a *real runtime compatibility issue*, not merely a filename convention.
- Official docs: https://docs.sillytavern.app/extensions/live2d/ – model installation and interaction settings.
- Codex CLI: https://github.com/openai/codex – local execution and MCP support.

## Design principles
- Prioritize actual SillyTavern rendering and expression switching over VTube Studio support.
- MVP: front-facing torso or bust, with blinking, eye tracking, mouth movement, gentle idle breathing and a few expressions. No initial requirement for complete full-body movement, precise phoneme lip sync, or face tracking.
- Separate image preparation, PSD creation, rigging/export, and SillyTavern deployment into independent stages with inspectable artifacts and automated QA.
- Use local image models where practical; do not choose/pull large model weights without checking licenses, requirements and user approval.

## Phase 0: compatibility gate – first Codex assignment
1. Identify the actual local SillyTavern installation and installed Live2D extension, versions/commits and the asset root; inspect rather than assume the path. If absent, record installation instructions without mutating existing installations.
2. Read extension source and bundled Live2D runtime dependencies. Determine model-format discovery and runtime support for Cubism model generations 2.x and 3+.
3. Inspect the latest installed PSD2Live export behavior. Prefer an upstream example PSD/project from its examples resources with clear permitted usage.
4. Produce a minimal full model export and a deterministic integrity validator for JSON references, case-sensitive filenames, textures, motions, expressions, and binary `.moc3` presence.
5. Load the exported model in the *actual SillyTavern extension* using a disposable fixture location; record the browser console output and successful or failed render. Do not modify upstream extension source or production assets without asking.
6. Write `docs/compatibility.md`: exact versions, supported/unsupported formats, reproduction steps, screenshots/log paths, and the next smallest viable change.

**Stop condition:** If a valid PSD2Live export is not loadable in SillyTavern, do not begin full image-segmentation work. Establish a verified adapter/runtime solution, or clearly explain that the goal is blocked.

## Phase 1: MCP proof of control
- Connect to the local PSD2Live MCP endpoint, using its own Settings > MCP configuration and appropriate authentication. Check `codex mcp list`.
- Start with `workspace_overview`, `workspace_inspect`; discover extra operations with `workspace_list_operations` and `workspace_call`.
- Use preview/dry run before atomic edits when supported, and verify edits survive save/reopen.
- Capture sample MCP requests/responses without leaking auth tokens.

## Phase 2: image-to-layers pipeline
- Import 1+ high-quality frontal character images; keep source unchanged.
- Proposed components (evaluate, don't assume): semantic segmentation, alpha matting, occlusion inpainting, transparency cleanup, standardized naming/ordering, layered PSD generation.
- Split visible parts: face base, hair front/back, eye whites/pupils/eyelids/brows, mouth shapes, neck, torso, accessories. Generate hidden pixels for deformation.
- Use `uv`, deterministic pipeline configs, previews/contact sheets and quality gates.
- Test generated PSD import and auto-rigging in PSD2Live before generalizing.

## Phase 3: rig MVP
- Parameter targets: blink, gaze, mouth open, breathing, subtle head angle, happy/sad/angry/surprised expression toggles; optional hair physics.
- Match *the actual SillyTavern extension's* supported parameter and expression mapping. Do not invent parameter ID support.
- Test extremes and in-between keyframes; reject tearing, seams, missing occluded pixels, or crushed eyelids.

## Phase 4: packaging and SillyTavern QA
- Export source PSD, editable project, runtime bundle and a concise manifest of tool versions/assets.
- Validate model loads, renders, idles, talks on text output, and responds to at least three expression triggers.
- Document any feature requiring the SillyTavern Classify extension or additional extension settings.
- Deploy to the user-selected SillyTavern assets path only with approval; back up any target conflict.

## Deliverables expected
- Reproducible CLI pipeline, tests, a local installation guide, a sample input test case with license provenance, a complete exported model bundle, source assets, QA renders, and a `docs/compatibility.md` report.

## First command to Codex
"Read AGENTS.md and docs/HANDOVER.md. Work on Phase 0 only. Verify the exact version/format compatibility of PSD2Live's .moc3/.model3.json output with my installed SillyTavern Live2D extension. Inspect existing versions and paths before editing anything. Implement only a reproducible compatibility smoke test and docs/compatibility.md. Stop and report if you need host installs, GUI access, or approval to alter SillyTavern."
