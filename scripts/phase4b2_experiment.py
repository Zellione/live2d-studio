"""Repeat optional inpainting from an immutable, semantically reviewed creation run."""
import argparse
import json
from pathlib import Path
from live2d_studio.creation import create,review
from live2d_studio.creation_quality import CHECKS,validate_review
from live2d_studio.manifest import digest
from live2d_studio.stages import verify


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--config',type=Path)
    parser.add_argument('--review',type=Path)
    parser.add_argument('--mode',choices=['deterministic','neural','hybrid'],default='neural')
    parser.add_argument('--until',default='validation')
    args=parser.parse_args()
    base=args.baseline.resolve();state=json.loads((base/'creation.json').read_text())
    def stage(name):
        item=state['stages'][name];directory=(base/item['directory']).resolve()
        if not directory.is_relative_to(base):raise ValueError('Stage escapes baseline')
        verify(directory,item['files'])
        return directory
    evidence=stage('readiness')/'quality.json'
    validate_review(json.loads((base/'reviews/semantic.json').read_text()),digest(evidence),CHECKS)
    original=next(stage('ingest').glob('original.*'))
    kwargs=dict(rights=state['identity']['rights'],decomposition=stage('inference')/'bridge',sam=stage('semantics')/'sam',
        preview=False,reconstruction=args.mode,inpainting_config=args.config,inpainting_review=args.review)
    create(original,args.output,until='readiness',**kwargs)
    current=json.loads((args.output/'creation.json').read_text())
    current_quality=args.output/current['stages']['readiness']['directory']/'quality.json'
    if digest(evidence)!=digest(current_quality):raise ValueError('Semantic evidence differs; new review required')
    if not (args.output/'reviews/semantic.json').exists():
        review(args.output,'semantic','accept','development-agent; exact prior semantic evidence replay',
            'Exact same semantic/source report as '+str(base)+'. Source/limb limitations retained. This is not user review of neural artwork.',list(CHECKS))
    print(json.dumps(create(original,args.output,until=args.until,**kwargs),indent=2))


if __name__=='__main__':main()
