"""Safety and inference/evaluation separation for the optional pose study."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
from phase4b7a_poses import ROOT, body_mask, digest, new_run, prepare
from phase4b7a_analysis import delta_regions, review_decisions, sam_masks


class PoseFeasibilityTests(unittest.TestCase):
    def test_mask_uses_raster_extent_and_keeps_space_for_new_silhouette(self):
        alpha=np.zeros((100,100),dtype=np.uint8);alpha[10:90,30:70]=255
        mask=body_mask(alpha,dict(top_fraction=.25,bottom_fraction=.75,horizontal_margin_fraction=.25))
        self.assertFalse(mask[:30].any());self.assertFalse(mask[70:].any())
        self.assertTrue(mask[30:70,20:80].all())
        self.assertTrue((mask & (alpha==0)).any())
        with self.assertRaises(ValueError):body_mask(alpha*0,dict(top_fraction=.25,bottom_fraction=.75,horizontal_margin_fraction=.25))

    def test_changed_pixels_are_not_truth_and_neutral_noise_is_excluded(self):
        src=np.zeros((12,12,3),dtype=np.uint8);neutral=src.copy();neutral[0:3]=100
        candidate=neutral.copy();candidate[5:8]=80
        mask=np.ones((12,12),dtype=bool);mask[7]=False
        changed,report=delta_regions(src,neutral,candidate,mask)
        self.assertFalse(changed[:3].any());self.assertFalse(changed[7].any())
        self.assertEqual(report['changed_pixels'],24)
        with self.assertRaises(ValueError):delta_regions(src,neutral,candidate[:4],mask)

    def test_wrong_source_is_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);Image.new('RGBA',(32,32),'white').save(folder/'source.png')
            (folder/'config.json').write_text(json.dumps(dict(source_sha256='0'*64)))
            with self.assertRaises(ValueError):prepare(folder/'source.png',folder/'config.json',folder/'output')
            self.assertFalse((folder/'output').exists())
            with self.assertRaises(ValueError):new_run(folder/'outside-project')
            with self.assertRaises(ValueError):new_run(ROOT/'runs/references/should-never-be-created')

    def test_reviews_and_semantic_outputs_are_image_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'pose').mkdir();img=root/'pose/composite.png'
            Image.new('RGB',(16,16),'white').save(img)
            review=dict(reviewer_kind='development-agent',user_approval=False,
                        poses=[dict(id='pose',decision='accept-exploratory',composite_sha256=digest(img))])
            self.assertIn('pose',review_decisions(review,root))
            duplicated=dict(review,poses=review['poses']*2)
            with self.assertRaises(ValueError):review_decisions(duplicated,root)
            Image.new('RGB',(16,16),'red').save(img)
            with self.assertRaises(ValueError):review_decisions(review,root)
            (root/'sam.json').write_text(json.dumps(dict(input_sha256='0'*64,tags=[])))
            with self.assertRaises(ValueError):sam_masks(root,img)


if __name__ == '__main__':unittest.main()
