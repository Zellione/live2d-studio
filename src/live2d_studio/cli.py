import argparse
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description='Local image-to-layers MVP; candidates require visual review')
    commands=parser.add_subparsers(dest='command',required=True)
    from .creation import ORDER
    p=commands.add_parser('create',help='Resumable local image-to-preview pipeline with explicit quality review')
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--rights',default='unspecified-local-only')
    p.add_argument('--decomposition',type=Path,help='Reuse an existing source-matched See-through bridge')
    p.add_argument('--sam',type=Path,help='Reuse existing source-matched SAM candidates')
    p.add_argument('--reconstruction',choices=['deterministic','neural','hybrid'],default='deterministic')
    p.add_argument('--facial-motion',choices=['legacy','aligned'],default='legacy',help='Experimental source-derived contour correspondence, with dense runtime review')
    p.add_argument('--mouths',choices=['preserve','coordinated'],default='preserve')
    p.add_argument('--body-motion',choices=['preserve','calm'],default='preserve')
    p.add_argument('--inpainting-config',type=Path,help='Offline model, target alternatives and pinned sampling parameters')
    p.add_argument('--inpainting-review',type=Path,help='Exact-image review required for selected hybrid alternatives')
    p.add_argument('--endpoint',default='http://127.0.0.1:23871/mcp')
    p.add_argument('--until',choices=ORDER,default='preview')
    p.add_argument('--no-preview',action='store_true')
    p.add_argument('--extension',type=Path)
    p.add_argument('--port',type=int,default=8768)
    p=commands.add_parser('review-create',help='Record acceptance/rejection tied to exact creation evidence')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--stage',choices=['semantic','visual'],required=True)
    p.add_argument('--decision',choices=['accept','reject'],required=True)
    p.add_argument('--reviewer',required=True)
    p.add_argument('--notes',required=True)
    p.add_argument('--checks',default='',help='Comma-separated completed review checks from quality.json')
    p=commands.add_parser('preview-live',help='Open a model in the standalone local browser viewer')
    source=p.add_mutually_exclusive_group()
    source.add_argument('--model',type=Path)
    source.add_argument('--run',type=Path,help='Open the verified current model from a creation run')
    p.add_argument('--compare-model',type=Path,help='Synchronize a second model at the same scale')
    p.add_argument('--extension',type=Path)
    p.add_argument('--port',type=int,default=8768)
    p.add_argument('--no-open',action='store_true')
    p=commands.add_parser('prepare-body',help='Author a separate body/head/hair candidate from a verified creation run; no inference')
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--endpoint',default='http://127.0.0.1:23871/mcp')
    p=commands.add_parser('prepare-performance',help='Compose optional mouths and body motion in a separate resumable candidate; no inference')
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mouths',choices=['preserve','coordinated'],default='preserve')
    p.add_argument('--body-motion',choices=['preserve','calm'],default='preserve')
    p.add_argument('--endpoint',default='http://127.0.0.1:23871/mcp')
    p=commands.add_parser('audit-production',help='Read-only audit; no production execution option')
    p.add_argument('--target',type=Path,required=True)
    p.add_argument('--package',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p=commands.add_parser('package')
    p.add_argument('--source',type=Path,default=Path('runs/phase3-final/runtime'))
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--core',type=Path,required=True)
    p=commands.add_parser('deploy')
    p.add_argument('--package',type=Path,required=True)
    p.add_argument('--target',type=Path,required=True)
    p.add_argument('--record',type=Path,required=True)
    p.add_argument('--name',default='girl2')
    p.add_argument('--adapter',action='store_true')
    p.add_argument('--replace',action='store_true')
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run',action='store_true')
    mode.add_argument('--execute',action='store_true')
    p=commands.add_parser('rollback')
    p.add_argument('--record',type=Path,required=True)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run',action='store_true')
    mode.add_argument('--execute',action='store_true')
    p=commands.add_parser('target-deploy',help='Phase 4A.2 disposable targets only; production disabled')
    p.add_argument('--package',type=Path,required=True)
    p.add_argument('--target',type=Path,required=True)
    p.add_argument('--transaction',type=Path,required=True)
    p.add_argument('--name',default='girl2-phase3-portrait-v1')
    p.add_argument('--adapter',action='store_true')
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run',action='store_true'); mode.add_argument('--execute',action='store_true')
    p=commands.add_parser('target-rollback',help='Standalone-compatible disposable recovery')
    p.add_argument('--transaction',type=Path,required=True)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run',action='store_true'); mode.add_argument('--execute',action='store_true')
    p=commands.add_parser('prepare')
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--rights',default='unspecified-local-only')
    p.add_argument('--backend',choices=['deterministic','see-through'],default='deterministic')
    p.add_argument('--decomposition',type=Path)
    p=commands.add_parser('inspect')
    p.add_argument('--project',type=Path,required=True)
    p=commands.add_parser('refine')
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--sam',type=Path)
    p.add_argument('--no-neck-repair',action='store_true')
    p.add_argument('--no-detail-repair',action='store_true')
    p=commands.add_parser('readiness')
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p=commands.add_parser('review-poses')
    p.add_argument('--frames',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p=commands.add_parser('prepare-rig')
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p=commands.add_parser('reconstruct')
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--max-fill-fraction',type=float,default=.25)
    p=commands.add_parser('flatten-fixture')
    p.add_argument('--art',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p=commands.add_parser('evaluate')
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--ground-truth',type=Path,required=True)
    p=commands.add_parser('build')
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--endpoint',default='http://127.0.0.1:23871/mcp')
    p=commands.add_parser('mcp-check')
    p.add_argument('--endpoint',default='http://127.0.0.1:23871/mcp')
    commands.add_parser('doctor')
    args=parser.parse_args()
    try:
        if args.command=='create':
            from .creation import create
            result=create(args.input,args.output,rights=args.rights,decomposition=args.decomposition,
                sam=args.sam,endpoint=args.endpoint,until=args.until,preview=not args.no_preview,
                extension=args.extension,port=args.port,reconstruction=args.reconstruction,
                inpainting_config=args.inpainting_config,inpainting_review=args.inpainting_review,facial_motion=args.facial_motion,
                mouths=args.mouths,body_motion=args.body_motion)
            print(json.dumps(result,indent=2))
            return 2 if result['status'].startswith(('blocked','needs-','rejected')) else 0
        elif args.command=='review-create':
            from .creation import review
            result=review(args.output,args.stage,args.decision,args.reviewer,args.notes,
                          [v.strip() for v in args.checks.split(',') if v.strip()])
        elif args.command=='preview-live':
            from .preview_live import serve
            model=args.model
            if args.run:
                from .creation import preview_model
                model=preview_model(args.run)
            result=serve(model,args.extension,args.port,not args.no_open,args.compare_model)
        elif args.command=='prepare-body':
            from .body_rig import prepare
            result=prepare(args.baseline,args.output,args.endpoint)
        elif args.command=='prepare-performance':
            from .performance import prepare
            result=prepare(args.baseline,args.output,args.mouths,args.body_motion,args.endpoint)
        elif args.command=='audit-production':
            from .production_audit import save_audit
            result=save_audit(args.target,args.package,args.output)
        elif args.command=='package':
            from .packaging import package
            result=package(args.source,args.output,args.core)
        elif args.command=='deploy':
            from .deployment import deploy
            result=deploy(args.package,args.target,args.record,args.name,args.adapter,args.replace,args.execute)
        elif args.command=='rollback':
            from .deployment import rollback
            result=rollback(args.record,args.execute)
        elif args.command=='target-deploy':
            from .target_transaction import deploy
            result=deploy(args.package,args.target,args.transaction,args.name,args.adapter,args.execute)
        elif args.command=='target-rollback':
            from .target_recovery import recover
            result=recover(args.transaction,args.execute)
        elif args.command=='prepare':
            from .backends import prepare
            result=prepare(args.input,args.output,args.rights,args.backend,args.decomposition)
        elif args.command=='prepare-rig':
            from .readiness import prepare
            result=prepare(args.project,args.output)
        elif args.command=='review-poses':
            from .visual_qa import review
            result=review(args.frames,args.output)
        elif args.command=='readiness':
            from .readiness import analyze
            result=analyze(args.project,args.output)
        elif args.command=='refine':
            from .refinement import refine
            result=refine(args.project,args.output,args.sam,not args.no_neck_repair,not args.no_detail_repair)
        elif args.command=='inspect':
            from .manifest import load_validate
            data=load_validate(args.project)
            result=dict(integrity='pass',layers=len(data['layers']),warnings=data['warnings'],missing=data['missing_regions'])
        elif args.command=='reconstruct':
            from .pipeline import reconstruct_project
            result=reconstruct_project(args.project,args.output,args.max_fill_fraction)
        elif args.command=='flatten-fixture':
            from .benchmark import flatten
            result=dict(input=str(flatten(args.art,args.output)))
        elif args.command=='evaluate':
            from .benchmark import evaluate
            result=evaluate(args.project,args.ground_truth)
        elif args.command=='build':
            from .mcp import build
            result=build(args.project,args.output,args.endpoint)
        elif args.command=='mcp-check':
            from .mcp import MCP
            value=MCP(args.endpoint).tool('workspace_inspect',{'request':{'scope':'project'}})
            if not value.get('ok'):
                raise RuntimeError('MCP inspection failed')
            result=dict(status='pass',read_only=True,loaded=value['data']['loaded'])
        else:
            from .device import doctor
            result=doctor()
        print(json.dumps(result,indent=2))
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as error:
        print('live2d-studio: '+str(error),file=sys.stderr)
        return 1
    return 0
