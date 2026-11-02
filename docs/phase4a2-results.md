# Phase 4A.2 — cross-filesystem implementation and classifier investigation

Continued from `b53c3eb`. **Disposable cross-filesystem deployment and exact
rollback pass. Reliable LLM expression integration remains blocked by the installed
ST API contract; the explicitly permitted fallback path was retained. Production
is unchanged and execution remains disabled.** No Phase 4B, training or real LLM
call was performed.

Implementation milestone `cde2ca8` adds target-local transactions and standalone
recovery. Read the [deployment/recovery plan](phase4a2-deployment.md),
[classifier investigation](phase4a2-classifier.md) and
[compact benchmark](benchmarks/phase4a2.json). Accepted art, model package,
Phase 3 patch/controller, dependency/model locks and earlier fixtures remain unchanged.

## What changed

`target-deploy` and `target-rollback` are separate from the original Phase 4A
commands. They accept only independently prepared instances in the two fixed test
bases, with private sibling transaction directories. They cannot install into
production or replace an existing model. No settings writer or provider change exists.

Complete cross-filesystem staging, all-file hash and metadata verification, pinned
runtime/Core validation, no-replace atomic publication, controller-first order,
verified backups, durable plans/journals and exact recovery are implemented. Original
extension restoration precedes controller removal. A copied stdlib-only helper
handles recovery without the checkout. The implementation preserves ownership,
permissions, mtime and xattrs, and refuses unknown edits or corrupt recovery material.
It uses advisory locking, matching mount identity and no unsafe copy/move fallback.

`audit_st_expression_contract.mjs` verifies and executes the actual installed ST
export with synthetic dependencies. `phase4a2_acceptance.py` reproduces fresh Btrfs
copies, model-only/adapter deployments, actual message handlers and rendering,
project-independent recovery, preference preservation and removal discovery.
`phase4a2_summary.py` creates the concise benchmark and local visual review.

## Validation

- **97 Python tests pass**, including all existing packaging/rollback restrictions.
  All **15 new transaction tests** additionally pass on actual Btrfs. No local
  prerequisite tests were skipped in this run.
- **Five JavaScript controller tests** and **three Node source behavior audits** pass
  (existing provider behavior, preference coexistence, new ST export contract).
- Real source ext4 device **66305** → target Btrfs device **48** staging and
  target-local publication, model-only and adapter. Private transactions are under
  `/home/zelli/tools/ai/live2d-studio-phase4a2-tests/`, outside production.
- SIGKILL after all three served publication and three rollback renames, plus all
  eight installation and eight rollback journal replacements. Interrupted recovery,
  partial copies, backup/helper/journal corruption, user edits, links, mount/version
  mismatch, permissions, conflicts and concurrent writers/transactions fail or recover
  as designed. Space checks and ENOSPC use fault injection, not filling the host disk.
- Both browser instances recover using their copied helper with **`/data` hidden**
  in a mount namespace. Original extension file hashes/metadata and existing assets
  return exactly; later browser-created settings/characters/chats remain untouched by
  rollback. Subsequent real model discovery finds the existing fixture and no Girl2.
- All 729 public baseline hashes, compatibility pins, projected production preferences,
  settings size/mtime/ctime and Live2D inventories remain unchanged. Installed ST
  1.18.0, extension 0.1.0 and actual Core 5.0.0 still accept MOC v5/24 drawables.
  No production private-chat/credential reads, HTTP calls, service changes or installs.

| Fresh isolated browser scenario | Upstream | Optional adapter |
| --- | --- | --- |
| Discovery/resources/Core and seven message-expression mappings | Pass | Pass |
| Text-driven talking, idle/blink, switching, reload | Pass | Pass |
| HTTP classification failure | Expected failure: caught listener error/stale expression | Pass: neutral |
| Older asynchronous reply arriving last | Not accepted as protected | Pass |
| Seven expressions and concurrent blink/mouth/head poses | Existing behavior retained | Fresh pass |
| Provider 2 retained | Happy fallback, zero classifier requests | Neutral fallback, zero classifier requests |
| Uninstall/discovery and previous files restored | Pass | Pass |

The main suite has eleven scenarios: ten pass, one deliberate upstream HTTP failure.
Two additional post-uninstall discovery scenarios pass. Real event handling uses
synthetic messages and deterministic supported-provider network mocks; all seven
expressions render correctly. The RP scenario makes eight mocked classification
requests for seven labelled messages plus one offline test, with no extra requests
observed in that scenario. This is not a shared-worker deduplication guarantee.

The exported built-in classifier returns seven simulated LLM labels in the Node
contract experiment. This is **not** LLM-provider-to-Live2D integration. Its errors
can be indistinguishable from valid fallback emotions; full-prompt mode uses app
context; repeated calls lack deduplication; exported `lastExpression` has no message
identity or success status. No reliable direct bridge was shipped. Broader shared
classification API work is required; provider 2 stays unchanged. Actual model/API
inference and cross-chat LLM races are not claimed validated.

## Visual review and retained evidence

Local review: `runs/phase4a2-review-final/index.html`. Full final integration evidence:
`runs/phase4a2-acceptance-v3/`; regression and API-contract logs:
`runs/phase4a2-audit/`. Target-side plans, backups and helper files remain in the
Btrfs test base, never Git. Generated packages and recordings remain excluded.

The neutral RGBA canvas equals Phase 3 byte-for-byte. The expression, talking and
combined-pose contact sheets were inspected. Seven expressions remain subtle;
text-driven mouth movement is visible with independent blinking. Flat intermediate
lids, hair/neck gaps at stress angles, and body-following sleeves remain. No missing
forearms/hands were generated. This is the same limited portrait prototype, not a
new anatomical or general limb-preservation validation. Strict raw opacity excursions
are retained in the benchmark alongside the unchanged numeric tolerance.

The first browser attempt used an incorrect assertion of mouth form 1 for happy;
the accepted expression is 0.85. That test failure and its logs are retained, the
assertion corrected, and the disposable install rolled back. The second suite passed;
the final third suite replays the committed helper and includes removal discovery
in one command. Development evidence is not relabelled as acceptance.

## Remaining decisions

Production needs a new explicit authorization and reviewed binding to the exact
production destination/target-side transaction path. Current commands cannot execute
that plan. Choose model-only or optional adapter, accept neutral/manual emotion
behavior with the current LLM provider or authorize broader classifier integration,
name the character/activation scope, and agree on a maintenance window and any
service operations. No preference or actual API-call approval is implied.

The production plan and exact unchanged package/adapter hashes are documented in
[deployment](phase4a2-deployment.md#final-proposed-production-plan--still-disabled).
A future activation must record conditional per-key settings undo; file rollback
must not restore old whole settings over later preferences. Recoverability tests do
not certify arbitrary hardware/power loss. Stop after Phase 4A.2; Phase 4B automation
and independent limb benchmarks remain separate assignments.
