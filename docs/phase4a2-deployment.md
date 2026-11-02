# Phase 4A.2 — target-filesystem transactions

The new `target-deploy` / `target-rollback` commands implement cross-filesystem
staging and target-local recovery **only for dedicated disposable instances**.
Production is rejected even with `--execute`. The old Phase 4A `deploy`/`rollback`
restrictions and implementation are unchanged. There is no production override,
replacement flag, settings writer or character activation command.

## Layout and transaction

Allowed test bases are fixed in `target_recovery.py`:

- `/home/zelli/tools/ai/live2d-studio-phase4a2-tests` — actual target Btrfs filesystem.
- `/data/projects/live2d-studio/.cache/phase4a2-tests` — local regression fixtures.

An instance must be exactly `BASE/RUN/instance`, with an exact disposable marker.
A transaction must be `BASE/RUN/transactions/ID`. No marker can authorize production.
Every operation rechecks ancestor links and deployment-relevant trees. No production
settings, cards, chats or credentials are copied into the disposable instance.

```text
BASE/RUN/
  instance/                         # independent public code/dependency copy
  transactions/                     # private 0700, outside all served paths
    ID/
      recover.py                    # copied stdlib-only recovery engine
      preparation.json              # pre-publication intent, original snapshots
      plan.json                     # exclusive immutable finalized plan
      journal.json                  # durable mutable state, plan digest
      stage/0/                      # entire 17-file model package
      stage/1                       # optional rp-talk.mjs
      stage/2                       # optional patched live2d.js
      backup/2                      # verified original live2d.js
      restore/2                     # verified recovery copy, if needed
      quarantine/0/                 # model removed on rollback
      quarantine/1                  # removed controller
      quarantine/2                  # preserved patched extension
```

The final disposable recovery helper SHA-256 is
`930baebc7f9dc9ad7b06a012449c93a0efa0c4cd203549ba7d4e9caf9088f648`.
Both final browser transactions contain that exact helper. A future production
helper would need a new reviewed hash after its separately authorized path binding.

Numeric indices are ordered operations; model-only has only operation 0. JSON
records are created mode 0600. The lock uses the disposable marker's inode and
`flock(LOCK_EX|LOCK_NB)`; a durable unfinished transaction also blocks a subsequent
install after process death. Records and recovery material are retained.

Preflight validates the complete accepted package, references, exact pinned
versions, actual Core instantiation, no existing/case-conflicting destination,
permissions, hardlinks/symlinks/special files, available space, and matching mount
IDs as well as device IDs for each publication. No `shutil.move`/copy fallback is
used when target-local renaming is impossible. Existing models are always refused.

The package crosses ext4→Btrfs only into private staging. Every staged file's
hash, file set, UID/GID, permission bits, mtime and xattrs are compared with the
source, then the staged runtime and Core are validated again. Backups preserve
original metadata, including ACLs exposed as xattrs. A final immutable plan records
all before/after snapshots, payload hashes, paths, package manifest, runtime pins
and recovery-helper hash. Dry run also enumerates payload hashes and stage/backup/
quarantine destinations without creating a transaction.

Files and nested directories are fsynced before publication. Each atomic journal
replacement fsyncs its file and directory. Linux `renameat2(RENAME_NOREPLACE)`
publishes new model/controller paths; `os.replace` atomically replaces the verified
original extension, whose verified backup already exists. Both rename parents are
fsynced. The order is model → controller → patched extension. There is no transient
patched extension importing an absent controller and no displaced-extension gap.

Before each publication, both current destination and staged content are checked
again. This protects against detected unexpected changes, not a hostile writer
racing between check and rename. Keep the disposable server stopped during file
operations; a future production maintenance window must exclude updates/writers.
Advisory locking is not a security boundary against the same filesystem owner.

## Rollback and recovery

Recovery preflights every installed path, backup, immutable plan/helper hash and
unchanged runtime dependency before mutation. Unknown edits, missing/corrupt backups,
links or incompatible runtime changes stop recovery. It restores `live2d.js`
atomically from a verified private copy **before** quarantining the controller and
model. Installed patch bytes are preserved privately. Original content, UID/GID,
mode, mtime and xattrs are checked; inode/ctime and directory access/change timestamps
are not restorable promises. Recorded original file atime is applied to restoration,
but reading/preflighting can affect access timestamps; atime is not an acceptance gate.

The helper runs without imports from the project or a project interpreter. Both
Btrfs variants were recovered using `/usr/bin/python3 -I` in a bubblewrap mount
namespace with **all of `/data` hidden**. This is stronger than merely setting a
different working directory. No production service was placed in that namespace.

An interrupted install can be rolled back at any tested publication/journal boundary.
An interrupted rollback resumes from before/after snapshots. Partial private restore
copies are preserved as `quarantine/partial-*`, then rebuilt from a verified backup;
partial installed files are never guessed at. ENOSPC during preparation leaves no
served mutation. A durable `preparation.json` permits verified abandonment without
requiring completed stage files. A crash during initial transaction-directory/helper/
preparation-record bootstrap can leave only an uninitialized private directory: no
publication is possible at that point. It fails closed and requires inspection; do
not manufacture a journal or delete uncertain files to bypass the pending gate.

The tests kill processes after each of three publication and three rollback renames,
and each of eight install and eight rollback journal replacements. They also cover
conflicts, permission refusal, simulated low-space/ENOSPC, partial recovery staging,
corrupt/missing backups, edited/deleted installed files, runtime drift, corrupt
journal/helper, links, concurrent lock/transaction rejection, and exact metadata
restoration including a real user xattr. ENOSPC is fault-injected; the shared Btrfs
filesystem was not intentionally filled. No destructive full-disk/power-loss test
was performed. Fsync and SIGKILL recovery are not universal power-loss certification.

## Repeatable isolated commands

Run from this repository; choose new IDs. Writes under `/home` and local browser
processes require the execution environment's permission, separately from project
safety checks. The following commands still cannot target production:

```sh
export UV_CACHE_DIR="$PWD/.cache/uv"
uv sync --frozen
uv run --frozen python -m unittest discover -s tests -v
node tests/test_rp_talk.mjs
PHASE4A2_TEST_BASE=/home/zelli/tools/ai/live2d-studio-phase4a2-tests \
  uv run --frozen python -m unittest discover -s tests -p test_target_transaction.py -v
uv run --frozen python scripts/phase4a2_acceptance.py --run-id my-new-run
```

The new transaction tests require the accepted local package and installed pinned
public runtime; they explicitly skip without those local prerequisites. Existing
fixture-based regressions retain their original coverage. The acceptance command
checks different device IDs and Btrfs, copies public code/dependencies into fresh
instances, runs real handlers with classifier mocks, hides `/data` during standalone
rollback, checks browser-created data survives rollback, and reopens the copies to
verify model discovery after removal. No manual file editing is required.

For a prepared disposable instance, exact CLI shape:

```sh
uv run --frozen live2d-studio target-deploy --dry-run \
  --package runs/phase4a-acceptance-v4/girl2 \
  --target /home/zelli/tools/ai/live2d-studio-phase4a2-tests/NEW/instance \
  --transaction /home/zelli/tools/ai/live2d-studio-phase4a2-tests/NEW/transactions/girl2 \
  --name girl2-phase3-portrait-v1 --adapter
```

Use `--execute` instead of `--dry-run` only for that disposable target; omit
`--adapter` for model-only. Recovery is either `target-rollback --transaction T
--dry-run/--execute` or `python3 T/recover.py --dry-run/--execute`. Never rewrite a
marker, allowed root or journal to promote this command to production.

## Final proposed production plan — still disabled

Destination remains
`/home/zelli/tools/ai/SillyTavern/data/default-user/assets/live2d/girl2-phase3-portrait-v1`.
Authoritative recovery would live at
`/home/zelli/tools/ai/.live2d-studio-transactions/SillyTavern/girl2-phase3-portrait-v1-001`,
on the target filesystem, outside all served trees. **These paths are rejected by
the current implementation.** A subsequent explicitly authorized implementation must
bind them to an approved plan rather than broaden the disposable allowlist.

The exact 17 package hashes and optional two adapter hashes in the
[Phase 4A.1 audit](phase4a1-production-audit.md#complete-proposed-file-dry-run) remain
unchanged. Package manifest SHA-256:
`5f3a30be1c1af850637a3cb3c4963db05a0003aad35730afd0e7fb27ac645b94`.
Model-only creates 17 served files; adapter additionally creates `rp-talk.mjs`,
replaces `live2d.js` and privately backs up its original. New private scaffolding
uses the layout above. No settings, character, chat, configuration, runtime library
or service changes belong to the file transaction.

Before any future execution:

1. Obtain explicit production authorization, model-only versus adapter selection,
   acceptance of the LLM fallback or a separately reviewed classifier solution,
   named character activation scope, and maintenance scope.
2. Re-audit production pins, preferences, assets, permissions/free space, mount
   identity and conflicts. Bind a new production-only plan and recovery helper to
   the exact approved paths. Review that narrow implementation; do not bypass gates.
3. Stage/verify on Btrfs; publish in the tested order with other writers excluded.
   Model-only is frontend asset publication; no inherent server restart is needed.
   Adapter requires all clients to hard reload. Any service stop/start needs explicit
   authorization; no production process manager was inspected or assumed here.
4. Validate resource loading, seven manual expressions, independent blink/idle,
   talking and model switching in an explicitly authorized synthetic test conversation.
   No actual API/LLM call is implied. Provider 2 currently means documented fallback.
5. Roll back with the target-side helper if interrupted or unsuccessful; refuse
   unknown edits. Preserve records. A separate activation delta must undo only
   approved per-character settings, conditionally, never restore whole settings over
   later preferences. File deployment itself does not activate or change preferences.

Production compatibility is established for the accepted runtime and current pins;
production execution and automatic LLM emotions are distinct, unpassed gates.
