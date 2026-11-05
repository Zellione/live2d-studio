"""Collect verified Phase 4B.4 evidence without granting user visual acceptance."""
import argparse,json,re,shutil,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from live2d_studio.manifest import digest,write_json
from live2d_studio.stages import verify
from live2d_studio.transition_quality import validate_samples


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('candidate','gallery','benchmark','python-log','javascript-log'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();root=a.candidate
    report=dict(schema_version=1,phase='4B.4',continued_from='65c34e4',candidate=str(root),
        user_approval=False,automatic_promotion=False,production_modified=False,
        inference_executed=False,models_downloaded=False,training=False,recognition_score=None)
    def rendered(folder,dense=False):
        q=json.loads((folder/'quality.json').read_text())
        r=json.loads((folder/'frames/result.json').read_text())['result']['value']
        if r['status']!='pass' or not all(c['pass'] for c in r['checks']):raise ValueError('Incomplete runtime checks')
        if q['geometry']['nonfinite'] or q['geometry']['invalid_opacity']:raise ValueError('Geometry failure')
        core=json.loads((folder/'core.json').read_text())
        record=dict(path=str(folder),frames=len(q['poses']),checks=len(r['checks']),geometry=q['geometry'],network=q['network'],
            quality_sha256=digest(folder/'quality.json'),moc_sha256=core['moc_sha256'],
            max_holes=max(v['enclosed_transparent_pixels'] for v in q['poses'].values()),
            max_detached=max(v['detached_small_component_pixels'] for v in q['poses'].values()))
        if dense:
            record['temporal']=validate_samples(r)
            t=json.loads((folder/'transition-core.json').read_text())
            if t['status']!='pass' or t['visible_reversals'] or len(t['samples'])!=72:raise ValueError('Transition audit failed')
            record['transition_core']=dict(samples=len(t['samples']),visible_reversals=t['visible_reversals'],sha256=digest(folder/'transition-core.json'))
        return record
    report['controlled']=rendered(root/'expressions-release')
    report['dense']=rendered(root/'dense',True)
    report['girl2_regression']=rendered(Path('runs/phase4b4-girl2-regression'),True)
    c=json.loads((root/'expression-core-with-mouth.json').read_text())
    if c['status']!='pass' or c['visible_reversals'] or len(c['samples'])!=756:raise ValueError('Expression Core audit failed')
    report['expression_core']={k:c[k] for k in ['status','nonfinite','invalid_opacity','strict_opacity_excursions','exact_neutral_geometry','visible_reversals']}
    report['expression_core'].update(samples=len(c['samples']),sha256=digest(root/'expression-core-with-mouth.json'))
    report['comparison']=json.loads((a.gallery/'comparison.json').read_text())
    source=json.loads((root/'authoring/source-art.json').read_text())
    if source['status']!='pass':raise ValueError('Source-art check failed')
    report['source_art']=source
    report['native_geometry_warnings']=[]
    for entry in json.loads((root/'authoring/mcp-transcript.json').read_text()):
        g=entry['result'].get('data',{}).get('geometry_diagnostics')
        if g and (g['warnings'] or not g['safe']):report['native_geometry_warnings'].append(dict(operation=entry['operation'],safe=g['safe'],warnings=g['warnings']))
    # Accepted artifact checks are independent of candidate render quality.
    pins=json.loads(Path('recipes/girl2-package.json').read_text());p31=json.loads(Path('docs/benchmarks/phase3-1.json').read_text())
    checks=[(Path('runs/phase3-final/runtime'),pins['accepted_source_sha256']),(Path('runs/phase3-final'),pins['provenance']['editable_sources_sha256']),
        (Path('runs/phase3-1-final-v2/runtime'),dict(p31['runtime']['files_sha256'],**{'Generated_artwork.model3.json':p31['runtime']['model_sha256']})),
        (Path('runs/phase3-1-final-v2'),{'character.psd2live':p31['editable_project_sha256'],'character.psd':p31['psd_sha256']})]
    for folder,files in checks:verify(folder,files)
    frozen={}
    for folder in [Path('runs/phase4b1-sara'),Path('runs/phase4b1-girl2'),Path('runs/phase4b3-sara-create-final')]+[Path('runs/phase4b2-'+n) for n in ['sara-qwen-rig','sara-qwen-hybrid','girl2-qwen-rig','sara-lama-rig','girl2-lama-rig']]:
        state=json.loads((folder/'creation.json').read_text())
        for s in state['stages'].values():verify(folder/s['directory'],s['files'])
        frozen[str(folder)]=dict(status='pass',stages=len(state['stages']))
    subprocess.run(['git','diff','--exit-code','65c34e4','--','tests/fixtures','recipes/girl2-package.json','uv.lock',
        'backends/inpainting/models.lock.json','backends/see-through/models.lock.json'],check=True)
    old=json.loads(Path('runs/phase4b3-girl2-deterministic-final/dense/core.json').read_text())
    if old['moc_sha256']!=report['girl2_regression']['moc_sha256']:raise ValueError('Girl2 runtime changed')
    report['preservation']=dict(accepted_phase3_31_files=sum(len(f) for _,f in checks),frozen_stages=frozen,
        golden_fixtures_package_and_locks_unchanged=True,girl2_moc_unchanged=True)
    py=a.python_log.read_text();js=a.javascript_log.read_text()
    if not py.rstrip().endswith('OK') or 'fail 0' not in js:raise ValueError('Missing passing test logs')
    (root/'tests').mkdir(exist_ok=True)
    shutil.copyfile(a.python_log,root/'tests/python.log');shutil.copyfile(a.javascript_log,root/'tests/javascript.log')
    report['tests']=dict(python=int(re.search(r'Ran (\d+) tests',py)[1]),javascript=int(re.search(r'tests (\d+)',js)[1]),
        python_log_sha256=digest(a.python_log),javascript_log_sha256=digest(a.javascript_log),status='pass')
    report['implementation_sha256']={str(f):digest(f) for f in [Path('src/live2d_studio/emotion_authoring.py'),Path('src/live2d_studio/preview_ui/viewer.js'),
        Path('scripts/phase4b4_experiment.py'),Path('scripts/phase4b4_expression_scenario.js'),Path('scripts/probe_expressions.cjs')]}
    inspection=json.loads((root/'authoring/expression-inspection.json').read_text());report['blush']=inspection['generated_artwork']
    report['provenance']=dict(artwork='Sara: ZeNeRIA29 / RPG Action, CC-BY-3.0; benchmarks/phase4b-art.json',
        psd2live='3.6.7, GPL-3.0 recorded in docs/compatibility.md',cubism_core='Installed 5.0.0, Live2D proprietary license; not redistributed',
        core_sha256=c['core_sha256'],new_runtime_dependency=False,procedural_blush='CC0-1.0; independent generated overlay')
    assessments={
        'neutral':'Original friendly resting smile retained; not an affectless face.',
        'angry':'Clearer mild displeasure: closed shallow frown and normally open eyes. High stylized brows limit forceful anger.',
        'confused':'Raised/lowered asymmetric brows, unequal eye apertures and small uncertain near-flat mouth; no friendly smile.',
        'embarrassed':'Softer eyes, shy smile and subtle cheek tint; closest remaining comparison is Happy, whose mouth is more open.',
        'happy':'Existing open smile retained; no observed regression.',
        'sad':'Existing behavior retained; source smile still weakens sadness. This phase intentionally does not re-author Sad.',
        'surprised':'Existing wide opening retained; no observed regression.'}
    review=dict(reviewer='development-agent',decision='candidate-for-user-review',user_approval=False,promotion=False,
        controlled_quality_sha256=report['controlled']['quality_sha256'],dense_quality_sha256=report['dense']['quality_sha256'],
        gallery_comparison_sha256=digest(a.gallery/'comparison.json'),
        head_zero_evaluated=True,identity='Retained in development visual inspection; exact imported source RGBA separately verified.',
        independent_blink_talk=True,exact_neutral_return=True,assessments=assessments,
        limitations=['No human recognition test or automatic emotion score','Brow interpretation over bangs remains stylistic/semantic uncertainty',
            'Simple mouth cavity and stylized closed lashes','Existing head/hair gaps','Blush is inferred cosmetic placement'])
    report['development_review']=review
    write_json(root/'phase4b4-development-review.json',review)
    report['retained_failures']=['sandbox socket refusal','brow mesh already had height keys','missing source-crop offsets',
        'first candidate insufficient brow/mouth distinction','one-component mouth fit produced slant',
        'quadratic pixel-read test harness timeout','first gallery path typo']
    write_json(a.benchmark,report);write_json(a.gallery/'benchmark.json',report)
    page=a.gallery/'index.html'
    marker='<h2>Runtime evidence and preview</h2>'
    if marker not in page.read_text():
        with page.open('a') as stream:
            stream.write(marker+'<p><a href="../phase4b4-review-final/transitions/index.html">Dense before/after transitions, head/talk combinations and recordings</a> · <a href="benchmark.json">Evidence and development assessment</a></p><p>Interactive candidate: run <code>uv run --frozen live2d-studio preview-live --model '+str(root)+'/export/runtime/Generated_artwork.model3.json</code>. Select Compare expressions for motion-free review. User visual approval remains pending.</p>')
    print(a.benchmark)

if __name__=='__main__':main()
