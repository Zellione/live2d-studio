# Phase 4B.6.2 — reviewed combined Codel reference

Continued from `ba0971a`. The exact Phase 4B.6.1 candidate is now **Codel combined
reference v1**, with limited user visual acceptance:

> Das sieht soweit gut aus jetzt.

This accepts the current combined facial and body animation. It does **not** grant
professional-quality, full-body/independent-arm, general conversion, or production
acceptance. Creation defaults, production SillyTavern and its settings are unchanged.

## Reference identity and preservation

- Tracked identity: [codel-combined-v1.json](references/codel-combined-v1.json).
- Original candidate: `runs/phase4b6-1-codel-v3/`, unchanged.
- Separate read-only snapshot: `runs/references/codel-combined-v1/`.
- Full manifest: `runs/references/codel-combined-v1/manifest.json`.
- Manifest SHA-256:
  `31a781ebc41f74fd81031dac37cc2a5d4b60d90310ccdb3f4d8ca1ddf772948e`.
- Acceptance record: `user-review.json` inside the snapshot, separately hashed.

The full manifest hashes **1,806 files**: all relevant candidate stages, editable
projects, PSD, original and portable exports, seven expressions, physics, motions,
validation reports and captured frames; original input, source layers, review
gallery/recording, provenance and dependency locks. Browser profiles, process
symlinks and the empty lock file are excluded. They remain at the original run.
The snapshot occupies approximately 479 MiB; generated files and artwork remain
outside Git. The small tracked manifest pins the full manifest hash, principal
artifacts, every runtime-folder file, feature configuration and known limitations.

Files are mode 0444 and directories 0555. This prevents accidental writes; it is
not root-proof storage. Integrity is established by the Git-pinned SHA-256 manifest.
Never repin or regenerate v1 in place. A future revision needs a new reference ID,
fresh artifacts and its own review. Do not run creation/resume commands with the
reference snapshot as the output directory.

The editable authoring project SHA-256 is
`8786087be08dce293e1c7b6d4e42ba287421bf87250f3c2379643db9f3661775`;
the PSD is
`53427e2dc0a916c61916a05abd30d2359e4f47f3d0f4f2c9a8f1a38474b2fca2`.
All other exact paths and hashes are in the tracked identity and full manifest.
Model3 hashes alone are insufficient because referenced MOC and expression contents
can change without changing the reference document.

Source remains LisadiKaprio's **Codel Visual Novel Sprite**, CC BY 4.0, from
OpenGameArt. The selected unmodified `Codel3.png` SHA-256 is
`98589fb8750ccfc3664935985fc42810381b2e09f22e1ae8cf4cd6dd45d39a2d`.
The manifest preserves archive provenance, attribution, selection exposure and
uncertainty about semantic ownership and reconstructed hidden pixels. It also
records the exact authoring configuration and source-code hashes. Historical
provenance's `user_acceptance=false` refers to the earlier benchmark; it is not
rewritten to imply that every earlier candidate was accepted.

## Acceptance and validation are separate

The new user-review record binds the whole runtime inventory and editable project.
The earlier development-review record and automated reports remain unchanged,
including their historical pending-review labels and failed attempts. They are
not converted into user approval or silently rewritten as passing reports.

Freeze verification established:

- All completed creation-stage inventories and `performance.json` output hashes
  match. The saved development-review runtime inventory, project and evidence
  hashes also match. Portable model references validate.
- Confused retains roundness=1, opening=.35 and curve=0. Surprised opening=.85 and
  all seven expression recipes remain pinned. Idle is 16 seconds; Idle, Nod and
  Question contain no mouth channels. Head X/Y/Z, breathing, independent blink
  channels and both hair-physics outputs remain present.
- Fresh installed-Core probes pass **819 mouth poses** and **496 body poses**.
  The old absolute seam result remains false; the previously reviewed structural/
  scale-aware contract remains unchanged. No threshold was weakened.
- The prior 481-pose exact body preservation comparison, 476-frame body suite,
  355-frame Confused coexistence suite, 213 mouth frames, 401 dense frames and
  72 eye samples remain hash-bound. These already demonstrate head/hair/breathing,
  gestures, expression/talking coexistence and exact neutral reload.
- The fresh `create` reproduction also passes its actual 401-frame browser suite
  and 72-sample eye/Core audit. This is separate from user acceptance of v1.
- **2,863 historical reference files**, including historical golden fixtures and
  accepted models, verify against the earlier reference inventory. The sealed
  Codel first run is unchanged. No rejected attempt was deleted or repaired.
- Girl2's **1,716 inherited visible lip reversals remain failed**. The old Codel
  `1e-7` seam failure remains failed. Their exact reports are pinned separately.

The plain cavity, existing eye/shading artifacts, uncertain facial backing,
conservative 2D head turn and shared unsided arms remain limitations. No independent
arm gestures, recovered anatomy, phonemes or professional-quality claim is added.

## Autonomous workflow verification

No individual rig operations were performed by Codex in this phase. Fresh,
unmodified CLI invocations drove the existing local PSD2Live workflow:

1. `prepare-performance` started from the preserved first-run creation output,
   applied coordinated mouths followed by calm body motion, and exported a fresh
   candidate under `runs/phase4b6-2-performance-check/`.
2. `create` used the original Codel PNG with its existing source-matched
   See-through bridge and SAM outputs, `deterministic` reconstruction, `aligned`
   facial motion, `coordinated` mouths and `calm` body motion. It regenerated the
   deterministic preparation and authoring stages and ran browser validation under
   `runs/phase4b6-2-create-check/`. No neural inference or downloads occurred.

The semantic checkpoint was retained. Its fresh quality evidence was byte-identical
to the already reviewed evidence (`161e2e45…abe46263`), so the existing, explicitly
labelled development-agent semantic review was reused unchanged. No fresh user
visual approval was invented for the rebuild.

**Both workflows reproduce all 15 model/runtime-referenced files byte-for-byte**,
including MOC, texture, seven expressions, physics, display metadata, three motions
and model3. The extra editor `.cmo3` and `.can3` containers differ between exports;
we do not claim bitwise identity of every editor source/archive. The first broad
all-folder comparison that detected these differences remains in the audit.

Both completed runs resume successfully without loopback access in the sandbox,
reusing their verified stages. Neither Codex nor an LLM is a runtime dependency.
The local MCP editor is needed for new authoring; the standalone viewer needs only
the exported model and installed local Cubism/PIXI libraries.

## Reproduction commands

For another character with an existing reviewed creation run using deterministic
facial preparation and aligned facial motion:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio prepare-performance \
  --baseline runs/OTHER-character-aligned \
  --output runs/OTHER-character-combined \
  --mouths coordinated --body-motion calm
```

Replace the two run paths. The command derives bindings from that character's
inspected semantic parts and geometry. Missing prerequisites are errors, not
permission to invent anatomy. The result still requires that character's review.

The complete `create` configuration, using existing matching inference outputs
and no new inference, is:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen live2d-studio create \
  --input assets/input/OTHER-character.png \
  --output runs/OTHER-character-combined \
  --rights 'REPLACE WITH VERIFIED SOURCE RIGHTS' \
  --decomposition runs/OTHER-existing/bridge \
  --sam runs/OTHER-existing/sam \
  --reconstruction deterministic --facial-motion aligned \
  --mouths coordinated --body-motion calm --no-preview
```

Replace input/cache/output paths and source rights with the other character's
values. Keep the semantic checkpoint: inspect its evidence, record the appropriate
review with `review-create`, then repeat the **same command and flags** to resume.
Never copy Codel's semantic review to another character. `create` also retains the
final visual-review gate. Source-matched caches are required by the no-inference
recipe above; omitting them would invoke the worker and was not done here.

The exact Codel reproduction arguments are retained in
`runs/phase4b6-2-audit/create-command.json`; use fresh output paths for another run.
Both optional feature defaults remain `preserve`; facial motion still defaults to
`legacy`, and reconstruction to `deterministic`.

## Regression verification and stop

The complete Python suite passes **152 tests** (including all six new reference
checks); JavaScript passes five talk-lifecycle tests and three numerical-contract
tests. Fresh verification reports and test logs are separately SHA-256-pinned in
the small tracked reference manifest, outside the immutable snapshot.

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python -m unittest discover -s tests -v
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python -m unittest discover \
  -s tests -p test_reviewed_codel.py -v
node --test tests/test_rp_talk.mjs tests/test_mouth_invariant.cjs
```

The reference tests check the immutable manifest, original candidate, all payload
hashes, read-only permissions, accepted feature channels and limited acceptance.
They also reject a modified Confused exp3 even when model3 is unchanged, retain
historical failures, and verify explicit options/defaults on both CLI entry points.
Local artifact tests skip when the intentionally untracked snapshot is absent;
tracked metadata and CLI contract tests still run.

Only documentation, tests and the small reference manifest enter Git. Product code,
creation defaults, model locks, production settings and previous artifacts remain
unchanged. No inference, model download, training or deployment occurred.
Stop after Phase 4B.6.2.
