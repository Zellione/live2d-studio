"""CPU tests for exploratory component reporting and the human-selection gate."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
from PIL import Image
import test_pose_reviewer as fixtures
from live2d_studio.pose_review import REPO,digest,write
sys.path.insert(0,str(REPO/'scripts'))
from phase4b7b_selected_semantics import components,summarize,evaluate
from phase4b7b_report import build


class SelectedSemanticsTests(unittest.TestCase):
    def test_components_ignore_small_noise_without_inventing_joints(self):
        mask=np.zeros((100,100),dtype=bool);mask[10:70,10:20]=True;mask[10:70,70:80]=True;mask[90,90]=True
        labels,regions=components(mask)
        self.assertEqual(len(regions),2);self.assertEqual([r['pixels'] for r in regions],[600,600])
        self.assertLess(regions[0]['centroid'][0],regions[1]['centroid'][0])
    def test_sam_hash_and_shape_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.png';Image.new('RGB',(100,100),'white').save(source)
            mask=np.zeros((100,100),dtype='uint8');mask[20:80,20:30]=255
            Image.fromarray(mask).save(root/'handwear.png');Image.new('L',(100,100)).save(root/'topwear.png')
            write(root/'sam.json',{'input_sha256':digest(source)})
            result=summarize(root,source,root/'overlay.png')
            self.assertEqual(result['substantial_arm_components'],1);self.assertFalse(result['hidden_anatomy_verified'])
            write(root/'sam.json',{'input_sha256':'wrong'})
            with self.assertRaises(ValueError):summarize(root,source,root/'bad.png')
            write(root/'sam.json',{'input_sha256':digest(source)});Image.new('L',(20,20)).save(root/'handwear.png')
            with self.assertRaises(ValueError):summarize(root,source,root/'bad.png')
    def test_empty_selected_set_never_runs_parser_and_releases_lock(self):
        fixture=fixtures.ReviewerTests();fixture.setUp()
        try:
            store=fixture.store;store.finish();sid=store.state()['exports'][-1]['id']
            def forbidden(*args,**kwargs):self.fail('Parser called without a selected pose')
            with self.assertRaises(ValueError):evaluate(store.root,sid,store.root/'empty-analysis',runner=forbidden)
            import os
            fd=store.gpu_lock();os.close(fd)
        finally:fixture.tearDown()

    def test_report_assessment_must_match_human_selected_image(self):
        fixture=fixtures.ReviewerTests();fixture.setUp()
        try:
            store=fixture.store;b=fixture.batch();c=b['candidates'][0]
            store.decide('accept','right-lift',c['id']);store.finish();s=store.state()
            root=fixture.folder;notes=root/'notes.json';write(notes,{})
            semantic_file=root/'semantics.json'
            write(semantic_file,{'source_sha256':s['source']['sha256'],'selection_sha256':s['exports'][-1]['sha256'],
                                 'selected':{'right-lift':{'image_sha256':c['sha256']}}})
            assessment={'human_visual_approval':{'candidate':c['id'],'image_sha256':c['sha256'],
                                                'selection_sha256':s['exports'][-1]['sha256']},
                        'semantic_report_sha256':digest(semantic_file),'conclusion':'Synthetic fixture only'}
            file=root/'assessment.json';write(file,assessment)
            build([],store.root,notes,root/'gallery',root/'benchmark.json',file)
            self.assertEqual(json.loads((root/'benchmark.json').read_text())['human_approved_count'],1)
            assessment['human_visual_approval']['image_sha256']='wrong';write(file,assessment)
            with self.assertRaises(ValueError):build([],store.root,notes,root/'bad-gallery',root/'bad-benchmark.json',file)
        finally:fixture.tearDown()

if __name__=='__main__':unittest.main()
