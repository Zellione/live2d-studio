# Responsive gesture controls

From `98e7cc3`, the gesture container was a non-wrapping flex row. Actual Chrome
rendering reproduced three buttons extending beyond the comparison panel at 140%
page zoom. The hotfix makes only `#gestures` a two-column grid with shrinkable,
wrapping buttons. Other `.row` controls retain their original flex behavior.
At widths up to 360 CSS pixels, reduced page/panel padding also accommodates the
existing controls without horizontal scrolling. No JavaScript, rig, motion,
expression, model asset or frozen reference was changed.

Validation used the installed Chrome and Cubism runtime with the immutable
`codel-frontal-elbows-v1` bundle. A disposable browser profile applied real page
zoom through Chrome's settings API; observed `devicePixelRatio` confirmed each
requested factor. No personal browser settings were read or changed.

- Both single-model and comparison viewers passed 60 layout cases: five zoom
  levels (100/125/140/150/200%), three window widths (1440/960/640), and original
  versus long German/Japanese labels, including unbroken words. The smallest
  effective viewport was 320 CSS pixels.
- Container/button rectangles stayed within the panel; text and document widths
  showed no horizontal overflow. Existing two-button rows stayed non-wrapping flex.
- Twelve actual pointer clicks exercised all six gestures in both viewers.
  Each changed its intended Core parameter and visible rendered geometry.
- Seven preview tests, four frozen-reference tests, and both existing JavaScript
  suites passed. All 225 reference files, including the manifest, remained exact.
- Evidence: `runs/ui-gesture-hotfix-v2/result.json`, `preservation.json` and
  single/comparison 140% screenshots. The original-overflow control and the first
  mobile-padding failure remain in ignored runs. No geometry gate was changed.

Reproduce with a fresh ignored output and the existing local runtime/reference:

```sh
uv run --frozen python scripts/gesture_layout_acceptance.py \
  --output runs/my-gesture-layout-check
uv run --frozen python -m unittest discover -s tests -p test_preview_live.py -v
uv run --frozen python -m unittest discover -s tests -p test_reviewed_elbows.py -v
node tests/test_rp_talk.mjs
node tests/test_mouth_invariant.cjs
```

Preview servers preload UI assets. Restart the relevant standalone preview server
after updating, then reload its browser page. Production SillyTavern is untouched.
