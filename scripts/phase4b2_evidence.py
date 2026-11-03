"""Collect retained Phase 4B.2 evidence; never used by inference or authoring."""
import argparse
import json
from pathlib import Path
import re
import numpy as np
from PIL import Image,ImageDraw
from live2d_studio.manifest import digest,write_json
from live2d_studio.stages import verify


def stage(root,name):
    d=json.loads((root/'creation.json').read_text());item=d['stages'][name]
    folder=root/item['directory'];verify(folder,item['files']);return folder


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--benchmark',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    report=dict(schema_version=1,base_commit='71ef58e497e2dc3c6626907a137b745b351e6a70',
        outcome='No tested candidate improved facial animation without a visual regression; retain deterministic default.',
        single_image=True,multi_reference=False,production_deployment=False,training=False,user_visual_approval=False,
        model_lock_sha256=digest(Path('backends/inpainting/models.lock.json')),inference={},runtime={},transitions={},preservation={})
    experiments={}
    for char in ['sara','girl2']:
        for scale in [1,2]:
            base=Path(f'runs/phase4b2-{char}-lama{scale}')
            experiments[f'{char}-lama{scale}']=(base,base/('predictions' if scale==1 else 'predictions-gpu'))
        base=Path(f'runs/phase4b2-{char}-qwen')
        experiments[f'{char}-qwen']=(base,base/('predictions-v2' if char=='sara' else 'predictions'))
    for name in ['boy1-holdout','boy1-holdout-native','sara-qwen-controlled']:
        base=Path('runs/phase4b2-'+name);experiments[name]=(base,base/'predictions')
    gallery=[]
    for label,(base,predictions) in experiments.items():
        r=json.loads((predictions/'report.json').read_text());entries=[]
        for t in r['tasks']:
            task=t['task'];request=base/'requests';src=np.array(Image.open(request/task['image']).convert('RGBA'))
            mask=np.array(Image.open(request/task['mask']))>0
            out=np.array(Image.open(predictions/task['id']/'composite.png').convert('RGBA'))
            if not np.array_equal(src[~mask],out[~mask]) or not np.array_equal(src[...,3],out[...,3]):raise ValueError('Source mask protection failed')
            if digest(predictions/task['id']/'composite.png')!=t['composite_sha256']:raise ValueError('Changed prediction')
            entries.append(dict(id=task['id'],seconds=t['seconds'],generated_pixels=t['generated_pixels'],
                outside_mask_changed=0,alpha_changed=0,seed=task['seed'],steps=task.get('steps') if r['model']=='qwen' else None))
        report['inference'][label]=dict(model=r['model'],gpu=r['gpu'],torch=r['torch'],cuda=r['cuda'],
            peak_allocated_bytes=max(t['max_allocated_bytes'] for t in r['tasks']),peak_reserved_bytes=max(t['max_reserved_bytes'] for t in r['tasks']),
            total_seconds=r['total_seconds'],unloaded=r['unloaded'],remaining_before_process_exit=r['remaining_allocated_bytes'],
            producer_report_sha256=digest(predictions/'report.json'),tasks=entries)
        sheet=Image.new('RGB',(960,240*len(r['tasks'])),(235,235,235));draw=ImageDraw.Draw(sheet)
        for i,t in enumerate(r['tasks']):
            task=t['task']
            for j,(caption,file) in enumerate([('conditioning input',base/'requests'/task['image']),('raw neural',predictions/task['id']/'raw.png'),('hard masked',predictions/task['id']/'composite.png')]):
                im=Image.open(file).convert('RGBA');im.thumbnail((310,210));sheet.paste(im,(320*j,i*240+25),im)
                draw.text((320*j+4,i*240+4),task['id']+' / '+caption,fill='black')
        sheet.save(a.output/(label+'.png'));gallery.append('<h2>'+label+'</h2><img src="'+label+'.png">')
    for char in ['sara','girl2']:
        base=Path('runs/phase4b1-'+char);layers=stage(base,'facial')/'layers'
        # Revalidate every frozen stage, not just the currently selected runtime.
        for name in json.loads((base/'creation.json').read_text())['stages']:stage(base,name)
        baseline=Path('runs/phase4b2-'+char+('-baseline-gpu' if char=='sara' else '-baseline-v2'))
        neutral=np.array(Image.open(baseline/'frames/neutral.png'))
        for kind in ['lama-rig','qwen-rig']+(['qwen-hybrid'] if char=='sara' else []):
            run=Path('runs/phase4b2-'+char+'-'+kind);current=stage(run,'facial')/'layers';render=stage(run,'validation')
            q=json.loads((render/'quality.json').read_text())
            files=[f for name in ['source','layers','masks','generated'] for f in (layers/name).rglob('*') if f.is_file()]
            equal=all(digest(f)==digest(current/f.relative_to(layers)) for f in files)
            if not equal:raise ValueError('Protected original facial layers changed')
            review=json.loads((run/'reviews/visual.json').read_text())
            report['runtime'][char+'-'+kind]=dict(poses=len(q['poses']),render_status=q['render_status'],geometry=q['geometry'],network=q['network'],
                neutral_holes=q['poses']['neutral']['enclosed_transparent_pixels'],max_holes=max(v['enclosed_transparent_pixels'] for v in q['poses'].values()),
                max_detached_pixels=max(v['detached_small_component_pixels'] for v in q['poses'].values()),
                neutral_differing_pixels=int(np.any(neutral!=np.array(Image.open(render/'frames/neutral.png')),axis=2).sum()),
                original_layer_files_equal=equal,original_layer_file_count=len(files),review=review,
                source_exact_fraction=json.loads((current/'facial-artwork.json').read_text())['fidelity']['exact_fraction'])
    for name in ['baseline','lama','qwen','hybrid']:
        root=Path('runs/phase4b2-sara-'+name+'-transitions');q=json.loads((root/'quality.json').read_text())
        raw=json.loads((root/'frames/result.json').read_text())['result']['value']
        report['transitions'][name]=dict(status=q['render_status'],frames=len(q['poses']),geometry=q['geometry'],network=q['network'],
            checks=raw['checks'],talking_ranges={k:[min(v),max(v)] for k,v in raw['talking'].items()})
    pins=json.loads(Path('recipes/girl2-package.json').read_text());p31=json.loads(Path('docs/benchmarks/phase3-1.json').read_text())
    checks=[(Path('runs/phase3-final/runtime'),pins['accepted_source_sha256']),(Path('runs/phase3-final'),pins['provenance']['editable_sources_sha256']),
        (Path('runs/phase3-1-final-v2/runtime'),dict(p31['runtime']['files_sha256'],**{'Generated_artwork.model3.json':p31['runtime']['model_sha256']})),
        (Path('runs/phase3-1-final-v2'),{'character.psd2live':p31['editable_project_sha256'],'character.psd':p31['psd_sha256']})]
    for root,files in checks:
        for name,value in files.items():
            if digest(root/name)!=value:raise ValueError('Changed accepted artifact')
    report['preservation'].update(phase3_31_files_verified=sum(len(v) for _,v in checks),phase4b1_all_stage_inventories='pass')
    original=stage(Path('runs/phase4b2-sara-qwen-hybrid'),'facial')/'layers'
    replay=stage(Path('runs/phase4b2-sara-hybrid-replay'),'facial')/'layers'
    pngs=list(original.rglob('*.png'))
    report['preservation']['hybrid_replay_pngs_equal']=all(digest(f)==digest(replay/f.relative_to(original)) for f in pngs)
    if not report['preservation']['hybrid_replay_pngs_equal']:raise ValueError('Hybrid replay differs')
    p=Path('runs/phase4b2-boy1-holdout');truth=np.array(Image.open(p/'evaluation/truth.png')).astype(float);mask=np.array(Image.open(p/'requests/skin-gap-mask.png'))>0
    errors={}
    for name,file in [('deterministic',p/'evaluation/deterministic.png'),('lama_native',Path('runs/phase4b2-boy1-holdout-native/predictions/skin-gap/composite.png')),
        ('lama_rescaled_confounded',p/'predictions/skin-gap/composite.png')]:
        im=np.array(Image.open(file)).astype(float);errors[name]=float(np.abs(im[mask,:3]-truth[mask,:3]).mean())
    report['boy1_holdout']=dict(pixels=int(mask.sum()),rgb_mae=errors,truth_is_evaluation_only=True,
        caveat='2x run has black-mask resampling halo; not a clean model comparison. Flat skin patch is not hidden anatomy validation.')
    report['retained_failures']=['sandbox CUDA/browser refusals','Qwen singleton VAE output-shape failure before image conversion',
        'Girl2 baseline talking assertion failure; fresh repeat passed','LaMa rescaled holdout boundary contamination',
        'all five rejected rendered candidates; no gate relaxed']
    log=Path('runs/phase4b2-research/python-tests-release.log').read_text();node=Path('runs/phase4b2-research/node-tests-release.log').read_text()
    passed=re.search(r'Ran (\d+) tests.*\n\nOK',log,re.S)
    if not passed or 'fail 0' not in node:raise ValueError('Missing passing test evidence')
    report['tests']=dict(python=int(passed.group(1)),javascript=5,status='pass')
    write_json(a.benchmark,report);write_json(a.output/'benchmark.json',report)
    (a.output/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Phase 4B.2 local inpainting review</title>
<style>body{font:17px system-ui;background:#eee;color:#223;max-width:1250px;margin:30px auto}img{max-width:100%}a{color:#256}</style>
<h1>Phase 4B.2 · retain deterministic reconstruction</h1>
<p>Local LaMa and quantized Qwen were executed. Smoother Qwen closed-eye stills failed the dense blink-ramp test: a curved neural lash and contracting original contour form a doubled loop. Qwen mouth edits reduce the visible opening; Girl2 lashes change style asymmetrically. Every rendered neural/hybrid candidate is rejected by development review. No user visual approval or production deployment.</p>
<ul><li><a href="../phase4b2-sara-comparison/index.html">Sara: deterministic / Qwen / hybrid poses</a></li>
<li><a href="../phase4b2-sara-transition-comparison/index.html">Sara: time-sampled blink, talking and fades</a></li>
<li><a href="../phase4b2-girl2-comparison/index.html">Girl2 regression: deterministic / LaMa / Qwen</a></li>
<li><a href="../phase4b2-sara-lama-comparison/index.html">Sara LaMa failure in actual motion</a></li>
<li><a href="benchmark.json">Measurements and exact development review records</a></li></ul>
<p>Below: conditioning inputs, raw model output and hard-mask composites. Skin-task conditioning inputs are original open-eye crops, not the deterministic skin alternative. Controlled prefilled inputs are labeled separately. Full deterministic comparison is in the runtime galleries above. Other expression sprites never enter inference.</p>'''+''.join(gallery))
    print(a.output/'index.html')


if __name__=='__main__':main()
