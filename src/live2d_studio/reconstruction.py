"""Deterministic, bounded nearest-colour continuation; never a plausibility claim."""
import numpy as np
from scipy import ndimage as ndi


def reconstruct(rgba, visible, role, generated=False, max_fraction=.25, colour=None):
    support = visible.copy()
    if role in {'face', 'eyewhite', 'irides', 'neck', 'topwear'} and not generated:
        holes = ndi.binary_fill_holes(visible) & ~visible
        if role == 'eyewhite':
            # Fill horizontal gaps between two observed white edges, even if
            # the iris gap opens into an eyelid. No new outer contour is drawn.
            spans = np.zeros_like(visible)
            for row in range(visible.shape[0]):
                xs = np.flatnonzero(visible[row])
                if len(xs)>1:
                    spans[row,xs[0]:xs[-1]+1]=True
            holes |= spans & ~visible
        # Reject large unsupported fills and leave them explicitly unfilled.
        # An iris can cover most of an eye white. Permit bounded enclosed eye
        # holes, never extend the outer contour or infer occluded eyelid edges.
        limit = max_fraction if role != 'eyewhite' else max(max_fraction, 1.0)
        if holes.sum() <= visible.sum() * limit:
            support |= holes
    reconstructed = support if generated else support & ~visible
    output = np.zeros_like(rgba)
    output[visible] = rgba[visible]
    if reconstructed.any():
        if generated:
            # Analytic alternate shape uses a sampled dark colour, not anatomy.
            colour = np.asarray(colour, dtype=np.uint8)
            output[reconstructed] = (*colour, 255)
        else:
            nearest = ndi.distance_transform_edt(~visible, return_distances=False, return_indices=True)
            output[reconstructed] = rgba[tuple(nearest[:, reconstructed])]
            output[reconstructed, 3] = 255
    return output, reconstructed
