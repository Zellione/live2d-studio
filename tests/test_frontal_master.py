"""Frontal authority, matte and independent arm contracts; no GPU/editor required."""
import json
from pathlib import Path
import unittest
from unittest import mock
import numpy as np
from PIL import Image
import test_canonical_gestures as fixtures
from live2d_studio.pose_family import freeze
from live2d_studio.frontal_master import promote, load, matte, create
from live2d_studio.frontal_arms import bind, recipe
from live2d_studio.frontal_family import aside_guide, initialize
from live2d_studio.pose_review import write, digest, REPO


class MasterTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.CanonicalGestureTests();self.fixture.setUp()
        self.store=self.fixture.store;self.root=self.fixture.fixture.folder
        batch,fd=self.store.reserve('right-lift','test')
        self.store.execute(batch,fd,fixtures.three_reference_worker)
        candidate=self.store.state()['batches'][0]['candidates'][0]
        self.store.decide('accept','right-lift',candidate['id'],reviewer='Synthetic human fixture')
        self.family=self.root/'family';freeze(self.store.root,self.family,export_if_missing=True)
        self.canonical=Path(self.store.state()['canonical_origin']['review_run'])
        self.master=self.root/'master';promote(self.canonical,self.family,self.master)
    def tearDown(self):self.fixture.tearDown()
    def test_primary_authority_keeps_synthetic_and_review_separate(self):
        data=load(self.master)
        self.assertNotEqual(data['primary']['sha256'],data['identity_style_only']['sha256'])
        self.assertFalse(data['rig_approved']);self.assertFalse(data['deployment_authorized'])
        self.assertEqual(data['approval']['reviewer_kind'],'human')
    def test_source_swap_or_payload_tamper_rejected(self):
        file=self.master/'master.json';file.chmod(0o644);data=load(self.master)
        data['primary'],data['identity_style_only']=data['identity_style_only'],data['primary'];write(file,data)
        with self.assertRaisesRegex(ValueError,'source roles'):load(self.master)
    def test_does_not_replace_existing_master(self):
        with self.assertRaisesRegex(ValueError,'fresh'):promote(self.canonical,self.family,self.master)
    def test_create_uses_frontal_never_original_identity(self):
        with mock.patch('live2d_studio.creation.create') as downstream:
            create(self.master,self.root/'new',until='readiness')
        self.assertEqual(downstream.call_args.args[0],self.master/'primary.png')
        self.assertEqual(downstream.call_args.kwargs['mouths'],'coordinated')
    def test_matte_copies_retained_rgba_and_does_not_change_master(self):
        before=digest(self.master/'primary.png');out=self.root/'matte';r=matte(self.master,out)
        self.assertTrue(r['retained_rgba_exact']);self.assertEqual(digest(self.master/'primary.png'),before)
        with self.assertRaisesRegex(ValueError,'fresh'):matte(self.master,out)
    def test_explicit_backing_review_is_hash_bound_and_not_runtime_approval(self):
        from live2d_studio.frontal_master import review
        folder=self.root/'backing-review';folder.mkdir()
        source=self.master/'master.json'
        write(folder/'evidence.json',{str(source.relative_to(REPO)):digest(source)})
        with self.assertRaisesRegex(ValueError,'Explicit'):review(folder,'accept','Synthetic reviewer','')
        record=review(folder,'accept','Synthetic reviewer','Reviewed synthetic fixture backing')
        self.assertFalse(record['animation_approved'])
        self.assertEqual(record['evidence_sha256'],digest(folder/'evidence.json'))
        with self.assertRaisesRegex(ValueError,'unreviewed'):review(folder,'reject','Synthetic reviewer','Retry')

    def test_new_family_keeps_exact_approval_and_locks_selected(self):
        before=self.store.state();presets=json.loads((REPO/'recipes/lightning-gesture-presets.json').read_text())
        with mock.patch('live2d_studio.frontal_family.aside_guide', return_value=(Image.new('RGB',(64,64),'white'),{'rs':[20,20]})):
            new=initialize(self.master,self.root/'frontal-review',presets)
        state=new.state()
        self.assertEqual(state['poses']['right-lift']['approval'],before['poses']['right-lift']['approval'])
        self.assertEqual(self.store.state(),before)
        self.assertIn('left-aside-v2',state['poses']);self.assertIn('right-aside-v2',state['poses'])
        self.assertNotIn('torso-open',state['poses'])
        self.assertEqual(state['used_seeds'],before['used_seeds'])
        with self.assertRaisesRegex(ValueError,'approved'):new.reserve('right-lift',next(iter(presets)))


class ArmContracts(unittest.TestCase):
    def binding_fixture(self):
        layers=[];view=[];items=[]
        for side in ('right','left'):
            for part in ('upper','forearm','hand'):
                name=side+'-'+part
                layers.append(dict(id=name,arm_part=part,anatomical_side=side))
                view.append(dict(id=name,name=name));items.append(dict(target='mesh:'+name,layerId=name,parentId=side))
        return {'layers':{'items':view}},items,{'layers':layers}
    def test_common_owner_per_side_only(self):
        v,o,l=self.binding_fixture();b=bind(v,o,l);self.assertNotEqual(b['right']['target'],b['left']['target'])
        o.append(dict(target='mesh:torso',layerId='torso',parentId='right'))
        with self.assertRaisesRegex(ValueError,'unrelated'):bind(v,o,l)
    def test_shapes_preserve_all_existing_body_keys_and_default(self):
        b={'right':{'target':'warp:r'},'left':{'target':'warp:l'}}
        d={row['target']:{'axes':{'Body':[-1,0,1],'Breath':[0,1]}} for row in b.values()}
        steps=recipe(b,d)
        self.assertEqual([len(s['shapes']) for s in steps],[6,6])
        self.assertTrue(all(s['parameter']['default']==0 for s in steps))
        self.assertLess(steps[0]['shapes'][0]['operations'][0]['controls'][-1],0)
        self.assertGreater(steps[1]['shapes'][0]['operations'][0]['controls'][-1],0)
        with self.assertRaises(ValueError):recipe(b,d,amount=20)
    def test_aside_guides_are_framed_and_distinct(self):
        im=Image.new('RGBA',(800,1536),'white')
        from PIL import ImageDraw
        ImageDraw.Draw(im).rectangle((180,60,620,1500),fill='#8070a0')
        for side in ('right','left'):
            _,p=aside_guide(im,side,'silhouette');k='r' if side=='right' else 'l'
            self.assertGreater(abs(p[k+'e'][0]-p[k+'s'][0]),100)
            self.assertTrue(all(0<x<800 and 0<y<1536 for x,y in p.values()))

if __name__=='__main__':unittest.main()
