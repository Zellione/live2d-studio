"""Conservative flat-colour baseline. No fixture metadata or trained weights."""
from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi


@dataclass
class Region:
    role: str
    side: str
    mask: np.ndarray
    z: int
    generated: bool = False
    default_visible: bool = True
    colour: tuple | None = None


def bounds(mask):
    y, x = np.nonzero(mask)
    if not len(x):
        raise ValueError("Empty region")
    return int(x.min()), int(y.min()), int(x.max() + 1), int(y.max() + 1)


def foreground(rgba):
    """Keep input alpha, or remove only a uniform border-connected background."""
    alpha = rgba[..., 3].copy()
    if np.any(alpha < 255):
        return alpha, "input-alpha"
    rgb = rgba[..., :3].astype(np.int16)
    border = np.concatenate((rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]))
    colour = np.median(border, axis=0)
    if np.mean(np.max(abs(border - colour), axis=1) <= 12) < .95:
        return alpha, "unresolved-background"
    candidate = np.max(abs(rgb - colour), axis=2) <= 12
    seeds = np.zeros_like(candidate)
    seeds[0] = candidate[0]
    seeds[-1] = candidate[-1]
    seeds[:, 0] = candidate[:, 0]
    seeds[:, -1] = candidate[:, -1]
    background = ndi.binary_propagation(seeds, mask=candidate)
    alpha[background] = 0
    return alpha, "uniform-border-flood"


def segment(rgba):
    """Infer candidate roles from quantized colour components and relative geometry.

    Screen-left is PSD2Live's left convention, as in the accepted Phase 1 art.
    Unclassified pixels survive in an explicitly unknown layer.
    """
    alpha, background = foreground(rgba)
    rgb = rgba[..., :3].astype(np.int16)
    fg = alpha > 0
    codes = (rgb[..., 0] // 16) * 256 + (rgb[..., 1] // 16) * 16 + rgb[..., 2] // 16
    colours, counts = np.unique(codes[fg], return_counts=True)
    candidates = []
    # Bounded work on photos/gradients; never silently claim complete parsing.
    for code in colours[np.argsort(-counts, kind="stable")[:48]]:
        if len(candidates) >= 96:
            break
        labels, _ = ndi.label((codes == code) & fg)
        sizes = np.bincount(labels.ravel())
        eligible = np.flatnonzero(sizes[1:] >= max(4, fg.size // 30000)) + 1
        eligible = sorted(eligible, key=lambda n:(-sizes[n],n))[:4]
        for label in eligible[:96-len(candidates)]:
            mask = labels == label
            x0, y0, x1, y1 = bounds(mask)
            colour = np.median(rgb[mask], axis=0)
            candidates.append(dict(mask=mask, colour=colour, area=int(mask.sum()),
                                   x=(x0+x1)/2, y=(y0+y1)/2, box=(x0,y0,x1,y1)))
    regions, used = [], set()

    def add(c, role, z, side="none"):
        used.add(id(c))
        regions.append(Region(role, side, c["mask"], z))

    warm = [c for c in candidates if c['colour'][0] > c['colour'][1] > c['colour'][2]
            and c['colour'][0] > 150 and c['colour'][1] > 100]
    if warm:
        face = max(warm, key=lambda c: c['area'])
        x0, y0, x1, y1 = face['box']
        fw, fh = x1-x0, y1-y0
        add(face, 'face', 30)
        inside = lambda c: x0 < c['x'] < x1 and y0 < c['y'] < y1
        whites = [c for c in candidates if inside(c) and np.min(c['colour']) > 220
                  and y0 + .2*fh < c['y'] < y0 + .65*fh and c['area'] > 10]
        whites = sorted(sorted(whites, key=lambda c: -c['area'])[:2], key=lambda c:c['x'])
        paired = len(whites) == 2 and whites[0]['x'] < face['x'] < whites[1]['x']
        if paired:
            for eye, side in zip(whites, ('left', 'right')):
                add(eye, 'eyewhite', 40, side)
                ex0, ey0, ex1, ey1 = eye['box']
                ew, eh = ex1-ex0, ey1-ey0
                dark = [c for c in candidates if id(c) not in used and np.mean(c['colour']) < 150
                        and abs(c['x']-eye['x']) < ew*.65]
                irises = [c for c in dark if ey0 <= c['y'] <= ey1
                          and c['box'][3]-c['box'][1] > eh*.3]
                if irises:
                    add(max(irises, key=lambda c:c['area']), 'irides', 50, side)
                lines = [c for c in dark if id(c) not in used
                         and c['box'][2]-c['box'][0] > ew*.5
                         and c['box'][3]-c['box'][1] < eh*.5]
                lids = [c for c in lines if ey0-eh*.6 < c['y'] < ey0+eh*.3]
                if lids:
                    lid = max(lids, key=lambda c:c['area'])
                    add(lid, 'eyelash', 60, side)
                    closed = ndi.shift(lid['mask'].astype(np.uint8),
                                       (round(eye['y']-lid['y']), 0), order=0) > 0
                    regions.append(Region('eye_close', side, closed, 61, True, False, tuple(lid['colour'])))
                brows = [c for c in lines if id(c) not in used
                         and y0 < c['y'] < ey0-eh*.4]
                if brows:
                    add(max(brows, key=lambda c:c['y']), 'eyebrow', 70, side)
        noses = [c for c in warm if id(c) not in used and inside(c)
                 and abs(c['x']-face['x']) < fw*.12 and .5 < (c['y']-y0)/fh < .75]
        if noses:
            add(max(noses, key=lambda c:c['area']), 'nose', 75)
        mouths = [c for c in candidates if id(c) not in used and inside(c)
                  and c['y'] > y0+fh*.65 and abs(c['x']-face['x']) < fw*.2
                  and c['colour'][0] > c['colour'][1]*1.5 and c['colour'][1] < 100]
        if mouths:
            mouth = max(mouths, key=lambda c:c['area'])
            add(mouth, 'mouth_open', 80)
            close = mouth['mask'].copy()
            yy = np.indices(close.shape)[0]
            close &= abs(yy-mouth['y']) <= max(1, (mouth['box'][3]-mouth['box'][1])*.08)
            regions.append(Region('mouth_close', 'none', close, 81, True, False, tuple(mouth['colour'])))
        necks = [c for c in warm if id(c) not in used and c['y'] > face['y']+fh*.4
                 and abs(c['x']-face['x']) < fw*.25]
        if necks:
            add(max(necks, key=lambda c:c['area']), 'neck', 10)
        torsos = [c for c in candidates if id(c) not in used and c['y'] > y1
                  and c['box'][2]-c['box'][0] > fw*.4]
        if torsos:
            add(max(torsos, key=lambda c:c['area']), 'topwear', 20)
    assigned = np.zeros(fg.shape, bool)
    for region in regions:
        if not region.generated:
            assigned |= region.mask
    if np.any(fg & ~assigned):
        regions.append(Region('unknown', 'none', fg & ~assigned, 90))
    if not regions:
        raise ValueError('No foreground pixels detected')
    return sorted(regions, key=lambda r:(r.z, r.side)), alpha, background
