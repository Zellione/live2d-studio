"""Build a local evidence gallery and small benchmark from immutable run records."""
import argparse
import html
import json
from pathlib import Path
import shutil
from live2d_studio.pose_review import Store,digest,write


def build(calibrations,review,screening,output,benchmark,assessment=None):
    notes=json.loads(screening.read_text());store=Store(review);state=store.state()
    store.verify_pins(state,producer=False)
    output.mkdir(parents=True,exist_ok=False);shutil.copyfile(store.safe(state['source']['path']),output/'source.png')
    cards=[];cases=[]
    for run in calibrations:
        report=json.loads((run/'report.json').read_text());plan=json.loads((run/'plan.json').read_text())
        for task in report['tasks']:
            file=run/task['id']/'image.png'
            if digest(file)!=task['image_sha256']:raise ValueError('Calibration image changed')
            name=task['id']+'.png';shutil.copyfile(file,output/name)
            note=notes.get(task['id'],{'assessment':'Not screened','reviewer_kind':'development-agent'})
            row=dict(task,development_screening=note,plan_sha256=digest(run/'plan.json'))
            cases.append(row)
            cards.append(f'<article><h2>{html.escape(task["id"])}</h2><img src="{name}"><p>{html.escape(note["assessment"])}</p><details><summary>Settings and evidence</summary><pre>{html.escape(json.dumps(row,indent=2))}</pre></details></article>')
    candidates=[]
    for batch in state['batches']:
        for c in batch['candidates']:
            if c['status']!='ready':continue
            store.verify_candidate(state,c['id']);name=c['id']+'.png';shutil.copyfile(store.safe(c['image']),output/name)
            decision=c.get('decision')
            public_decision={k:decision[k] for k in ('action','image_sha256','reviewer_kind','time','reason') if k in decision} if decision else None
            candidates.append({'pose':batch['pose'],'candidate':c['id'],'seed':c['seed'],'sha256':c['sha256'],
                               'config':batch['config'],'decision':public_decision,'seconds':c['result']['seconds']})
            label=c.get('decision',{}).get('action','awaiting human review')
            cards.append(f'<article><h2>{html.escape(batch["pose"])} · {c["seed"]}</h2><img src="{name}"><p>{html.escape(label)}</p></article>')
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Guided pose evidence</title><style>body{font:16px system-ui;background:#f3f2ed;color:#243c33;margin:30px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px}article{background:white;padding:16px;border-radius:10px}img{width:100%;height:440px;object-fit:contain}pre{white-space:pre-wrap;font-size:11px}</style><h1>Guided Qwen pose evidence</h1><p>Calibration assessments are development review, not user approval. Exposed generated regions remain uncertain.</p><main><article><h2>Immutable source</h2><img src="source.png"></article>'+''.join(cards)+'</main>')
    data={'schema_version':1,'phase':'4B.7b','baseline_commit':'c56a59d','source_reference':'codel-combined-v1',
          'default_changes':False,'downloads':False,'production_access':False,'arm_rig_built':False,
          'source':state['source'],'producer_pins':state['producer_pins'],
          'model_lock':json.loads(Path('backends/inpainting/models.lock.json').read_text()),
          'calibration':cases,'candidates':candidates,'poses':{k:v['status'] for k,v in state['poses'].items()},
          'human_approved_count':sum(p['status']=='approved' for p in state['poses'].values()),
          'anatomical_truth':False,'arm_rigging_solved':False,
          'feasibility':('human-selected images await separate anatomical evaluation' if any(p['status']=='approved' for p in state['poses'].values())
                         else 'pending human selection and selected-only anatomical evaluation'),
          'artifacts':{'review_run':str(review),'gallery':str(output),'screening':str(screening)}}
    if assessment:
        evaluated=json.loads(assessment.read_text());semantic_file=assessment.parent/'semantics.json'
        semantics=json.loads(semantic_file.read_text());approval=evaluated['human_visual_approval']
        if digest(semantic_file)!=evaluated['semantic_report_sha256'] or semantics['source_sha256']!=state['source']['sha256']:
            raise ValueError('Assessment evidence mismatch')
        b,c=store.verify_candidate(state,approval['candidate'])
        if state['poses'][b['pose']]['selected']!=c['id'] or approval['image_sha256']!=c['sha256']:
            raise ValueError('Assessment does not belong to the selected candidate')
        if semantics['selected'][b['pose']]['image_sha256']!=c['sha256']:
            raise ValueError('Semantic assessment belongs to another image')
        saved=next(e for e in state['exports'] if e['sha256']==approval['selection_sha256'])
        if digest(store.safe('selections/'+saved['id']+'/selection.json'))!=saved['sha256'] or semantics['selection_sha256']!=saved['sha256']:
            raise ValueError('Selected-set evidence changed')
        data['feasibility']=evaluated['conclusion']
        data['selected_evaluation']={'assessment':evaluated,'semantics':semantics,
                                    'assessment_sha256':digest(assessment),'semantics_sha256':digest(semantic_file)}
        data['artifacts']['selected_assessment']=str(assessment.parent)
    write(output/'summary.json',data);write(benchmark,data)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--calibration',type=Path,action='append',required=True)
    p.add_argument('--review',type=Path,required=True);p.add_argument('--screening',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--benchmark',type=Path,required=True)
    p.add_argument('--assessment',type=Path)
    a=p.parse_args();build(a.calibration,a.review,a.screening,a.output,a.benchmark,a.assessment)
