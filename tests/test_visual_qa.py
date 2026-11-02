import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from PIL import Image
from live2d_studio.visual_qa import diagnose,review


class VisualQATests(unittest.TestCase):
    def test_detects_holes_detachment_and_colour_edges_without_aesthetic_pass(self):
        a=np.zeros((30,30,4),np.uint8);a[5:25,5:25]=[200,150,100,255]
        a[10:12,10:12]=0;a[1,1]=[0,0,0,255];a[15:18,15:18]=[0,0,0,255]
        r=diagnose(a)
        self.assertEqual(r['enclosed_transparent_pixels'],4)
        self.assertEqual(r['components'],2)
        self.assertEqual(r['detached_small_component_pixels'],1)
        self.assertGreater(r['strong_internal_colour_steps'],0)

    def test_render_pass_does_not_grant_visual_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=np.zeros((30,30,4),np.uint8);a[5:25,5:25]=[200,100,80,255]
            Image.fromarray(a).save(root/'neutral.png');a[10:12,10:12]=0;Image.fromarray(a).save(root/'pose.png')
            (root/'result.json').write_text(json.dumps({'result':{'value':{'frames':['neutral','pose'],'status':'pass','control_noise_pixels':0}}}))
            report=review(root,root/'qa')
            self.assertEqual(report['visual_animation'],'requires-review')
            self.assertFalse(report['production_ready'])
            self.assertTrue(report['poses']['pose']['warning_candidates'])
            self.assertTrue((root/'qa/poses.png').exists())
            with self.assertRaises(FileExistsError):review(root,root/'qa')
