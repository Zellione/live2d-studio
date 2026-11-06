"""Local, persistent human selection and bounded offline pose jobs."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import threading
import time
import uuid
from PIL import Image
from .pose_guides import POSES,guide,prompt

REPO=Path(__file__).resolve().parents[2]
REASONS=['wrong pose','identity drift','extra limbs','bad hands','clothing drift','style drift','missing torso information']


def digest(file):
    with Path(file).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def write(file,value):
    temp=file.with_name(file.name+'.'+uuid.uuid4().hex+'.tmp')
    with temp.open('x') as f:
        json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    temp.replace(file)
    fd=os.open(file.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)


def fresh_seeds(used,count=5,random=secrets.randbits):
    if count!=5:raise ValueError('Exactly five candidates per batch')
    selected=[];known=set(used)
    for _ in range(10000):
        seed=random(52)  # Exact integer representation in browser JSON as well as Python.
        if seed not in known:
            selected.append(seed);known.add(seed)
        if len(selected)==count:return selected
    raise ValueError('Could not allocate unique seeds')


def validate_preset(cfg):
    required={'long_edge','steps','cfg','shift','denoise','guidance','latent','mask','sampler','scheduler','cfg_norm'}
    if not isinstance(cfg,dict) or not required<=cfg.keys() or cfg.keys()-required-{'negative_prompt','prompt_suffix'}:
        raise ValueError('Missing or unknown preset fields')
    if type(cfg['steps']) is not int or type(cfg['cfg_norm']) is not bool:
        raise ValueError('Steps must be an integer and cfg_norm must be boolean')
    if (cfg['long_edge'] not in (1024,1536) or not 1<=cfg['steps']<=60 or not 0<cfg['cfg']<=10
        or not 0<cfg['shift']<=10 or not 0<cfg['denoise']<=1 or cfg['guidance'] not in ('skeleton','silhouette')
        or cfg['latent'] not in ('source','empty') or cfg['mask'] not in ('none','legacy-body')
        or cfg['sampler'] not in ('euler','dpmpp_2m') or cfg['scheduler'] not in ('simple','beta')):
        raise ValueError('Unsupported or unbounded preset')
    for key in ('negative_prompt','prompt_suffix'):
        if not isinstance(cfg.get(key,''),str) or len(cfg.get(key,''))>2000:raise ValueError('Invalid prompt text')


def initialize(root,source,presets,rights,*,workflow='auxiliary'):
    if workflow not in ('auxiliary','canonical','canonical-helpers'):raise ValueError('Unknown review workflow')
    root=root.resolve();source=source.resolve()
    if not root.is_relative_to(REPO/'runs') or root.is_relative_to(REPO/'runs/references'):
        raise ValueError('New reviewer runs must be under project runs/, outside references')
    if not presets or not rights.strip():raise ValueError('Presets and source rights required')
    for cfg in presets.values():validate_preset(cfg)
    root.mkdir(parents=True,exist_ok=False);(root/'assets').mkdir();(root/'batches').mkdir()
    shutil.copyfile(source,root/'assets/source.png')
    im=Image.open(source).convert('RGBA');supported={}
    poses=POSES;make_guide=guide
    if workflow!='auxiliary':
        from .canonical_pose import frontal_guide,TITLE
        make_guide=frontal_guide
        if workflow=='canonical':poses={'canonical':(TITLE,'')}
    for pose,(title,_) in poses.items():
        try:
            files={}
            for kind in ('skeleton','silhouette'):
                g,points=make_guide(im,pose,kind);name=f'assets/{pose}-{kind}.png';g.save(root/name)
                files[kind]={'path':name,'sha256':digest(root/name),'joints':points}
            supported[pose]={'title':title,'status':'pending','selected':None,'guides':files}
        except ValueError as exc:supported[pose]={'title':title,'status':'unsupported','selected':None,'reason':str(exc),'guides':{}}
    pins={name:digest(REPO/name) for name in ['backends/inpainting/pose_worker.py','backends/inpainting/qwen.py',
        'backends/inpainting/models.lock.json','backends/inpainting/qwen-env/uv.lock','src/live2d_studio/pose_guides.py']}
    state={'schema_version':1,'run_id':uuid.uuid4().hex,'source':{'path':'assets/source.png','sha256':digest(source),'rights':rights},
           'presets':presets,'presets_sha256':fingerprint(presets),'producer_pins':pins,'poses':supported,
           'batches':[],'used_seeds':[],'events':[],'exports':[]}
    if workflow!='auxiliary':
        from .canonical_pose import WORKER,PROMPT
        state.update(workflow=workflow,worker=WORKER)
        for name in (WORKER,'src/live2d_studio/canonical_pose.py'):pins[name]=digest(REPO/name)
        if workflow=='canonical':
            state['poses']['canonical']['prompt']=PROMPT
            state['definition_sha256']=fingerprint({'workflow':workflow,'prompt':PROMPT})
    write(root/'review.json',state)
    return Store(root)


class Store:
    def __init__(self,root):
        self.root=Path(root).resolve()
        if not (self.root/'review.json').is_file():raise ValueError('Not a review run')

    def safe(self,relative):
        p=Path(relative)
        if p.is_absolute() or '..' in p.parts or '\\' in str(p):raise ValueError('Invalid artifact path')
        out=(self.root/p).resolve()
        if not out.is_relative_to(self.root):raise ValueError('Artifact escapes run')
        return out

    @contextmanager
    def transaction(self):
        with (self.root/'.state.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            state=json.loads((self.root/'review.json').read_text())
            yield state
            write(self.root/'review.json',state)

    def verify_pins(self,state,producer=True):
        if state.get('workflow') in ('canonical','canonical-helpers'):
            from .canonical_pose import WORKER
            if state.get('worker')!=WORKER:raise ValueError('Canonical worker binding changed')
        if state.get('workflow')=='canonical-helpers' and (not state.get('identity_reference') or not state.get('canonical_origin')):
            raise ValueError('Canonical helper initialization is incomplete')
        if fingerprint(state['presets'])!=state['presets_sha256']:raise ValueError('Preset changed')
        if digest(self.safe(state['source']['path']))!=state['source']['sha256']:raise ValueError('Source changed')
        if state.get('workflow')=='canonical':
            if fingerprint({'workflow':'canonical','prompt':state['poses']['canonical']['prompt']})!=state['definition_sha256']:
                raise ValueError('Canonical prompt changed')
        if state.get('identity_reference'):
            item=state['identity_reference']
            if digest(self.safe(item['path']))!=item['sha256']:raise ValueError('Original identity reference changed')
        if state.get('canonical_origin'):
            item=state['canonical_origin']
            if digest(self.safe('canonical-provenance.json'))!=item['local_provenance_sha256'] or state['source']['sha256']!=item['canonical_sha256']:
                raise ValueError('Canonical provenance changed')
            if state['identity_reference']['sha256']!=item['original_sha256']:
                raise ValueError('Canonical identity/geometry roles changed')
        if producer:
            for name,h in state['producer_pins'].items():
                if digest(REPO/name)!=h:raise ValueError('Producer changed; use a fresh review run: '+name)

    def gpu_lock(self):
        fd=os.open(self.root/'.gpu.lock',os.O_CREAT|os.O_RDWR,0o600)
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd);raise ValueError('A GPU batch is already running for this review')
        return fd

    def add_preset(self,name,config):
        if not name or len(name)>80 or not all(c.isalnum() or c in '-_' for c in name):
            raise ValueError('Use a short alphanumeric preset name')
        validate_preset(config)
        with self.transaction() as s:
            self.verify_pins(s)
            if name in s['presets']:raise ValueError('Existing presets cannot be overwritten')
            previous=s['presets_sha256'];s['presets'][name]=config
            s['presets_sha256']=fingerprint(s['presets'])
            s['events'].append({'action':'add-preset','name':name,'config':config,'config_sha256':fingerprint(config),
                                'previous_catalog_sha256':previous,'catalog_sha256':s['presets_sha256'],'time':time.time()})

    def reconcile(self,state,have_gpu_lock=False):
        for batch in state['batches']:
            for c in batch['candidates']:
                result=self.safe(c['directory'])/'result.json'
                if c['status']=='pending' and result.is_file():
                    row=json.loads(result.read_text());im=result.parent/'image.png'
                    planfile=self.safe(batch['directory'])/'plan.json'
                    if digest(planfile)!=batch['plan_sha256']:raise ValueError('Batch plan changed')
                    plan=json.loads(planfile.read_text())
                    task=next(t for t in plan['tasks'] if t['id']==c['task_id'])
                    if (row['id']!=c['task_id'] or row['seed']!=c['seed'] or row['config']!=batch['config']
                        or row['prompt']!=task['prompt'] or row.get('negative_prompt','')!=task['negative_prompt']
                        or row['guide_sha256']!=plan['inputs']['guide.png'] or digest(im)!=row['image_sha256']):
                        raise ValueError('Worker result does not match reserved candidate')
                    if plan.get('identity') and row.get('identity_sha256')!=plan['inputs'][plan['identity']]:
                        raise ValueError('Worker identity reference mismatch')
                    c.update(status='ready',image=c['directory']+'/image.png',sha256=row['image_sha256'],result=row)
            if batch['status']=='running':
                report=self.safe(batch.get('execution_directory',batch['directory']))/'report.json'
                if report.exists():
                    status=json.loads(report.read_text())['status']
                    if status in ('failed','completed'):batch['status']=status
                if batch['status']=='running':
                    if have_gpu_lock:
                        batch['status']='interrupted';continue
                    try:fd=self.gpu_lock()
                    except ValueError:pass
                    else:
                        os.close(fd);batch['status']='interrupted'

    def state(self):
        with self.transaction() as s:
            self.reconcile(s)
            if s.get('workflow')=='canonical':
                from .canonical_reference import ensure_freeze
                ensure_freeze(self,s)
            return s

    @staticmethod
    def candidate(state,cid):
        for b in state['batches']:
            for c in b['candidates']:
                if c['id']==cid:return b,c
        raise ValueError('Unknown candidate')

    def verify_candidate(self,state,cid):
        b,c=self.candidate(state,cid)
        if c['status']!='ready' or digest(self.safe(c['image']))!=c['sha256']:raise ValueError('Candidate missing or hash mismatch')
        return b,c

    def decide(self,action,pose,cid=None,reason='',reviewer='local user'):
        if action not in ('accept','reject','unsupported'):raise ValueError('Invalid decision')
        if len(reason)>2000 or not reviewer.strip() or len(reviewer)>120:raise ValueError('Invalid review text')
        with self.transaction() as s:
            self.reconcile(s);self.verify_pins(s,producer=False)
            if pose not in s['poses']:raise ValueError('Unknown pose')
            p=s['poses'][pose]
            if p['status'] in ('approved','unsupported'):raise ValueError('Approved/unsupported pose is frozen; start another review for changes')
            if any(b['pose']==pose and b['status']=='running' for b in s['batches']):raise ValueError('Wait for this pose batch to finish')
            event={'action':action,'pose':pose,'candidate':cid,'reason':reason,'reviewer':reviewer,'reviewer_kind':'human','time':time.time()}
            if action=='unsupported':p.update(status='unsupported',reason=reason)
            else:
                b,c=self.verify_candidate(s,cid)
                if b['pose']!=pose:raise ValueError('Candidate belongs to another pose')
                event['image_sha256']=c['sha256'];c['decision']=event
                if action=='accept':p.update(status='approved',selected=cid,approval=event)
                else:p['status']='rejected'
            s['events'].append(event)
        if action=='accept' and s.get('workflow')=='canonical':self.state()
        return event

    def reserve(self,pose,preset):
        fd=self.gpu_lock()
        try:
            with self.transaction() as s:
                self.reconcile(s,have_gpu_lock=True);self.verify_pins(s)
                p=s['poses'].get(pose)
                if not p or p['status'] in ('approved','unsupported'):raise ValueError('Pose is approved or unsupported')
                if preset not in s['presets']:raise ValueError('Unknown preset')
                cfg=s['presets'][preset];seeds=fresh_seeds(s['used_seeds'])
                bid='b-'+uuid.uuid4().hex;directory='batches/'+bid;folder=self.safe(directory);folder.mkdir()
                shutil.copyfile(self.safe(s['source']['path']),folder/'source.png')
                g=p['guides'][cfg['guidance']]
                if digest(self.safe(g['path']))!=g['sha256']:raise ValueError('Guide changed')
                shutil.copyfile(self.safe(g['path']),folder/'guide.png')
                if digest(folder/'source.png')!=s['source']['sha256'] or digest(folder/'guide.png')!=g['sha256']:
                    raise ValueError('Input changed while reserving batch')
                text=p.get('prompt') or prompt(pose,cfg['guidance'])
                if s.get('workflow')=='canonical-helpers':
                    text=('Picture 1 is the reviewed synthetic front-facing base and primary geometry. '
                          'Picture 2 is the target pose guide. Picture 3 is the original character for identity, '
                          'facial features, clothing and style only; do not restore its angled or crossed-arm pose. '+text)
                text+=(' '+cfg['prompt_suffix'] if cfg.get('prompt_suffix') else '')
                tasks=[{'id':'c'+str(i+1),'seed':seed,'config':cfg,'prompt':text,
                        'negative_prompt':cfg.get('negative_prompt',''),'guide':'guide.png'} for i,seed in enumerate(seeds)]
                plan={'source':'source.png','inputs':{n:digest(folder/n) for n in ('source.png','guide.png')},
                      'model_lock_sha256':s['producer_pins']['backends/inpainting/models.lock.json'],'tasks':tasks}
                if s.get('identity_reference'):
                    identity=s['identity_reference'];shutil.copyfile(self.safe(identity['path']),folder/'identity.png')
                    if digest(folder/'identity.png')!=identity['sha256']:raise ValueError('Identity changed during copy')
                    plan['identity']='identity.png';plan['inputs']['identity.png']=identity['sha256']
                    plan['canonical_origin']=s['canonical_origin']
                write(folder/'plan.json',plan)
                batch={'id':bid,'pose':pose,'preset':preset,'config':cfg,'config_sha256':fingerprint(cfg),
                       'directory':directory,'plan_sha256':digest(folder/'plan.json'),'status':'running','created':time.time(),
                       'candidates':[{'id':bid+'-'+t['id'],'task_id':t['id'],'seed':t['seed'],'directory':directory+'/'+t['id'],'status':'pending'} for t in tasks]}
                if s.get('worker'):batch['worker']=s['worker']
                s['used_seeds']+=seeds;s['batches'].append(batch)
            return batch,fd
        except BaseException:os.close(fd);raise

    def execute(self,batch,fd,runner=subprocess.run):
        try:
            folder=self.safe(batch.get('execution_directory',batch['directory']))
            with (folder/'worker.log').open('a') as log:
                worker=batch.get('worker','backends/inpainting/pose_worker.py')
                if worker not in ('backends/inpainting/pose_worker.py','backends/inpainting/pose_reference_worker.py'):raise ValueError('Unknown worker')
                proc=runner([str(REPO/'backends/inpainting/qwen-env/.venv/bin/python'),str(REPO/worker),
                             '--plan',str(folder/'plan.json')],cwd=REPO,stdout=log,stderr=subprocess.STDOUT,pass_fds=(fd,),timeout=3600)
            with self.transaction() as s:
                self.reconcile(s)
                row=next(b for b in s['batches'] if b['id']==batch['id'])
                row['status']='completed' if proc.returncode==0 and all(c['status']=='ready' for c in row['candidates']) else 'failed'
                row['returncode']=proc.returncode
                return row['status']=='completed'
        except Exception as exc:
            with self.transaction() as s:
                row=next(b for b in s['batches'] if b['id']==batch['id']);row.update(status='failed',error=str(exc))
            return False
        finally:os.close(fd)

    def generate(self,pose,preset):
        batch,fd=self.reserve(pose,preset)
        threading.Thread(target=self.execute,args=(batch,fd),daemon=True).start()
        return batch['id']

    def resume(self,bid,background=True):
        fd=self.gpu_lock()
        try:
            with self.transaction() as s:
                self.reconcile(s,have_gpu_lock=True);self.verify_pins(s)
                b=next((b for b in s['batches'] if b['id']==bid),None)
                if not b or b['status'] not in ('failed','interrupted'):raise ValueError('Batch is not resumable')
                if s['poses'][b['pose']]['status'] in ('approved','unsupported'):raise ValueError('Pose is frozen')
                original=self.safe(b['directory'])/'plan.json'
                if digest(original)!=b['plan_sha256']:raise ValueError('Batch plan changed')
                plan=json.loads(original.read_text());missing=[]
                for c in b['candidates']:
                    if c['status']=='ready':self.verify_candidate(s,c['id'])
                    else:missing.append(c['task_id'])
                if not missing:raise ValueError('No unfinished candidates')
                directory=b['directory']+'/retry-'+uuid.uuid4().hex;folder=self.safe(directory);folder.mkdir()
                for name in plan['inputs']:
                    source=(original.parent/name).resolve()
                    if not source.is_relative_to(original.parent):raise ValueError('Invalid plan input')
                    shutil.copyfile(source,folder/name)
                plan['tasks']=[t for t in plan['tasks'] if t['id'] in missing];write(folder/'plan.json',plan)
                for c in b['candidates']:
                    if c['task_id'] in missing:c['directory']=directory+'/'+c['task_id']
                b.update(status='running',execution_directory=directory)
            if background:threading.Thread(target=self.execute,args=(b,fd),daemon=True).start();return bid
            return b,fd
        except BaseException:os.close(fd);raise

    def finish(self,reviewer='local user'):
        with self.transaction() as s:
            self.reconcile(s);self.verify_pins(s,producer=False)
            if s.get('workflow')=='canonical':
                from .canonical_reference import ensure_freeze
                ensure_freeze(self,s)
            if any(b['status']=='running' for b in s['batches']):raise ValueError('Wait for the active batch')
            selected={};export_id=uuid.uuid4().hex;folder=self.root/'selections'/export_id;folder.mkdir(parents=True)
            for pose,p in s['poses'].items():
                if p['status']!='approved':continue
                b,c=self.verify_candidate(s,p['selected']);shutil.copyfile(self.safe(c['image']),folder/(pose+'.png'))
                selected[pose]={'candidate':c['id'],'image':pose+'.png','sha256':c['sha256'],'seed':c['seed'],
                    'config':b['config'],'prompt':c['result']['prompt'],'negative_prompt':c['result'].get('negative_prompt',''),
                    'guide_sha256':c['result']['guide_sha256'],'plan_sha256':b['plan_sha256'],
                    'approval':p['approval'],'anatomically_verified':False,'useful_articulation_evidence':None,
                    'independently_verified_source_pixels':False}
            manifest={'schema_version':1,'run_id':s['run_id'],'source':s['source'],'producer_pins':s['producer_pins'],
                      'selected':selected,'poses':{k:v['status'] for k,v in s['poses'].items()},'reviewer':reviewer,
                      'scope':'Human-selected synthetic auxiliary poses, not anatomy or rig approval','created':time.time()}
            if s.get('canonical_reference'):manifest['canonical_reference']=s['canonical_reference']
            write(folder/'selection.json',manifest);s['exports'].append({'id':export_id,'sha256':digest(folder/'selection.json')})
            return manifest

    def asset(self,key):
        s=self.state()
        if key=='source':record=s['source']
        elif key=='identity' and s.get('identity_reference'):record=s['identity_reference']
        elif key.startswith('guide/'):
            _,pose,kind=key.split('/');record=s['poses'][pose]['guides'][kind]
        else:
            _,c=self.verify_candidate(s,key);record={'path':c['image'],'sha256':c['sha256']}
        file=self.safe(record['path'])
        if digest(file)!=record['sha256']:raise ValueError('Asset hash mismatch')
        return file
