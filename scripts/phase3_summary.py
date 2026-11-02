"""Summarize retained, actual Phase 3 browser evidence; never infer aesthetics."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
from live2d_studio.manifest import digest,write_json
from live2d_studio.rp_qa import evaluate,load_results

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
def browser(path):return read(path+'/result.json')['result']['value']
def spans(rows):
    return {id:dict(min=min(r[id] for r in rows),max=max(r[id] for r in rows))
            for id in ['ParamAngleX','ParamAngleY','ParamAngleZ','ParamEyeLOpen','ParamEyeROpen','ParamMouthOpenY','ParamMouthForm','ParamBrowMood']}
def run():
    output=ROOT/'docs/benchmarks/phase3.json'
    if output.exists():raise FileExistsError('Preserve historical report; review before replacing')
    sources=['runs/phase3-final-rp','runs/phase3-final-lifecycle','runs/phase3-http-fallback-adapter','runs/phase3-race-adapter','runs/phase3-final-visual']
    results=load_results([ROOT/s for s in sources]);rp=evaluate(results)
    if rp['failures']:raise ValueError(rp['failures'])
    exp=browser('runs/phase3-final-expressions');quality=read('runs/phase3-final-expression-review/quality.json')
    if exp['status']!='pass' or read('runs/phase3-final/validation.json')['status']!='pass' or read('runs/phase3-final/core-validation.json')['status']!='pass':
        raise ValueError('Final runtime validation failed')
    before=read('runs/phase3-expressions-v4-review/quality.json')['poses']
    with Image.open(ROOT/'runs/phase3-baseline-browser/neutral.png') as a, Image.open(ROOT/'runs/phase3-final-expressions/neutral.png') as b:
        neutral_equal=a.size==b.size and a.convert('RGBA').tobytes()==b.convert('RGBA').tobytes()
    texture_equal=digest(ROOT/'runs/phase3-final/runtime/Generated_artwork.4096/texture_00.png')==digest(ROOT/'runs/phase2-6-oga-v2-build/runtime/Generated_artwork.4096/texture_00.png')
    psd_equal=digest(ROOT/'runs/phase3-final/character.psd')==digest(ROOT/'runs/phase2-6-oga-v2-build/character.psd')
    if not (neutral_equal and texture_equal and psd_equal):raise ValueError('Source preservation regressed')
    scenarios={r['mode']:dict(status=r['status'],network=r['network_validation'],source=source,
            samples={label:dict(count=len(rows),parameters=spans(rows)) for label,rows in r['samples'].items()},
            raw_opacity_excursions=sum(g['rawOpacityExcursions'] for g in r['geometry'].values()),
            max_opacity=max(g['opacity_max'] for g in r['geometry'].values()),
            nonfinite=sum(g['nonfinite'] for g in r['geometry'].values()),
            invalid_opacity=sum(g['invalidOpacity'] for g in r['geometry'].values()),
            out_of_range=sum(g['outOfRange'] for g in r['geometry'].values())) for source,r in zip(sources,[results[m] for m in ['rp','lifecycle','failure','race','visual']])}
    report=dict(schema_version=1,phase='3',starting_commit='addd895',character='CC0 Girl2',
        scope='Character-specific prototype, no production installation or new inference',
        source_sha256='09011ad707e0325c345fdc39da23d9b1a1640c3327c1ba2dfe192001da736f41',
        tools=dict(psd2live='3.6.7',core='5.0.0',sillytavern='8172dcd0ee672d3cd9a5e5f7af134f91a45cd2b8',extension='d1801d36a32ace9451cf6377c005a7a64292fc39',neural_inference_runs=0,new_packages=0),
        artifacts=dict(project='runs/phase3-final/character.psd2live',psd='runs/phase3-final/character.psd',runtime='runs/phase3-final/runtime',gallery='runs/phase3-review/index.html'),
        gates=dict(semantic='Inherited Girl2 coarse acceptance, not re-parsed',source_preservation='Accepted: unchanged texture and exact runtime-neutral equality',
            hidden_geometry='Reviewed incomplete; no new pixels',psd2live_import='Accepted save/reopen/export',runtime_geometry='Accepted, raw float32 opacity excursions retained',
            visual_animation='Accepted limited RP prototype; flat lids, subtle expressions and residual hair gaps',rp_integration=rp['rp_integration'],production_ready=False),
        source_preservation=dict(visible_exact_rgba_fraction_inherited=310621/310977,neutral_equals_phase26=neutral_equal,texture_equals_phase26=texture_equal,psd_equals_phase26=psd_equal,texture_sha256=digest(ROOT/'runs/phase3-final/runtime/Generated_artwork.4096/texture_00.png')),
        expression_pixel_changes=exp['expression_changes'],pose_count=len(quality['poses']),
        poses={k:{a:v[a] for a in ['enclosed_transparent_pixels','detached_small_component_pixels','strong_internal_colour_steps','geometry']} for k,v in quality['poses'].items()},
        hair_tuning=dict(before_max_hole_pixels=max(p['enclosed_transparent_pixels'] for p in before.values()),after_max_hole_pixels=max(p['enclosed_transparent_pixels'] for p in quality['poses'].values()),before_max_small_component_pixels=max(p['detached_small_component_pixels'] for p in before.values()),after_max_small_component_pixels=max(p['detached_small_component_pixels'] for p in quality['poses'].values()),neutral_rgba_equal=neutral_equal),
        classifier=dict(inference_tested=False,vocabulary=results['rp']['classifier_vocabulary'],mapping_checks=results['rp']['mapping_checks']),
        rp_acceptance=rp,scenarios=scenarios,mouth_roi=results['visual']['mouth_roi'],mouth_pixel_changes=results['visual']['mouth_pixel_changes'],
        upstream_http_failure=dict(status=browser('runs/phase3-http-failure-verified')['status'],network=browser('runs/phase3-http-failure-verified')['network_validation']),
        upstream_idle=spans(browser('runs/phase3-lifecycle-upstream')['samples']['idle']),
        replay=read('runs/phase3-audit/full-export-replay.json'),
        regression=dict(python_tests=59,javascript_talk_tests=5,phase0_browser=browser('runs/phase3-regression-phase0')['status'],phase1_browser=browser('runs/phase3-regression-phase1')['status']),
        isolation={k:v for k,v in read('runs/phase3-audit/isolation.json').items() if k!='files'},
        limitations=['No audio/phoneme lipsync or real classifier inference','Intermediate lids remain flat','Some expressions are subtle; no blush/teeth/tongue artwork','Residual hair gaps; no validated new hidden anatomy','RP acceptance requires optional isolated adapter for failure handling and controlled idle','CMO3/CAN3 editor containers not byte-identical across full replay','Float32 interpolation overshoot is recorded separately; eight ULP tolerance only for numeric classification'])
    write_json(output,report)
    gallery=ROOT/'runs/phase3-review';gallery.mkdir(exist_ok=False)
    def faces(directory,names,target,columns=4):
        sheet=Image.new('RGB',(1200,300*((len(names)+columns-1)//columns)),'#eee')
        draw=ImageDraw.Draw(sheet)
        for i,name in enumerate(names):
            with Image.open(ROOT/directory/(name+'.png')) as source:
                box=source.getbbox()
                im=source.crop((box[0],box[1],box[2],box[1]+int((box[3]-box[1])*.58)))
            im.thumbnail((290,270));x=i%columns*300;y=i//columns*300
            sheet.paste(im,(x,y+25),im);draw.text((x+4,y+5),name,fill='black')
        sheet.save(gallery/target)
    faces(Path('runs/phase3-final-expressions'),['neutral']+['expression_'+n for n in ['happy','sad','angry','surprised','confused','embarrassed']],'expressions.png')
    faces(Path('runs/phase3-final-visual'),['talk_'+str(i) for i in range(16)],'talking.png')
    (gallery/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Girl2 Phase 3 review</title>
<style>body{font:18px system-ui;max-width:1400px;margin:auto;background:#eee;color:#222}img{max-width:100%}a{color:#147}</style>
<h1>Girl2: actual Cubism / isolated SillyTavern renders</h1>
<p>Limited RP prototype accepted with optional isolated adapter. Flat lids and residual hair gaps remain. No production deployment, TTS lipsync or real emotion-classifier inference.</p>
<h2>Expressions</h2><img src="expressions.png">
<h2>Actual message-driven mouth sequence</h2><img src="talking.png">
<p>Sequence sampled from the actual running extension, not generated animation frames. <a href="../phase3-final-visual/result.json">Final measured mouth ROI and pixel changes</a>.</p>
<h2>All controlled poses and combinations</h2><img src="../phase3-final-expression-review/poses.png">
<h2>Tuning comparison: upper before / lower after</h2><img src="../phase3-audit/tuning-comparison.png">
<p><a href="../phase3-final/runtime/Generated_artwork.model3.json">Final runtime</a> · <a href="../phase3-final-rp/result.json">Message and emotion tests</a> · <a href="../phase3-final-lifecycle/result.json">Lifecycle</a> · <a href="../phase3-http-failure-verified/result.json">Retained upstream failure</a></p>''')
    print(output)
if __name__=='__main__':run()
