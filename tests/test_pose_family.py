"""Synthetic approval, geometry and inference-gate tests; no GPU required."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock
import numpy as np
from PIL import Image
from live2d_studio.pose_family import freeze,load
from live2d_studio.pose_review import REPO,write,digest
from live2d_studio.arm_evidence import fit_elbow,centerline,assess_image
import test_canonical_gestures as fixtures
sys.path.insert(0,str(REPO/'scripts'))
from phase4b9_assess import infer


class FamilyTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.CanonicalGestureTests();self.fixture.setUp();self.store=self.fixture.store;self.folder=self.fixture.fixture.folder
    def tearDown(self):self.fixture.tearDown()
    def approve(self,pose='right-lift'):
        b,fd=self.store.reserve(pose,'test');self.store.execute(b,fd,fixtures.three_reference_worker)
        c=self.store.state()['batches'][-1]['candidates'][0];self.store.decide('accept',pose,c['id'],reviewer='Synthetic fixture human')
    def test_four_approvals_freeze_without_fifth_and_keep_decisions(self):
        for pose in ('right-lift','left-lift','explain','wave'):self.approve(pose)
        before=self.store.state();family=freeze(self.store.root,self.folder/'family',export_if_missing=True);after=self.store.state()
        self.assertEqual(len(family['images']),5);self.assertEqual(after['poses'],before['poses']);self.assertEqual(after['batches'],before['batches'])
        self.assertEqual(family['pose_statuses']['torso-open'],'pending');self.assertEqual(len(after['exports']),1)
        self.assertEqual(load(self.folder/'family'),family)
        freeze(self.store.root,self.folder/'again');self.assertEqual(len(self.store.state()['exports']),1)
    def test_no_approval_never_infers_or_creates_family(self):
        with self.assertRaisesRegex(ValueError,'No human'):freeze(self.store.root,self.folder/'bad',export_if_missing=True)
        self.assertFalse((self.folder/'bad').exists());self.assertFalse(self.store.state()['exports'])
    def test_development_or_detached_decision_cannot_be_approval(self):
        self.approve()
        for patch in ('reviewer_kind','image_sha256'):
            with self.store.transaction() as s:
                saved=copy.deepcopy(s['poses']['right-lift']['approval']);s['poses']['right-lift']['approval'][patch]='development'
            with self.assertRaisesRegex(ValueError,'human approval'):freeze(self.store.root,self.folder/'bad',export_if_missing=True)
            with self.store.transaction() as s:s['poses']['right-lift']['approval']=saved
    def test_changed_candidate_and_changed_frozen_payload_rejected(self):
        self.approve();family=freeze(self.store.root,self.folder/'family',export_if_missing=True)
        file=self.folder/'family'/family['images']['right-lift']['path'];file.chmod(0o644);file.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'payload changed'):load(self.folder/'family')
        candidate=self.store.state()['poses']['right-lift']['selected'];_,c=self.store.candidate(self.store.state(),candidate)
        self.store.safe(c['image']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):freeze(self.store.root,self.folder/'bad',export_if_missing=True)
    def test_inference_only_selected_inputs_and_serialized(self):
        self.approve();family=self.folder/'family';freeze(self.store.root,family,export_if_missing=True);seen=[]
        def runner(argv,**kwargs):
            seen.append(Path(argv[argv.index('--input')+1]).name)
            with self.assertRaisesRegex(ValueError,'GPU batch'):self.store.gpu_lock()
        infer(family,self.folder/'sam',runner=runner)
        self.assertEqual(seen,['canonical.png','right-lift.png'])
    def test_family_path_escape_rejected_before_parser(self):
        self.approve();family=self.folder/'family';freeze(self.store.root,family,export_if_missing=True)
        p=family/'family.json';p.chmod(0o644);data=json.loads(p.read_text());data['images']['right-lift']['path']='../outside.png';write(p,data)
        with self.assertRaises(ValueError):infer(family,self.folder/'sam',runner=lambda *a,**kw:self.fail('Parser ran'))


class GeometryTests(unittest.TestCase):
    def test_straight_sleeve_does_not_certify_elbow(self):
        path=np.column_stack([np.ones(100)*20,np.arange(100)])
        result=fit_elbow(path);self.assertEqual(result['status'],'unresolved-near-straight')
        self.assertGreater(result['candidate_bbox'][3]-result['candidate_bbox'][1],60)
    def test_bent_contour_hypothesis_and_disconnected_rejection(self):
        path=np.vstack([np.column_stack([np.zeros(40),np.arange(40)]),np.column_stack([np.arange(1,41),np.ones(40)*39])])
        r=fit_elbow(path);self.assertLess(np.linalg.norm(np.array(r['point'])-[0,39]),2)
        self.assertIn('not independently observed',r['warning'])
        mask=np.zeros((80,80),bool);mask[5:30,10:25]=True;mask[50:70,10:25]=True
        with self.assertRaisesRegex(ValueError,'Disconnected'):centerline(mask,[16,12],[16,60])
    def test_wrong_image_sam_fails_before_output(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);im=root/'source.png';Image.new('RGB',(40,60),'white').save(im)
            write(root/'sam.json',{'input_sha256':'wrong'})
            with self.assertRaisesRegex(ValueError,'another image'):assess_image(im,root,root/'out')
            self.assertFalse((root/'out').exists())

if __name__=='__main__':unittest.main()
