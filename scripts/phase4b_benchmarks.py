"""Repeat cached real-art regressions; GT is evaluation-only, never a creation input."""
import argparse
import json
from pathlib import Path
import sys
from live2d_studio.creation import create, review
from live2d_studio.manifest import write_json
from evaluate_oga import evaluate


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    records={}
    cases=[
        ('girl2','runs/phase2-5-oga-ground-truth','runs/phase2-5-oga-neural','runs/phase2-5-oga-sam','benchmarks/oga-oga.json'),
        ('girl1','runs/phase2-6-girl1-truth','runs/phase2-6-girl1-neural','runs/phase2-6-girl1-sam','benchmarks/oga-girl1.json'),
        ('boy1','runs/phase2-6-boy1-truth','runs/phase2-6-boy1-neural','runs/phase2-6-boy1-sam','benchmarks/oga-boy1.json'),
        ('boy2','runs/phase4b-boy2-truth','runs/phase4b-boy2-neural','runs/phase4b-boy2-sam','benchmarks/oga-boy2.json'),
        ('wikipe','assets/references/wikipe-tan','runs/phase2-5-wikipe-neural','runs/phase2-5-wikipe-sam',None)]
    for name,truth,neural,sam,definition in cases:
        source=Path(truth)/('original.png' if name=='wikipe' else 'flat.png')
        rights='Kasuga; CC-BY-SA-3.0' if name=='wikipe' else 'stevenburrow; CC0'
        run=a.output/name
        result=create(source,run,rights=rights,decomposition=Path(neural)/'bridge',sam=Path(sam),until='readiness',preview=False)
        manifest=json.loads((run/'creation.json').read_text())
        project=run/manifest['stages']['restore']['directory']/'layers'
        quality=json.loads((run/manifest['review_evidence']['semantic']).read_text())
        records[name]=dict(status=result['status'],quality=quality)
        if definition:
            records[name]['independent_evaluation']=evaluate(project,Path(truth),json.loads(Path(definition).read_text()))
        if name!='girl2' and quality['decision']!='blocked':
            # Explicit historical negative review, not a new automatic semantic claim.
            review(run,'semantic','reject','Historical negative regression',
                   'Retain Phase 2.6 rejection: fine beard/brow or facial ownership is not established. No automatic rig.',[])
            records[name]['status']='rejected-historical-semantic-review'
        if any(stage in manifest['stages'] for stage in ['project','rig','export']):
            raise RuntimeError('Unreviewed benchmark reached rigging')
    write_json(a.output/'summary.json',records)
    print(json.dumps({k:dict(status=v['status'],reasons=v['quality']['blocking_reasons']) for k,v in records.items()},indent=2))


if __name__=='__main__':main()
