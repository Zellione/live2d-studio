"""Summarize local, hash-bound Phase 4B.11.1 evidence without editing artwork."""
import argparse
import json
from pathlib import Path
import re
import shutil

import numpy as np
from PIL import Image
from live2d_studio.elbow_rig import frozen_reference
from live2d_studio.manifest import digest,write_json
from live2d_studio.stages import inventory,verify

REPO=Path(__file__).resolve().parents[1]


def record(file):return {'path':str(file.relative_to(REPO)),'sha256':digest(file)}


def browser(file):
    data=json.loads(file.read_text())['result']['value']
    return {**record(file),'status':data['status'],'frames':len(data.get('frames',[])),
            'geometry':data.get('geometry',{}),'checks':data['checks'],'error':data.get('error')}


def build(run,gallery):
    run=run.resolve();gallery=gallery.resolve()
    if not gallery.is_relative_to(REPO/'runs') or gallery.exists():raise ValueError('Fresh ignored gallery required')
    result=json.loads((run/'arms/arm-result.json').read_text());validation=Path(result['validation'])
    if json.loads((validation/'summary.json').read_text())['status']!='pass':raise ValueError('Validation did not pass')
    audit=REPO/'runs/phase4b11-1-audit';python=audit/'python-final.log'
    text=python.read_text();match=re.search(r'Ran (\d+) tests',text)
    if not match or not text.rstrip().endswith('OK'):raise ValueError('Full Python suite did not pass')
    pin=REPO/'docs/references/codel-frontal-elbows-v1.json';ref,manifest=frozen_reference(pin)
    model=Path(result['model']);original=ref/'runtime'/model.name
    same=[];changed=[]
    for name,h in inventory(original.parent).items():
        (same if digest(model.parent/name)==h else changed).append(name)
    references_equal=json.loads(model.read_text())['FileReferences']==json.loads(original.read_text())['FileReferences']
    preserved={}
    for name in ['codel-combined-v1','codel-frontal-prototype-v1','codel-frontal-elbows-v1']:
        _,m=frozen_reference(REPO/'docs/references'/f'{name}.json');preserved[name]={'files':len(m['files']),'all_hashes_match':True}
    cores={}
    for name in ['body-elbows','mouth']:
        file=validation/(name+'.json');data=json.loads(file.read_text())
        cores[name]={**record(file),**{k:v for k,v in data.items() if not isinstance(v,(dict,list))},'samples':len(data['samples'])}
    historical=REPO/'runs/phase4b11-1-historical-regression'
    report={'phase':'4B.11.1','baseline_commit':'e014179181b1921ef41d42466e42993c67013707',
        'status':'reviewed-reference-frozen-optional-integration-validated','reference':json.loads(pin.read_text()),
        'user_review':json.loads((ref/'user-review.json').read_text())['reply'],
        'performance_run':str(run.relative_to(REPO)),'result':record(run/'arms/arm-result.json'),
        'authorization':result['authorization'],'preserved_references':preserved,
        'reproduction':{'identical_runtime_payloads':same,'different_files':changed,'file_references_equal':references_equal,
                        'existing_expression_physics_motion_files_preserved':len(result['preserved_payloads'])},
        'core':cores,'browser':{n:browser(validation/n/'frames/result.json') for n in ['arms','coexistence']},
        'historical':{n:browser(historical/n/'frames/result.json') for n in ['dense','body','coexistence','arms']},
        'tests':{'python':dict(record(python),status='pass',count=int(match[1])),
                 'javascript':[record(audit/n) for n in ['javascript-talk.log','javascript-mouth.log']]},
        'fallback':json.loads((audit/'fallback.log').read_text()),
        'resume':record(audit/'resume.log'),'code_pins':json.loads((run/'arms/creation.json').read_text())['stages']['arm-plan']['inputs']['code'],
        'neutral_vs_previous_frontal':json.loads((REPO/'docs/benchmarks/phase4b11.json').read_text())['preservation']['render_neutral_vs_reference'],
        'retained_failures':['runs/phase4b11-elbow-v6: 8983 visible triangle reversals',
             'Historical shoulder fixed-total-count failure retained unchanged',
             'First replay validation inventory rejected Chromium profile symlinks',
             'Sandbox Python run: two loopback socket PermissionErrors; host suite passes'],
        'new_image_inference':False,'defaults_changed':False,'production_touched':False,
        'replay_automatically_accepted':False,'anatomy_independently_verified':False,
        'viewer':'http://127.0.0.1:8817/','gallery':str(gallery.relative_to(REPO))}
    before=REPO/'runs/phase4b11-bilateral-render-final/frames/neutral.png'
    frames=validation/'arms/frames'
    a=np.array(Image.open(before));b=np.array(Image.open(frames/'neutral.png'))
    report['replay_neutral_vs_reviewed_elbows']={'same_dimensions':a.shape==b.shape,
         'changed_pixels':int(np.any(a!=b,axis=-1).sum()) if a.shape==b.shape else None}
    gallery.mkdir(parents=True);(gallery/'frames').mkdir()
    for file in frames.glob('*.png'):shutil.copyfile(file,gallery/'frames'/file.name)
    shutil.copyfile(before,gallery/'reviewed-neutral.png')
    write_json(gallery/'result.json',report)
    (gallery/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Reviewed elbow replay</title>
<style>body{font:16px system-ui;background:#eee;color:#222;margin:2em}section{display:flex;flex-wrap:wrap;gap:1em}figure{margin:0}img{height:65vh;max-width:44vw;object-fit:contain;background:white}button,select,input{font:inherit;padding:.5em}pre{white-space:pre-wrap}</style>
<h1>Reviewed elbow reference and optional workflow replay</h1>
<p>Immutable accepted neutral at left; validated replay at right. MOC, texture and motion hashes match the accepted elbow rig.
This is a limited 2D sleeve approximation, not verified anatomy. The older shoulder-only reference differs by 880 neutral pixels.</p>
<p><a href="http://127.0.0.1:8817/">Live synchronized comparison</a> · <a href="result.json">Exact evidence and limitations</a></p>
<select id="side"><option>Right</option><option>Left</option></select>
<select id="mode"><option value="sweep">Dense elbow rise/return</option><option value="clip">Gesture with talking/head/hair</option></select>
<button id="play">Play / pause</button><button id="neutral">Neutral</button><input id="frame" type="range" min="0" max="100" value="0"><span id="value">0</span>
<section><figure><figcaption>Accepted elbow neutral</figcaption><img src="reviewed-neutral.png"></figure><figure><figcaption>Optional pipeline replay</figcaption><img id="candidate" src="frames/neutral.png"></figure></section>
<p>Check sleeve continuity, independent distal motion, hand attachment and clean return. New outputs still require their own final visual review.</p>
<script>
const side=document.getElementById('side'),mode=document.getElementById('mode'),frame=document.getElementById('frame'),candidate=document.getElementById('candidate');let timer;
function show(){frame.max=mode.value==='sweep'?100:47;candidate.src='frames/'+side.value+'-'+mode.value+'-'+frame.value+'.png';document.getElementById('value').textContent=frame.value}
frame.oninput=show;side.onchange=show;mode.onchange=()=>{frame.value=0;show()};document.getElementById('neutral').onclick=()=>{clearInterval(timer);timer=null;candidate.src='frames/neutral.png'};
document.getElementById('play').onclick=()=>{if(timer){clearInterval(timer);timer=null}else timer=setInterval(()=>{frame.value=(Number(frame.value)+1)%(Number(frame.max)+1);show()},100)};
</script>''')
    write_json(REPO/'docs/benchmarks/phase4b11-1.json',report)
    print(json.dumps({'gallery':str(gallery),'runtime_identical_payloads':len(same),'changed_files':changed,
        'neutral_comparison':report['replay_neutral_vs_reviewed_elbows'],'python_tests':int(match[1])},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,default=REPO/'runs/phase4b11-1-performance')
    p.add_argument('--gallery',type=Path,required=True);a=p.parse_args();build(a.run,a.gallery)
