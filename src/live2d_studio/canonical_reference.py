"""Approval-bound synthetic working-reference snapshots and explicit helper handoff."""
import json
import shutil

def ensure_freeze(store,state):
    """Recoverable write-once snapshot; downstream loading also requires persisted approval."""
    from .pose_review import digest,write
    if state.get('workflow')!='canonical' or state['poses']['canonical']['status']!='approved':return
    pose=state['poses']['canonical'];batch,candidate=store.verify_candidate(state,pose['selected'])
    store.verify_pins(state,producer=False)
    record=state.get('canonical_reference')
    if record:
        file=store.safe(record['manifest'])
        if digest(file)!=record['sha256']:raise ValueError('Canonical manifest changed')
        data=json.loads(file.read_text())
    else:
        directory='canonical/'+candidate['id'];folder=store.safe(directory)
        folder.mkdir(parents=True,exist_ok=True)
        data={'schema_version':1,'reference_name':'canonical-'+state['run_id'],
              'kind':'reviewed-synthetic-canonical-working-base','run_id':state['run_id'],
              'original':{'path':'original.png','sha256':state['source']['sha256'],'rights':state['source']['rights']},
              'canonical':{'path':'canonical.png','sha256':candidate['sha256']},
              'approval':pose['approval'],'candidate':candidate['id'],'seed':candidate['seed'],
              'config':batch['config'],'prompt':candidate['result']['prompt'],
              'negative_prompt':candidate['result'].get('negative_prompt',''),
              'guide_sha256':candidate['result']['guide_sha256'],'plan_sha256':batch['plan_sha256'],
              'producer_pins':state['producer_pins'],'anatomically_verified':False,
              'scope':'Synthetic working geometry only; original remains identity/style authority; no accepted rig replacement'}
        for key,source in [('original',store.safe(state['source']['path'])),('canonical',store.safe(candidate['image']))]:
            target=folder/data[key]['path']
            if not target.exists():
                temp=target.with_suffix('.pending');shutil.copyfile(source,temp);temp.replace(target)
            if digest(target)!=data[key]['sha256']:raise ValueError('Canonical payload changed')
            target.chmod(0o444)
        file=folder/'manifest.json'
        if file.exists():
            if json.loads(file.read_text())!=data:raise ValueError('Existing freeze conflicts with approval')
        else:write(file,data)
        file.chmod(0o444)
        record={'manifest':str(file.relative_to(store.root)),'sha256':digest(file)}
        state['canonical_reference']=record
    if data['approval']!=pose['approval'] or data['canonical']['sha256']!=candidate['sha256']:
        raise ValueError('Canonical freeze does not match approval')
    for key in ('original','canonical'):
        payload=store.safe(str((file.parent/data[key]['path']).relative_to(store.root)))
        if digest(payload)!=data[key]['sha256']:raise ValueError('Canonical payload changed')
    return data


def load_frozen(run):
    from .pose_review import Store
    store=Store(run);state=store.state()
    data=ensure_freeze(store,state)
    if not data or not state.get('canonical_reference'):raise ValueError('No approved canonical base')
    return store,state,data


def initialize_helpers(run,output,presets):
    """Explicit opt-in preparation only. No helper inference or migration occurs."""
    from .pose_review import initialize,digest,write
    store,state,data=load_frozen(run);folder=store.safe(state['canonical_reference']['manifest']).parent
    target=initialize(output,folder/'canonical.png',presets,data['original']['rights'],workflow='canonical-helpers')
    with target.transaction() as current:
        shutil.copyfile(folder/'original.png',target.root/'assets/identity.png')
        current['identity_reference']={'path':'assets/identity.png','sha256':data['original']['sha256']}
        current['canonical_origin']={'review_run':str(store.root),'manifest':state['canonical_reference'],
                                     'canonical_sha256':data['canonical']['sha256'],'original_sha256':data['original']['sha256']}
        write(target.root/'canonical-provenance.json',data)
        current['canonical_origin']['local_provenance_sha256']=digest(target.root/'canonical-provenance.json')
    return target
