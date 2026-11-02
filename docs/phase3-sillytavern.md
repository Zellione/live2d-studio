# Isolated SillyTavern RP integration

The real installed Extension-Live2d event handlers are exercised. Test messages
are synthetic assistant messages added to the disposable ST chat, rendered with
`addOneMessage`, then delivered through ST's `MESSAGE_RECEIVED` event. Tests do
not call `playTalk` or `updateExpression` directly. No LLM, real user chat, TTS,
audio lipsync or classifier-model inference is claimed.

Classification is mocked at `/api/extra/classify` in the isolated browser only.
Character selection can trigger earlier startup classification requests before the
mock is installed; these failed for missing local weights. The copied server sets
`extensions.models.autoDownload=false` (`local_files_only=true`); no classifier
weights were downloaded and no successful real classification is claimed.
The extension's real fetch/parser → `classify_mapping` → expression application
runs unchanged except for the explicitly isolated optional fixes described below.
Seven labels are tested through actual events, all 28 installed labels have a
portable mapping. Multiple labels share an expression; there is no `uncertainty`
label in the installed vocabulary. `sillytavern_settings.json` is read by the
actual extension when a character/model has no existing settings. It does not
replace existing user settings. No production settings were edited.

## Upstream findings and optional adapter

The upstream baseline can talk and switch expressions; short/long messages,
interruption, character switch and reload were observed. However:

- Non-OK classifier HTTP responses fall through without a label, causing
  `Cannot read properties of undefined (reading 'expression')`. ST catches this
  in its EventEmitter. `Runtime.exceptionThrown` alone misses the error: the QA
  now checks the logged `Error in event listener` as well. The retained first
  exploratory report's generic pass is **not** fallback acceptance; the verified
  negative regression reports fail and preserves two caught listener errors.
- `playTalk` uses `sin(elapsed milliseconds)` and asynchronous additive writes,
  yielding abrupt timing-dependent mouth jumps. It is text-duration animation.
- The bundled Cubism renderer adds its own fixed head/breath oscillation even
  after cursor parameter mappings are set to `none`. Measured idle X extended
  approximately −5.67…+6.72° in a 4.5 s baseline sample; combined samples reached
  about ±8.9°, beyond the authored ±2° idle.
- `force_loop` repeats the last explicit motion; leave it **off**. Also leave
  `force_animation` off: it reloads the model whenever a motion is requested.
- The renderer normally resets expressions when starting motions. The adapter
  enables its existing `preserveExpressionOnMotion` option.

`integrations/sillytavern/rp-talk.mjs` provides a frame-aligned, bounded smooth
mouth envelope, attached after motion evaluation and before expression composition.
Each new message cancels its previous session. Completion, reload and removal
release callbacks/timers and reset the mouth base; expressions may retain their
intentional resting offset (happy 0.1, surprise 0.3). Duration is text length ×
configured milliseconds, capped at 60 seconds. It is **not audio/phoneme lipsync**.

`scripts/patch_st_phase3.py` patches only an independently copied ST tree under
this repository's `.cache/`, requires `snapshot-hashes.json`, verifies the exact
upstream `live2d.js` SHA-256, and saves an unmodified backup. It refuses other
paths, unexpected versions and an already patched destination. It also adds
neutral HTTP/offline/unknown-label fallback, discards stale classifier responses
and prevents delayed older events from restarting speech. There is no production
installer. The upstream implementation and its negative evidence remain available.

The portable preset's `rp_animation` options opt this Girl2 into smooth talk and
use of authored idle. Upstream ignores these extra options. The optional patch
stops the renderer's extra breath/head channel for opted-in models, and sets the
renderer-wide preserve-expression-on-motion option in the isolated application.
This is not a generic multi-model integration guarantee.

## Reproduction

Use an isolated code copy and fresh browser profile, as in previous phases:

```sh
python3 scripts/prepare_st_smoke.py \
  --source /home/zelli/tools/ai/SillyTavern \
  --extension /home/zelli/tools/ai/SillyTavern/data/default-user/extensions/Extension-Live2d \
  --destination .cache/phase3-new-st
python3 scripts/patch_st_phase3.py .cache/phase3-new-st
```

Copy the **new** packaged runtime into that copy's
`data/default-user/assets/live2d/phase3/`. Start the copied server on loopback and
a dedicated Chrome profile with CDP on loopback. Run each scenario separately:

```sh
node scripts/cdp_smoke.mjs http://127.0.0.1:9227 \
  'http://127.0.0.1:8766/?qaAsset=phase3&mode=rp&adapter=1' \
  scripts/phase3_browser_scenario.js runs/phase3-new-rp
```

Other modes: `expressions`, `lifecycle`, `failure`, `race`, `visual`. Each output
must be new. `failure` injects HTTP 503; `race` returns an older joy classification
after a newer anger response. The upstream failure test is intentionally negative.
The lifecycle tests sample actual pre-Core-update values without overriding them;
only the separate expression pose test controls base poses to isolate blending.
`visual` records running idle/talk frames and derives the mouth ROI from Core
mouth/lip geometry, transformed through PIXI's real model transform.

`rp_qa.evaluate` requires all five event/lifecycle/visual scenarios, correct
applied expression parameters, measured mouth movement, resting-mouth recovery,
character cleanup, idle recovery and error-free network/event results. Its RP gate
is separate from visual acceptance and never grants production readiness.
