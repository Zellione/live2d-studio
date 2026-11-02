# Phase 4A — safe packaging, isolated deployment and rollback

Completed from `a106c5f`. Girl2 can be packaged reproducibly, installed into a
fresh disposable SillyTavern instance, exercised through real message handling,
and removed with exact restoration of deployment-owned files. **Production
installation remains disabled and unchanged.** No Phase 4B work or training.

Implementation milestones: `654f277` packaging/recovery and `ba2e0c9` isolated
integration, removal checks and review tooling.

The tested package is `runs/phase4a-acceptance-v4/girl2/`; editable PSD/project and
accepted source runtime remain unchanged in `runs/phase3-final/`. Local
[visual review](../runs/phase4a-review-final/index.html),
[integration report](../runs/phase4a-acceptance-v4/integration.json),
[compact benchmark](benchmarks/phase4a.json) and
[reproduction/recovery guide](phase4a-deployment.md) describe the evidence.

## Implementation

- `package`: 17 self-contained files, including manifest, seven expressions,
  authored Idle/Nod, texture, physics, display info and 28-label preset. Complete
  references, exact accepted hashes, mapping targets and actual Cubism Core
  instantiation are checked. Two independent package builds match 17/17 hashes.
- `deploy --dry-run/--execute`: isolated-marker/path checks, pinned application/
  extension/Core versions, permission/conflict detection, verified staging and
  backups. Existing models require explicit `--replace`. Existing outputs and
  conflicting adapter files are refused. No settings are overwritten.
- `rollback --dry-run/--execute`: durable transaction recovery, all-path preflight,
  exact previous content/mode/mtime restoration, including replaced models and
  empty subdirectories. Unknown edits and corrupt backups fail closed. Rollback
  resumes after interruptions; backups/quarantined files remain inspectable.
- Source inventory separates portrait/half/full-body framing from anatomical
  completeness. Per-side source visibility, preservation, ownership and animation
  are explicit. Structural independent-mask checks catch loss, duplicate ownership
  and absorption of visible skin limbs into clothing. Girl2 alone cannot establish
  general limb preservation; independent real arm/hand benchmarks remain missing.

The optional adapter remains a small pinned `live2d.js` patch plus `rp-talk.mjs`.
Inspection found no supported companion hook providing private model access and
safe replacement of the existing classification/talk lifecycle. Both changed files
are journaled; original bytes are preserved and restored. Upstream remains usable
for basic rendering, mapped expressions, text-driven talking and blinking, with its
known fallback, race, extra head-motion and talk-quality limitations.

## Actual acceptance

Installed ST `8172dcd0` / 1.18.0, extension `d1801d36` / 0.1.0, Core 5.0.0,
accepted PSD2Live 3.6.7 output. Tests use independent code/dependency copies,
loopback servers, fresh Chrome profiles and software WebGL. No new dependencies,
weights, image inference, original-art edits or production copying.

| Check | Unmodified upstream | Optional adapter |
| --- | --- | --- |
| Discovery, Core load and resources | Pass | Pass |
| Seven actual message-to-expression mappings | Pass | Pass |
| Short/long talking and interruption | Pass, original abrupt envelope | Pass, smooth bounded envelope |
| Idle, blink, character switch, reload | Pass | Pass, authored head range retained |
| HTTP classifier failure | Expected failure; one caught listener error, stale emotion | Pass, neutral fallback |
| Delayed old classification/reply | Not accepted as protected | Pass |
| Controlled expressions/combined poses | Inherited Phase 3 evidence | Fresh pass; neutral exactly equals Phase 3 |
| Rollback file restoration | Pass | Pass, original extension SHA-256 restored |
| Asset discovery after uninstall/restart | Girl2 absent, existing fixture present | Girl2 absent, existing fixture present |

Messages are synthetic assistant replies delivered through `addOneMessage` and
`MESSAGE_RECEIVED`; classifier responses are mocked at the network boundary.
Startup classification is also mocked before application navigation. These are
actual extension handlers, not direct calls substituting for message behavior.
No classification inference, audio/phoneme lip synchronization or TTS is claimed.

The first attempt was blocked by sandbox loopback permissions. The second found
a startup classifier request before the scenario mock, producing a caught upstream
lifecycle error. Both attempts and their logs remain under `runs/`; their deployed
packages were rolled back. The corrected third run passes. The final fourth run repeats the complete
one-command workflow, including regression tests and post-uninstall discovery.
The deliberate upstream fallback failure remains a failure in both successful suites.

75 Python regression tests and all five JS controller tests pass. New coverage
includes every install rename boundary, interrupted rollback, actual child-process
exit during install, simulated disk failure, corrupt/missing/extra files, case/path/
link/version checks, production rejection and changed-user-file refusal. Unmodified
Phase 0/1 browser goldens pass. Full logs and PNG sequences remain outside Git.

All **730 recorded production file hashes** match before/after, covering source,
public code, extension, Live2D assets and settings where present. Accepted Girl2
source runtime, PSD/project, original XCF and golden fixtures are unchanged.
Dependency/model locks and historical benchmark JSON are unchanged. Test servers
and browsers were stopped after acceptance and uninstall verification.

## Restoration scope and visual review

The CLI never changes settings. Browser interactions intentionally create settings,
characters and chats in the disposable fixture. The harness preserves those in
`*-browser-data-after`, resets its fixture-owned non-deployment state, then verifies
the entire original data-file hash set after CLI rollback. Post-uninstall restart
state is also preserved/reset. This is **not** a claim that uninstall reverts later
user chats/settings. Deployment-owned bytes, modes and modification times are
restored; unrelated parent access/change timestamps are outside the guarantee.

Actual expression, talk, full neutral and combined stress frames were reviewed.
The neutral RGBA canvas is identical to the accepted Phase 3 frame. Both sleeves
and shoulder contours remain visible. Mouth-region pixel changes during the
message-driven sequence range from 170 to 635 pixels. The model remains a limited
portrait prototype: flat intermediate lids, hair/neck gaps under stress, subtle
mouth shapes and body-following sleeves. Strict opacity excursion counts remain
in the benchmark (adapter RP 20, lifecycle 1, fallback 19, visual 2); the existing
eight-float32-ULP numeric tolerance is unchanged. No aesthetic improvement is claimed.

Girl2 passes portrait completeness because its supplied clothed upper-body silhouette
is preserved. Source forearms/hands do not exist, including hidden/off-canvas leaves.
The shirt aggregate exact-RGBA measurement does not establish independent sleeve
IoU or elbow/wrist control. No missing anatomy was generated.

## Remaining work requiring another assignment

Production deployment needs explicit authorization and a subsequent implementation:
a reviewed destination/user/model selection, current installed-version validation,
concrete backup/restore plan, handling of pre-existing model settings without silent
overwrite, and an explicit adapter choice. The current CLI has no production bypass.
Multi-model adapter behavior and upgrades require additional acceptance.

Phase 4B image-to-model automation needs independently licensed arm/hand and half/
full-body benchmark artwork, per-limb masks and semantic/deformation evaluation,
better parsing and hidden-region quality gates, and reproducible authoring beyond
this Girl2-specific recipe. Retain Girl1/Wikipe-tan/Boy1 failures. Real eyelid art,
hair/face support and stronger expressive mouth geometry remain quality work.
No custom training or production deployment is authorized by this completion.
