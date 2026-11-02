import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from live2d_studio import packaging as pkg, deployment as dep
from live2d_studio.completeness import analyze, measure_visible_limb


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory(prefix='phase4a-test-', dir=pkg.REPO / 'runs')
        self.cache = tempfile.TemporaryDirectory(prefix='phase4a-test-', dir=pkg.REPO / '.cache')
        self.addCleanup(self.work.cleanup); self.addCleanup(self.cache.cleanup)
        self.base = Path(self.work.name); self.root = Path(self.cache.name)
        (self.root / pkg.EXT).mkdir(parents=True)
        (self.root / 'data/default-user/assets/live2d').mkdir(parents=True)
        (self.root / pkg.EXT / 'live2d.js').write_text('original extension\n')
        (self.root / pkg.CORE).parent.mkdir()
        (self.root / pkg.CORE).write_text('test core')
        pkg.write_json(self.root / dep.MARKER, dict(root=str(self.root), source='/nonexistent/production', purpose='phase4a-disposable'))
        self.source = self.base / 'source'; self.source.mkdir()
        self.spec = copy.deepcopy(pkg.policy())
        model = dict(Version=3, FileReferences=dict(Moc='test.moc3', Textures=['test.png'], Expressions=[], Motions={}))
        (self.source / 'test.moc3').write_bytes(b'MOC3' + bytes(64))
        (self.source / 'test.png').write_bytes(b'\x89PNG\r\n\x1a\nsynthetic')
        for expr in self.spec['expressions']:
            pkg.write_json(self.source / (expr + '.json'), {})
            model['FileReferences']['Expressions'].append(dict(Name=expr, File=expr + '.json'))
        for motion in ['Idle', 'Nod']:
            pkg.write_json(self.source / (motion + '.json'), {})
            model['FileReferences']['Motions'][motion] = [dict(File=motion + '.json')]
        self.spec['model'] = 'test.model3.json'
        pkg.write_json(self.source / self.spec['model'], model)
        preset = dict(classify_mapping={k:dict(expression='neutral', motion='none') for k in self.spec['classifier_labels']})
        preset.update({k:dict(expression='neutral', motion='none') for k in ['animation_default','animation_starter','animation_click']})
        pkg.write_json(self.source / 'sillytavern_settings.json', preset)
        self.spec['runtime_sha256'] = pkg.files(self.source)
        self.spec['accepted_source_sha256'] = pkg.files(self.source)
        self.spec['compatibility']['target_sha256'] = {pkg.EXT + '/live2d.js':pkg.digest(self.root / pkg.EXT / 'live2d.js')}
        for obj, name, value in [(pkg,'policy',lambda:self.spec),(dep,'policy',lambda:self.spec),
                                 (pkg,'core_probe',lambda *a:dict(status='pass')),(dep,'core_probe',lambda *a:dict(status='pass')),
                                 (dep,'adapter_bytes',lambda *a:b'patched extension\n')]:
            p = patch.object(obj,name,value); p.start(); self.addCleanup(p.stop)
        self.package = self.base / 'package'
        pkg.package(self.source, self.package, self.root / pkg.CORE)
        self.record = self.base / 'record'
        self.dest = self.root / 'data/default-user/assets/live2d/girl2'

    def install(self, **kw):
        return dep.deploy(self.package,self.root,self.record,execute=True,**kw)

    def test_reproducible_and_exclusive(self):
        second = self.base / 'second'
        pkg.package(self.source,second,self.root / pkg.CORE)
        self.assertEqual(pkg.files(self.package),pkg.files(second))
        with self.assertRaises(FileExistsError): pkg.package(self.source,second,self.root / pkg.CORE)

    def test_missing_modified_extra_and_symlink_bundle(self):
        for attack in ['missing','modified','extra','symlink']:
            with self.subTest(attack=attack):
                target=self.base / attack; shutil.copytree(self.package,target)
                if attack=='missing': (target/'test.moc3').unlink()
                if attack=='modified': (target/'test.moc3').write_bytes(b'wrong')
                if attack=='extra': (target/'unlisted').write_text('extra')
                if attack=='symlink': (target/'link').symlink_to(self.package/'test.moc3')
                with self.assertRaises((ValueError,OSError)): pkg.verify(target)

    def test_dry_runs_do_not_write(self):
        before=dep.snapshot(self.root)
        dep.deploy(self.package,self.root,self.record,execute=False,adapter=True)
        self.assertEqual(before,dep.snapshot(self.root)); self.assertFalse(self.record.exists())
        self.install(adapter=True)
        before=dep.snapshot(self.root); records=dep.snapshot(self.record)
        dep.rollback(self.record)
        self.assertEqual(before,dep.snapshot(self.root)); self.assertEqual(records,dep.snapshot(self.record))

    def test_conflict_replace_and_exact_rollback(self):
        self.dest.mkdir(); (self.dest/'user-asset').write_text('keep me'); (self.dest/'empty').mkdir()
        (self.dest/'user-asset').chmod(0o640)
        before=dep.snapshot(self.dest); extension=dep.snapshot(self.root/pkg.EXT)
        with self.assertRaises(FileExistsError):self.install()
        self.install(replace=True,adapter=True)
        self.assertNotEqual(before,dep.snapshot(self.dest))
        dep.rollback(self.record,True)
        self.assertEqual(before,dep.snapshot(self.dest))
        # Parent directory timestamps are not part of file restoration claims.
        self.assertEqual(extension['entries']['live2d.js'],dep.snapshot(self.root/pkg.EXT)['entries']['live2d.js'])
        self.assertFalse((self.root/pkg.EXT/'rp-talk.mjs').exists())
        self.assertEqual(dep.rollback(self.record,True)['status'],'rolled-back')

    def test_interrupt_each_install_boundary(self):
        for boundary in ['removed','installed']:
            for index in range(3):
                with self.subTest(boundary=boundary,index=index):
                    self.record=self.base/f'record-{boundary}-{index}'
                    def crash(stage,i):
                        if (stage,i)==(boundary,index):raise KeyboardInterrupt()
                    with self.assertRaises(KeyboardInterrupt):self.install(adapter=True,_checkpoint=crash)
                    dep.rollback(self.record,True)
                    self.assertFalse(self.dest.exists())
                    self.assertEqual((self.root/pkg.EXT/'live2d.js').read_text(),'original extension\n')

    def test_interrupted_restore_is_resumable(self):
        self.dest.mkdir(); (self.dest/'old').write_text('original')
        before=dep.snapshot(self.dest);self.install(replace=True,adapter=True)
        def crash(stage,i):
            if stage=='removed' and i==0:raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):dep.rollback(self.record,True,_checkpoint=crash)
        dep.rollback(self.record,True)
        self.assertEqual(before,dep.snapshot(self.dest))

    def test_disk_failure_and_pending_transaction(self):
        def fail(stage,i): raise OSError('simulated disk failure')
        with self.assertRaises(OSError):self.install(_checkpoint=fail)
        with self.assertRaises(ValueError):dep.deploy(self.package,self.root,self.base/'other',execute=True)
        dep.rollback(self.record,True);self.assertFalse(self.dest.exists())

    def test_process_death_after_rename_recovers(self):
        pid=os.fork()
        if pid==0:
            def die(stage,i):os._exit(73)
            self.install(adapter=True,_checkpoint=die)
            os._exit(0)
        _,status=os.waitpid(pid,0)
        self.assertEqual(os.waitstatus_to_exitcode(status),73)
        dep.rollback(self.record,True)
        self.assertFalse(self.dest.exists())
        self.assertEqual((self.root/pkg.EXT/'live2d.js').read_text(),'original extension\n')

    def test_modified_installed_files_and_backups_fail_closed(self):
        self.dest.mkdir(); (self.dest/'old').write_text('keep')
        self.install(replace=True)
        (self.dest/'user-edit').write_text('new work')
        with self.assertRaises(ValueError):dep.rollback(self.record,True)
        self.assertTrue((self.dest/'user-edit').exists())
        (self.dest/'user-edit').unlink()
        (self.record/'backup-0/old').write_text('corrupt')
        with self.assertRaises(ValueError):dep.rollback(self.record,True)

    def test_production_symlink_permissions_and_versions(self):
        with self.assertRaises(ValueError):dep.record_path(pkg.REPO/'runs/../../outside')
        with self.assertRaises(ValueError):pkg.package(self.source,pkg.REPO/'runs/../../outside',self.root/pkg.CORE)
        with self.assertRaises(ValueError):dep.deploy(self.package,Path('/home/zelli/tools/ai/SillyTavern'),self.record,execute=True)
        assets=self.dest.parent
        assets.chmod(0o555)
        with self.assertRaises(PermissionError):self.install()
        assets.chmod(0o755)
        (self.root/pkg.EXT/'live2d.js').write_text('unknown revision')
        with self.assertRaises(ValueError):self.install()
        link=self.base/'target';link.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError):dep.isolated(link)
        self.assertFalse(self.record.exists())

    def test_tampered_journal_path_is_rejected(self):
        self.install()
        journal=json.loads((self.record/'deployment.json').read_text())
        journal['operations'][0]['path']='../../production'
        pkg.write_json(self.record/'deployment.json',journal)
        with self.assertRaises(ValueError):dep.rollback(self.record,True)


class CompletenessTests(unittest.TestCase):
    def test_independent_mask_detects_loss_duplicate_and_clothing_absorption(self):
        import numpy as np
        rgba=np.full((4,4,4),255,dtype=np.uint8)
        mask=np.zeros((4,4),dtype=bool); mask[:,0]=True
        good=('arm',rgba,mask)
        self.assertEqual(measure_visible_limb(rgba,mask,[good],{'arm'})['structural_preservation'],'pass')
        for layers in [[],[('shirt',rgba,mask)],[good,good]]:
            self.assertEqual(measure_visible_limb(rgba,mask,layers,{'arm'})['structural_preservation'],'blocked')
        with self.assertRaises(ValueError):measure_visible_limb(rgba,mask[:2],[],{'arm'})

    def test_girl2_passes_portrait_without_hands(self):
        r=analyze(pkg.policy()['completeness'])
        self.assertEqual(r['portrait_completeness'],'pass')
        self.assertFalse(r['general_limb_preservation_validated'])
        self.assertFalse(r['anatomical_completeness'])

    def test_visible_limb_cannot_be_dropped_or_hidden_in_clothing(self):
        for failure in ['lost','merged','omitted','uncertain','unreviewed']:
            d=copy.deepcopy(pkg.policy()['completeness']);r=d['limbs'][0]
            if failure=='lost':r['preservation']['lost_pixels']=1
            if failure=='merged':r['source_surface']='skin'
            if failure=='omitted':d['limbs'].pop()
            if failure=='uncertain':r['source_visibility']='uncertain'
            if failure=='unreviewed':r['neutral_and_motion_review']=None
            self.assertEqual(analyze(d)['portrait_completeness'],'blocked',failure)

    def test_framing_does_not_prove_anatomy(self):
        for framing in ['portrait/bust','half-body','full-body']:
            d=copy.deepcopy(pkg.policy()['completeness']);d['framing']=framing
            self.assertFalse(analyze(d)['anatomical_completeness'])
