"""Standalone image-to-preview orchestration. No agent, hosted inference or deployment."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image

from .manifest import digest, local_file, load_validate, write_json
from .stages import Stages, inventory, verify, atomic_json
from .creation_quality import CHECKS, VISUAL_CHECKS, validate_review

REPO = Path(__file__).resolve().parents[2]
ORDER = ('ingest', 'inference', 'semantics', 'restore', 'readiness', 'facial',
         'project', 'rig', 'animation', 'export', 'validation', 'preview')


def code_hash(*names):
    return {name: digest(REPO/name) for name in names}


def worker(source, output, sam=False):
    python = REPO/'backends/see-through/.venv/bin/python'
    if not python.is_file():
        raise RuntimeError('Missing separate See-through environment; see backends/see-through/README.md')
    with (output.parent/(output.name+'.log')).open('w') as log:
        result = subprocess.run([str(python), str(REPO/'backends/see-through/worker.py'),
            '--input', str(source), '--output', str(output)] + (['--sam'] if sam else []),
            cwd=REPO, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Offline inference failed; inspect ' + str(log.name))


def copy_bridge(source, output, input_hash):
    """Import only bridge-owned files; provenance validation happens before reuse."""
    from .seethrough import PINNED_SOURCE, MODEL_REVISIONS
    data = json.loads((source/'decomposition.json').read_text())
    if data['input_sha256'] != input_hash or data['source_revision'] != PINNED_SOURCE or data['models'] != MODEL_REVISIONS:
        raise ValueError('Cached inference input/model provenance mismatch')
    output.mkdir()
    for name in ['decomposition.json', data['normalized_path']] + [l['path'] for l in data['layers']]:
        file = local_file(source, name)
        destination = output/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, destination)


def create(source, output, *, rights='unspecified-local-only', decomposition=None, sam=None,
           endpoint='http://127.0.0.1:23871/mcp', until='preview', preview=True,
           extension=None, port=8768, client_factory=None):
    source = Path(source).resolve()
    if until not in ORDER:
        raise ValueError('Unknown creation stage')
    identity = dict(input_sha256=digest(source), rights=rights, pipeline='phase4b-v1')
    stages = Stages(output, identity)
    with stages.locked():
        paths = {}
        def run(name, inputs, action):
            print('create: ' + name, file=sys.stderr, flush=True)
            result = stages.run(name, inputs, action)
            paths[name] = result
            return result
        def stop(name):
            if until == name:
                stages.data['status'] = 'stopped-after-' + name
                stages.save()
                return True
            return False
        def result():
            return dict(status=stages.data['status'], manifest=str(stages.file),
                        stages={k:str(v) for k,v in paths.items()})
        def ingest(root):
            with Image.open(source) as im:
                if im.format not in {'PNG','WEBP','JPEG'} or im.width*im.height > 4_194_304:
                    raise ValueError('Supported input: PNG/WebP/JPEG up to 4 megapixels')
                if im.getexif().get(274,1) != 1:
                    raise ValueError('Normalize EXIF orientation into a separate input copy first')
                im.load()
            shutil.copyfile(source, root/('original'+source.suffix.lower()))
            if digest(source) != identity['input_sha256']:
                raise ValueError('Input changed during ingestion')
            write_json(root/'source.json', identity)
        ing = run('ingest', identity, ingest)
        if stop('ingest'): return result()
        original = next(ing.glob('original.*'))
        inference_key = dict(source=identity['input_sha256'], code=code_hash(
            'backends/see-through/worker.py','backends/see-through/models.lock.json','backends/see-through/uv.lock'))
        # A validated prior stage wins over cache options: no needless GPU rerun.
        def infer(root):
            if decomposition:
                copy_bridge(Path(decomposition).resolve(), root/'bridge', identity['input_sha256'])
            else:
                worker(original, root/'worker')
                copy_bridge(root/'worker/bridge', root/'bridge', identity['input_sha256'])
            # Fully validate dimensions/order/PNG data before checkpointing inference.
            from .seethrough import import_decomposition
            import_decomposition(original, root/'validated', rights, root/'bridge')
        inf = run('inference', inference_key, infer)
        if stop('inference'): return result()
        old_semantics=stages.data['stages'].get('semantics')
        sam_key=inventory(Path(sam)) if sam else (
            old_semantics['inputs']['sam'] if old_semantics else 'offline-worker')
        def semantics(root):
            from .seethrough import import_decomposition
            from .semantic_order import order_eyes
            import_decomposition(original, root/'imported', rights, inf/'bridge')
            order_eyes(root/'imported',root/'layers')
            sam_source=Path(sam) if sam else None
            if sam_source is None and old_semantics and old_semantics['status']=='complete':
                previous=(stages.root/old_semantics['directory']).resolve()
                if not previous.is_relative_to(stages.root):
                    raise ValueError('Previous semantic stage escapes run')
                verify(previous,old_semantics['files'])
                sam_source=previous/'sam'
            if sam_source is not None:
                from .refinement import sam_masks
                masks = sam_masks(sam_source,identity['input_sha256'],Image.open(original).size)
                (root/'sam').mkdir()
                for name in ['sam.json'] + [name+'.png' for name in masks]:
                    shutil.copyfile(local_file(sam_source,name),root/'sam'/name)
            else:
                worker(original, root/'sam', sam=True)
        sem = run('semantics', dict(inference=stages.data['stages']['inference']['files'],
            code=code_hash('src/live2d_studio/seethrough.py','src/live2d_studio/refinement.py',
                           'src/live2d_studio/semantic_order.py'),
            sam=sam_key), semantics)
        if stop('semantics'): return result()
        def restore(root):
            from .refinement import refine
            refine(sem/'layers',root/'layers',sem/'sam')
        restored = run('restore', dict(parent=stages.data['stages']['semantics']['files'],
            code=code_hash('src/live2d_studio/refinement.py')),restore)/'layers'
        if stop('restore'): return result()
        def readiness(root):
            from .creation_quality import analyze
            analyze(restored,root)
        ready = run('readiness',dict(parent=stages.data['stages']['restore']['files'],
            code=code_hash('src/live2d_studio/creation_quality.py')),readiness)
        quality = json.loads((ready/'quality.json').read_text())
        stages.data['review_evidence'] = dict(semantic=str((ready/'quality.json').relative_to(stages.root)))
        if quality['decision'] == 'blocked':
            stages.data['status'] = 'blocked-semantic-quality'
            stages.save()
            return dict(result(), reasons=quality['blocking_reasons'])
        if stop('readiness'): return result()
        review_file = stages.root/'reviews/semantic.json'
        if not review_file.is_file():
            stages.data['status'] = 'needs-semantic-review'
            stages.save()
            return dict(result(), review=str(ready/'quality.json'), layers=str(restored/'preview/index.html'))
        semantic_review=json.loads(review_file.read_text())
        if semantic_review.get('decision')=='reject':
            stages.data['status']='rejected-semantic'
            stages.save()
            return result()
        validate_review(semantic_review,digest(ready/'quality.json'),CHECKS)
        # These later stages each reopen a saved predecessor and preserve failed attempts.
        from .generic_rig import facial_plan, create_project, author_rig, author_animation, export_model
        from .mcp import MCP
        factory = client_factory or (lambda: MCP(endpoint))
        face = run('facial',dict(parent=stages.data['stages']['restore']['files'], review=digest(review_file),
            code=code_hash('src/live2d_studio/generic_rig.py','src/live2d_studio/facial_artwork.py')),lambda root: facial_plan(restored,root))
        if stop('facial'): return result()
        project = run('project',dict(parent=stages.data['stages']['facial']['files'],
            source=digest(restored/'layer_manifest.json'),
            code=code_hash('src/live2d_studio/generic_rig.py','src/live2d_studio/facial_authoring.py','src/live2d_studio/mcp.py')),
            lambda root:create_project(factory(),face/'layers',root))
        if stop('project'): return result()
        rig = run('rig',dict(parent=stages.data['stages']['project']['files'],
            code=code_hash('src/live2d_studio/generic_rig.py','src/live2d_studio/portrait_profile.json')),lambda root:author_rig(factory(),project,root))
        if stop('rig'): return result()
        animation = run('animation',dict(parent=stages.data['stages']['rig']['files']),
            lambda root:author_animation(factory(),rig,root))
        if stop('animation'): return result()
        exported = run('export',dict(parent=stages.data['stages']['animation']['files']),
            lambda root:export_model(factory(),animation,root))
        if stop('export'): return result()
        model = next((exported/'runtime').glob('*.model3.json'))
        from .creation_validation import validate_runtime
        from .preview_live import DEFAULT_EXTENSION, serve
        extension = Path(extension or DEFAULT_EXTENSION).resolve()
        validation = run('validation',dict(parent=stages.data['stages']['export']['files'],
            libraries=inventory(extension/'lib'), code=code_hash('src/live2d_studio/creation_validation.py',
                'scripts/phase4b1_browser_scenario.js','scripts/cdp_smoke.mjs',
                'src/live2d_studio/preview_live.py','src/live2d_studio/preview_ui/viewer.js',
                'src/live2d_studio/visual_qa.py')),
            lambda root:validate_runtime(model,root,extension,REPO/'scripts/phase4b1_browser_scenario.js'))
        stages.data['review_evidence']['visual'] = str((validation/'quality.json').relative_to(stages.root))
        stages.data['model'] = str(model.relative_to(stages.root))
        stages.data['status'] = 'needs-visual-review'
        stages.save()
        if stop('validation'): return result()
        run('preview',dict(model=digest(model),location=str(model)),lambda root:write_json(root/'preview.json',dict(
            command=['uv','run','--frozen','live2d-studio','preview-live','--model',str(model)],
            visual_review='required',production_ready=False)))
        visual = stages.root/'reviews/visual.json'
        if visual.is_file():
            visual_review=json.loads(visual.read_text())
            if visual_review.get('decision')=='reject':
                stages.data['status']='rejected-visual'
                stages.save()
                return result()
            validate_review(visual_review,digest(validation/'quality.json'),VISUAL_CHECKS)
            stages.data['status'] = 'accepted-limited-prototype'
        stages.save()
        if preview:
            serve(model,extension,port,True)
        return result()


def review(output, stage, decision, reviewer, notes, checks):
    root = Path(output).resolve()
    data = json.loads((root/'creation.json').read_text())
    with Stages(root,data['identity']).locked() as stages:
        evidence = local_file(root,stages.data['review_evidence'][stage])
        report = json.loads(evidence.read_text())
        if decision == 'accept' and report.get('decision') == 'blocked':
            raise ValueError('Cannot override failed structural/source gates')
        record = dict(evidence_sha256=digest(evidence), decision=decision, reviewer=reviewer,
                      notes=notes, checks=checks)
        if decision == 'accept':
            validate_review(record,digest(evidence),CHECKS if stage=='semantic' else VISUAL_CHECKS)
        folder = root/'reviews'
        folder.mkdir(exist_ok=True)
        file = folder/(stage+'.json')
        if file.exists():
            raise ValueError('Review already recorded; preserve it and use a new run for a rejected candidate')
        atomic_json(file,record)
        stages.data['status'] = ('reviewed-' if decision=='accept' else 'rejected-') + stage
        stages.save()
        return record


def preview_model(output):
    """Resolve only the verified current export, including after an explicit rejection."""
    from .stages import verify
    root=Path(output).resolve()
    data=json.loads((root/'creation.json').read_text())
    stage=data['stages'].get('export',{})
    if stage.get('status')!='complete' or 'model' not in data:
        raise ValueError('Creation has no validated preview model yet')
    directory=(root/stage['directory']).resolve()
    if not directory.is_relative_to(root):
        raise ValueError('Export escapes creation run')
    verify(directory,stage['files'])
    model=local_file(root,data['model'])
    if not model.is_relative_to(directory/'runtime'):
        raise ValueError('Preview model is not the current creation export')
    return model
