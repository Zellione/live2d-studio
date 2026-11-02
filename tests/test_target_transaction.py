"""Linux transaction regressions with the pinned accepted local runtime."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from live2d_studio import target_recovery as tx, target_transaction as installer
from live2d_studio.packaging import REPO, EXT, policy

PACKAGE=REPO/'runs/phase4a-acceptance-v4/girl2'
SOURCE=Path('/home/zelli/tools/ai/SillyTavern')


@unittest.skipUnless(PACKAGE.exists() and SOURCE.exists(),'Requires accepted local package and pinned public runtime')
class TargetTransactionTests(unittest.TestCase):
    def setUp(self):
        base=Path(os.environ.get('PHASE4A2_TEST_BASE',str(tx.TEST_BASES[1])))
        if base not in tx.TEST_BASES: raise ValueError('Invalid test base')
        base.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=base,prefix='test-'); self.addCleanup(self.temp.cleanup)
        self.run=Path(self.temp.name); self.root=self.run/'instance'; self.root.mkdir()
        for rel in set(policy()['compatibility']['target_sha256']) | {EXT+'/live2d.js'}:
            out=self.root/rel; out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(SOURCE/rel,out)
        (self.root/tx.ASSETS).mkdir(parents=True)
        (self.root/tx.MARKER).write_text(json.dumps(dict(root=str(self.root),purpose='phase4a2-disposable')))
        self.record=self.run/'transactions/one'
        self.original=tx.snapshot(self.root/EXT/'live2d.js')
        self.dest=self.root/tx.ASSETS/'girl2-phase3-portrait-v1'

    def install(self,**kw): return installer.deploy(PACKAGE,self.root,self.record,execute=True,**kw)

    def restored(self):
        self.assertFalse(self.dest.exists())
        self.assertFalse((self.root/EXT/'rp-talk.mjs').exists())
        self.assertEqual(tx.snapshot(self.root/EXT/'live2d.js'),self.original)

    def test_normal_metadata_and_standalone(self):
        f=self.root/EXT/'live2d.js'; f.chmod(0o640); os.setxattr(f,'user.phase4a2',b'preserve'); self.original=tx.snapshot(f)
        self.install(adapter=True)
        p=subprocess.run(['/usr/bin/python3','-I',str(self.record/'recover.py'),'--execute'],cwd='/tmp',capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr); self.restored()

    def test_dry_run_and_model_only(self):
        before=tx.snapshot(self.root)
        installer.deploy(PACKAGE,self.root,self.record)
        self.assertEqual(before,tx.snapshot(self.root)); self.assertFalse(self.record.exists())
        self.install(); tx.recover(self.record); tx.recover(self.record,True); self.restored()
        tx.recover(self.record,True)

    def test_conflicts_permissions_space_versions_and_production(self):
        self.dest.mkdir()
        with self.assertRaises(FileExistsError): self.install()
        self.dest.rmdir(); self.dest.parent.chmod(0o555)
        with self.assertRaises(PermissionError): self.install()
        self.dest.parent.chmod(0o755)
        with patch.object(installer.shutil,'disk_usage',return_value=shutil._ntuple_diskusage(1,1,0)):
            with self.assertRaises(OSError):self.install()
        with self.assertRaises(ValueError):installer.deploy(PACKAGE,SOURCE,self.record,execute=True)
        (self.root/EXT/'live2d.js').write_text('changed')
        with self.assertRaises(ValueError):self.install()
        self.assertFalse(self.record.exists())

    def test_symlink_hardlink_and_partial_package(self):
        link=self.root/EXT/'unsafe'; link.symlink_to('/tmp')
        with self.assertRaises(ValueError):self.install()
        link.unlink(); os.link(self.root/EXT/'live2d.js',link)
        with self.assertRaises(ValueError):self.install()
        link.unlink()
        bad=self.run/'bad'; shutil.copytree(PACKAGE,bad); (bad/'neutral.exp3.json').unlink(missing_ok=True)
        (bad/'package-manifest.json').unlink()
        with self.assertRaises(FileNotFoundError):installer.deploy(bad,self.root,self.record,execute=True)

    def test_kill_each_publication_and_recovery_boundary(self):
        for action in ['install','rollback']:
            for boundary in range(3):
                with self.subTest(action=action,boundary=boundary):
                    self.record=self.run/f'transactions/{action}-{boundary}'
                    if action=='rollback':self.install(adapter=True)
                    pid=os.fork()
                    if pid==0:
                        def kill(stage,index):
                            if index==boundary:os.kill(os.getpid(),signal.SIGKILL)
                        if action=='install':self.install(adapter=True,checkpoint=kill)
                        else:tx.recover(self.record,True,checkpoint=kill)
                        os._exit(1)
                    _,status=os.waitpid(pid,0);self.assertEqual(os.waitstatus_to_exitcode(status),-9)
                    tx.recover(self.record,True);self.restored()

    def test_missing_corrupt_backup_and_modified_install(self):
        self.install(adapter=True)
        backup=self.record/'backup/2'; data=backup.read_bytes(); backup.unlink()
        with self.assertRaises(ValueError):tx.recover(self.record,True)
        backup.write_bytes(b'corrupt')
        with self.assertRaises(ValueError):tx.recover(self.record,True)
        # Restore metadata from the immutable plan for this test's repair only.
        backup.write_bytes(data)
        op=json.loads((self.record/'plan.json').read_text())['operations'][2]
        os.utime(backup,ns=(op['original_atime_ns'],op['before']['.']['mtime_ns']))
        extra=self.dest/'user-work';extra.write_text('never overwrite')
        with self.assertRaises(ValueError):tx.recover(self.record,True)
        self.assertEqual(extra.read_text(),'never overwrite')

    def test_concurrent_transactions_and_lock(self):
        with tx.lock(self.root):
            with self.assertRaises(BlockingIOError):self.install()
        self.install()
        with self.assertRaises(ValueError):installer.deploy(PACKAGE,self.root,self.run/'transactions/two',execute=True)
        tx.recover(self.record,True)

    def test_journal_and_helper_corruption(self):
        self.install()
        (self.record/'recover.py').write_text('changed')
        with self.assertRaises(ValueError):tx.recover(self.record,True)
        self.assertTrue(self.dest.exists())

    def test_copy_enospc_and_recovery_before_publication(self):
        original=tx.copy_verified
        def fail(source,dest):
            if dest.name=='0':raise OSError(28,'injected ENOSPC')
            return original(source,dest)
        with patch.object(tx,'copy_verified',fail):
            with self.assertRaises(OSError):self.install(adapter=True)
        tx.recover(self.record,True);self.restored()

    def test_atomic_no_replace_and_mount_mismatch(self):
        a=self.run/'a'; b=self.run/'b';a.write_text('new');b.write_text('old')
        with self.assertRaises(FileExistsError):tx.rename(a,b)
        self.assertEqual(b.read_text(),'old')
        with patch.object(tx,'mount_id',side_effect=['1','2']):
            with self.assertRaises(ValueError):tx.rename(a,b)

    def test_missing_installed_file_refused(self):
        self.install(adapter=True); (self.root/EXT/'rp-talk.mjs').unlink()
        with self.assertRaises(ValueError):tx.recover(self.record,True)

    def test_partial_restore_copy_and_runtime_changes(self):
        self.install(adapter=True)
        partial=self.record/'restore/2';partial.write_text('interrupted copy')
        tx.recover(self.record,True); self.restored()
        self.record=self.run/'transactions/two';self.install(adapter=True)
        (self.root/EXT/'constants.js').write_text('new upstream runtime')
        with self.assertRaises(ValueError):tx.recover(self.record,True)

    def test_corrupt_journal_and_private_directory(self):
        self.record.parent.mkdir(mode=0o755)
        with self.assertRaises(PermissionError):self.install()
        self.record.parent.chmod(0o700);self.install()
        (self.record/'journal.json').write_text('{}')
        with self.assertRaises((KeyError,ValueError)):tx.recover(self.record,True)

    def test_kill_journal_renames(self):
        # Kill after atomic journal replacement both before and after publication.
        for wanted in [1,2,3,4,5,6,7,8]:
            self.record=self.run/f'transactions/journal-{wanted}'
            pid=os.fork()
            if pid==0:
                original=tx.rename; count=0
                def kill_after(source,dest,replace=False):
                    nonlocal count
                    original(source,dest,replace)
                    if dest.name=='journal.json':
                        count+=1
                        if count==wanted:os.kill(os.getpid(),signal.SIGKILL)
                with patch.object(tx,'rename',kill_after):self.install(adapter=True)
                os._exit(1)
            _,status=os.waitpid(pid,0);self.assertEqual(os.waitstatus_to_exitcode(status),-9)
            tx.recover(self.record,True);self.restored()

    def test_kill_each_rollback_journal_rename(self):
        for wanted in range(1,9):
            self.record=self.run/f'transactions/rollback-journal-{wanted}'
            self.install(adapter=True)
            self.assertEqual((self.record/'journal.json').stat().st_mode & 0o777,0o600)
            pid=os.fork()
            if pid==0:
                original=tx.rename; count=0
                def kill_after(source,dest,replace=False):
                    nonlocal count
                    original(source,dest,replace)
                    if dest.name=='journal.json':
                        count+=1
                        if count==wanted:os.kill(os.getpid(),signal.SIGKILL)
                with patch.object(tx,'rename',kill_after):tx.recover(self.record,True)
                os._exit(1)
            _,status=os.waitpid(pid,0);self.assertEqual(os.waitstatus_to_exitcode(status),-9)
            tx.recover(self.record,True);self.restored()
