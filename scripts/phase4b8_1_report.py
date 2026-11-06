"""Hash-bound gesture study report. Development screening never creates approval."""
import argparse
import html
import json
from pathlib import Path
import shutil
from live2d_studio.pose_review import Store,REPO,digest,write


def report(run,output,benchmark,controls=()):
    store=Store(run);state=store.state();store.verify_pins(state)
    if state.get('workflow')!='canonical-helpers':raise ValueError('Canonical helper run required')
    output.mkdir(parents=True,exist_ok=False);cards=[];rows=[]
    def card(name,title,note=''):
        cards.append(f'<article><h2>{html.escape(title)}</h2><p>{html.escape(note)}</p><a href="{name}"><img src="{name}"></a></article>')
    for key,title in [('source','Frozen canonical · synthetic geometry'),('identity_reference','Original · identity/style')]:
        record=state[key];name=key+'.png';shutil.copyfile(store.safe(record['path']),output/name);card(name,title)
    for batch in state['batches']:
        planfile=store.safe(batch['directory']+'/plan.json')
        if digest(planfile)!=batch['plan_sha256']:raise ValueError('Plan changed')
        plan=json.loads(planfile.read_text());guide=store.safe(batch['directory']+'/guide.png')
        name=batch['id']+'-guide.png';shutil.copyfile(guide,output/name);card(name,'Target: '+state['poses'][batch['pose']]['title'])
        for c in batch['candidates']:
            if c['status']!='ready':continue
            store.verify_candidate(state,c['id']);name=c['id']+'.png';shutil.copyfile(store.safe(c['image']),output/name)
            label='human-approved' if state['poses'][batch['pose']]['selected']==c['id'] else (c.get('decision') or {}).get('action','not selected')
            card(name,c['task_id']+' · '+label,f"Seed {c['seed']} · {c['result']['reference_latent_count']} references · {c['result']['seconds']:.1f}s")
            rows.append({'candidate':c['id'],'pose':batch['pose'],'batch':batch['id'],'input_hashes':plan['inputs'],
                         'plan_sha256':batch['plan_sha256'],'result':c['result'],
                         'decision':{k:v for k,v in (c.get('decision') or {}).items() if k!='reviewer'}})
    data={'schema_version':1,'phase':'4B.8.1','baseline_commit':'46717d4','source_canonical':state['source'],
          'identity_original':state['identity_reference'],'canonical_origin':state['canonical_origin'],
          'gesture_profile':state.get('gesture_profile'),'producer_pins':state['producer_pins'],
          'presets':state['presets'],'candidates':rows,'poses':{k:{'status':v['status'],'selected':v['selected']} for k,v in state['poses'].items()},
          'selections':state['exports'],'controls':[],
          'scope':'Synthetic helper evidence only; reference count and visual acceptance are distinct from gesture compliance and anatomy',
          'arm_rigging':False,'runtime_replacement':False,'production_access':False,'downloads':False,
          'artifacts':{'run':str(run),'gallery':str(output)}}
    screen=store.root/'development-screening.json'
    if screen.exists():
        screening=json.loads(screen.read_text())
        if screening['canonical_sha256']!=state['source']['sha256']:raise ValueError('Screening canonical mismatch')
        for row in screening['candidates']:
            _,c=store.verify_candidate(state,row['candidate'])
            if c['sha256']!=row['sha256']:raise ValueError('Screening candidate mismatch')
        data['development_screening']=screening
    for directory in controls:
        meta=json.loads((directory/'control.json').read_text());plan=json.loads((directory/'plan.json').read_text())
        if digest(directory/'plan.json')!=meta['control_plan_sha256']:raise ValueError('Control plan changed')
        result=json.loads((directory/'c1/result.json').read_text());image=directory/'c1/image.png'
        if digest(image)!=result['image_sha256'] or result['seed']!=meta['seed']:raise ValueError('Control result mismatch')
        name='control-'+meta['mode']+'.png';shutil.copyfile(image,output/name)
        card(name,'Diagnostic only: '+meta['mode'],'Not a reviewed candidate; same parent seed. '+meta['change'])
        data['controls'].append({'metadata':meta,'result':result,'input_hashes':plan['inputs'],'directory':str(directory)})
    semantics=store.root/'selected-assessment-v1/semantics.json'
    if semantics.exists():
        measured=json.loads(semantics.read_text())
        if measured['source_sha256']!=state['source']['sha256']:raise ValueError('Semantic baseline mismatch')
        for pose,row in measured['selected'].items():
            p=state['poses'][pose]
            if p['status']!='approved':raise ValueError('Unapproved semantic evidence')
            _,c=store.verify_candidate(state,p['selected'])
            if row['image_sha256']!=c['sha256']:raise ValueError('Semantic selection mismatch')
            for name,title in [(f"source-{row['baseline_long_edge']}-arms.png",'Canonical arm proposals'),(pose+'-arms.png','Selected gesture arm proposals')]:
                shutil.copyfile(semantics.parent/name,output/name);card(name,title,'Connected components are not individual joints.')
        data['selected_semantics']=measured
    data['validation_evidence']={}
    for name in ['runs/phase4b8-1-audit/python-regression-final.log','runs/phase4b8-1-audit/javascript-regression.log',
                 'runs/phase4b8-1-browser-synthetic-v2/result.json','runs/phase4b8-1-browser-real/result.json',
                 'runs/phase4b8-1-audit/preservation-after.json','runs/phase4b8-1-audit/conditioning-inspection.json']:
        file=REPO/name
        if file.exists():data['validation_evidence'][name]=digest(file)
    write(output/'summary.json',data);write(benchmark,data)
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Canonical guided gestures</title><style>body{font:16px system-ui;margin:30px;background:#f3f2ed;color:#243c33}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}article{background:white;padding:15px;border-radius:10px}img{width:100%;height:480px;object-fit:contain}</style><h1>Canonical-based guided gesture study</h1><p>Target: anatomical right forearm raised (viewer left), elbow bent, hand at chest height. Arms-down results fail this target even if segmentation is clean. Only explicit human selections enter downstream analysis.</p><p><a href="summary.json">Exact metadata, hashes and separate development screening</a></p><main>'+''.join(cards)+'</main>')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--benchmark',type=Path,required=True);p.add_argument('--control',type=Path,action='append',default=[])
    a=p.parse_args();report(a.run,a.output,a.benchmark,a.control)
