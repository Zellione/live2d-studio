"""Canonical workflow contracts on synthetic fixtures; no GPU/human approval claims."""
import json
import os
from unittest import mock
import unittest
from PIL import Image
import test_pose_reviewer as fixtures
from live2d_studio.pose_review import Store,initialize,digest
from live2d_studio.canonical_pose import frontal_guide,PROMPT,WORKER
from live2d_studio.canonical_reference import load_frozen,initialize_helpers


class CanonicalTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.ReviewerTests();self.fixture.setUp();self.folder=self.fixture.folder
        self.store=initialize(self.folder/'canonical',self.fixture.source,{'test':fixtures.PRESET},'Synthetic fixture',workflow='canonical')
    def tearDown(self):self.fixture.tearDown()
    def batch(self):
        b,fd=self.store.reserve('canonical','test');self.assertTrue(self.store.execute(b,fd,fixtures.synthetic_worker))
        return self.store.state()['batches'][-1]
    def approve(self):
        b=self.batch();self.store.decide('accept','canonical',b['candidates'][1]['id'],reviewer='Synthetic test reviewer')
        return self.store.state()
    def test_canonical_only_and_pinned_prompt(self):
        s=self.store.state();self.assertEqual(set(s['poses']),{'canonical'});self.assertEqual(s['poses']['canonical']['prompt'],PROMPT)
        b=self.batch();plan=json.loads(self.store.safe(b['directory']+'/plan.json').read_text())
        self.assertEqual(b['worker'],WORKER);self.assertTrue(all(t['prompt']==PROMPT for t in plan['tasks']))
        with self.store.transaction() as state:state['poses']['canonical']['prompt']='changed'
        with self.assertRaises(ValueError):self.store.reserve('canonical','test')
    def test_two_batches_have_five_fresh_seeds_each(self):
        self.batch();self.batch();s=self.store.state()
        self.assertEqual(len(set(s['used_seeds'])),10);self.assertNotIn('canonical_reference',s)
    def test_approval_freezes_original_and_synthetic_separately(self):
        before=digest(self.fixture.source);s=self.approve();store,state,data=load_frozen(self.store.root)
        self.assertEqual(digest(self.fixture.source),before);self.assertEqual(data['original']['sha256'],before)
        self.assertNotEqual(data['canonical']['sha256'],before);self.assertFalse(data['anatomically_verified'])
        self.assertEqual(data['approval'],s['poses']['canonical']['approval'])
        self.assertEqual(Store(self.store.root).state()['canonical_reference'],s['canonical_reference'])
        with self.assertRaises(ValueError):self.store.reserve('canonical','test')
        self.assertEqual(self.store.finish()['canonical_reference'],s['canonical_reference'])
    def test_rejection_and_unsuccessful_never_freeze(self):
        b=self.batch();self.store.decide('reject','canonical',b['candidates'][0]['id'],'wrong pose')
        self.store.decide('unsupported','canonical',reason='Frontal identity not preserved')
        self.assertNotIn('canonical_reference',self.store.state())
        with self.assertRaises(ValueError):load_frozen(self.store.root)
    def test_freeze_recovers_after_approval_and_state_write_interruptions(self):
        b=self.batch()
        with mock.patch('live2d_studio.canonical_reference.ensure_freeze',side_effect=RuntimeError('interrupt')):
            with self.assertRaises(RuntimeError):self.store.decide('accept','canonical',b['candidates'][0]['id'])
        raw=json.loads((self.store.root/'review.json').read_text());self.assertEqual(raw['poses']['canonical']['status'],'approved')
        s=self.store.state();pinned=s['canonical_reference']
        with self.store.transaction() as current:del current['canonical_reference']
        self.assertEqual(self.store.state()['canonical_reference'],pinned)
    def test_freeze_payload_tamper_blocks_handoff(self):
        s=self.approve();folder=self.store.safe(s['canonical_reference']['manifest']).parent
        p=folder/'canonical.png';p.chmod(0o644);p.write_bytes(b'changed')
        with self.assertRaises(ValueError):load_frozen(self.store.root)
        with self.assertRaises(ValueError):initialize_helpers(self.store.root,self.folder/'helpers',{'test':fixtures.PRESET})
    def test_explicit_helper_handoff_uses_canonical_primary_original_identity(self):
        with self.assertRaises(ValueError):initialize_helpers(self.store.root,self.folder/'unapproved',{'test':fixtures.PRESET})
        self.assertFalse((self.folder/'unapproved').exists());self.approve()
        helper=initialize_helpers(self.store.root,self.folder/'helpers',{'test':fixtures.PRESET});s=helper.state()
        self.assertEqual(s['batches'],[]);self.assertEqual(s['used_seeds'],[])
        self.assertEqual(s['identity_reference']['sha256'],digest(self.fixture.source))
        self.assertNotEqual(s['source']['sha256'],s['identity_reference']['sha256'])
        b,fd=helper.reserve('wave','test')
        try:
            plan=json.loads(helper.safe(b['directory']+'/plan.json').read_text())
            self.assertEqual(plan['inputs']['source.png'],s['source']['sha256'])
            self.assertEqual(plan['inputs']['identity.png'],s['identity_reference']['sha256'])
            self.assertTrue(all('Picture 3 is the original character' in t['prompt'] for t in plan['tasks']))
        finally:os.close(fd)
    def test_frontal_guides_are_symmetric_and_source_unchanged(self):
        im=Image.open(self.fixture.source);before=digest(self.fixture.source);_,points=frontal_guide(im)
        for a,b in [('rs','ls'),('re','le'),('rw','lw'),('right_eye','left_eye')]:
            self.assertAlmostEqual(points[a][0]+points[b][0],im.width);self.assertEqual(points[a][1],points[b][1])
        self.assertEqual(before,digest(self.fixture.source))
    def test_legacy_auxiliary_producer_pins_remain_valid(self):
        s=self.fixture.store.state();self.fixture.store.verify_pins(s)
        self.assertNotIn('workflow',s);self.assertNotIn(WORKER,s['producer_pins'])

if __name__=='__main__':unittest.main()
