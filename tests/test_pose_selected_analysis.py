"""Selected diagnostics never consume unapproved candidates."""
import importlib.util
import json
from pathlib import Path
import unittest
from PIL import Image
import test_pose_reviewer as fixtures
from live2d_studio.pose_review import REPO,digest,write
from live2d_studio.pose_guides import layout

spec=importlib.util.spec_from_file_location('pose_analysis',REPO/'scripts/phase4b7b_analyze_selected.py')
analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)


class SelectedAnalysisTests(unittest.TestCase):
    def setUp(self):self.fixture=fixtures.ReviewerTests();self.fixture.setUp();self.store=self.fixture.store
    def tearDown(self):self.fixture.tearDown()
    def test_empty_selection_refused(self):
        self.store.finish();sid=self.store.state()['exports'][-1]['id']
        with self.assertRaises(ValueError):analysis.analyze(self.store.root,sid,self.store.root/'diagnostics')
        self.assertFalse((self.store.root/'diagnostics').exists())
    def test_only_approved_image_is_read_and_hash_checked(self):
        b,fd=self.store.reserve('right-lift','test')
        def worker(argv,**kwargs):
            result=fixtures.synthetic_worker(argv,**kwargs);folder=Path(argv[-1]).parent/'c1'
            Image.new('RGB',layout((120,240),1024)[0],'red').save(folder/'image.png')
            row=json.loads((folder/'result.json').read_text());row['image_sha256']=digest(folder/'image.png');write(folder/'result.json',row)
            return result
        self.store.execute(b,fd,worker);b=self.store.state()['batches'][0]
        self.store.decide('accept','right-lift',b['candidates'][0]['id'])
        self.store.finish();sid=self.store.state()['exports'][-1]['id']
        # An unselected candidate can be unavailable without entering this analysis.
        self.store.safe(b['candidates'][1]['image']).unlink()
        report=analysis.analyze(self.store.root,sid,self.store.root/'diagnostics')
        self.assertEqual(set(report),{'right-lift'});self.assertFalse(report['right-lift']['independently_verified_source_pixels'])
        (self.store.root/'selections'/sid/'right-lift.png').write_bytes(b'tampered')
        with self.assertRaises(ValueError):analysis.analyze(self.store.root,sid,self.store.root/'diagnostics2')

if __name__=='__main__':unittest.main()
