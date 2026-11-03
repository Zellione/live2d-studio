"""Attach regression/transition/model-review evidence to the Phase 4B.1 comparison."""
import argparse
import json
import re
from pathlib import Path
from PIL import Image,ImageDraw
from live2d_studio.manifest import write_json,digest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gallery',type=Path,required=True);p.add_argument('--benchmark',type=Path,required=True)
    p.add_argument('--girl2',type=Path,default=Path('runs/phase4b1-girl2'))
    p.add_argument('--transitions',type=Path,default=Path('runs/phase4b1-sara-transitions'))
    p.add_argument('--negatives',type=Path,default=Path('runs/phase4b1-negative-regression/summary.json'))
    a=p.parse_args();b=json.loads(a.benchmark.read_text())
    d=json.loads((a.girl2/'creation.json').read_text());v=a.girl2/d['stages']['validation']['directory'];q=json.loads((v/'quality.json').read_text())
    f=a.girl2/d['stages']['facial']['directory']/'layers/facial-artwork.json'
    b['girl2_regression']=dict(status=d['status'],poses=len(q['poses']),geometry=q['geometry'],
        max_holes=max(v['enclosed_transparent_pixels'] for v in q['poses'].values()),
        max_detached_pixels=max(v['detached_small_component_pixels'] for v in q['poses'].values()),
        mouth_strategy=json.loads(f.read_text())['changes'][-1])
    pins=json.loads(Path('recipes/girl2-package.json').read_text())
    phase31=json.loads(Path('docs/benchmarks/phase3-1.json').read_text())
    checks=[(Path('runs/phase3-final/runtime'),pins['accepted_source_sha256']),
            (Path('runs/phase3-final'),pins['provenance']['editable_sources_sha256']),
            (Path('runs/phase3-1-final-v2/runtime'),dict(phase31['runtime']['files_sha256'],**{'Generated_artwork.model3.json':phase31['runtime']['model_sha256']})),
            (Path('runs/phase3-1-final-v2'),{'character.psd2live':phase31['editable_project_sha256'],'character.psd':phase31['psd_sha256']})]
    for root,expected in checks:
        if any(digest(root/name)!=value for name,value in expected.items()):raise ValueError('Accepted reference changed: '+str(root))
    b['accepted_reference_preservation']=dict(status='pass',pinned_files=sum(len(v) for _,v in checks),
        sources=['recipes/girl2-package.json','docs/benchmarks/phase3-1.json'])
    q=json.loads((a.transitions/'quality.json').read_text());r=json.loads((a.transitions/'frames/result.json').read_text())['result']['value']
    b['transitions']=dict(poses=len(q['poses']),status=q['render_status'],geometry=q['geometry'],network=q['network'],
        talking_ranges={k:[min(v),max(v)] for k,v in r['talking'].items()},
        checks=r['checks'],caveat='Nominal 100ms talk samples and 150ms fades; not a real-time latency benchmark.')
    negatives=json.loads(a.negatives.read_text());b['regressions']={k:dict(status=v['status'],reasons=v['quality']['blocking_reasons']) for k,v in negatives.items()}
    model_review=Path('benchmarks/phase4b1-model-review.json')
    b['model_review']=dict(path=str(model_review),sha256=digest(model_review),weights_downloaded=False)
    pylog=Path('runs/phase4b1-python-tests.log');jslog=Path('runs/phase4b1-node-tests.log')
    py=pylog.read_text();js=jslog.read_text()
    if not py.rstrip().endswith('OK') or 'fail 0' not in js:raise ValueError('Missing passing test evidence')
    b['validation_tests']=dict(python=int(re.search(r'Ran (\d+) tests',py)[1]),
        javascript_talk=int(re.search(r'tests (\d+)',js)[1]),python_log_sha256=digest(pylog),javascript_log_sha256=digest(jslog),
        scope='Full local Python suite and existing Node talk tests; no production or new Btrfs acceptance run.')
    write_json(a.benchmark,b)
    frames=[]
    for name in ['neutral','happy','sad','angry','surprised','confused','embarrassed']:
        for i in range(10):
            im=Image.open(a.transitions/'frames'/f'talk-{name}-{i}.png').convert('RGBA');canvas=Image.new('RGB',im.size,(235,235,235));canvas.paste(im,(0,0),im)
            ImageDraw.Draw(canvas).text((12,12),'Actual sampled talking: '+name,fill='black');frames.append(canvas)
    frames[0].save(a.gallery/'talking.gif',save_all=True,append_images=frames[1:],duration=100,loop=0)
    fades=[]
    for name in ['happy','sad','angry','surprised','confused','embarrassed']:
        for i in range(4):
            im=Image.open(a.transitions/'frames'/f'fade-{name}-{i}.png').convert('RGBA');canvas=Image.new('RGB',im.size,(235,235,235));canvas.paste(im,(0,0),im)
            ImageDraw.Draw(canvas).text((12,12),'Actual sampled return from '+name,fill='black');fades.append(canvas)
    fades[0].save(a.gallery/'fades.gif',save_all=True,append_images=fades[1:],duration=150,loop=0)
    with (a.gallery/'index.html').open('a') as stream:
        stream.write('<h2>Actual time-sampled animation</h2><p>Ten talking samples per expression; four fade samples returning to neutral. Nominal sample intervals, not a playback performance benchmark.</p><img src="talking.gif"><img src="fades.gif">')
    print(a.benchmark)

if __name__=='__main__':main()
