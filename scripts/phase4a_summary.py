"""Condense actual isolated evidence and create a local screenshot review."""
import argparse
import json
import re
from pathlib import Path
from PIL import Image, ImageDraw
from live2d_studio.packaging import REPO, digest, files, policy, write_json


def run(source, output):
    report=json.loads((source/'integration.json').read_text())
    if report.get('status')!='pass':raise ValueError('Integration must pass first')
    output.mkdir()
    def browser(name):return json.loads((source/name/'result.json').read_text())['result']['value']
    report['regression']={phase:browser(phase)['status'] for phase in ['phase0','phase1']}
    python_log=(source/'regression-python.log').read_text()
    js_log=(source/'regression-js.log').read_text()
    count=re.search(r'^Ran (\d+) tests',python_log,re.M)
    js_count=re.search(r'tests (\d+)',js_log)
    if not count or not js_count or '\nOK\n' not in python_log or 'fail 0' not in js_log:
        raise ValueError('Passing regression logs required')
    report['regression'].update(python_tests=int(count[1]),javascript_controller_tests=int(js_count[1]))
    report['uninstall']={}
    for variant in ['upstream','adapter']:
        r=browser(variant+'-uninstall/browser')
        if r['status']!='pass':raise ValueError('Uninstall discovery failed')
        report['uninstall'][variant]=r
    manifest=json.loads((source/'girl2/package-manifest.json').read_text())
    report['package']=dict(file_count=len(files(source/'girl2')),manifest_sha256=digest(source/'girl2/package-manifest.json'),
        runtime_sha256=manifest['files_sha256'],core_probe=manifest['core_probe'],provenance=manifest['provenance'],
        completeness=manifest['readiness'])
    report['artifacts']=dict(package=str((source/'girl2').relative_to(REPO)),review=str(output.relative_to(REPO)),integration=str((source/'integration.json').relative_to(REPO)))
    report['limitations']=policy()['limitations']
    report['rollback_scope']='Exact deployment-owned files, modes and mtimes; browser fixture state separately preserved/reset, never user settings rollback'
    report['earlier_attempts']=[dict(run='runs/phase4a-acceptance-v1',result='Sandbox blocked loopback listen; no browser claim'),dict(run='runs/phase4a-acceptance-v2',result='Saved-chat startup classification preceded mock; caught upstream lifecycle error retained')]
    for variant in ['upstream','adapter']:
        rows=browser(variant+'-lifecycle')['samples']['idle']
        report.setdefault('idle_ranges',{})[variant]={key:dict(min=min(r[key] for r in rows),max=max(r[key] for r in rows)) for key in ['ParamAngleX','ParamEyeLOpen','ParamEyeROpen','ParamMouthOpenY']}
    exp=browser('adapter-expressions')
    report['neutral_equals_phase3']=False
    with Image.open(source/'adapter-expressions/neutral.png') as a,Image.open(REPO/'runs/phase3-final-expressions/neutral.png') as b:
        report['neutral_equals_phase3']=a.size==b.size and a.convert('RGBA').tobytes()==b.convert('RGBA').tobytes()
    if not report['neutral_equals_phase3']:raise ValueError('Neutral runtime changed')
    def sheet(folder,names,filename,columns=4):
        result=Image.new('RGB',(1200,330*((len(names)+columns-1)//columns)),'#eeeeee')
        draw=ImageDraw.Draw(result)
        for i,name in enumerate(names):
            with Image.open(source/folder/(name+'.png')) as raw:
                im=raw.convert('RGBA');box=im.getbbox()
                im=im.crop((box[0],box[1],box[2],box[1]+int((box[3]-box[1])*.60)))
                im.thumbnail((290,295))
            x=i%columns*300;y=i//columns*330
            result.paste(im,(x,y+28),im);draw.text((x+5,y+7),name,fill='black')
        result.save(output/filename)
    sheet('adapter-expressions',['neutral']+['expression_'+n for n in ['happy','sad','angry','surprised','confused','embarrassed']],'expressions.png')
    sheet('adapter-visual',['talk_'+str(i) for i in range(16)],'talking.png')
    sheet('adapter-expressions',['combined_neutral','combined_happy','stress_open_minus','stress_open_plus','blink_25','blink_50','closed_L','closed_R'],'combined.png')
    with Image.open(source/'adapter-expressions/neutral.png') as raw:
        portrait=raw.convert('RGBA');portrait=portrait.crop(portrait.getbbox())
        portrait.save(output/'portrait.png')
    write_json(output/'report.json',report)
    (output/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Phase 4A Girl2 review</title>
<style>body{font:18px system-ui;max-width:1250px;margin:30px auto;background:#eee;color:#222}img{max-width:100%}a{color:#145}</style>
<h1>Girl2 package: actual isolated SillyTavern renders</h1>
<p>Deployed through the Phase 4A CLI. Optional adapter enabled for these frames.
Limited portrait prototype: flat intermediate lids, residual hair gaps and subtle mouth shapes remain.
No new anatomy, audio lipsync or classifier-model inference.</p>
<p><a href="report.json">Integration and rollback report</a>. Upstream fallback failure is retained;
all adapter RP scenarios pass. Both copies were removed with original extension files restored.
Browser-created chat/settings fixtures are reset separately from deployment rollback.</p>
<h2>Complete supplied portrait silhouette</h2><img style="max-width:420px" src="portrait.png">
<h2>Seven expressions</h2><img src="expressions.png">
<h2>Real message-driven talking sequence</h2><img src="talking.png">
<h2>Combined-motion and eyelid limitations</h2><img src="combined.png">
<p>Neutral canvas RGBA matches the accepted Phase 3 frame exactly. These images are contact sheets
of runtime screenshots, not generated illustrations. Source has no forearms/hands; sleeves are body-following only.</p>''')
    print(output/'index.html')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();run(args.source.absolute(),args.output.absolute())
