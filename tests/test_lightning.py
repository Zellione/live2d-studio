"""Lightning metadata/orchestration tests with synthetic images and no GPU."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock
from PIL import Image
import test_canonical_pose as fixtures
import test_pose_reviewer as base
from live2d_studio import lightning
from live2d_studio.pose_review import Store,REPO,digest,write,validate_preset
from live2d_studio.canonical_reference import initialize_helpers


def synthetic(argv,**kwargs):
    file=Path(argv[-1]);plan=json.loads(file.read_text());lock=json.loads((REPO/lightning.LOCK).read_text())
    for task in plan['tasks']:
        folder=file.parent/task['id'];folder.mkdir();Image.new('RGB',(32,48),(task['seed']%255,100,150)).save(folder/'image.png')
        name,strength=lightning.validate(task['config']);adapter={'id':name,'strength':strength,'patch_count':0}
        if name!='none':adapter.update(sha256=lock['files'][name]['sha256'],revision=lock['revision'],patch_count=720)
        row=dict(id=task['id'],seed=task['seed'],config=task['config'],prompt=task['prompt'],negative_prompt=task.get('negative_prompt',''),
                 guide_sha256=plan['inputs']['guide.png'],identity_sha256=plan['inputs']['identity.png'],
                 image_sha256=digest(folder/'image.png'),output_size=[32,48],seconds=0,
                 reference_latent_count=3,reference_latent_shapes=[[1,16,1,8,4]]*3,
                 lora=adapter,lightning_lock_sha256=plan['lightning_lock_sha256'],synthetic_test_fixture=True)
        write(folder/'result.json',row)
    write(file.parent/'report.json',{'status':'completed'});return SimpleNamespace(returncode=0)


class LightningTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.CanonicalTests();self.fixture.setUp();self.fixture.approve()
        self.presets={'experimental':dict(base.PRESET,steps=8,cfg=1,lora='lightning-8',lora_strength=1),
                      'reference':dict(base.PRESET,steps=40,cfg=4,lora='none',lora_strength=0)}
        self.original=(self.fixture.store.root/'review.json').read_bytes()
        self.store=initialize_helpers(self.fixture.store.root,self.fixture.folder/'lightning',self.presets,gesture_profile='chest-forearm-v1',lightning=True)
    def tearDown(self):self.fixture.tearDown()
    def batch(self):
        b,fd=self.store.reserve('right-lift','experimental');self.assertTrue(self.store.execute(b,fd,synthetic));return self.store.state()['batches'][-1]
    def test_opt_in_pins_and_old_reference_unchanged(self):
        self.assertEqual((self.fixture.store.root/'review.json').read_bytes(),self.original)
        s=self.store.state();self.store.verify_pins(s)
        self.assertEqual(s['worker'],lightning.WORKER);self.assertIn(lightning.LOCK,s['producer_pins'])
        with self.assertRaises(ValueError):initialize_helpers(self.fixture.store.root,self.fixture.folder/'implicit',self.presets)
    def test_optional_config_is_bounded_and_legacy_valid(self):
        validate_preset(base.PRESET)
        for cfg in self.presets.values():validate_preset(cfg)
        for patch in [dict(lora='unreviewed'),dict(lora_strength=0),dict(lora_strength=float('nan'))]:
            with self.assertRaises(ValueError):validate_preset(dict(self.presets['experimental'],**patch))
    def test_legacy_preset_rejection_is_atomic(self):
        original=(self.fixture.store.root/'review.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'fresh Lightning'):
            self.fixture.store.add_preset('new-adapter',self.presets['experimental'])
        self.assertEqual((self.fixture.store.root/'review.json').read_bytes(),original)
    def test_five_fresh_seeds_replay_approval_and_export(self):
        self.batch();b=self.batch();s=self.store.state();self.assertEqual(len(set(s['used_seeds'])),10)
        plan=json.loads(self.store.safe(b['directory']+'/plan.json').read_text())
        self.assertEqual(plan['lightning_lock_sha256'],digest(REPO/lightning.LOCK));self.assertEqual(len(plan['inputs']),3)
        for task,c in zip(plan['tasks'],b['candidates']):self.assertEqual(task['config'],c['result']['config']);self.assertEqual(task['seed'],c['seed'])
        self.store.decide('accept','right-lift',b['candidates'][0]['id'],reviewer='Synthetic fixture')
        reopened=Store(self.store.root);self.assertEqual(reopened.state()['poses']['right-lift']['selected'],b['candidates'][0]['id'])
        with self.assertRaises(ValueError):reopened.reserve('right-lift','reference')
        export=reopened.finish();self.assertEqual(set(export['selected']),{'right-lift'})
        self.assertEqual(export['selected']['right-lift']['config']['lora'],'lightning-8')
    def test_missing_or_incompatible_patch_evidence_is_rejected(self):
        def bad(argv,**kw):
            result=synthetic(argv,**kw);file=Path(argv[-1]).parent/'c1/result.json'
            row=json.loads(file.read_text());row['lora']['patch_count']=0;write(file,row);return result
        b,fd=self.store.reserve('right-lift','experimental');self.assertFalse(self.store.execute(b,fd,bad))
        with self.assertRaisesRegex(ValueError,'patch evidence'):self.store.state()
    def test_interrupted_batches_keep_adapter_pin_and_inputs(self):
        b,fd=self.store.reserve('right-lift','experimental');os.close(fd);s=self.store.state();self.assertEqual(s['batches'][0]['status'],'interrupted')
        with mock.patch.object(self.store,'execute',side_effect=lambda b,fd:Store.execute(self.store,b,fd,synthetic)):
            self.assertTrue(self.store.resume(b['id'],background=False))
        after=self.store.state();self.assertEqual(after['used_seeds'],s['used_seeds'])
        plan=json.loads(self.store.safe(after['batches'][0]['execution_directory']+'/plan.json').read_text())
        self.assertEqual(plan['lightning_lock_sha256'],digest(REPO/lightning.LOCK));self.assertEqual(len(plan['inputs']),3)
    def test_missing_or_changed_weights_fail_without_loading(self):
        root=self.fixture.folder/'weights';(root/'backends/inpainting').mkdir(parents=True)
        payload=root/'model.safetensors';payload.write_bytes(b'synthetic fixture')
        lock={'repo':'fixture','revision':'pinned','license':'fixture','files':{'lightning-8':{'path':payload.name,'size':payload.stat().st_size,'sha256':digest(payload)}}}
        write(root/lightning.LOCK,lock)
        with mock.patch.object(lightning,'REPO',root):
            file,record=lightning.weight(self.presets['experimental']);self.assertEqual(file,payload)
            payload.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):lightning.weight(self.presets['experimental'])
            payload.unlink()
            with self.assertRaises(ValueError):lightning.weight(self.presets['experimental'])
    def test_comfy_filename_shadowing_is_rejected(self):
        file=self.fixture.folder/'pinned.safetensors'
        folders=mock.Mock();folders.get_full_path.return_value=str(file)
        lightning.register_weight(folders,file)
        folders.add_model_folder_path.assert_called_once_with('loras',str(file.parent))
        for wrong in (None,str(self.fixture.folder/'other/pinned.safetensors')):
            folders.get_full_path.return_value=wrong
            with self.assertRaisesRegex(ValueError,'pinned file'):lightning.register_weight(folders,file)
    def test_comparison_changes_only_requested_sampling_and_adapter(self):
        import sys
        sys.path.insert(0,str(REPO/'scripts'))
        from phase4b8_2_compare import prepare
        b=self.batch();plans=prepare(self.store.root,b['id'],self.fixture.folder/'comparison')
        rows=[json.loads(p.read_text()) for p in plans];first=rows[0]['tasks'][0]
        for row in rows:
            task=row['tasks'][0];self.assertEqual(task['seed'],first['seed']);self.assertEqual(task['prompt'],first['prompt'])
            self.assertEqual(row['inputs'],rows[0]['inputs'])
            cfg={k:v for k,v in task['config'].items() if k not in ('steps','cfg','lora','lora_strength')}
            self.assertEqual(cfg,{k:v for k,v in first['config'].items() if k not in ('steps','cfg','lora','lora_strength')})

if __name__=='__main__':unittest.main()
