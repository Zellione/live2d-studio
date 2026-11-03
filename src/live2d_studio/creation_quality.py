"""Conservative candidate gates; semantic and visual review cannot be inferred from names."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from .manifest import load_validate, digest, write_json

CHECKS = ('semantic_ownership', 'hidden_face', 'source_preservation', 'visible_limbs')
VISUAL_CHECKS = ('blink', 'mouth', 'head_overlap', 'expressions', 'holes_contours', 'visible_limbs')


def analyze(project, output):
    project, output = Path(project), Path(output)
    data = load_validate(project)
    quality = json.loads((project/'quality.json').read_text())
    reasons = list(quality['structural_semantics']['reasons'])
    roles = {}
    for layer in data['layers']:
        alpha = np.array(Image.open(project/layer['rgba_path']))[..., 3] > 127
        if alpha.sum() < 4:
            continue
        roles.setdefault(layer['role'], []).append(layer['side'])
    for role in ('eyewhite', 'irides', 'eyelash', 'eyebrow'):
        if set(roles.get(role, [])) != {'left', 'right'}:
            reasons.append('Missing paired ' + role)
    for role in ('face', 'mouth', 'neck'):
        if role not in roles:
            reasons.append('Missing ' + role)
    if 'unknown' in roles:
        reasons.append('Unresolved semantic layers')
    if (quality['fidelity']['exact_fraction'] or 0) < .995:
        reasons.append('Less than 99.5% exact foreground preservation')
    if (quality['fidelity']['silhouette_iou'] or 0) < .995:
        reasons.append('Source silhouette incomplete')
    report = dict(schema_version=1, manifest_sha256=digest(project/'layer_manifest.json'),
        decision='blocked' if reasons else 'needs-semantic-review', blocking_reasons=reasons,
        fidelity=quality['fidelity'], structural_semantics=quality['structural_semantics'],
        source_samples_copied=quality['source_samples_copied'],
        small_components=quality['small_components'], available_roles=roles,
        limb_inventory=dict(status='requires-source-review',
            candidates={k:v for k,v in roles.items() if k in ('handwear','topwear','legwear','footwear')},
            caveat='Clothing names do not identify anatomy. Review bilateral shoulders, arms, hands, legs and feet against input; record absent, cropped, preserved or misassigned.'),
        required_review=list(CHECKS), production_ready=False)
    write_json(output/'quality.json', report)
    return report


def validate_review(review, evidence_hash, checks):
    if review.get('evidence_sha256') != evidence_hash:
        raise ValueError('Review is stale or belongs to different artifacts')
    if review.get('decision') != 'accept':
        raise ValueError('Candidate rejected by reviewer')
    if not review.get('reviewer') or not review.get('notes'):
        raise ValueError('Review requires reviewer and notes')
    if set(review.get('checks', [])) != set(checks):
        raise ValueError('Review must cover all required checks')
    return review
