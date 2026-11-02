# Girl2 animation authoring

Work in progress: Phase 3, from accepted Phase 2.6 commit `addd895`.
The original `runs/phase2-6-oga-v2-build/character.psd2live` remains unchanged.

`recipes/girl2-animation.json` is the reviewed MCP recipe for this character;
`live2d_studio.animation.recipe` reproduces it using inspected brow axes. The
existing head/lean combinations all receive the new independent `ParamBrowMood`
axis. No raster layer, observed-pixel mask or texture changes. Seven expressions
combine brow inclination/height, eye multipliers, mouth form/additive opening and
small head offsets. The first inclination direction was rejected after rendering;
the checked-in recipe contains the corrected direction.

A 16-second Idle has modest X ±2°, Y ±0.8°, Z ±1.2°, body Z ±0.35°, breathing
and four authored blinks, including one double blink. Mouth opening is deliberately
absent from the motion, so text-talk remains independent. A two-second Nod returns
to zero. Eyes multiply the blink value; expressions add mouth/form offsets. Neutral
uses identity multipliers and zero offsets, with 0.45-second expression fades.

Hair tuning reduces sway/curl/perspective and follows head roll more closely.
Across matching static stress poses, maximum enclosed transparency decreased
502→349 pixels, with unchanged maximum small-component pixels (3). Neutral browser
RGBA is identical. Lid-curve/corner tuning does not supply missing skin eyelids;
intermediate blinks remain simplified. The rejected Phase 2.6 guard fill is unused.

Rebuild in a fresh directory, using an explicitly supplied local MCP token:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv run --frozen python scripts/build_phase3.py \
  --source runs/phase2-6-oga-v2-build/character.psd2live \
  --output runs/phase3-new-build
```

The script saves a snapshot of the current editor first, never discards unsaved
work, verifies the accepted input hash, authors through MCP, saves PSD/project,
reopens and exports. A different rig requires a separately reviewed recipe.
Connected authenticated MCP is the experimentally exercised route; the CLI needs
`PSD2LIVE_MCP_TOKEN` from the user environment and never reads profile secrets.

`animation.package` copies to a fresh runtime directory, selects only the authored
Idle/Nod groups, and adds `sillytavern_settings.json`. PSD2Live still exported
builtin motion files despite disabled presets; only selected references are used.
No binary/texture is patched. All 23 packaged files reproduce exactly in a second
packaging run. Optional `rp_animation` settings are ignored by upstream ST; their
isolated adapter is evaluated separately, not installed into production.
