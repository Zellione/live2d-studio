"""Verify frozen artifacts and bind mouth candidate evidence; never grants approval."""
import argparse,json,re,shutil,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from live2d_studio.manifest import digest,write_json
from live2d_studio.stages import verify
from live2d_studio.generic_rig import archived_art
from live2d_studio.transition_quality import validate_samples


def rendered(folder,dense=False):
    q=json.loads((folder/'quality.json').read_text());r=json.loads((folder/'frames/result.json').read_text())['result']['value']
    if r['status']!='pass' or not all(c['pass'] for c in r['checks']):raise ValueError('Incomplete render '+str(folder))
    if r['geometry']['nonfinite'] or r['geometry']['invalid_opacity'] or r['geometry'].get('parameter_range_violations',0):raise ValueError('Geometry failed')
    record=dict(path=str(folder),frames=len(r['frames']),checks=len(r['checks']),geometry=r['geometry'],network=q['network'],
                report_sha256=digest(folder/'frames/result.json'),quality_sha256=digest(folder/'quality.json'),
                max_holes=max(v['enclosed_transparent_pixels'] for v in q['poses'].values()),
                max_detached=max(v['detached_small_component_pixels'] for v in q['poses'].values()))
    if dense:
        record['temporal']=validate_samples(r)
        t=json.loads((folder/'transition-core.json').read_text())
        if t['status']!='pass' or t['visible_reversals'] or len(t['samples'])!=72:raise ValueError('Eye transition audit failed')
        record['transition_core']=dict(samples=len(t['samples']),visible_reversals=t['visible_reversals'],sha256=digest(folder/'transition-core.json'))
    return record


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['candidate','before','gallery','girl2','benchmark','python-log','javascript-log']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();root=a.candidate
    report=dict(schema_version=1,phase='4B.4.1',continued_from='889faf1',candidate=str(root),user_approval=False,
                automatic_promotion=False,production_modified=False,inference_executed=False,training=False,models_downloaded=False,recognition_score=None)
    report['mouths']=rendered(root/'mouths-release');report['before']=rendered(a.before)
    report['dense']=rendered(root/'dense',True);report['girl2_regression']=rendered(a.girl2,True)
    c=json.loads((root/'expression-core-rest.json').read_text())
    if c['status']!='pass' or len(c['samples'])!=819 or c['visible_reversals'] or not c['source_seam_opening_invariant']:raise ValueError('Mouth Core audit failed')
    report['mouth_core']={k:c[k] for k in ['status','nonfinite','invalid_opacity','strict_opacity_excursions','exact_neutral_geometry','visible_reversals','source_seam_opening_invariant','mouth_orientation_reference']}
    report['mouth_core'].update(samples=len(c['samples']),sha256=digest(root/'expression-core-rest.json'))
    before=Path(json.loads((root/'experiment.json').read_text())['baseline'])
    for f,h in json.loads((root/'predecessor-inventory.json').read_text()).items():
        if digest(before/f)!=h:raise ValueError('Phase 4B.4 artifact changed: '+f)
    source=json.loads((root/'authoring/source-art.json').read_text())
    old_art=archived_art(before/'authoring/character.psd2live');new_art=archived_art(root/'authoring/character.psd2live')
    if source['status']!='pass' or old_art!=new_art:raise ValueError('Archived source/artwork changed')
    pixels=lambda f:np.asarray(Image.open(f).convert('RGBA'))
    diff=int(np.any(pixels(a.before/'frames/neutral.png')!=pixels(root/'mouths-release/frames/neutral.png'),axis=2).sum())
    if diff:raise ValueError('Neutral pixel mismatch')
    report['source_preservation']=dict(imported_source=source,all_archived_pngs=len(old_art),all_archived_pngs_identical=True,neutral_changed_pixels=diff)
    report['legacy_form_axis_changed_pixels']={str(v):int(np.any(pixels(a.before/f'frames/axis-ParamMouthForm-{v}.png')!=pixels(a.before/'frames/axis-ParamMouthForm-0.png'),axis=2).sum()) for v in [-1,1]}
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
    subprocess.run(['git','diff','--exit-code','889faf1','--','tests/fixtures','recipes/girl2-package.json','uv.lock',
        'backends/inpainting','backends/see-through/models.lock.json'],check=True)
    old=json.loads(Path('runs/phase4b3-girl2-deterministic-final/dense/core.json').read_text())
    girl=json.loads((a.girl2/'core.json').read_text())
    if old['moc_sha256']!=girl['moc_sha256']:raise ValueError('Girl2 MOC changed')
    report['preservation']=dict(accepted_phase3_31_files=sum(len(f) for _,f in checks),frozen_stages=frozen,phase4b4_inventory_unchanged=True,
        golden_fixtures_package_locks_and_inference_unchanged=True,girl2_moc_unchanged=True)
    py=a.python_log.read_text();js=a.javascript_log.read_text()
    if not py.rstrip().endswith('OK') or 'fail 0' not in js:raise ValueError('Missing regression pass')
    (root/'tests').mkdir(exist_ok=True)
    shutil.copyfile(a.python_log,root/'tests/python.log');shutil.copyfile(a.javascript_log,root/'tests/javascript.log')
    report['tests']=dict(python=int(re.search(r'Ran (\d+) tests',py)[1]),javascript=int(re.search(r'tests (\d+)',js)[1]),status='pass',
        python_log_sha256=digest(a.python_log),javascript_log_sha256=digest(a.javascript_log))
    report['provenance']=dict(artwork='Sara: ZeNeRIA29 / RPG Action, CC-BY-3.0; benchmarks/phase4b-art.json',
        psd2live='3.6.7, GPL-3.0 recorded in docs/compatibility.md',cubism_core='Installed 5.0.0; proprietary Live2D license; not redistributed',
        core_sha256=c['core_sha256'],new_artwork=False,new_runtime_dependency=False)
    report['implementation_sha256']={str(f):digest(f) for f in [Path('src/live2d_studio/mouth_authoring.py'),Path('src/live2d_studio/preview_ui/viewer.js'),
        Path('scripts/phase4b4_1_experiment.py'),Path('scripts/phase4b4_1_mouth_scenario.js'),Path('scripts/probe_expressions.cjs')]}
    report['comparison']=json.loads((a.gallery/'comparison.json').read_text())
    report['development_review']=dict(reviewer='development-agent',decision='candidate-for-explicit-user-review',user_approval=False,
        gallery_sha256=digest(a.gallery/'comparison.json'),mouth_report_sha256=report['mouths']['report_sha256'],
        identity='Original resting face exactly preserved; expressive runtime movement is not source-pixel equality.',
        assessments=dict(neutral='Unchanged original friendly resting seam.',happy='Fuller smile with raised corners; still a simple untextured cavity.',
            sad='Soft downward corners, no retained smile at rest.',angry='Compressed nearly horizontal seam; distinct from sad frown.',
            confused='Small parted oval, related to surprised; intended questioning emotion still needs human review.',
            surprised='Larger vertical oval, no smiling curvature.',embarrassed='Smaller closed asymmetric smile; perceived shyness needs human review.'),
        transitions='Inspected opening sheets: early source-corner accumulation fixed; source/cavity handoff aligned. All emotions return to their own rest after talk.',
        limitations=['Single low-resolution sparse source contour with a centre gap','Dark flat cavity without teeth/tongue or phonemes',
                    'Existing eyebrow/eye/hair limitations unchanged','No human perception study, no automatic visual acceptance'])
    report['retained_failures']=['sandbox loopback/browser refusals','v2 thin happy and weak embarrassed mouths',
        'v3 accumulated source geometry at early opening','initial triangle reference used an invisible squashed cavity',
        'first Girl2 regression used wrong correspondence path']
    write_json(root/'phase4b4-1-development-review.json',report['development_review'])
    write_json(a.benchmark,report);write_json(a.gallery/'benchmark.json',report)
    print(a.benchmark)

if __name__=='__main__':main()
