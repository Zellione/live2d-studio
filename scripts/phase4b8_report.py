"""Record canonical review evidence without making an acceptance decision."""
import argparse
import html
import json
from pathlib import Path
import shutil
from live2d_studio.pose_review import Store,digest,write,REPO
from live2d_studio.canonical_reference import load_frozen


def report(run,output,benchmark):
    store=Store(run);state=store.state();store.verify_pins(state)
    if state.get('workflow')!='canonical':raise ValueError('Not a canonical review')
    output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(store.safe(state['source']['path']),output/'original.png')
    candidates=[];cards=[]
    for batch in state['batches']:
        g=state['poses']['canonical']['guides'][batch['config']['guidance']]
        guide_name=batch['id']+'-guide.png';shutil.copyfile(store.safe(g['path']),output/guide_name)
        cards.append(f'<article><h2>Target guide</h2><p>{html.escape(batch["preset"])}</p><img src="{guide_name}"></article>')
        for c in batch['candidates']:
            if c['status']!='ready':continue
            store.verify_candidate(state,c['id']);name=c['id']+'.png';shutil.copyfile(store.safe(c['image']),output/name)
            decision=c.get('decision');public={k:v for k,v in decision.items() if k!='reviewer'} if decision else None
            candidates.append({'id':c['id'],'batch':batch['id'],'preset':batch['preset'],'result':c['result'],'decision':public})
            label='approved canonical base' if state['poses']['canonical']['selected']==c['id'] else public['action'] if public else 'not selected'
            cards.append(f'<article><h2>Seed {c["seed"]}</h2><p>{html.escape(batch["preset"])} · {html.escape(label)}</p><a href="{name}"><img src="{name}"></a><details><summary>Exact settings</summary><pre>{html.escape(json.dumps(c["result"],indent=2))}</pre></details></article>')
    frozen=None
    if state.get('canonical_reference'):
        _,_,frozen=load_frozen(run)
        frozen=dict(frozen,approval={k:v for k,v in frozen['approval'].items() if k!='reviewer'})
    data={'schema_version':1,'phase':'4B.8','baseline_commit':'ad8340a',
          'source_reference':'codel-combined-v1','original':state['source'],
          'workflow':'original -> canonical candidates -> human selection -> synthetic working freeze -> optional future helpers',
          'producer_pins':state['producer_pins'],'model_lock_sha256':digest(REPO/'backends/inpainting/models.lock.json'),
          'presets':state['presets'],'candidates':candidates,'status':state['poses']['canonical']['status'],
          'canonical_reference':state.get('canonical_reference'),'frozen_manifest':frozen,
          'evaluation':'pending human approval and selected-only assessment' if not frozen else 'human-approved; anatomical usefulness requires separate assessment',
          'default_changes':False,'historical_references_modified':False,'helper_poses_generated':0,
          'arm_rigging_started':False,'production_access':False,'downloads':False,
          'artifacts':{'review_run':str(run),'gallery':str(output)}}
    assessment=store.root/'development-screening.json'
    if assessment.exists():
        screened=json.loads(assessment.read_text())
        if screened['original_sha256']!=state['source']['sha256']:raise ValueError('Screening source mismatch')
        for row in screened['candidates']:
            _,c=store.verify_candidate(state,row['candidate'])
            if c['sha256']!=row['sha256']:raise ValueError('Screening image mismatch')
        data['development_screening']=screened
    if state['poses']['canonical']['status']=='unsupported':data['evaluation']='Canonicalization marked unsuccessful by reviewer; no working base frozen'
    data['validation_evidence']={}
    for name in ('runs/phase4b8-audit/python-regression.log','runs/phase4b8-audit/pose-final-host.log',
                 'runs/phase4b8-audit/rp-js.log','runs/phase4b8-audit/mouth-js.log',
                 'runs/phase4b8-browser-synthetic/result.json','runs/phase4b8-browser-complete/result.json'):
        file=REPO/name
        if file.exists():data['validation_evidence'][name]=digest(file)
    semantics=store.root/'selected-assessment-v1/semantics.json'
    if semantics.exists():
        measured=json.loads(semantics.read_text())
        if not frozen or measured['source_sha256']!=state['source']['sha256']:raise ValueError('Unapproved or mismatched semantic assessment')
        if measured['selected']['canonical']['image_sha256']!=frozen['canonical']['sha256']:raise ValueError('Semantic candidate mismatch')
        data['selected_semantics']=measured
        data['evaluation']='Human-approved synthetic working base; selected-only segmentation comparison recorded; anatomy unverified'
        edge=measured['selected']['canonical']['baseline_long_edge']
        for name,title in [(f'source-{edge}-arms.png','Original: exploratory arm components'),
                           ('canonical-arms.png','Approved canonical: exploratory arm components'),
                           ('canonical.png','Original / canonical / unregistered difference')]:
            shutil.copyfile(semantics.parent/name,output/('assessment-'+name))
            cards.append(f'<article><h2>{title}</h2><p>Proposal only; no verified joints or hidden anatomy.</p><a href="assessment-{name}"><img src="assessment-{name}"></a></article>')
    write(output/'summary.json',data);write(benchmark,data)
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Canonical-base candidates</title><style>body{font:16px system-ui;margin:30px;background:#f3f2ed;color:#243c33}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}article{background:white;padding:15px;border-radius:10px}img{width:100%;height:480px;object-fit:contain}pre{white-space:pre-wrap;font-size:11px}</style><h1>Front-facing canonical working-base review</h1><p>Original artwork remains unchanged. Candidate images are synthetic; no automatic approval, anatomy validation or rig migration.</p><main><article><h2>Original</h2><img src="original.png"></article>'+''.join(cards)+'</main>')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--benchmark',type=Path,required=True)
    a=p.parse_args();report(a.run,a.output,a.benchmark)
