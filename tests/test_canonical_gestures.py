"""Three-reference gesture orchestration on small synthetic fixtures, no GPU."""
import json
import os
from pathlib import Path
from unittest import mock
import unittest
import test_canonical_pose as canonical
import test_pose_reviewer as fixtures
from live2d_studio.pose_review import Store,digest,write
from live2d_studio.canonical_reference import initialize_helpers
from live2d_studio.gesture_profile import PROFILE,guide


def three_reference_worker(argv,**kwargs):
    from PIL import Image
    from types import SimpleNamespace
    planfile=Path(argv[-1]);plan=json.loads(planfile.read_text());rows=[]
    for task in plan['tasks']:
        folder=planfile.parent/task['id'];folder.mkdir()
        Image.new('RGB',(32,48),(task['seed']%255,100,150)).save(folder/'image.png')
        row={'id':task['id'],'seed':task['seed'],'config':task['config'],'prompt':task['prompt'],
             'guide_sha256':plan['inputs']['guide.png'],'image_sha256':digest(folder/'image.png'),
             'output_size':[32,48],'seconds':0.0,'synthetic_test_fixture':True,
             'identity_sha256':plan['inputs']['identity.png'],'reference_latent_count':3,
             'reference_latent_shapes':[[1,16,1,8,4]]*3,
             'reference_roles':['primary geometry','target guide','original identity/style']}
        write(folder/'result.json',row);rows.append(row)
    write(planfile.parent/'report.json',{'status':'completed','tasks':rows})
    return SimpleNamespace(returncode=0)


class CanonicalGestureTests(unittest.TestCase):
    def setUp(self):
        self.fixture=canonical.CanonicalTests();self.fixture.setUp();self.canonical=self.fixture.store
        self.fixture.approve()
        self.original_state=(self.canonical.root/'review.json').read_bytes()
        self.store=initialize_helpers(self.canonical.root,self.fixture.folder/'gestures',{'test':fixtures.PRESET},gesture_profile=PROFILE)
    def tearDown(self):self.fixture.tearDown()
    def batch(self,runner=three_reference_worker):
        b,fd=self.store.reserve('right-lift','test');self.store.execute(b,fd,runner)
        return self.store.state()['batches'][-1]
    def test_exact_input_roles_and_immutable_canonical(self):
        b=self.batch();s=self.store.state();plan=json.loads(self.store.safe(b['directory']+'/plan.json').read_text())
        self.assertEqual(plan['inputs']['source.png'],s['canonical_origin']['canonical_sha256'])
        self.assertEqual(plan['inputs']['identity.png'],s['canonical_origin']['original_sha256'])
        self.assertNotEqual(plan['inputs']['source.png'],plan['inputs']['identity.png'])
        self.assertEqual((self.canonical.root/'review.json').read_bytes(),self.original_state)
        self.assertEqual(self.store.asset('identity').read_bytes(),self.fixture.fixture.source.read_bytes())
        self.assertTrue(all(c['result']['reference_latent_count']==3 for c in b['candidates']))
    def test_missing_third_reference_evidence_is_rejected(self):
        def bad(argv,**kw):
            result=three_reference_worker(argv,**kw);p=Path(argv[-1]).parent/'c1/result.json'
            row=json.loads(p.read_text());row['reference_latent_count']=2;write(p,row);return result
        with self.assertRaisesRegex(ValueError,'Three-reference'):self.batch(bad)
    def test_wrong_identity_or_shapes_cannot_become_ready(self):
        for index,(field,value) in enumerate([('identity_sha256','0'*64),('reference_latent_shapes',[[1,16,1,8,4]]*2),('reference_latent_shapes',None)]):
            with self.subTest(field=field):
                # Independent run per deliberately corrupt completed worker report.
                store=initialize_helpers(self.canonical.root,self.fixture.folder/(field+str(index)),{'test':fixtures.PRESET},gesture_profile=PROFILE)
                b,fd=store.reserve('right-lift','test')
                def bad(argv,**kw):
                    result=three_reference_worker(argv,**kw);p=Path(argv[-1]).parent/'c1/result.json'
                    row=json.loads(p.read_text());row[field]=value;write(p,row);return result
                self.assertFalse(store.execute(b,fd,bad))
                with self.assertRaises(ValueError):store.state()
                raw=json.loads((store.root/'review.json').read_text())
                self.assertEqual(raw['poses']['right-lift']['status'],'pending')
                self.assertNotEqual(raw['batches'][0]['candidates'][0]['status'],'ready')
    def test_fresh_batches_approval_resume_and_selected_only_export(self):
        first=self.batch();second=self.batch();s=self.store.state()
        self.assertEqual(len(set(s['used_seeds'])),10)
        self.store.decide('reject','right-lift',first['candidates'][0]['id'],'wrong pose')
        cid=second['candidates'][1]['id'];self.store.decide('accept','right-lift',cid,reviewer='Synthetic test')
        reopened=Store(self.store.root);state=reopened.state()
        self.assertEqual(state['poses']['right-lift']['approval']['image_sha256'],second['candidates'][1]['sha256'])
        for operation in [lambda:reopened.reserve('right-lift','test'),lambda:reopened.decide('reject','right-lift',cid)]:
            with self.assertRaises(ValueError):operation()
        self.assertEqual(set(reopened.finish()['selected']),{'right-lift'})
        self.assertEqual([b['pose'] for b in state['batches']],['right-lift']*2)
    def test_interruption_retains_all_three_inputs_and_seeds(self):
        b,fd=self.store.reserve('right-lift','test');os.close(fd)
        s=self.store.state();self.assertEqual(s['batches'][0]['status'],'interrupted')
        with mock.patch.object(self.store,'execute',side_effect=lambda batch,fd:Store.execute(self.store,batch,fd,three_reference_worker)):
            self.store.resume(b['id'],background=False)
        resumed=self.store.state()['batches'][0]
        plan=json.loads(self.store.safe(resumed['execution_directory']+'/plan.json').read_text())
        self.assertEqual(len(plan['inputs']),3);self.assertEqual([t['seed'] for t in plan['tasks']],s['used_seeds'])
    def test_gesture_direction_and_definition_are_pinned(self):
        from PIL import Image
        im=Image.open(self.store.asset('source'));_,p=guide(im,'right-lift','silhouette');_,q=guide(im,'left-lift','silhouette')
        self.assertLess(p['rw'][1],p['re'][1]);self.assertGreater(p['lw'][1],p['le'][1])
        self.assertLess(p['rs'][0],p['ls'][0]);self.assertLess(q['lw'][1],q['le'][1])
        self.assertGreater(q['rw'][1],q['re'][1])
        with self.store.transaction() as s:s['poses']['right-lift']['prompt']='both arms down'
        with self.assertRaisesRegex(ValueError,'Gesture definition'):self.store.reserve('right-lift','test')
    def test_control_changes_only_the_named_reference_family(self):
        import sys
        from live2d_studio.pose_review import REPO
        sys.path.insert(0,str(REPO/'scripts'))
        from phase4b8_1_control import prepare
        b=self.batch();parent=json.loads(self.store.safe(b['directory']+'/plan.json').read_text())
        for mode in ('two-references','skeleton'):
            file=prepare(self.store.root,b['id'],self.fixture.folder/mode,mode)
            plan=json.loads(file.read_text());self.assertEqual(len(plan['tasks']),1)
            self.assertEqual(plan['tasks'][0]['seed'],parent['tasks'][0]['seed'])
            self.assertEqual(plan['inputs']['source.png'],parent['inputs']['source.png'])
            if mode=='two-references':
                self.assertNotIn('identity',plan);self.assertEqual(len(plan['inputs']),2)
                self.assertEqual(plan['tasks'][0]['config'],parent['tasks'][0]['config'])
                self.assertNotIn('Picture 3',plan['tasks'][0]['prompt'])
                self.assertEqual(plan['inputs']['guide.png'],parent['inputs']['guide.png'])
            else:
                self.assertEqual(len(plan['inputs']),3)
                self.assertEqual(plan['tasks'][0]['prompt'],parent['tasks'][0]['prompt'])
                self.assertEqual(plan['inputs']['identity.png'],parent['inputs']['identity.png'])
        self.assertEqual(len(self.store.state()['batches']),1)

    def test_original_identity_tamper_blocks_generation(self):
        self.store.asset('identity').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'identity reference'):self.store.reserve('right-lift','test')

if __name__=='__main__':unittest.main()
