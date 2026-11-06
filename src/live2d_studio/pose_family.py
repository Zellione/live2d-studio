"""Hash-bound copies of human-selected synthetic poses; no inferred approvals."""
import json
import os
from pathlib import Path
import shutil
from .pose_review import Store,REPO,digest,write
from .canonical_reference import load_frozen


def freeze(run,output,*,export_if_missing=False):
    output=Path(output).resolve()
    if not output.is_relative_to(REPO/'runs') or output.is_relative_to(REPO/'runs/references'):raise ValueError('Fresh ignored family directory required')
    if output.exists():raise ValueError('Family output already exists')
    store=Store(run);state=store.state();store.verify_pins(state,producer=False)
    if state.get('workflow')!='canonical-helpers':raise ValueError('Canonical helper run required')
    approved={k:p for k,p in state['poses'].items() if p['status']=='approved'}
    if not approved:raise ValueError('No human-approved helpers')
    for pose,p in approved.items():
        _,c=store.verify_candidate(state,p['selected']);approval=p.get('approval',{})
        if (approval.get('reviewer_kind')!='human' or approval.get('action')!='accept' or
            approval.get('image_sha256')!=c['sha256'] or approval.get('candidate')!=c['id'] or
            approval.get('pose')!=pose or c.get('decision')!=approval or approval not in state['events']):
            raise ValueError('Explicit hash-bound human approval required')
    parent,canonical_state,canonical=load_frozen(Path(state['canonical_origin']['review_run']))
    if (canonical['canonical']['sha256']!=state['source']['sha256'] or
        canonical['original']['sha256']!=state['identity_reference']['sha256'] or
        canonical_state['canonical_reference']!=state['canonical_origin']['manifest']):
        raise ValueError('Canonical ancestry mismatch')
    if canonical['approval'].get('reviewer_kind')!='human':raise ValueError('Canonical human approval required')
    record=None;manifest=None
    for candidate in reversed(state['exports']):
        file=store.safe('selections/'+candidate['id']+'/selection.json')
        if digest(file)!=candidate['sha256']:raise ValueError('Selection manifest changed')
        m=json.loads(file.read_text())
        if set(m['selected'])==set(approved) and all(m['selected'][k]['approval']==p['approval'] for k,p in approved.items()):
            record=candidate;manifest=m;break
    if record is None:
        if not export_if_missing:raise ValueError('Export the current human selections first')
        store.finish('Automated selected-only export; approvals remain the saved human decisions')
        return freeze(run,output,export_if_missing=False)
    for pose,row in manifest['selected'].items():
        if digest(store.safe('selections/'+record['id']+'/'+row['image']))!=row['sha256'] or row['sha256']!=approved[pose]['approval']['image_sha256']:
            raise ValueError('Selected payload changed')
    output.mkdir(parents=True,exist_ok=False);(output/'guides').mkdir()
    entries={}
    def copy(source,name):
        shutil.copyfile(source,output/name);return {'path':name,'sha256':digest(output/name)}
    entries['canonical']=dict(copy(store.safe(state['source']['path']),'canonical.png'),approval=canonical['approval'],kind='human-reviewed synthetic neutral',anatomically_verified=False)
    original=copy(store.safe(state['identity_reference']['path']),'original.png')
    for pose,row in manifest['selected'].items():
        b,c=store.verify_candidate(state,row['candidate'])
        guide_file=store.safe(b['directory']+'/guide.png')
        if digest(guide_file)!=row['guide_sha256']:raise ValueError('Approved pose guide changed')
        entries[pose]=dict(copy(store.safe('selections/'+record['id']+'/'+row['image']),pose+'.png'),approval=row['approval'],kind='human-reviewed synthetic helper',
            candidate=row['candidate'],seed=row['seed'],config=row['config'],prompt=row['prompt'],negative_prompt=row['negative_prompt'],
            guide=copy(guide_file,'guides/'+pose+'.png'),anatomically_verified=False)
    provenance=copy(store.safe('selections/'+record['id']+'/selection.json'),'selection.json')
    canon=copy(parent.safe(canonical_state['canonical_reference']['manifest']),'canonical-provenance.json')
    family={'schema_version':1,'review_run':str(store.root.relative_to(REPO)),'selection_id':record['id'],'selection':provenance,
        'canonical_provenance':canon,'original':original,'rights':canonical['original']['rights'],'images':entries,
        'pose_statuses':{k:p['status'] for k,p in state['poses'].items()},'producer_pins':state['producer_pins'],
        'scope':'Frozen human-selected synthetic evidence; no verified anatomy or rig approval'}
    write(output/'family.json',family)
    for p in output.rglob('*'):
        if p.is_file():p.chmod(0o444)
    return family


def load(folder):
    folder=Path(folder).resolve();data=json.loads((folder/'family.json').read_text())
    for record in [data['selection'],data['canonical_provenance'],data['original'],*data['images'].values(),*[v['guide'] for v in data['images'].values() if 'guide' in v]]:
        file=(folder/record['path']).resolve()
        if not file.is_relative_to(folder) or digest(file)!=record['sha256']:raise ValueError('Frozen family payload changed')
    selection=json.loads((folder/data['selection']['path']).read_text());canonical=json.loads((folder/data['canonical_provenance']['path']).read_text())
    if data['original']['sha256']!=canonical['original']['sha256'] or selection['source']['sha256']!=canonical['canonical']['sha256']:
        raise ValueError('Original/canonical identity changed')
    for pose,row in data['images'].items():
        approval=row['approval']
        if approval.get('reviewer_kind')!='human' or approval.get('action')!='accept' or approval.get('image_sha256')!=row['sha256']:raise ValueError('Human approval mismatch')
        expected=canonical['approval'] if pose=='canonical' else selection['selected'][pose]['approval']
        if approval!=expected:raise ValueError('Saved approval mismatch')
    if set(data['images'])!={'canonical',*selection['selected']}:raise ValueError('Selected-only family mismatch')
    return data
