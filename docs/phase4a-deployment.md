# Phase 4A isolated packaging and rollback

Production deployment is deliberately unavailable. `deploy` and `rollback` only
accept a marked, independently copied `.cache/phase4a-*` instance in this checkout.
There is no production override. Keep the disposable server stopped during either
operation. Packages and transaction records must be under `runs/`; originals and
accepted Phase 3 sources are read-only inputs.

## Reproduce

From the repository, with the installed local Node/Chrome/ST dependencies:

```sh
uv sync --frozen
uv run --frozen python -m unittest discover -s tests -v
node tests/test_rp_talk.mjs
uv run --frozen python scripts/phase4a_acceptance.py --run-id my-new-run
```

Choose a fresh ID each time. The scenario copies the installed ST code and
extension, creates fresh settings, disables model downloads, packages Girl2 twice,
compares every packaged hash, and exercises upstream and adapter copies separately.
Ports default to loopback 8766/9227; `--port` and `--cdp-port` select alternatives.
No original profile, credentials or chats are copied. Production code, extension,
Live2D assets and settings are hashed before/after, without deserializing settings.

Explicit commands (all paths below must be new):

```sh
python3 scripts/prepare_st_smoke.py --phase4a \
  --source /home/zelli/tools/ai/SillyTavern \
  --extension /home/zelli/tools/ai/SillyTavern/data/default-user/extensions/Extension-Live2d \
  --destination .cache/phase4a-manual
uv run --frozen live2d-studio package \
  --output runs/phase4a-girl2-package \
  --core .cache/phase4a-manual/data/default-user/extensions/Extension-Live2d/lib/live2dcubismcore.min.js
uv run --frozen live2d-studio deploy --dry-run \
  --package runs/phase4a-girl2-package --target .cache/phase4a-manual \
  --record runs/phase4a-manual-transaction --name girl2 --adapter
uv run --frozen live2d-studio deploy --execute \
  --package runs/phase4a-girl2-package --target .cache/phase4a-manual \
  --record runs/phase4a-manual-transaction --name girl2 --adapter
uv run --frozen live2d-studio rollback --dry-run --record runs/phase4a-manual-transaction
uv run --frozen live2d-studio rollback --execute --record runs/phase4a-manual-transaction
```

Omit `--adapter` for unmodified upstream. Existing model directories fail closed;
`--replace` explicitly requests a verified backup and replacement. Existing adapter
companions, unsupported versions, extra/missing package files, case conflicts,
symlinks, hardlinks, path traversal and unwritable destinations are rejected.
Dry runs make no output files. A deployment record is created on execution.

## Package contract

`recipes/girl2-package.json` pins the accepted Phase 3 source directory, all
runtime-consumed files, versions, provenance and reviewed limitations. Only that
reviewed Girl2 build is supported. Packaging includes seven expressions, authored
Idle/Nod, physics, texture, display info, mapping and provenance. Unreferenced
editor exports and redundant motions stay in the immutable source directory.
The PSD/project remain under `runs/phase3-final/`; their hashes are recorded.

Reference validation, exact file-set/hash checks, seven expression names, both
motion groups and all 28 classifier mappings must pass. The installed pinned Core
actually instantiates the MOC, checks parameters and reviewed sleeve/torso/neck
meshes. The resulting manifest records the Core probe, hashes, rights, tool
versions, source inventory and limitations. No runtime libraries are redistributed.
Repeated packaging produces identical file bytes, including the manifest; filesystem
timestamps and archives are not claimed reproducible. Existing outputs are refused.

Framing (`portrait/bust`, `half-body`, `full-body`) is independent of anatomy.
A complete bilateral inventory records source visibility, image/anatomical sides,
preservation, semantic ownership and animation separately. Missing inventory,
uncertainty, lost/duplicate pixels, a visible skin limb assigned to clothing, or
missing motion review blocks acceptance. The independent-mask evaluator can detect
loss, duplicates and wrong owners; its synthetic tests are structural tests, not
validation on independent real arm/hand benchmark art.

Girl2 passes portrait completeness from the reviewed source audit: shoulders and
clothed upper-arm silhouettes survive in sleeve meshes; forearms/hands were never
present. Shirt aggregate exact-RGBA counts do not become independent sleeve IoU.
It has body-following sleeves, no independent elbow/wrist rigging, and residual
semantic errors elsewhere. No anatomy is generated. Future characters require
independent source masks, semantic evidence, full-canvas and combined-motion review;
this pinned Girl2 recipe cannot authorize a new character merely from part names.

## Transaction and recovery contract

An advisory lock serializes CLI operations. A durable write-ahead journal records
intended destination, package hash, every changed path, before/after hashes,
permissions, modification times and backups. Data is staged and backups verified
before touching target files. Same-filesystem renames publish the model and patch.
A persistent transaction pointer blocks another deployment until rollback.

Interrupted installs remain recoverable with the same `rollback` command. Each
operation records its rename gap before mutation. Rollback preflights **all**
backups and target states, quarantines installed files by atomic rename, restores
verified prior files/directories, and checks their hashes, modes and modification
times. Existing models, including empty subdirectories, are restored, not deleted.
New models/companions are removed. Original extension bytes are restored exactly.
Backups, displaced files and recovery journals remain in `runs/` for inspection.
Rollback can resume after interruption and is idempotent after completion.

User edits or corrupt backups cause refusal before restoration; preserve and
resolve those conflicts explicitly. Do not edit a transaction journal to force
rollback. No concurrent external writer or hostile filesystem actor is supported;
this is a local operational safety boundary, not a security sandbox. Atomic
renames and fsynced journals support process-interruption recovery; no universal
power-loss/storage-hardware durability claim is made.

The installer **never writes user settings**. The preset initializes settings only
when the extension has none; existing settings remain authoritative. Rollback
restores deployment-owned files, not later chat history or settings deliberately
changed through ST. The acceptance harness preserves browser-created data in
`*-browser-data-after`, resets its own disposable fixture state, then verifies the
entire previous data-file hash set after rollback. This fixture reset is reported
separately; it is not a claim that uninstall erases user activity. Parent-directory
access/change timestamps are not part of the file restoration guarantee.

## Optional adapter strategy

Inspected installed extension `d1801d36` and ST `8172dcd0`, including
`index.js:293–294`, `live2d.js` exports/private state and the ST event API.
ST allows companion extensions and event listeners, but the required model state
is module-private. The existing anonymous listeners close over imported functions;
a companion cannot safely replace the classifier/fallback/talk lifecycle through
a documented hook. Ticker introspection, global fetch overrides or replacing
listeners would be brittle production mechanisms. The network mock is test-only.

Therefore retain one small pinned upstream patch (`scripts/patch_st_phase3.py`)
and the separate `integrations/sillytavern/rp-talk.mjs` controller. Deployment changes
exactly `live2d.js` and adds `rp-talk.mjs`; every file is journaled and the original
is preserved. The original `live2d.js` SHA-256 must be
`f6bae7eff0705593403de51062b9dead7a1a5799a8aaa1754c677149fb117c5b`.
Other loader/UI/Core dependency hashes are checked too. Updates require a new
source review and acceptance run; no best-effort patching of unknown versions.
No edits to `index.js`, runtime libraries or user settings are needed.

Upstream renders, maps expressions, blinks and animates text-driven talking;
classifier HTTP failures can leave stale expression and caught listener errors.
Its extra head/breath oscillation remains, talk is abrupt, and stale asynchronous
responses are unprotected. The optional adapter supplies neutral fallback, request
ordering, smooth bounded text-talk and authored-idle-only motion. Explicit motions
preserve expression via a renderer-wide setting: multi-model behavior is still
outside this Girl2 acceptance. `force_loop` and `force_animation` remain off.
Neither path implements audio lip synchronization.
