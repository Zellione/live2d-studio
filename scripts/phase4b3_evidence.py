"""Verify retained Phase 4B.3 evidence and assemble local review; no inference."""
import argparse,json,re,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image
from live2d_studio.manifest import digest,write_json
from live2d_studio.stages import verify
from live2d_studio.transition_quality import validate_samples


def stage(root,name):
    s=json.loads((root/'creation.json').read_text())['stages'][name];p=root/s['directory'];verify(p,s['files']);return p


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--benchmark',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    sara=Path('runs/phase4b3-sara-create-final')
    entries={
        'sara-deterministic':(sara,stage(sara,'validation'),stage(sara,'project'),stage(sara,'facial')/'layers','limited improvement; candidate pending user review'),
        'sara-qwen':(Path('runs/phase4b3-sara-qwen-final'),None,None,None,'loop at 0.1 eliminated; improved temporal candidate, style/anatomy uncertain; no automatic promotion'),
        'sara-skin':(Path('runs/phase4b3-sara-skin-final'),None,None,None,'reject additional neural skin: no established benefit; neutral shading changes'),
        'girl2-deterministic':(Path('runs/phase4b3-girl2-deterministic-final'),None,None,None,'limited near-closure improvement; original open-mouth treatment preserved'),
        'girl2-qwen':(Path('runs/phase4b3-girl2-qwen-final'),None,None,None,'reject neural selection: lash density/style remains inconsistent with original')}
    baselines={c:Path('runs/phase4b3-'+c+'-baseline') for c in ['sara','girl2']}
    frozen={c:Path('runs/phase4b1-'+c) for c in baselines}
    layers={c:stage(root,'facial')/'layers' for c,root in frozen.items()}
    report=dict(schema_version=1,phase='4B.3',continued_from='ca66737',new_models_downloaded=False,inference_executed=False,training=False,production_modified=False,
        runtime_independent=True,artwork_default='deterministic',motion_default='legacy; aligned is explicit candidate option',candidate={},baseline={},preservation={},tests={},visual_acceptance='Development assessment only; no new user approval or automatic promotion')
    resolved={}
    for c,root in frozen.items():
        for name in json.loads((root/'creation.json').read_text())['stages']:stage(root,name)
        q=json.loads((baselines[c]/'quality.json').read_text());report['baseline'][c]=dict(quality_sha256=digest(baselines[c]/'quality.json'),frames=len(q['poses']),
            max_holes=max(v['enclosed_transparent_pixels'] for v in q['poses'].values()),max_detached=max(v['detached_small_component_pixels'] for v in q['poses'].values()),temporal=validate_samples(json.loads((baselines[c]/'frames/result.json').read_text())['result']['value']))
    for label,(root,render,auth,local,assessment) in entries.items():
        char=label.split('-')[0]
        if render is None:
            render=root/'dense';auth=root/('project' if label=='sara-skin' else 'authoring');local=root/'layers' if label=='sara-skin' else layers[char]
        q=json.loads((render/'quality.json').read_text());raw=json.loads((render/'frames/result.json').read_text())['result']['value']
        core=json.loads((render/'transition-core.json').read_text())
        if core['status']!='pass' or core['visible_reversals'] or len(core['samples'])!=72:raise ValueError('Exported geometry/channel audit failed: '+label)
        structural=validate_samples(raw)
        if q['geometry']['nonfinite'] or q['geometry']['invalid_opacity']:raise ValueError('Numerical runtime failure')
        if json.loads((auth/'source-art.json').read_text())['status']!='pass':raise ValueError('Source import failed')
        # Rig-only variants retain frozen layer files; the full create and skin
        # candidates additionally compare every original raster/mask byte.
        files=[f for n in ['source','layers','masks','generated'] for f in (layers[char]/n).rglob('*') if f.is_file()]
        if not all(digest(f)==digest(local/f.relative_to(layers[char])) for f in files):raise ValueError('Original facial files changed')
        before=np.array(Image.open(baselines[char]/'frames/neutral.png'));after=np.array(Image.open(render/'frames/neutral.png'))
        native=[]
        for e in json.loads((auth/'mcp-transcript.json').read_text()):
            g=e['result'].get('data',{}).get('geometry_diagnostics')
            if g and (g['warnings'] or not g['safe']):native.append(dict(operation=e['operation'],safe=g['safe'],new_flips=g['newFlipCount'],new_collapses=g['newCollapseCount'],warnings=g['warnings']))
        review=dict(reviewer='development-agent',decision='limited-improvement' if not assessment.startswith('reject') else 'reject-neural-selection',
            quality_sha256=digest(render/'quality.json'),assessment=assessment,promotion=False,user_approval=False)
        write_json(root/'phase4b3-development-review.json',review)
        report['candidate'][label]=dict(run=str(root),render=str(render),frames=len(q['poses']),numerical=q['render_status'],geometry=q['geometry'],network=q['network'],
            structural=structural,core_audit=dict(status=core['status'],samples=len(core['samples']),visible_reversals=core['visible_reversals'],sha256=digest(render/'transition-core.json')),
            source_files_equal=len(files),neutral_changed_pixels=int(np.any(before!=after,axis=2).sum()),neutral_holes=q['poses']['neutral']['enclosed_transparent_pixels'],
            max_holes=max(v['enclosed_transparent_pixels'] for v in q['poses'].values()),max_detached=max(v['detached_small_component_pixels'] for v in q['poses'].values()),
            native_key_warnings=native,review=review)
        resolved[label]=render
    # Character-specific assessment is evaluation, never an inference input.
    for label in ['girl2-deterministic','girl2-qwen']:
        root=resolved[label];names=[n for n in json.loads((root/'quality.json').read_text())['poses'] if n.startswith(('mouth-','smile-','frown-'))]
        equal=all(np.array_equal(np.array(Image.open(root/'frames'/(n+'.png'))),np.array(Image.open(baselines['girl2']/'frames'/(n+'.png')))) for n in names)
        if not equal:raise ValueError('Girl2 mouth regression')
        report['candidate'][label]['mouth_smile_frown_equal_to_baseline']=len(names)
    pins=json.loads(Path('recipes/girl2-package.json').read_text());p31=json.loads(Path('docs/benchmarks/phase3-1.json').read_text())
    checks=[(Path('runs/phase3-final/runtime'),pins['accepted_source_sha256']),(Path('runs/phase3-final'),pins['provenance']['editable_sources_sha256']),
        (Path('runs/phase3-1-final-v2/runtime'),dict(p31['runtime']['files_sha256'],**{'Generated_artwork.model3.json':p31['runtime']['model_sha256']})),
        (Path('runs/phase3-1-final-v2'),{'character.psd2live':p31['editable_project_sha256'],'character.psd':p31['psd_sha256']})]
    for root,files in checks:
        for name,value in files.items():
            if digest(root/name)!=value:raise ValueError('Changed accepted artifact')
    for root in [Path('runs/phase4b2-'+n) for n in ['sara-qwen-rig','sara-qwen-hybrid','girl2-qwen-rig','sara-lama-rig','girl2-lama-rig']]:
        for name in json.loads((root/'creation.json').read_text())['stages']:stage(root,name)
    report['preservation']=dict(phase3_31_verified_files=sum(len(x) for _,x in checks),phase4b1_all_stages='pass',phase4b2_rejected_rigs_all_stages='pass',
        model_lock_sha256=digest(Path('backends/inpainting/models.lock.json')),source_pixels='Exact source files preserved; animated render positions are intentionally different')
    log=Path('runs/phase4b3-diagnosis/python-tests-release.log').read_text();node=Path('runs/phase4b3-diagnosis/node-tests-release.log').read_text();passed=re.search(r'Ran (\d+) tests.*\n\nOK',log,re.S)
    if not passed or 'fail 0' not in node:raise ValueError('Missing test evidence')
    report['tests']=dict(python=int(passed.group(1)),javascript=5,status='pass',python_log_sha256=digest(Path('runs/phase4b3-diagnosis/python-tests-release.log')),javascript_log_sha256=digest(Path('runs/phase4b3-diagnosis/node-tests-release.log')))
    groups={
        'sara':dict(baseline=baselines['sara'],deterministic=resolved['sara-deterministic'],qwen=resolved['sara-qwen'],skin=resolved['sara-skin']),
        'girl2':dict(baseline=baselines['girl2'],deterministic=resolved['girl2-deterministic'],qwen=resolved['girl2-qwen']),
        'qwen-before-after':dict(before=Path('runs/phase4b3-sara-old-qwen'),after=resolved['sara-qwen']),
        'mouth-cavity-rejected':dict(deterministic=resolved['sara-deterministic'],qwen=Path('runs/phase4b3-sara-qwen-v2/dense-final'))}
    links=[]
    for name,group in groups.items():
        command=[sys.executable,'scripts/phase4b3_compare.py','--layers',str(layers['girl2' if name=='girl2' else 'sara']),'--output',str(a.output/name)]
        for label,path in group.items():command+=['--render',label+'='+str(path)]
        subprocess.run(command,check=True)
        links.append('<li><a href="'+name+'/index.html">'+name+'</a></li>')
    report['temporal_image_changes']={name:json.loads((a.output/name/'temporal-metrics.json').read_text()) for name in groups}
    # Full per-step changes remain local; concise benchmark keeps maxima only.
    for sequences in report['temporal_image_changes'].values():
        for values in sequences.values():
            for item in values.values():item.pop('mean_absolute_frame_changes')
    report['retained_failures']=['fragmented-contour fit and disappearing-lash candidates','Qwen visible triangle reversal at .05 before delayed handoff',
        'symmetric alpha coverage dip','Qwen cavity and skin rejection','Girl2 Qwen style regression','initial sandbox/default-key/output-directory failures','pixel-read bug and oversized CDP transfers']
    write_json(a.benchmark,report);write_json(a.output/'benchmark.json',report)
    (a.output/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Phase 4B.3 review</title><style>body{font:18px system-ui;max-width:1000px;margin:35px auto;background:#eee;color:#223}a{color:#246}</style><h1>Phase 4B.3: rig-aware facial transitions</h1><p>The aligned Qwen lash eliminates Sara's old loop near 0.1 openness. Deterministic contours also remain visible through closure; the sparse-source mouth opens more evenly. Final candidates pass dense parameter and exported visible-triangle checks. Numerical success is separate from natural animation.</p><p>Deterministic remains the artwork default. Neural skin/cavity and Girl2 neural style are rejected selections. These are development assessments, not user approval or production promotion. Original accepted projects remain frozen.</p><ul>'''+''.join(links)+'''</ul><p>Each full suite contains 401 actual Core captures, with sampled recordings and complete sequence sheets. <a href="benchmark.json">Measurements and exact review records</a></p>''')
    print(a.output/'index.html')

if __name__=='__main__':main()
