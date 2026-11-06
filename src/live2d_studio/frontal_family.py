"""Fresh frontal helper run retaining exact prior human selections and history."""
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import shutil
from PIL import Image, ImageDraw
from .canonical_reference import initialize_helpers
from .frontal_master import load
from .gesture_profile import PROFILE, COMMON, definition, guide
from .pose_review import Store, digest, fingerprint, REPO

VERSION = 'frontal-family-v2'


def aside_guide(image, side, kind):
    _, points = guide(image, 'torso-open', kind)
    prefix = 'r' if side == 'right' else 'l'
    # Restore the relaxed opposite arm from the opposite lift's unaffected side.
    _, rest = guide(image, 'left-lift' if side == 'right' else 'right-lift', kind)
    points = rest
    shoulder = points[prefix+'s']; old_elbow = points[prefix+'e']
    length = math.dist(shoulder, old_elbow)
    direction = -1 if side == 'right' else 1
    angle = math.radians(24)
    elbow = (shoulder[0]+direction*length*math.sin(angle), shoulder[1]+length*math.cos(angle))
    wrist = (elbow[0]-direction*image.width*.035, elbow[1]+image.height*.18)
    points[prefix+'e'] = elbow; points[prefix+'w'] = wrist
    # The opposite-lift guide must be reset to a relaxed elbow/wrist.
    other = 'l' if side == 'right' else 'r'
    _, relaxed = guide(image, 'right-lift' if side == 'right' else 'left-lift', kind)
    for suffix in ('e','w'): points[other+suffix] = relaxed[other+suffix]
    if any(not (8 <= x < image.width-8 and 8 <= y < image.height-8) for x,y in points.values()):
        raise ValueError('Aside guide exceeds framing; mark unsupported or use a separately reviewed wider frame')
    result = Image.new('RGB', image.size, 'black' if kind == 'skeleton' else 'white')
    d = ImageDraw.Draw(result); unit = max(3, round(image.height/180))
    if kind == 'silhouette':
        d.polygon([points[k] for k in ('rs','ls','lh','rh')], fill='#aaaaaa')
        x,y = points['nose']; radius = image.height*.07
        d.ellipse((x-radius,y-radius,x+radius,y+radius), fill='#aaaaaa')
    edges = [('nose','neck'),('neck','rs'),('rs','re'),('re','rw'),('neck','ls'),('ls','le'),('le','lw'),('neck','rh'),('rh','rk'),('neck','lh'),('lh','lk'),('rh','lh')]
    for a,b in edges: d.line([points[a],points[b]], fill='#777777' if kind == 'silhouette' else '#ffbb55', width=unit*5 if kind == 'silhouette' else unit)
    for x,y in points.values(): d.ellipse((x-unit,y-unit,x+unit,y+unit),fill='white' if kind=='skeleton' else '#555555')
    return result, points


def initialize(master, output, presets):
    data = load(master); family_root = REPO / data['family']['path']
    family = json.loads((family_root / 'family.json').read_text())
    old = Store(REPO / family['review_run']); fd = old.gpu_lock()
    try:
        state = old.state(); old.verify_pins(state)
        target = initialize_helpers(REPO / data['canonical_run'], output, presets,
                                    gesture_profile=PROFILE, lightning=True)
        with target.transaction() as current:
            current['poses'].pop('torso-open')
            image = Image.open(target.safe(current['source']['path']))
            for side in ('right','left'):
                key = side+'-aside-v2'
                row = {'title': 'Anatomical '+side+' arm moved aside (24° upper-arm guide)',
                       'status': 'pending', 'selected': None, 'guides': {},
                       'prompt': COMMON + 'Move the anatomical '+side.upper()+' upper arm outward following the guide, making a clear side silhouette. Bend the forearm slightly inward to keep the hand in frame. The other arm stays relaxed. Do not leave both arms in the original arms-down silhouette.'}
                for kind in ('silhouette','skeleton'):
                    rendered, points = aside_guide(image,side,kind)
                    name = 'assets/'+key+'-'+kind+'.png'; rendered.save(target.root/name)
                    row['guides'][kind] = {'path':name,'sha256':digest(target.root/name),'joints':points}
                current['poses'][key] = row
            selected = set(family['images']) - {'canonical'}
            for pose in selected:
                if state['poses'][pose]['approval'] != family['images'][pose]['approval']:
                    raise ValueError('Frozen human selection differs from live review')
                current['poses'][pose] = deepcopy(state['poses'][pose])
                for row in current['poses'][pose]['guides'].values():
                    shutil.copyfile(old.safe(row['path']), target.safe(row['path']))
            for batch in state['batches']:
                if batch['pose'] in selected:
                    if batch['status'] == 'running': raise ValueError('Active batch must finish')
                    shutil.copytree(old.safe(batch['directory']), target.safe(batch['directory']))
                    current['batches'].append(deepcopy(batch))
            current['events'] = [deepcopy(e) for e in state['events'] if e.get('pose') in selected]
            current['used_seeds'] = deepcopy(state['used_seeds'])
            current['gesture_profile'] = VERSION
            current['gesture_definition_sha256'] = fingerprint(definition(current))
            current['producer_pins']['src/live2d_studio/frontal_family.py'] = digest(REPO/'src/live2d_studio/frontal_family.py')
            current['master_origin'] = {'manifest_sha256':digest(Path(master)/'master.json'),
                'family_sha256':data['family']['sha256'], 'previous_review':str(old.root),
                'approval_policy':'Exact copied human decisions; no automatic new approval',
                'legacy_torso_open':'Preserved only in historical run; new v2 definitions are separate'}
        target.verify_pins(target.state())
        return target
    finally:
        os.close(fd)
