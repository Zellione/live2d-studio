"""Destination-filesystem staging for dedicated disposable instances only."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

from . import target_recovery as tx
from .packaging import REPO, EXT, CORE, verify, policy, core_probe
from .deployment import adapter_bytes, versions


def deploy(package,target,transaction,name='girl2-phase3-portrait-v1',adapter=False,execute=False,checkpoint=None):
    root,record=tx.guard(target,transaction)
    package=Path(package).absolute()
    with tx.lock(root):
        if not re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9-]{0,63}',name): raise ValueError('Invalid name')
        if record.exists(): raise FileExistsError('Transaction already exists')
        if record.parent.exists():
            tx.safe(record.parent)
            if record.parent.stat().st_mode & 0o077 or record.parent.stat().st_uid!=os.getuid():
                raise PermissionError('Transaction parent must be private and owned by caller')
            for sibling in record.parent.iterdir():
                if sibling.is_dir():
                    state=sibling/'journal.json'
                    if not state.exists() or json.loads(state.read_text())['status']!='rolled-back':
                        raise ValueError('Concurrent/pending transaction')
        manifest=verify(package)
        versions(root,manifest['compatibility'])
        core_probe(package,root/CORE,policy())
        dest=root/tx.ASSETS/name
        if any(p.name.casefold()==name.casefold() for p in dest.parent.iterdir()): raise FileExistsError('Model conflict')
        changes=[(dest,package,None)]
        if adapter:
            companion=root/EXT/'rp-talk.mjs'
            if companion.exists() or (root/EXT/'live2d.upstream.js').exists(): raise FileExistsError('Adapter conflict')
            changes += [(companion,REPO/'integrations/sillytavern/rp-talk.mjs',None),
                        (root/EXT/'live2d.js',None,adapter_bytes(root))]
        for p,_,_ in changes: tx.safe(p); tx.writable(p.parent)
        parent=record.parent if record.parent.exists() else record.parent.parent
        tx.writable(parent)
        if any(tx.mount_id(p.parent)!=tx.mount_id(parent) for p,_,_ in changes): raise ValueError('Stage and destination mounts differ')
        needed=sum(p.stat().st_size for p in package.rglob('*') if p.is_file())*3+4*1024*1024
        if shutil.disk_usage(parent).free<needed: raise OSError(28,'Insufficient free space for staging, backups and recovery')
        plan=dict(schema=2,target=str(root),name=name,adapter=adapter,production_enabled=False,
                  package_manifest_sha256=tx.sha(package/'package-manifest.json'),
                  source_device=package.stat().st_dev,target_device=dest.parent.stat().st_dev,
                  target_mount=tx.mount_id(parent),recovery_sha256=tx.sha(Path(tx.__file__)),
                  compatibility=manifest['compatibility']['target_sha256'],
                  settings_policy='untouched',operations=[])
        for i,(p,source,data) in enumerate(changes):
            payload=({rel:meta['sha256'] for rel,meta in tx.snapshot(source).items() if meta['kind']=='file'}
                     if source is not None else {'.':hashlib.sha256(data).hexdigest()})
            plan['operations'].append(dict(path=str(p.relative_to(root)),before=tx.snapshot(p),
                original_atime_ns=p.stat().st_atime_ns if p.exists() else None,
                payload_sha256=payload,stage=f'stage/{i}',backup=f'backup/{i}' if p.exists() else None,
                quarantine=f'quarantine/{i}'))
        if not execute: return plan
        record.parent.mkdir(mode=0o700,exist_ok=True); tx.sync(record.parent.parent)
        record.mkdir(mode=0o700); tx.sync(record.parent)
        for folder in ['stage','backup','restore','quarantine']:
            (record/folder).mkdir(mode=0o700)
        tx.copy_verified(Path(tx.__file__),record/'recover.py')
        tx.atomic(record/'preparation.json',plan,exclusive=True)
        # No served mutation can occur until complete verified staging and durable plan.
        for i,((p,source,data),op) in enumerate(zip(changes,plan['operations'])):
            if op['before'] is not None: tx.copy_verified(p,record/f'backup/{i}')
            stage=record/f'stage/{i}'
            if source is not None: tx.copy_verified(source,stage)
            else:
                stage.write_bytes(data); shutil.copystat(p,stage)
                if (stage.stat().st_uid,stage.stat().st_gid)!=(p.stat().st_uid,p.stat().st_gid): os.chown(stage,p.stat().st_uid,p.stat().st_gid)
                tx.sync(stage)
            op['after']=tx.snapshot(stage)
        verify(record/'stage/0'); core_probe(record/'stage/0',root/CORE,policy())
        tx.sync_tree(record)
        tx.atomic(record/'plan.json',plan,exclusive=True)
        journal=dict(plan_sha256=tx.sha(record/'plan.json'),status='prepared',pending=None,completed=[])
        tx.atomic(record/'journal.json',journal,exclusive=True)
        # Recheck everything after staging before publishing any file.
        versions(root,manifest['compatibility'])
        for op in plan['operations']:
            if tx.snapshot(root/op['path'])!=op['before']: raise ValueError('Target changed during staging')
        for i,op in enumerate(plan['operations']):
            p=root/op['path']
            if tx.snapshot(p)!=op['before']: raise ValueError('Concurrent target modification')
            journal.update(status='installing',pending=i); tx.atomic(record/'journal.json',journal)
            if tx.snapshot(record/f'stage/{i}')!=op['after']: raise ValueError('Staged files changed')
            tx.rename(record/f'stage/{i}',p,replace=op['before'] is not None)
            if checkpoint: checkpoint('install',i)
            journal['completed'].append(i)
            journal['pending']=None; tx.atomic(record/'journal.json',journal)
        journal['status']='installed'; tx.atomic(record/'journal.json',journal)
        return dict(plan,status='installed')
