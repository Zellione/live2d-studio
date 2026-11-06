# Phase 4B.9 — reviewed multi-pose arm assessment

**The four-pose assessment is complete; the rig gate remains blocked.** The
selected family provides useful bilateral sleeve, cuff, hand and bend evidence.
It does not yet provide a reliable arm replacement for the exact accepted angled
Codel rig. No new PSD2Live project or gesture runtime was authored or promoted.

Continued from clean `998e86abc2cfab029cc8ca5fb69c824e61115d9a`. The user explicitly
confirmed **“Keep the exact accepted artwork and rig”** when asked about the
frontal canonical versus angled accepted model. This rules out replacing its
body or recreating its facial/head behavior on a different canonical rig.
The fifth pose stayed pending; no Qwen generation was performed.

## Frozen reviewed family

The live reviewer contained four explicit `reviewer_kind=human` accept records,
each bound to a candidate and image SHA-256. No screenshot, development screening
or presumed approval was used. There was no selected-set export, so the existing
selected-only export operation created `48fd4925948c4e72a7a9d636c8f7fffe`, manifest
SHA `469d5ac71c0576960a78ac2a216fcf4cf3652c0f0ec10a0829bd4d60783ae32b`.
The export operation did not create or change any image approval.

| Pose | Candidate | Approved image SHA-256 |
|---|---|---|
| Right forearm raised | `b-34832b77ecbf471f81ea1477f36adb21-c4` | `379af73a203cbd3fc5adc063a55950e33f0377b4d5572ccaa73631b04ff71810` |
| Left forearm raised | `b-9994d724922a44d6b3649b02bc871c57-c1` | `7050793b721a3cddbda846d59962fff2bcf259b0ae4816af0ee9c7f9033a46f1` |
| Right explanation | `b-e812a8e04218468ab7c00d5df8e81fd0-c1` | `69bda9774597898ed0078dcbe7d28edc0fe0a10a57d04308fa8cb70cde6f7430` |
| Left greeting/wave | `b-4c7c81e9db6845fb80ec470299b635d7-c1` | `903c48c14c5d24dfe8a577f85220a7f5ee7e454af855c2ba36b2e3688e03a9fd` |

`runs/phase4b9-family` contains read-only copies of these images, their exact
approval/configuration/prompt/guide metadata, the approved canonical neutral,
the original identity artwork and both provenance manifests. The
[benchmark](benchmarks/phase4b9.json) binds the family manifest hash.
Canonical SHA remains `ab2a52ae…d78da3e`; original SHA remains
`98589fb8…39a2d`. Full hashes are in the benchmark and family manifest.

Of 1,932 pre-inventoried files, 1,931 remain byte-identical. The only changed file
is the active review JSON, whose **only changed field is `exports`**. Pose states,
approvals, batches, seeds and guides are identical. Original/canonical payloads,
previous selections, historical Codel references, accepted Girl2/Sara assets and
production SillyTavern were not modified. The pending fifth slot was not relabelled.

## Visible anatomy and consistency

The unchanged local SAM parser analyzed only canonical neutral and the four
human-selected helpers. All outputs are 800 × 1536. Model:
`24yearsold/l2d_sam_iter2`, revision
`0b0608310fb7a89e32ecd7397147a249540cf1e7`, Apache-2.0; checkpoint SHA
`dda82b916f6c340bc5a6c3a077ff1214f9906906abe3707b1076d55b508f253f`.
The separate pinned See-through environment runs SAM in float32, Torch
2.8.0+cu128. Parser stages took 2.13–2.26 seconds per image, excluding startup,
with 4.66 GiB peak Torch allocation. No new weights or dependencies were installed.

| Image | Substantial arm regions | Right / left mask pixels | Arm–torso mask overlap |
|---|---:|---:|---:|
| Canonical neutral | 2 | 59,658 / 58,819 | 1,481 |
| Right raised | 2 | 52,416 / 53,288 | 1,442 |
| Left raised | 2 | 54,552 / 48,966 | 1,447 |
| Explanation | 2 | 36,282 / 54,317 | 1,540 |
| Wave | 2 | 54,144 / 51,410 | 1,272 |

These are mask measurements, not anatomical accuracy or hidden-coverage scores.
Components require at least max(32 pixels, 5% of the arm mask). Anatomical right
is viewer left for these inspected frontal, non-mirrored views. Component ordering
would not establish ownership for crossed or mirrored poses.

The family adds useful bent sleeves, exposed cuffs and different hand orientations
beyond canonical neutral. Shoulder **surfaces** are readable, but their top contours
are not observed joint pivots. Wrist hypotheses use skin-to-cloth transitions;
finger count/topology and ink boundaries remain visually reviewed, not certified
by the skin mask. Upper-arm/forearm partitions are proposals with unresolved
occlusion at bent sleeves. Sleeve shade and crease patterns vary across poses.

The canonical already exposes the torso front. The helpers do not independently
recover the original clothing behind its crossed forearm, underarm caps or hidden
joint backing. Apparent foreground/background ordering suggests a raised forearm
in front of its upper sleeve, but the merged cloth region does not establish depth
or separable overlapping textures.

| Bent view | Side | Projected upper / torso height | Projected forearm / torso height |
|---|---|---:|---:|
| Right raised | right | 0.658 | 0.384 |
| Explanation | right | 0.687 | 0.139 |
| Left raised | left | 0.633 | 0.348 |
| Wave | left | 0.558 | 0.432 |

The right upper estimates differ by about 4.5%, but its projected forearm differs
by **2.77×**. The left estimates differ by about 13.5% upper and 24.1% forearm.
These are uncertain cloth-axis projections: foreshortening, redraw and mask/joint
errors cannot be separated. They do not prove changing bone length. Straight
neutral sleeves permit many elbow locations and are excluded from these ratios.
No common fixed-length 2-D skeleton is validated by this family.

Early landmark passes are retained. A topmost-pixel heuristic mistook raised
fingers for shoulders; an RGB-only cuff test included dark skin/ink; a shortest
interior path cut across touching bent sleeves. The final method uses torso
adjacency, chromatic cloth/skin separation and a separate sleeve-lobe hypothesis.
It preserves alternative elbow locations and their disagreement. Yellow circles
are heuristic inspection regions, not calibrated confidence intervals. Orange
boxes explicitly mark unresolved straight-arm elbows.

## Articulation decision and tested failure

**A — continuous mesh/deformer articulation: defer.** The exact accepted rig has
one unsided `handwear` layer/mesh containing both crossed arms (260,082 observed
pixels, no generated arm backing in the inspected layer). Its original-view
shoulder/elbow/wrist ownership and overlapping cut lines are not resolved by a
frontal redraw. Its torso contains generated backing, but that backing has no new
anatomical approval. Rotating the merged component would not establish independent
motion; forcing the ambiguous cuts could damage the other arm or expose gaps.

**B — gesture-specific artwork: preferred next path, not yet rig-ready.** A
canonical-only diagnostic registered the approved right-raised arm by torso
height and shoulder surface, then kept all other pixels fixed. Its endpoint has
a visible shoulder cut seam and residual original outline pixels. In 21 sampled
neutral→pose→neutral frames, every intermediate fade shows displaced old/new arms
simultaneously. Returning to neutral is byte-identical and pixels outside the arm
union stay exact, but those numerical properties do not make the transition usable.
A hard switch avoids translucent duplicate arms; it still needs a clean attachment,
backing and source-view correspondence. The probe is not a PSD2Live animation.

This failed simple compositor does **not** prove that all hybrid techniques are
impossible. It demonstrates that current automatic masks and registration are
insufficient. The exact accepted angled rig adds the unresolved original arm split;
substituting a frontal body would violate the user's confirmed constraint. The
conditional rig gate therefore stops this phase **before authoring**, as requested
when reliable articulation is not sufficiently supported.

## Fifth guide and next step

The saved torso-open guide puts the right upper arm only **13.42° from vertical**
(and shoulder-to-wrist axis 13.17°), so it supplies a modest outward displacement,
not the distinct abducted silhouette requested in feedback. Its image, definition
and reviewer history are unchanged. A future version can request 40–55° upper-arm
abduction, but must check the existing frame: a fully extended arm may leave it.
A bent forearm may be needed to keep the hand visible. Use a versioned definition
and fresh run; none was created or generated here.

Recommended next step: review **original-view bilateral arm cut lines, one elbow
and shoulder attachment, and the backing revealed when that arm moves**, using
this selected family as uncertain shape/clothing evidence. Then test one discrete
gesture layer in a cloned accepted project. The fifth helper is not required.
No further articulation begins before user review of these proposals.

## Review and regressions

- [Assessment gallery](http://127.0.0.1:8805/): `runs/phase4b9-review-final`.
- [Unchanged accepted live rig](http://127.0.0.1:8806/): no production server needed.
- [Method and repeatable commands](phase4b9-arm-assessment.md).
- Frozen family, raw SAM, final geometry, failed attempts and hybrid probe remain
  in ignored `runs/phase4b9-*` directories.

215 Python tests pass, including nine new selection/inference/geometry checks;
the final changed-module subset also passes. Both existing JS suites pass (5 talk,
3 mouth-invariant tests). Fresh accepted-runtime regressions pass 496 body and 819
mouth/expression Core samples plus 401 dense facial, 476 body and 355 coexistence
browser frames. Head/hair/breathing, mouth/expression composition, Nod/Question and
exact neutral reset/reload remain intact. Browser scenarios report no failed or
external requests. Core reports reproduce the frozen report hashes exactly.

The legacy absolute seam test remains false; the existing MOC-bound structural/
float32 contract passes unchanged. Raw opacity excursions remain recorded (220
mouth Core; 132 dense, 825 body, 55 coexistence browser samples), with no invalid
opacity under the existing policy. No threshold or historical failure was waived.
A first gallery check lacked its scenario file; the corrected check passed all 20
images and five approved-family entries. The failed diagnostic is retained.

These runtime checks prove preservation of the **old** rig, not a new arm system.
There is no experimental MOC/PSD2Live project to approve. Stop after Phase 4B.9's
assessment gate, with no promotion, deployment, final arm rig or new pose generation.
