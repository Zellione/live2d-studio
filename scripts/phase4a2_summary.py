"""Build a compact benchmark and local visual review from actual Phase 4A.2 evidence."""
import argparse
import json
import re
from pathlib import Path
from PIL import Image, ImageDraw
from live2d_studio.packaging import REPO, digest, write_json


def run(source,output):
    source=source.absolute();output=output.absolute()
    if '..' in output.parts or not output.is_relative_to(REPO/'runs') or any(p.is_symlink() for p in [output,*output.parents]):
        raise ValueError('Review output must be a fresh path under runs/')
    output.mkdir()
    data=json.loads((source/'integration.json').read_text())
    assert data['status']=='pass-with-classifier-blocker'
    before=json.loads((source/'production-before.json').read_text())
    after=json.loads((source/'production-after.json').read_text())
    checks=['pinned_files','runtime_hashes','global_assets','character_assets','preferences','settings_metadata','versions']
    assert all(before[k]==after[k] for k in checks)
    assert after['inherited_browser_evidence']['mismatches']==[]
    audit=REPO/'runs/phase4a2-audit'
    logs={n:(audit/f).read_text() for n,f in [('python','python-regression-validated.log'),('btrfs','btrfs-tests-final.log')]}
    for text in logs.values():assert '\nOK\n' in text
    counts={k:int(re.search(r'^Ran (\d+) tests',v,re.M)[1]) for k,v in logs.items()}
    js=(audit/'js-tests.log').read_text();assert 'fail 0' in js
    counts['javascript_controller']=int(re.search(r'tests (\d+)',js)[1])
    def browser(name):return json.loads((source/name/'result.json').read_text())['result']['value']
    scenarios={}
    for name in data['scenarios']:
        r=browser(name)
        assert r['status']==('fail' if name=='upstream-failure' else 'pass')
        scenarios[name]=dict(status=r['status'],network=r['network_validation'],
            mapped_expressions=len(r.get('mapping_checks',{})),
            raw_opacity_excursions=sum(g['rawOpacityExcursions'] for g in r['geometry'].values()),
            provider_preserved=r.get('provider_preserved'),fallback=r.get('actual_fallback'))
    uninstall={v:browser(v+'-uninstall/browser')['status'] for v in ['upstream','adapter']}
    assert all(v=='pass' for v in uninstall.values())
    with Image.open(source/'adapter-expressions/neutral.png') as a,Image.open(REPO/'runs/phase3-final-expressions/neutral.png') as b:
        neutral_equal=a.size==b.size and a.convert('RGBA').tobytes()==b.convert('RGBA').tobytes()
    assert neutral_equal
    def sheet(folder,names,filename):
        result=Image.new('RGB',(1200,330*((len(names)+3)//4)),'#eeeeee');draw=ImageDraw.Draw(result)
        for i,name in enumerate(names):
            with Image.open(source/folder/(name+'.png')) as raw:
                im=raw.convert('RGBA');box=im.getbbox();im=im.crop((box[0],box[1],box[2],box[1]+int((box[3]-box[1])*.60)));im.thumbnail((290,295))
            x=i%4*300;y=i//4*330;result.paste(im,(x,y+28),im);draw.text((x+5,y+7),name,fill='black')
        result.save(output/filename)
    sheet('adapter-expressions',['neutral']+['expression_'+n for n in ['happy','sad','angry','surprised','confused','embarrassed']],'expressions.png')
    sheet('adapter-visual',['talk_'+str(i) for i in range(16)],'talking.png')
    sheet('adapter-expressions',['combined_neutral','combined_happy','stress_open_minus','stress_open_plus','blink_25','blink_50','closed_L','closed_R'],'combined.png')
    report=dict(phase='4A.2',starting_commit='b53c3eb',status='completed-with-LLM-integration-blocker',
        gates=dict(target_transaction='pass-isolated-Btrfs',runtime_integration='pass-with-known-upstream-HTTP-failure',
                   visual='unchanged-limited-portrait',LLM_integration='blocked-no-bridge-shipped',production='disabled'),
        tests=counts,scenarios=scenarios,uninstall=uninstall,restoration=data['restoration'],filesystems=data['filesystems'],
        production_unchanged=dict(projected_settings_and_metadata=True,assets=True,compatibility_pins=True,
                                  public_baseline_files=after['inherited_browser_evidence']['files_checked']),
        versions=after['versions'],core=after['core_probe'],neutral_equals_phase3=neutral_equal,
        classifier_contract=json.loads((audit/'classifier-contract.json').read_text()),
        real_LLM_inference=False,audio_lipsync=False,power_loss_certified=False,
        package_manifest_sha256=after['package_manifest_sha256'],
        release_recovery_sha256=digest(REPO/'src/live2d_studio/target_recovery.py'),
        evidence=str(source.relative_to(REPO)),review=str(output.relative_to(REPO)))
    write_json(output/'report.json',report)
    (output/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Phase 4A.2 isolated review</title>
<style>body{font:18px system-ui;max-width:1250px;margin:30px auto;background:#eee}img{max-width:100%}</style>
<h1>Girl2 on disposable Btrfs SillyTavern</h1><p>Actual browser frames after cross-filesystem deployment, optional RP adapter enabled.
The neutral canvas equals Phase 3. Flat intermediate eyelids, residual stress-pose hair gaps and body-following sleeves remain.</p>
<p>Both instances rolled back with /data hidden; browser-created preferences survived. Production unchanged.
LLM integration is blocked: provider 2 retains neutral adapter fallback. Seven displayed emotions use supported-provider mocks or manual expression selection, not real inference.</p>
<p><a href="report.json">Integration report</a>. Upstream HTTP fallback is an expected negative result. No audio lip synchronization or power-loss certification.</p>
<h2>Seven expressions</h2><img src="expressions.png"><h2>Text-driven talking</h2><img src="talking.png">
<h2>Combined poses and eyelid limitations</h2><img src="combined.png">''')
    print(output/'report.json')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.source,a.output)
