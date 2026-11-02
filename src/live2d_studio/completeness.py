"""Reviewed source inventory, independent of framing and parser part names."""
PARTS = ('shoulder', 'upper_arm', 'elbow', 'forearm', 'hand', 'thigh', 'knee', 'lower_leg', 'foot')
VISIBILITY = {'visible', 'partially-visible', 'occluded', 'canvas-truncated', 'not-depicted', 'uncertain'}


def measure_visible_limb(source, mask, layers, semantic_owners):
    """Evaluate a supplied independent source mask; never infer source absence.

    Layers contain RGBA and protected-original masks on the source grid. This
    measures pixel ownership only; connectivity/deformation still need review.
    No independent arm/hand benchmark is currently available in this repository.
    """
    import numpy as np
    mask = np.asarray(mask, dtype=bool)
    source = np.asarray(source)
    if source.shape != (*mask.shape, 4) or not mask.any():
        raise ValueError('Nonempty independent source mask and matching RGBA required')
    counts = np.zeros(mask.shape, dtype=np.uint16)
    semantic = np.zeros(mask.shape, dtype=bool)
    exact = np.zeros(mask.shape, dtype=bool)
    for name, rgba, observed in layers:
        rgba, observed = np.asarray(rgba), np.asarray(observed, dtype=bool)
        if rgba.shape != source.shape or observed.shape != mask.shape:
            raise ValueError('Limb evidence grid mismatch')
        owned = observed & (rgba[..., 3] > 0)
        counts += owned
        exact |= owned & np.all(rgba == source, axis=2)
        if name in semantic_owners:
            semantic |= owned
    lost = int(np.count_nonzero(mask & (counts == 0)))
    duplicate = int(np.count_nonzero(mask & (counts > 1)))
    wrong = int(np.count_nonzero(mask & (counts > 0) & ~semantic))
    total = int(mask.sum())
    return dict(source_pixels=total, lost_pixels=lost, unassigned_pixels=lost,
                duplicate_pixels=duplicate, wrong_semantic_pixels=wrong,
                exact_rgba_pixels=int(np.count_nonzero(mask & exact & (counts == 1))),
                alpha_recall=(total-lost)/total,
                structural_preservation='pass' if not (lost or duplicate or wrong) else 'blocked',
                animation='requires-visual-review')


def analyze(inventory):
    failures, review = [], []
    if inventory.get('framing') not in {'portrait/bust', 'half-body', 'full-body'}:
        failures.append('Unknown framing')
    if not inventory.get('source_review') or not inventory.get('full_canvas_reviewed'):
        review.append('Independent full-source visual inventory required')
    rows = inventory.get('limbs', [])
    expected = {(side, part) for side in ('image-left', 'image-right') for part in PARTS}
    actual = [(r.get('image_side'), r.get('part')) for r in rows]
    if set(actual) != expected or len(actual) != len(expected):
        failures.append('Complete bilateral inventory required; absent parser labels are not source absence')
    for r in rows:
        name = f"{r.get('image_side')} {r.get('part')}"
        v = r.get('source_visibility')
        if v not in VISIBILITY or not r.get('source_evidence'):
            review.append(name + ': source visibility needs review')
        if r.get('anatomical_side') not in {'left', 'right', 'unknown'}:
            failures.append(name + ': anatomical side required separately')
        if v in {'visible', 'partially-visible', 'canvas-truncated'}:
            p = r.get('preservation', {})
            if p.get('status') != 'reviewed-preserved' or not p.get('evidence'):
                failures.append(name + ': preservation unverified')
            if any(p.get(k, 0) for k in ('lost_pixels', 'unassigned_pixels', 'duplicate_pixels', 'wrong_semantic_pixels')):
                failures.append(name + ': lost/unassigned/duplicated source pixels')
            if r.get('semantic_ownership') not in {'reviewed-separated', 'reviewed-clothed-silhouette'}:
                failures.append(name + ': merged/unknown semantic ownership')
            if r.get('semantic_ownership') == 'reviewed-clothed-silhouette' and r.get('source_surface') != 'clothing':
                failures.append(name + ': visible anatomy cannot pass as clothing')
            if r.get('animation') not in {'independent-reviewed', 'follows-body-only', 'static-reviewed'}:
                review.append(name + ': animation capability unreviewed')
            if not r.get('neutral_and_motion_review'):
                review.append(name + ': neutral and combined-motion review required')
        if v == 'uncertain':
            review.append(name + ': uncertain source anatomy')
    return dict(framing=inventory.get('framing'), portrait_completeness='pass' if not failures and not review else 'blocked',
                failures=failures, visual_review_required=review, general_limb_preservation_validated=False,
                anatomical_completeness=False, generated_anatomy=False)
