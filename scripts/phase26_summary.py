"""Assemble compact Phase 2.6 measurements from local reproducible runs.

Never infers visual acceptance from numeric changes. Local visual judgement is
recorded explicitly below, with measured failures retained.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from compare_decompositions import measure
from evaluate_oga import evaluate
from live2d_studio.manifest import write_json,digest,load_validate
from live2d_studio.refinement import fidelity

ROOT=Path(__file__).resolve().parents[1]

def read(name):return json.loads((ROOT/name).read_text())


def main():
    output=ROOT/'docs/benchmarks/phase2-6.json'
    if output.exists():raise FileExistsError('Retain historical summary; choose deliberate reviewed update')
    result=dict(schema_version=1,scope='Four images, three CC0 characters from one artist; no broad generalization',
        phase25_reference_sha256=digest(ROOT/'docs/benchmarks/phase2-5.json'),
        baseline_exact_reproduction=read('runs/phase2-6-audit/baseline.json')['exact_reference_match'],
        algorithms=['native-owner-v2','connected skin neck extension','near-feature ink ownership'],
        neural_source_unchanged=True,main_dependencies_unchanged=True,benchmarks={})
    for name in ('oga','wikipe','girl1','boy1'):
        old=ROOT/(f'runs/phase2-5-{name}-layers' if name in ('oga','wikipe') else f'runs/phase2-6-{name}-layers')
        new=ROOT/f'runs/phase2-6-{name}-release'
        data=load_validate(new);q=read(str(new.relative_to(ROOT)/'quality.json'))
        original=np.array(Image.open(new/data['sources'][0]['normalized_path']))
        old_comp=np.array(Image.open(old/'preview/composite.png').resize((original.shape[1],original.shape[0]),Image.Resampling.LANCZOS))
        record=dict(source_sha256=data['sources'][0]['sha256'],before=dict(coverage=measure(old),fidelity=fidelity(original,old_comp)),
            after=dict(coverage=measure(new),fidelity=q['fidelity']),
            structural_semantics=q['structural_semantics'],uncertain_source_samples=q['uncertain_copied_samples'],
            neck_reassigned_pixels=q['neck_reassigned_pixels'],detail_reassigned_pixels=q['detail_reassigned_pixels'],
            small_component_flags=len(q['small_components']),
            postprocess_seconds=read(str(new.relative_to(ROOT)/'metrics.json'))['seconds'],
            manifest_sha256=digest(new/'layer_manifest.json'),
            gates=dict(semantic_decomposition='rejected',source_preservation='rejected',hidden_reconstruction='not-accepted',
                psd2live_import='not-tested',runtime_geometry='not-tested',visual_animation='not-tested'),production_ready=False)
        if name!='wikipe':
            truth=ROOT/('runs/phase2-5-oga-ground-truth' if name=='oga' else f'runs/phase2-6-{name}-truth-replay')
            definition=read(f'benchmarks/oga-{name}.json')
            record['before']['independent_semantics']=evaluate(old,truth,definition)
            record['after']['independent_semantics']=evaluate(new,truth,definition)
            record['rights']='stevenburrow; CC0; https://opengameart.org/content/anime-girl-and-boy-portraits'
        else:record['rights']='Kasuga; CC-BY-SA-3.0; https://commons.wikimedia.org/wiki/File:Wikipe-tan_face.png'
        if name=='oga':
            record['gates']=dict(semantic_decomposition='accepted-coarse-benchmark',source_preservation='accepted-with-small-unassigned-fringe',
                hidden_reconstruction='reviewed-incomplete',psd2live_import='accepted',runtime_geometry='accepted-numeric-with-triangle-warnings',
                visual_animation='accepted-limited-prototype; high-quality gate not met')
            record['defects']=['thin hair gaps at combined poses','flat intermediate lids','brows through bangs','hidden anatomy not independently known']
        elif name=='boy1':
            record['gates']['semantic_decomposition']='accepted-coarse-only; fine beard/brow ownership rejected'
            record['gates']['source_preservation']='accepted-with-small-unassigned-fringe'
            record['defects']=['beard attached to neck','hair fragment classified eyebrow','missing independently supported back head geometry; rig not attempted']
        elif name=='girl1':record['defects']=['face assigned to back hair','missing chest','missing left iris; copied detail does not repair independent geometry']
        else:record['defects']=['cropped/tilted face assigned back hair','padding did not restore face geometry']
        result['benchmarks'][name]=record
    result['ablation']={name:read(f'runs/{folder}/evaluation.json') for name,folder in
        [('preservation_only','phase2-6-oga-preserve-v1'),('neck_without_ink','phase2-6-oga-v1'),('neck_and_ink','phase2-6-oga-v2')]}
    result['render_comparison']={}
    for name,folder in [('phase25','phase2-6-baseline-review'),('initial_restore','phase2-6-oga-review-v1'),('recommended','phase2-6-oga-v2-review'),('guards_rejected','phase2-6-oga-guards-review')]:
        q=read(f'runs/{folder}/quality.json');poses=q['poses']
        result['render_comparison'][name]=dict(status=q['render_status'],poses=len(poses),control_noise=q['control_noise_pixels'],
            neutral_hole_pixels=poses['neutral']['enclosed_transparent_pixels'],max_hole_pixels=max(v['enclosed_transparent_pixels'] for v in poses.values()),
            max_detached_small_pixels=max(v['detached_small_component_pixels'] for v in poses.values()),
            max_triangle_flips=max(v['geometry'].get('new_triangle_flips',0) for v in poses.values()),
            invalid_numeric_or_opacity=sum(v['geometry'].get('nonfinite',0)+v['geometry'].get('invalidOpacity',0) for v in poses.values()),
            expanded_triangles=max(v['geometry'].get('expanded_triangles',0) for v in poses.values()),
            network=q['network'],warning='Counts are candidates, not artistic scores; intended blink folds can flip triangles.')
    result['guard_experiment']=dict(**read('runs/phase2-6-oga-guards/guard-report.json'),decision='rejected for recommended export; new hair fragments')
    result['padding_experiment']=dict(**read('runs/phase2-6-wikipe-padded-refined/quality.json'),decision='rejected; padding cannot recover missing source anatomy')
    result['gpu_runs']={n:read(f'runs/phase2-6-{n}/metrics.json') for n in ('girl1-neural','boy1-neural','wikipe-padding-neural','girl1-sam','boy1-sam','wikipe-padding-sam')}
    result['rig_import']=read('runs/phase2-6-oga-v2-build/import-validation.json')
    result['rig_import_scope']='animation_tested=false is import-only; actual animation recorded in render_comparison and separate visual review.'
    result['regression']=dict(unit_tests=51,synthetic=read('runs/phase2-6-audit/synthetic-evaluation.json'),
        isolation=read('runs/phase2-6-audit/isolation.json'),
        browser={name:read(f'runs/phase2-6-regression-{name}/result.json')['result']['value']['status'] for name in ('phase0','phase1')})
    result['recommendation']='Retain optional source-preserving postprocessing and reviewed Girl2 prototype; no production-ready character or default neural promotion.'
    write_json(output,result)
    preview=ROOT/'runs/phase2-6-review';preview.mkdir(exist_ok=False)
    html=['<!doctype html><meta charset="utf-8"><title>Phase 2.6 comparisons</title><style>body{font:16px sans-serif}img{max-width:32%;background:#ddd}figure{margin:0}a{display:block}</style><h1>Phase 2.6 — source fidelity versus animation</h1>']
    for name in result['benchmarks']:
        old=f'phase2-5-{name}-layers' if name in ('oga','wikipe') else f'phase2-6-{name}-layers'
        new=f'phase2-6-{name}-release'
        html.append(f'<h2>{name}: original / neural / restored</h2><figure><img src="../{new}/source/normalized.png"><img src="../{old}/preview/composite.png"><img src="../{new}/preview/composite.png"></figure><p>{result["benchmarks"][name]["gates"]}</p>')
    for folder,label in [('phase2-6-baseline-review','Phase 2.5 same pose set'),('phase2-6-oga-review-v1','Initial restoration: rejected duplicate eye/mouth lines'),('phase2-6-oga-v2-review','Recommended contour-corrected prototype'),('phase2-6-oga-guards-review','Guard experiment: rejected hair fragments')]:
        html.append(f'<a href="../{folder}/index.html">{label}</a>')
    (preview/'index.html').write_text('\n'.join(html))
    print(output)

if __name__=='__main__':main()
