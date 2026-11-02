"""Standalone Linux recovery engine. Stdlib only; production execution disabled.

This file is copied into each private transaction. Never broaden TEST_BASES as a
production bypass. The lock excludes cooperative writers, not a hostile owner.
"""
import argparse
import base64
from contextlib import contextmanager
import ctypes
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import uuid

TEST_BASES = (Path('/home/zelli/tools/ai/live2d-studio-phase4a2-tests'),
              Path('/data/projects/live2d-studio/.cache/phase4a2-tests'))
EXT = 'data/default-user/extensions/Extension-Live2d'
ASSETS = 'data/default-user/assets/live2d'
MARKER = '.phase4a2-disposable.json'


def safe(path):
    path = Path(path).absolute()
    if '..' in path.parts:
        raise ValueError('Traversal forbidden')
    for p in (path, *path.parents):
        if p.is_symlink(): raise ValueError('Symlink forbidden')
    if path.exists():
        for p in [path, *path.rglob('*')] if path.is_dir() else [path]:
            s = p.lstat()
            if not (stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode)) or (p.is_file() and s.st_nlink != 1):
                raise ValueError('Nonregular or linked entry forbidden')
    return path


def sha(path):
    # Avoid changing original atime when the calling owner can use O_NOATIME.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME)
    with os.fdopen(fd, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def snapshot(path):
    path = safe(path)
    if not path.exists(): return None
    def entry(p):
        s = p.stat()
        return dict(kind='dir' if p.is_dir() else 'file', sha256=None if p.is_dir() else sha(p),
                    mode=stat.S_IMODE(s.st_mode), uid=s.st_uid, gid=s.st_gid,
                    mtime_ns=s.st_mtime_ns,
                    xattrs={n:base64.b64encode(os.getxattr(p,n)).decode() for n in os.listxattr(p)})
    return {str(p.relative_to(path)):entry(p) for p in ([path,*sorted(path.rglob('*'))] if path.is_dir() else [path])}


def sync(path):
    fd=os.open(path,os.O_RDONLY | os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)


def sync_tree(path):
    safe(path)
    for p in sorted(path.rglob('*'),key=lambda p:len(p.parts),reverse=True): sync(p)
    sync(path); sync(path.parent)


def atomic(path, data, exclusive=False):
    safe(path.parent); safe(path)
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:
        f.write((json.dumps(data,sort_keys=True,indent=2)+'\n').encode()); f.flush(); os.fsync(f.fileno())
    rename(temp,path,replace=not exclusive)


def rename(source,dest,replace=False):
    safe(source); safe(dest)
    if source.parent.stat().st_dev != dest.parent.stat().st_dev: raise ValueError('Cross-device publication forbidden')
    # mount IDs also catch bind mounts sharing st_dev; kernel rejects cross mounts.
    if mount_id(source.parent)!=mount_id(dest.parent): raise ValueError('Cross-mount publication forbidden')
    if replace: os.replace(source,dest)
    else:
        libc=ctypes.CDLL(None,use_errno=True)
        if libc.renameat2(-100,os.fsencode(source),-100,os.fsencode(dest),1):
            e=ctypes.get_errno(); raise OSError(e,os.strerror(e),str(dest))
    sync(source.parent); sync(dest.parent)


def mount_id(path):
    fd=os.open(path,os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        return next(line.split(':',1)[1].strip() for line in Path(f'/proc/self/fdinfo/{fd}').read_text().splitlines() if line.startswith('mnt_id:'))
    finally: os.close(fd)


def writable(path):
    if not path.stat().st_mode & 0o222 or not os.access(path,os.W_OK): raise PermissionError(str(path))


def guard(root,transaction):
    root,transaction=Path(root).absolute(),Path(transaction).absolute()
    if root.name!='instance' or root.parent.parent not in TEST_BASES:
        raise ValueError('Production disabled: dedicated Phase 4A.2 disposable targets only')
    if transaction.parent != root.parent/'transactions' or not transaction.name.replace('-','').isalnum():
        raise ValueError('Transaction must be a private sibling of disposable instance')
    for p in (root,root.parent,transaction):
        # Don't scan entire node_modules; only check ancestors here.
        for a in (p,*p.parents):
            if a.is_symlink(): raise ValueError('Symlink ancestor')
    marker=json.loads((safe(root/MARKER)).read_text())
    if marker != dict(purpose='phase4a2-disposable',root=str(root)):
        raise ValueError('Invalid disposable marker')
    for p in (root/EXT,root/ASSETS): safe(p); writable(p)
    return root,transaction


@contextmanager
def lock(root):
    with (root/MARKER).open('rb') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def copy_verified(source,dest):
    before=snapshot(source)
    if before is None: raise FileNotFoundError(source)
    if dest.exists(): raise FileExistsError(dest)
    if source.is_dir(): shutil.copytree(source,dest,copy_function=shutil.copy2)
    else: shutil.copy2(source,dest)
    # copy2 doesn't preserve ownership. Fail if caller cannot preserve it.
    for rel,meta in before.items():
        p=dest/rel if rel!='.' else dest
        if (p.stat().st_uid,p.stat().st_gid)!=(meta['uid'],meta['gid']): os.chown(p,meta['uid'],meta['gid'])
        os.chmod(p,meta['mode'])
        for n,v in meta['xattrs'].items(): os.setxattr(p,n,base64.b64decode(v))
    if snapshot(dest)!=before or snapshot(source)!=before: raise ValueError('Copy/metadata verification failed')
    if dest.is_dir(): sync_tree(dest)
    else: sync(dest); sync(dest.parent)


def load(transaction):
    transaction=safe(transaction)
    plan=json.loads((transaction/'plan.json').read_text())
    root,transaction=guard(plan['target'],transaction)
    journal=json.loads((transaction/'journal.json').read_text())
    if plan['schema']!=2 or journal['plan_sha256']!=sha(transaction/'plan.json'): raise ValueError('Journal/plan mismatch')
    if sha(transaction/'recover.py')!=plan['recovery_sha256']: raise ValueError('Recovery helper changed')
    expected=[ASSETS+'/'+plan['name']]
    if plan['adapter']: expected += [EXT+'/rp-talk.mjs',EXT+'/live2d.js']
    if not plan['name'].replace('-','').isalnum() or [op['path'] for op in plan['operations']]!=expected:
        raise ValueError('Unexpected operation path')
    for relative,expected_hash in plan['compatibility'].items():
        if '..' in Path(relative).parts or Path(relative).is_absolute(): raise ValueError('Unsafe compatibility path')
        if relative!=EXT+'/live2d.js' and sha(safe(root/relative))!=expected_hash:
            raise ValueError('Runtime changed since deployment')
    if journal['status'] not in {'prepared','installing','installed','restoring','rolled-back'}: raise ValueError('Invalid state')
    return root,plan,journal


def recover(transaction,execute=False,checkpoint=None):
    transaction=Path(transaction).absolute()
    safe(transaction)
    if not (transaction/'journal.json').exists():
        # Preparation never mutates served paths; independently verify that claim.
        plan=json.loads((transaction/'preparation.json').read_text())
        root,_=guard(plan['target'],transaction)
        with lock(root):
            if sha(transaction/'recover.py')!=plan['recovery_sha256']: raise ValueError('Recovery helper changed')
            allowed={ASSETS+'/'+plan['name'],EXT+'/rp-talk.mjs',EXT+'/live2d.js'}
            for op in plan['operations']:
                if op['path'] not in allowed or '..' in Path(op['path']).parts: raise ValueError('Invalid preparation path')
                if snapshot(root/op['path'])!=op['before']: raise ValueError('Target changed during failed preparation')
            if execute:
                atomic(transaction/'journal.json',dict(status='rolled-back',preparation_aborted=True))
            return dict(status='rolled-back' if execute else 'preparing',served_files_unchanged=True)
    early=json.loads((transaction/'journal.json').read_text())
    if early.get('preparation_aborted'):
        plan=json.loads((transaction/'preparation.json').read_text()); guard(plan['target'],transaction)
        return early
    root,plan,journal=load(transaction)
    with lock(root):
        # Whole-transaction preflight: never start restoration with damaged backups.
        for i,op in enumerate(plan['operations']):
            dest=root/op['path']; safe(dest); writable(dest.parent)
            if op['before'] is not None and snapshot(transaction/f'backup/{i}')!=op['before']:
                raise ValueError('Backup missing or corrupt')
            allowed=(op['before'],op['after'])
            if journal['status']=='installed': allowed=(op['after'],)
            if journal['status']=='rolled-back': allowed=(op['before'],)
            if journal['status']=='installing' and i in journal['completed']: allowed=(op['after'],)
            if snapshot(dest) not in allowed: raise ValueError('Installed files changed; recovery refused')
        if not execute: return dict(status=journal['status'],rollback_preflight='pass',production_enabled=False)
        journal['status']='restoring'; atomic(transaction/'journal.json',journal)
        # Reverse order restores original JS before removing its imported controller.
        for i in reversed(range(len(plan['operations']))):
            op=plan['operations'][i]; dest=root/op['path']
            if snapshot(dest)==op['before']: continue
            if snapshot(dest)!=op['after']: raise ValueError('Concurrent installed-file change')
            journal['pending']=i; atomic(transaction/'journal.json',journal)
            if op['before'] is None:
                rename(dest,transaction/f'quarantine/{i}')
            else:
                preserved=transaction/f'quarantine/{i}'
                if preserved.exists() and snapshot(preserved)!=op['after']:
                    rename(preserved,transaction/('quarantine/partial-'+uuid.uuid4().hex))
                if not preserved.exists(): copy_verified(dest,preserved)
                restore=transaction/f'restore/{i}'
                if restore.exists() and snapshot(restore)!=op['before']:
                    # Interrupted private copy, not an installed/user file. Preserve evidence.
                    rename(restore,transaction/('quarantine/partial-'+uuid.uuid4().hex))
                if not restore.exists(): copy_verified(transaction/f'backup/{i}',restore)
                if snapshot(dest)!=op['after']: raise ValueError('Concurrent change')
                os.utime(restore,ns=(op['original_atime_ns'],op['before']['.']['mtime_ns']))
                sync(restore)
                rename(restore,dest,replace=True)
            if checkpoint: checkpoint('rollback',i)
            if snapshot(dest)!=op['before']: raise ValueError('Restoration mismatch')
            journal['pending']=None; atomic(transaction/'journal.json',journal)
        journal['status']='rolled-back'; atomic(transaction/'journal.json',journal)
        return journal


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--execute',action='store_true'); mode.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    print(json.dumps(recover(Path(__file__).absolute().parent,args.execute),indent=2))
