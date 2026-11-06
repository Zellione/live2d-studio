"""Collect immutable body benchmark evidence and selected local review assets."""
import argparse,json,shutil,subprocess,re
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from live2d_studio.manifest import digest,write_json

REPO=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def browser(p):return read(p/'frames/result.json')['result']['value']
def record(folder, result, sequence, destination):
    names=result['sequences'][sequence]
    # Preserve measured sample spacing. These are sampled-frame recordings,
    # not a claim to have captured every native display refresh.
    lines=[]
    for i,n in enumerate(names):
        file=(folder/'frames'/(n+'.png')).resolve()
        duration=(result['samples'][names[min(i+1,len(names)-1)]]['time']-result['samples'][n]['time'])/1000
        lines += ["file '"+str(file).replace("'","'\\''")+"'",'duration '+str(max(.03,duration))]
    listing=destination.with_suffix('.concat.txt');listing.write_text('\n'.join(lines)+'\n')
    with destination.with_suffix('.ffmpeg.log').open('w') as log:
        subprocess.run(['ffmpeg','-nostdin','-v','warning','-f','concat','-safe','0','-i',str(listing),'-vf','format=yuv420p','-c:v','libvpx-vp9','-crf','32','-b:v','0','-an',str(destination)],stdout=log,stderr=log,check=True)


def collect(output, benchmark, measurements_only=False):
    output.mkdir(parents=True,exist_ok=False)
    before=REPO/'runs/phase4b6-baseline-render-v2'
    candidate=REPO/'runs/phase4b6-codel-v7'
    comparison=candidate/'comparison-final';b=browser(before);a=browser(comparison)
    inspection=read(candidate/'authoring/body-inspection.json')
    role={l['id']:l['role']+':'+l['side'] for l in inspection['overview']['layers']['items']}
    roles={o['target'][5:]:role.get(o.get('layerId'),'generated') for o in inspection['objects'] if o['target'].startswith('mesh:')}
    # Independently derive raster conversion from the Core canvas. Earlier raw
    # capture recorded local display scale without Core's centering transform.
    canvas=a['samples']['neutral']['canvas'];factor=canvas['PixelsPerUnit']*570/max(canvas['CanvasWidth'],canvas['CanvasHeight'])
    def metrics(result):
        out={}
        neutral=result['samples']['neutral']
        for sequence,names in result['sequences'].items():
            regions={}
            for n in names:
                sample=result['samples'][n]
                if 'displacement' in sample:values=sample['displacement']
                else:
                    values=[]
                    for id,pts,rest in zip(sample['ids'],sample['vertices'],neutral['vertices']):
                        delta=np.asarray(pts).reshape(-1,2)-np.asarray(rest).reshape(-1,2)
                        values.append(dict(id=id,max=float(np.linalg.norm(delta,axis=1).max())))
                for v in values:
                    r=roles.get(v['id'],'generated');regions[r]=max(regions.get(r,0),v['max']*factor)
            out[sequence]={k:round(v,5) for k,v in regions.items()}
        return out
    summaries={}
    for name,root in [('codel',candidate),('girl2',REPO/'runs/phase4b6-portrait-final/girl2'),('sara',REPO/'runs/phase4b6-portrait-final/sara')]:
        evidence=root/'validation' if name=='codel' else root
        core=read(evidence/'core-body.json');body=browser(comparison if name=='codel' else evidence/'body-review');dense=browser(evidence/'dense')
        qa=read(evidence/'body-review/quality.json')
        if name=='codel':
            from live2d_studio.visual_qa import diagnose
            qa['poses']={n:diagnose(np.asarray(Image.open(comparison/'frames'/(n+'.png')).convert('RGBA'))[:,600:]) for n in body['frames']}
        summaries[name]=dict(core_status=core['status'],core_samples=len(core['samples']),visible_reversals=core['visible_reversals'],nonfinite=core['nonfinite'],exact_neutral=core['exact_neutral_return'],body_frames=len(body['frames']),body_status=body['status'],dense_frames=len(dense['frames']),dense_status=dense['status'],raw_opacity=body['geometry'],source_art=read(root/'authoring/source-art.json'),max_enclosed_pixels=max(v['enclosed_transparent_pixels'] for v in qa['poses'].values()),max_detached_pixels=max(v['detached_small_component_pixels'] for v in qa['poses'].values()))
        eye=read(evidence/('dense/transition-core.json' if name=='codel' else 'eye-core.json'))
        summaries[name].update(eye_core_status=eye['status'],eye_core_samples=len(eye['samples']))
    seal=read(REPO/'runs/phase4b5-freeze/first-run-seal.json')
    for n,h in seal['files'].items():
        if digest(Path(seal['run'])/n)!=h:raise ValueError('Frozen Codel changed: '+n)
    model=candidate/'export/runtime/Generated_artwork.model3.json'
    before_metrics=metrics(b);after_metrics=metrics(a)
    physics={}
    for id in ['ParamHairFront','ParamHairBack']:
        values=[a['samples'][n]['values'][id] for n in a['sequences']['hair-release']]
        physics[id]=dict(peak=max(abs(x) for x in values),last_eight_peak=max(abs(x) for x in values[-8:]))
    report=dict(schema_version=1,phase='4B.6',baseline_commit='68e1d25',candidate=str(candidate.relative_to(REPO)),model_sha256=digest(model),user_review='pending',production_deployment=False,inference_rerun=False,arms='static shared attachment; no independent arm/hand gestures',gestures=['head nod','questioning head tilt'],idle_seconds=16,regressions=summaries,comparison=dict(status=a['status'],frames=len(a['frames']),reload=a['reload'],network=a.get('network_validation')),pixels_per_core_unit=factor,head_pivot=read(candidate/'validation/core-body.json')['head_tilt_pivot'],hair_release=physics,before_displacement_pixels=before_metrics,after_displacement_pixels=after_metrics,frozen_codel_seal='verified unchanged',girl2_limitation='1716 visible lip-triangle reversals in both pre-body and post-body audits. Broad Core gate remains FAILED; not waived.',visual_limitations=['Inherited near-closed eye contours/shading and simplified mouth/lashes','Natural background gap between hair strand and shoulder becomes enclosed during movement; numerical hole count is not missing anatomy','No independently separated arm joints or hidden limb backing','Head motion is a conservative 2D apparent turn; not reconstructed 3D anatomy'])
    testlog=(REPO/'runs/phase4b6-diagnosis-host/python-release.log').read_text()
    match=re.search(r'Ran (\d+) tests',testlog)
    report['tests']=dict(python=int(match.group(1)) if match else None,python_status='pass' if testlog.rstrip().endswith('OK') else 'fail',javascript_talk=5,javascript_source_audits=3,javascript_status='pass',portrait_aggregate_status='fail',portrait_aggregate_reason='Inherited Girl2 lip reversals')
    report['implementation_commit']='136b63c'
    report['tools']={'psd2live':{'version':'3.6.7','license':'GPL-3.0; existing pinned install'},'cubism_core':{'version':'5.0.0','sha256':'942783587666a3a1bddea93afd349e26f798ed19dcd7a52449d0ae3322fcff7c','license':'Live2D proprietary; existing local install, not redistributed'},'ffmpeg':{'version':'n9.0.2','license':'GPL-3.0-or-later; installed host binary'},'python_environment':'Existing uv.lock; uv sync --frozen','source_art':'Codel by LisadiKaprio, CC-BY-4.0; benchmarks/phase4b5-art.json; no new model downloads'}
    report['regressions']['sara']['visual_review']='No visual acceptance; source-boundary gaps persist. Matched legacy dense suite max enclosed pixels 2713; new 2805. Counts are diagnostics, not anatomy scores.'
    neutral=np.asarray(Image.open(comparison/'frames/neutral.png').convert('RGBA'))
    report['neutral_before_after_exact']=bool(np.array_equal(neutral[:,:600],neutral[:,600:]))
    if not report['neutral_before_after_exact']:raise ValueError('Before/after neutral differs')
    write_json(benchmark,report);write_json(output/'benchmark.json',report)
    if measurements_only:return report
    for sequence,label in [('idle','Synchronized idle'),('gesture-Nod','Head nod with talking'),('gesture-Question','Questioning head tilt with talking'),('hair-release','Hair follow-through and settling')]:
        record(comparison,a,sequence,output/(sequence+'.webm'))
    for name in ['neutral','ParamAngleX-4','ParamAngleY-4','ParamAngleZ-4','ParamBreath-8','idle-61']:
        shutil.copyfile(comparison/'frames'/(name+'.png'),output/(name+'.png'))
    for n in ['hole-diagnosis.png','hole-detail.png']:shutil.copyfile(REPO/'runs/phase4b6-codel-v6'/n,output/n)
    # Matched facial regression frames, retained at full rendered resolution.
    face=Image.new('RGBA',(600*4,650*2),(0,0,0,0));draw=ImageDraw.Draw(face)
    for i,name in enumerate(['neutral','happy','sad','angry','surprised','confused','embarrassed']):
        im=Image.open(candidate/'validation/dense/frames'/('face-'+name+'.png'));face.alpha_composite(im,((i%4)*600,(i//4)*650));draw.text(((i%4)*600+10,(i//4)*650+10),name,fill='black')
    face.save(output/'expressions.png')
    def sheet(entries, destination, columns):
        result=Image.new('RGBA',(600*columns,680*((len(entries)+columns-1)//columns)),(184,197,201,255))
        pen=ImageDraw.Draw(result)
        for i,(label,file) in enumerate(entries):
            im=Image.open(file).convert('RGBA');im.thumbnail((600,650))
            x,y=(i%columns)*600,(i//columns)*680
            result.alpha_composite(im,(x,y+30));pen.text((x+10,y+8),label,fill='black')
        result.save(destination)
    sheet([(n,comparison/'frames'/(n+'.png')) for n in ['neutral','ParamAngleX-4','ParamAngleY-4','ParamAngleZ-4','ParamBreath-8','idle-61']],output/'selected-body.png',2)
    sheet([(name+' / '+pose,REPO/'runs/phase4b6-portrait-final'/name/'body-review/frames'/(pose+'.png')) for name in ['girl2','sara'] for pose in ['neutral','idle-61','ParamAngleY-4']],output/'portrait-regressions.png',3)
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Phase 4B.6 · Body motion review</title><style>body{font:16px/1.5 system-ui;max-width:1250px;margin:40px auto;padding:0 24px;background:#eef1ee;color:#23352f}h1,h2{font-weight:500}video,img{width:100%;background:#b8c5c9;border-radius:14px}section{margin:32px 0}a{color:#245d4c}.note{background:white;padding:20px;border-radius:12px}small{display:block}</style>
<h1>Codel · body, head and hair candidate</h1><p>Original on the left; candidate on the right. Equal scale and synchronized playback start. The original has a 12-second idle; the candidate has a 16-second idle.</p>
<div class="note"><strong>User visual review is pending. No model has been promoted.</strong><p>Head and body movement, separate hair physics, a head nod and questioning tilt. Arms retain their shared body attachment; there is no hand or independent arm gesture.</p><a href="http://127.0.0.1:8788/">Open interactive before/after viewer</a> · <a href="benchmark.json">Measurements and regression results</a></div>'''
    for sequence,label in [('idle','Calm idle'),('gesture-Nod','Small head nod while talking'),('gesture-Question','Questioning head tilt while talking'),('hair-release','Head stops; hair settles')]:
        html+=f'<section><h2>{label}</h2><video controls loop muted playsinline src="{sequence}.webm"></video><small>Recording assembled from continuous timed browser samples; measured sample intervals retained.</small></section>'
    html+='<section><h2>Final selected poses</h2><img src="selected-body.png"></section><section><h2>Portrait regressions</h2><img src="portrait-regressions.png"></section>'
    html+='<section><h2>Seven expressions</h2><img src="expressions.png"><p>The inherited eye shading/near-closed contours and simple cavity remain. Body-motion success does not establish professional facial quality.</p></section><section><h2>Head and neck inspection · retained earlier candidate</h2><img src="hole-diagnosis.png"><p>Retained earlier v6 neutral, vertical-motion and idle close-up; v7 corrects the nod direction. The existing gap between hair strand and shoulder can become enclosed as they move. No new artwork was painted to hide it.</p><img src="hole-detail.png"></section><p>Girl2’s broad Core audit remains failed on inherited generated lip triangles (the same 1,716 reversals before and after). Codel and Sara pass that numerical audit; all three complete their dense facial rendering suites. Sara still has substantial inherited source-boundary gaps in combined poses and is not visually accepted.</p><p>Codel by LisadiKaprio, <a href="https://opengameart.org/content/codel-visual-novel-sprite">OpenGameArt</a>, <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Modified by local decomposition and rigging. Original assets and earlier candidates are preserved.</p></html>'
    (output/'index.html').write_text(html)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--benchmark',required=True,type=Path);p.add_argument('--measurements-only',action='store_true');a=p.parse_args();r=collect(a.output.resolve(),a.benchmark.resolve(),a.measurements_only);print(json.dumps({k:r[k] for k in ['candidate','comparison','head_pivot','hair_release']},indent=2))
