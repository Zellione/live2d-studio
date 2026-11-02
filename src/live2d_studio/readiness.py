"""Rig preparation analysis, deliberately separate from import and visual acceptance."""
from pathlib import Path
import numpy as np
from PIL import Image
from .manifest import load_validate,digest,write_json


def analyze(project,output):
    project,output=Path(project),Path(output)
    if output.exists():raise FileExistsError('Choose a new readiness report')
    data=load_validate(project)
    parts={}
    for layer in data['layers']:
        if np.array(Image.open(project/layer['rgba_path']))[...,3].max()==0:continue
        parts.setdefault(layer['role'],[]).append(layer['side'])
    pairs={r:all(s in parts.get(r,[]) for s in ('left','right')) for r in ('eyewhite','irides','eyelash','eyebrow')}
    missing=[r+':paired' for r,ok in pairs.items() if not ok]
    for r in ('face','neck','mouth','front_hair','back_hair'):
        if r not in parts:missing.append(r)
    report=dict(schema_version=1,manifest_sha256=digest(project/'layer_manifest.json'),
        available_parts=parts,paired_eye_parts=pairs,missing_basic_parts=missing,
        alternatives=dict(blink='prefer PSD2Live procedural eyelash/white rig; half/combined poses require review',
            mouth='prefer PSD2Live procedural lips; source mouth is not a complete mouth-interior model'),
        unprovided_structures=['separate pupils','eyelid skin','independently validated hidden face and neck',
            'teeth/tongue system','authored closed/open mouth variants'],
        generated_alternatives=[],
        decision='blocked-missing-basic-parts' if missing else 'eligible-for-reviewed-experiment',
        semantic_acceptance='not-established-by-part-presence',
        production_ready=False,manual_intervention='visual review required; no manual painting performed')
    write_json(output,report)
    return report
