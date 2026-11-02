# Phase 0 fixture provenance

Created locally on 2026-11-02 for format testing. `tile.png` is a uniform
64×64 RGBA image (40, 180, 220, 255), placed at (32,32) on a 128×128 canvas.
No third-party illustration or model was used. The trivial geometric input
is original test data; no external asset license is required. No bundled
Live2D runtime is redistributed here.

PSD2Live **3.6.7** generated the source archive, PSD and export. The installed
JAR hash and the installed runtime hashes are in
`docs/evidence/phase0/installation.json`. Export diagnostics are retained in
`docs/evidence/phase0/export.json`. PSD2Live is GPL-3.0 according to upstream;
this does not imply that Live2D Cubism Core has an open-source license.

To regenerate using the connected PSD2Live MCP:

1. `workspace_overview` / `workspace_inspect`: obtain current state and ensure
   there is no unsaved user project. Never use `discard_unsaved=true` here.
2. `workspace_call(project_create_artwork)` with `width=128`, `height=128`,
   `layers=[{path: ABSOLUTE_TILE_PNG, name:"phase0-tile", role:"objects", x:32, y:32}]`
   and the current `state`. Wait for a completed job; retain returned state/project ID.
3. `project_save_as` to a fresh `tile.psd2live` path; `project_export_psd`
   with `scale=1` to `tile.psd`; `project_export_model` to a fresh output directory.
   Pass the returned current state and project ID to each operation.
4. Run the commands in `docs/compatibility.md` against the new model JSON.

The export includes generated motion/expression files and parameter IDs, but
no eye or mouth artwork. It is **not a character rig**. It cannot demonstrate
blinking, lip sync, emotional expressions or realistic head motion.
