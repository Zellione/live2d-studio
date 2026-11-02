# Phase 4A.1 — production readiness audit

Audited from `f1c7e39`, 2026-11-02. **The accepted Girl2 package is compatible
with the currently installed code and Core. Production execution is not ready:
the installer needs a target-filesystem transaction implementation, and the user's
current LLM expression preference does not produce classified emotions through
this extension.** No production files/settings were modified, no model or adapter
installed, no production browser/API session opened, and no services stopped or
restarted. The Phase 4A isolation restrictions remain intact.

Local detailed dry run: `runs/phase4a1-audit/report-complete.json`. Candidate adapter
bytes are in `runs/phase4a1-audit/proposed-live2d.js`, **not** in SillyTavern.
The accepted package remains `runs/phase4a-acceptance-v4/girl2/`.

## Scope, privacy and confidence

The new `audit-production` command reads public application/extension code,
Live2D asset trees, filesystem metadata and an allowlisted projection of
`data/default-user/settings.json`. The streaming projection skips unrelated values
without materializing them; custom model preferences/click messages are skipped,
character identifiers are reduced to counts, and no raw settings copy or whole-file
settings hash is produced. No chats, character cards, credential stores, API keys,
custom prompts, process command lines or environment secrets are inspected/logged.
No production HTTP request is made: even an assets-list endpoint can initialize
folders. Report output is exclusive and restricted to project `runs/`.

All 11 Phase 4A compatibility file hashes match. All **729 public code/extension
files** from the successful Phase 4A browser baseline match again. This binds the
existing real-handler/browser evidence to today's installed code; it is not a new
production browser test. A fresh invocation of the installed Core instantiates the
accepted MOC: Core version `83886080` (5.0.0), MOC version **5**, supported maximum
**5**, **24 drawables**, no missing required parameters, and all reviewed sleeve,
neck and torso drawables present. No filename conversion or guessed compatibility.

The audit checks pinned file hashes, settings size/mtime/ctime and the asset
inventory again before returning. They are unchanged. Earlier Phase 4A's 730-file
snapshot included an opaque full settings hash; this audit deliberately uses the
restricted projection and metadata instead. It does not claim to detect unrelated
production files outside the inspected scope or simultaneous external writers.

## Installed versions and runtime hashes

| Component | Observed version/revision |
| --- | --- |
| SillyTavern | 1.18.0; `8172dcd0ee672d3cd9a5e5f7af134f91a45cd2b8` |
| Extension-Live2d | 0.1.0; `d1801d36a32ace9451cf6377c005a7a64292fc39` |
| Cubism Core | 5.0.0; actual instantiation passes |
| PIXI | 6.5.2 in installed header/runtime |
| Cubism bridge `index.min.js` | embedded version 0.4.0; exact hash is authoritative |
| `live2d.min.js`, `extra.min.js` | no reliable independent version marker found; pinned by hash |
| Accepted authoring provenance | PSD2Live 3.6.7; original CC0 Girl2, unchanged |

Licenses retain Phase 0/4A provenance: ST AGPL-3.0, extension GPL-3.0,
PSD2Live GPL-3.0, PIXI MIT, proprietary Cubism Core. Runtime libraries are already
installed; no new library/model is downloaded or redistributed by the package.

| Installed runtime file (`Extension-Live2d/lib/`) | SHA-256 |
| --- | --- |
| `extra.min.js` | `f71e5b58190bab324eed2ac49fa6f84be090ec63df068b70b9d826b5e6ed9d16` |
| `index.min.js` | `e32028b54c6f975e93469a51fc73421eff175f5bf61b73b56b41ab2051829e04` |
| `live2d.min.js` | `96cd98047edc7ff319c35c344ede4dc62a286d3c7e1173e5365e7a7ea6bad69e` |
| `live2dcubismcore.min.js` | `942783587666a3a1bddea93afd349e26f798ed19dcd7a52449d0ae3322fcff7c` |
| `pixi.min.js` | `ce14152237354383ef19362e1d83cad5c62c6af70f6598c2bf54820af8e7eaf1` |

The other compatibility hashes are recorded here to make the preflight reviewable:

| Relative to production SillyTavern root | SHA-256 |
| --- | --- |
| `data/default-user/extensions/Extension-Live2d/constants.js` | `3090cd81e1fc037dd685266175592d6030b7386fd7fb35149039ccafba080bdd` |
| `data/default-user/extensions/Extension-Live2d/index.js` | `dd81761fc5aeae0797c257f1fbc0f7d15ca34bfc3715ef52eb1bb4a74757d7de` |
| `data/default-user/extensions/Extension-Live2d/live2d.js` | `f6bae7eff0705593403de51062b9dead7a1a5799a8aaa1754c677149fb117c5b` |
| `data/default-user/extensions/Extension-Live2d/manifest.json` | `4bf26ee47a01557c5add12ca6194d0ebfd86989a8c602cf3d4ebf82559912502` |
| `data/default-user/extensions/Extension-Live2d/ui.js` | `440231a50ec9d192eead0af98c832ce5e1daef7e60f80e4a583fc7468bd89c78` |
| `package.json` | `d712414b552e27c6284cb75202fb9af75ad0db1f340ce1fa7ea739e625a9a960` |
| `public/scripts/extensions.js` | `42437984d17b8f41dbfeb2ac4e907c89050890193e870a61d4c72b3a5a5a335c` |
| `src/endpoints/assets.js` | `890a4fe32ca20d24b0c1aa178e0e9c6b3de82f64f51b01d3f3766105b9fb4b8a` |

## Assets, preferences and conflicts

- Global `data/default-user/assets/live2d/`: **zero files/models**.
- Character-specific `characters/<name>/live2d/` subtrees: **zero locations/models**.
  Character cards and chat content were not opened.
- No `extension_settings.live2d` object, mapped characters, configured model pairs,
  or preferences referencing the proposed model URL exist in the on-disk settings.
- Live2D is not in the disabled-extension list. This does not mean a model is
  currently enabled: on first initialization upstream defaults `enabled`,
  `followCursor`, `force_loop` and `force_animation` to false.
- Proposed model directory, `rp-talk.mjs`, legacy `live2d.upstream.js` and proposed
  transaction location are absent. No exact/case-folded destination conflict found.
- Inspected target directories are owned by UID/GID 1000, mode 0755. Original
  `live2d.js` is UID/GID 1000, mode 0644, 25,411 bytes. No permission change is planned.
  Host mount flags are writable; no test write was performed. Permissions, ACLs,
  free space and path identity must be rechecked at deployment time.

**Current expression provider is `extension_settings.expressions.api = 2` (LLM).**
The legacy `extension_settings.api === 2` condition is false. The installed
Live2D function has a `TODO: proper LLM classification` and tests the wrong root
field in that branch (`live2d.js:407`). With the actual preference, it falls through
to `FALLBACK_EXPRESSION` (joy). The existing RP adapter changes that fallback to
neutral; it does not add LLM classification support. The Girl2 preset maps joy
to happy, so upstream would use the happy expression regardless of reply emotion.

A synthetic execution of the exact pinned function confirms:

| Preference | Unmodified extension | Existing adapter | Classifier requests |
| --- | --- | --- | --- |
| Current LLM `api=2` | joy fallback | neutral fallback | zero |
| Local `api=0`, mocked response anger | anger | anger | one mocked fetch |

Evidence: `classifier-preference-test.json`; no real classification, network or
user message was used. **Seven expression files and 28 mappings are valid, but
current preferences will not automatically select varied emotions.** Manual
expression selection, idle/blink and text talking remain separate capabilities.

Do not silently change the shared expressions provider to local: that would alter
existing non-Live2D preferences and might require classifier weights. Options for
a later approved phase are to retain the current provider and accept the fallback,
explicitly choose/test an installed supported classifier, or investigate delegating
to ST's exported `getExpressionLabel` in `public/scripts/extensions/expressions/index.js`.
That export exists in this revision, but such an adapter change has not been
implemented or validated. No LLM call, classifier download or configuration change
is authorized by this audit.

## Preset coexistence

`ui.js:424–470` initializes a model record only when the selected character/model
pair is undefined. It then fetches `sillytavern_settings.json` and uses it for that
new pair. It leaves other character/model entries and global preferences alone.
Existing records, **including incomplete records**, do not fetch or merge the preset.

The exact initialization block was executed with synthetic new, existing and
partial-existing settings. New records receive the full preset; existing records
remain byte-equivalent as serialized, with zero preset fetches/saves; unrelated
preferences survive. Evidence: `settings-coexistence-test.json`. This is an exact
source-block test with mocked UI/fetch dependencies, not a production UI session.

The new model URL avoids current preferences entirely. Its preset selects neutral,
Idle, scale 0.4, x −75/y 0, mouth parameter `ParamMouthOpenY`, speed 3 and 30 ms per
character, plus the 28-label mapping and per-model RP opt-ins. Existing global flags
are not changed. These framing defaults may need later UI adjustment for the user's
viewport. Installation alone neither chooses a character nor enables Live2D.

A future activation must name the chosen character and separately record the
logical settings delta: prior presence/value of its model mapping and the new
character/model entry, plus any explicitly approved global change. Do not replace
`settings.json` wholesale or restore an old full settings backup over subsequent
preferences. Abort on unexpectedly pre-existing destination settings; do not reset
or fill them silently. No settings write or settings backup belongs to the file
installation dry run below.

## Filesystems and transaction design

Host mount inspection was performed read-only outside the sandbox because its
read-only `/home` view is an enforcement overlay, not the host mount policy.

| Location | Host filesystem | Device (`st_dev`) |
| --- | --- | --- |
| `/data/projects/live2d-studio` | ext4, `/dev/nvme1n1p1`, mounted `/data`, rw | 66305 (259:1) |
| `/home/zelli/tools/ai/SillyTavern` | Btrfs, `/dev/nvme0n1p5`, `@home`, rw/noatime | 48 (0:48) |
| Target asset/extension directories and `/home/zelli/tools/ai` | same observed Btrfs device | 48 |

**They are different filesystems.** Current Phase 4A keeps its record, stage and
backups in project `runs/`, and refuses a device mismatch on execute. Its dry run
does not perform that later same-device check. Production is independently rejected
by the isolated-marker/path gate. Neither restriction was relaxed.

Required future layout, absent today:

```text
/home/zelli/tools/ai/.live2d-studio-transactions/
  SillyTavern/
    lock
    girl2-phase3-portrait-v1-001/
      plan.json
      journal.json
      recover.py                  # future reviewed stdlib-only recovery helper
      stage/model/                 # complete package copied across filesystems
      stage/adapter/live2d.js      # only if adapter explicitly selected
      stage/adapter/rp-talk.mjs    # only if adapter explicitly selected
      backup/adapter/live2d.js     # exact original, verified before any mutation
      quarantine/                 # retain removed/replaced transaction-owned files
```

This private sidecar is outside the ST Git tree, `public/`, user assets, characters
and served extension paths. Backup model JSON must never be placed under assets:
ST recursively discovers files containing `model` and ending `.json`. Creating a
hidden directory there would not make backups safely undiscoverable.

A reviewed production implementation must:

1. Acquire a target-side exclusive lock; verify approved absolute destinations,
   package/revision/hashes, no links/traversal/hardlinks, UID/GID, writable parents,
   absent conflicts, free space and active transaction state. Verify mount identity
   and rename capability for **each** destination, not only `st_dev`; fail on
   `EXDEV`. Do not fall back to `shutil.move` or a partially served recursive copy.
2. Copy the complete package across filesystems **into private target-side staging**.
   Copy the optional controller/candidate there; hash every staged byte, validate
   references and Core again. Project `runs/` may receive audit copies but must not
   be the authoritative recovery store. Include a reviewed, hash-pinned standalone
   recovery helper on the target filesystem so recovery does not depend on the
   project interpreter/source under `/data`; its implementation and hash are still
   pending. Use private directories (0700) and journal files (0600); preserve the
   existing extension's owner/group, mode, mtime and
   applicable ACL/xattrs in verified backups. Runtime files remain readable by ST.
3. Make the journal durable before mutation. Fsync staged files, every created
   directory from leaves upward, backups and journal replacements; fsync both
   source/destination parents after renames. Phase 4A fsyncs files and some parents,
   but does not completely flush nested directory creation or every rename source
   parent. Its process-interruption tests are **not power-loss certification**.
4. Publish the model directory with no-replace atomic rename on the target mount.
   For the adapter, publish `rp-talk.mjs` before replacing `live2d.js`; the latter
   must never reference a missing controller. Back up and recheck the original
   extension hash immediately before its atomic replacement. Keep a maintenance
   window free of other clients/updaters/writers. There is no atomic rename spanning
   the model directory and two extension files; use recorded per-operation states.
5. Record installed hashes and verify final files. Keep backups and journal until
   explicit retention cleanup; do not delete the only recovery material. Unknown
   file changes must cause refusal, never automatic overwrite.

Phase 4A currently publishes `live2d.js` before its new controller and relies on a
stopped disposable server; its recovery is designed/tested for process interruption.
A production implementation must reverse that adapter publication order and address
the durability gaps above. Existing isolated code remains unchanged in this audit.

## Complete proposed file dry run

Definitions (exact absolute paths):

- `P` = `/data/projects/live2d-studio/runs/phase4a-acceptance-v4/girl2`
- `D` = `/home/zelli/tools/ai/SillyTavern/data/default-user/assets/live2d/girl2-phase3-portrait-v1`
- `E` = `/home/zelli/tools/ai/SillyTavern/data/default-user/extensions/Extension-Live2d`
- `T` = `/home/zelli/tools/ai/.live2d-studio-transactions/SillyTavern/girl2-phase3-portrait-v1-001`
- Model URL = `/assets/live2d/girl2-phase3-portrait-v1/Generated_artwork.model3.json`

The package is **833,288 bytes in 17 files**, manifest SHA-256
`5f3a30be1c1af850637a3cb3c4963db05a0003aad35730afd0e7fb27ac645b94`.
Every row below is a **new** file at `D/<relative path>`, copied first to
`T/stage/model/<relative path>`. No existing model backup is required because the
destination must be absent; preserve that absence in the journal and refuse any
new conflict. The directory `D/Generated_artwork.4096/` is also created.

| Relative path under D (create) | SHA-256 |
| --- | --- |
| `Generated_artwork.4096/texture_00.png` | `fe6668bc67467761a47ffd2a9bea3956d18e8707fc3fe1a16806701fc20708ab` |
| `Generated_artwork.cdi3.json` | `076db70d6923dbe25dd3b85b9645a8d4bac2cbbe745c222104b7a0dd71d311da` |
| `Generated_artwork.moc3` | `ee5211e840fa1144db0882e1985d3a7ca5eb5b4bccd556c11ce193548062999b` |
| `Generated_artwork.model3.json` | `3dcb97f3e20b0f1c6b208257675ab218e0d57ddbd00f0744e83e5fab17cda66e` |
| `Generated_artwork.physics3.json` | `385846be2c653e6bf3eda4a4e49353ba7c8ea6051a0e88aa86b5e2db749b30e1` |
| `Generated_artwork.rpIdle.motion3.json` | `00c9c1896d937f51832c6afc0f7b21588454fb3930347a5b7f4f09fd9a046146` |
| `Generated_artwork.rpNod.motion3.json` | `65ef1428f5479f01866da86f4a9f67f23d352a9543a2d17fcd8755b045e6cd05` |
| `Generated_artwork.rp_angry.exp3.json` | `3e73fcd146b73a0fb219728b7ff5a189dfe2c28d540d0ffa75ac3ef0538666f3` |
| `Generated_artwork.rp_confused.exp3.json` | `212845f21068903b2acf2342173e09f8f36ea9a3a8f110b41820821312be6662` |
| `Generated_artwork.rp_embarrassed.exp3.json` | `73a5bba642526550dc8ff964e8f9f7a237db3485984d4af8f079a90c7f53d558` |
| `Generated_artwork.rp_happy.exp3.json` | `ac79645f8e3acaa14c561c0ce18740651e48611372c35414ae5bd0862c1b3998` |
| `Generated_artwork.rp_neutral.exp3.json` | `add942af772e4ae1390c01c63b0287894dc60c5bbee8386757d57386f2f56280` |
| `Generated_artwork.rp_sad.exp3.json` | `50051d9adc1dd0b7bd72e0d7c1cec42834de76f63ca3e11971c744eddbc19773` |
| `Generated_artwork.rp_surprised.exp3.json` | `cd33e7c119e53f5cafad59d23fe65ec991239dfcec4a79a00b65372b3ff0f1c5` |
| `animation-provenance.json` | `f8cdd5692c31e871cb2e1fddd287d57e818adb1bbedf0ae11713e05e7d8f6643` |
| `package-manifest.json` | `5f3a30be1c1af850637a3cb3c4963db05a0003aad35730afd0e7fb27ac645b94` |
| `sillytavern_settings.json` | `9614cf4e674e072efcb84aca5ea2d9ff41526b24e48ee1bcb3f745ec7671cb92` |

Optional adapter, **only if separately selected**:

| Path/action | Before SHA-256 | Installed SHA-256 | Backup/stage |
| --- | --- | --- | --- |
| `E/live2d.js` — modify-if-adapter-approved | `f6bae7eff0705593403de51062b9dead7a1a5799a8aaa1754c677149fb117c5b` | `49302ca308e1f06200bda476481e765330ada9531ad57ccea899f2f30754bb3d` | `T/backup/adapter/live2d.js`; `T/stage/adapter/live2d.js` |
| `E/rp-talk.mjs` — create-if-adapter-approved | `absent` | `f41f6568994652f9cf6b690b5da358526a71f9ed6418e0981808d6b97fb8119c` | No original; `T/stage/adapter/rp-talk.mjs` |

Model-only: **17 created served files, zero modified served files**. With adapter:
**18 created served files, one modified served file, one exact original-file
backup**. No `index.js`, UI, manifest, library, settings, character, chat, config,
service or dependency file is changed. The package contains a source/limitation
manifest; it does not contain Cubism libraries, PSD/project files or credentials.

Transaction scaffolding is also a write and requires approval: the sidecar root,
`SillyTavern/`, `T/`, `stage/model/Generated_artwork.4096/`, `stage/adapter/`,
`backup/adapter/`, `quarantine/`, the sidecar `lock`, immutable `T/plan.json` and
mutable `T/journal.json`, and future standalone `T/recover.py`. The recovery helper
is not implemented, so its exact content/hash must be reviewed before a production
plan is executable; this is an implementation gate, not an omitted known payload.
Intermediate parent directories are created as needed.
`journal.json.<nonce>.tmp` is the private atomic-write temporary file; its nonce,
state timestamps and resulting journal hash cannot be fixed before execution.
Rollback creates `T/stage/restore/live2d.js` from the verified original backup
(the original SHA-256 above), then atomically restores it. It quarantines the
installed extension/controller as `T/quarantine/live2d.js` and `rp-talk.mjs`, and
the model directory as `T/quarantine/model/`; their recorded installed hashes
remain applicable. Original backups remain intact. The machine-readable plan enumerates all installed/staged/backup paths.
No scaffolding or candidate byte has been written to `/home` during this audit.

## Adapter scope and features

The currently installed `live2d.js` exactly matches the patcher's required hash.
The candidate was computed only in project `runs/`, and its hash matches the
Phase 4A tested adapter. Unknown versions/hashes must block it. No complete
companion hook exists for the existing module-private model/talk lifecycle; the
one-file patch remains necessary for those fixes in this revision.

| Capability | Unmodified extension | Existing optional adapter |
| --- | --- | --- |
| Model/Core loading, seven expression assets | Supported by matching isolated evidence | Same |
| Independent blink, authored Idle/Nod, basic text-talk | Works; added head/breath oscillation and abrupt talk | Smooth bounded text-talk; authored idle retained |
| Successful supported-provider emotion mapping | Works | Works |
| Current LLM provider | joy fallback, no classifier request | neutral fallback, no classifier request |
| HTTP/offline/unknown label fallback | HTTP can leave stale expression and caught error | Neutral fallback |
| Stale async classification/replies | Not protected | Request/generation guards |
| Explicit motion preserving expression | Runtime may reset it | Renderer-wide preservation option |
| Audio/phoneme synchronization | Not implemented | Not implemented |

Classifier/fallback/race changes affect the extension generally. Smooth text-talk
and authored idle are per-model opt-ins, while expression preservation is renderer
wide once opted in. There are currently no other configured Live2D models, but
future multi-model behavior remains outside Girl2's acceptance. The extension
manifest has `auto_update: true`; ST can auto-update extensions after a version
change if its server configuration permits. That private configuration was not
read. Do not update the extension concurrently or disable updating silently.
Any upstream update requires re-audit and fresh compatibility tests; this patch
must not be reapplied best-effort to changed code.

## Downtime, validation and rollback

Model-only publication is one small target-local directory rename; no server-code
change inherently requires a restart. Refresh model discovery and select the model
through ST only after activation is authorized. The adapter is frontend code:
all clients need a hard reload to replace cached ES modules. Reserve a short
controlled maintenance window for publication and several minutes for validation;
no measured downtime estimate is claimed. Close active clients and suspend competing
updates/writes; a controlled server stop/start is the conservative option if those
conditions cannot otherwise be ensured, and needs explicit authorization. No
production service state, process manager or stop/restart command was assumed.

After an approved install, validate discovery/resource HTTP success, Core/model
load, texture/neutral appearance, all seven manual expressions, blink/idle,
message-triggered talking, interruption, character switching and reload. Confirm
existing preferences survive and use a dedicated synthetic validation conversation
only if separately approved. Do not inspect existing chats. Provider/failure/race
checks should initially use mocks in an isolated copy; production inference/network
calls require separate permission. With provider 2 retained, record fallback behavior
rather than claim classified emotions. No audio lipsync claim.

Rollback/recovery requirements:

- Preflight every installed path and every backup against the journal. Later user
  changes, unexpected assets or damaged backups block rollback before mutation.
- Restore original `live2d.js` atomically **before** removing its controller; verify
  original bytes, mode, owner/group, mtime and any captured ACL/xattrs. Quarantine
  the installed controller after no restored code references it.
- Rename the new model directory into private quarantine. Verify that the prior
  model destination is absent again and that unrelated assets remain unchanged.
  No settings restoration is necessary for the file-only transaction. For later
  authorized activation, use conditional per-key undo of the recorded delta;
  preserve intervening user changes instead of replacing all settings.
- Reboot/reload only under the agreed maintenance scope, confirm the restored
  extension hash and absence from discovery. Parent access/change timestamps and
  inode/ctime identity are not restorable promises.
- On process death or failed publication, keep the service/client maintenance
  boundary in place. Recover from the **target-side** journal even if `/data` is
  unavailable: identify prepared/published/restoring states by before/after hashes;
  prefer verified rollback over guessing how far installation got. A crash after
  copying but before publication leaves only private staging. A crash between
  adapter files is recoverable because the controller is published first and
  original bytes are already durable. No automatic deletion of uncertain files.
- Future tests must cover real cross-filesystem source copying, target-local
  rename failures, ENOSPC/permissions, SIGKILL at every publication/restoration
  boundary, journal corruption, missing project mount and concurrent-update
  rejection. No power-loss guarantee until separately validated.

## Exact commands: available audit and proposed later installation

Executable **now**, read-only with respect to production (choose a new report path):

```sh
cd /data/projects/live2d-studio
export UV_CACHE_DIR="$PWD/.cache/uv"
uv run --frozen live2d-studio audit-production \
  --target /home/zelli/tools/ai/SillyTavern \
  --package runs/phase4a-acceptance-v4/girl2 \
  --output runs/phase4a1-recheck/audit.json
```

The following are **exact proposed command contracts for a future implementation**,
not commands provided by today's CLI. They currently fail as unknown subcommands.
They must only become runnable after explicit authorization, implementation review,
and cross-filesystem/interrupt testing. This audit does not add them or an override.

```sh
uv run --frozen live2d-studio production-deploy \
  --plan /data/projects/live2d-studio/runs/phase4a1-audit/report-complete.json \
  --package /data/projects/live2d-studio/runs/phase4a-acceptance-v4/girl2 \
  --transaction /home/zelli/tools/ai/.live2d-studio-transactions/SillyTavern/girl2-phase3-portrait-v1-001 \
  --adapter none --preserve-settings --execute
```

For the separately approved adapter variant, use the same invocation with
`--adapter pinned-rp` instead of `--adapter none`; no other path changes.
The planned rollback and interrupted-deployment recovery interface is:

```sh
uv run --frozen live2d-studio production-rollback \
  --transaction /home/zelli/tools/ai/.live2d-studio-transactions/SillyTavern/girl2-phase3-portrait-v1-001 \
  --dry-run
uv run --frozen live2d-studio production-rollback \
  --transaction /home/zelli/tools/ai/.live2d-studio-transactions/SillyTavern/girl2-phase3-portrait-v1-001 \
  --execute
```

If `/data` is unavailable, the future stdlib-only recovery helper must support
this proposed target-local equivalent (also not implemented or executable today):

```sh
python3 /home/zelli/tools/ai/.live2d-studio-transactions/SillyTavern/girl2-phase3-portrait-v1-001/recover.py \
  --dry-run
```

It must verify its pinned hash and all journal/backup hashes before offering the
same command with `--execute`; no package or project mount may be needed.

No supported production execution command exists yet. Do not copy a disposable
marker into production, use the old patcher on production, move `runs/` backups
across mounts, or substitute ad-hoc copy commands for the planned transaction.

## Validation and decision needed

82 Python tests and all five existing JavaScript controller tests pass, including
all Phase 4A interruption, exact-restoration, changed-file, link, version and
production-refusal tests. New tests cover settings redaction/projection, malformed
selected fields, pre-existing model preferences and output-path safety. Both new
Node source-behavior audits pass. Earlier development test failures are retained
locally; no failing result is reported as accepted.

No deployment/rollback/adapter implementation or dependency/model lock was changed.
The accepted runtime and historical browser/benchmark evidence remain immutable.
The new audit CLI has no `--execute` option and cannot write its report outside
project `runs/`. Browser evidence is inherited from Phase 4A: the installed 729-file
code baseline is unchanged and the existing isolated restoration regressions pass. No new
browser session or production rendering/inference is claimed.

**Stop here.** Request explicit authorization for a separate production phase:
implement/test the target-filesystem transaction, choose model-only or optional
adapter, agree on maintenance and the character to activate, and decide whether
current classifier fallback is acceptable. Any provider change, new LLM bridge,
production validation messages or actual classification calls need explicit scope.
Phase 4B automation and training remain unassigned.
