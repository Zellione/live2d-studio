"""Concealed overlap remains derived, bounded and separate from original artwork."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image
from live2d_studio.elbow_overlap import prepare
from live2d_studio.manifest import digest
from live2d_studio.pose_review import REPO

class OverlapTests(unittest.TestCase):
    def test_patch_samples_are_inside_existing_sleeve_and_source_unchanged(self):
        with tempfile.TemporaryDirectory(dir=REPO/'runs') as tmp:
            root=Path(tmp);(root/'layer_manifest.json').write_text('{}');a=np.zeros((80,60,4),np.uint8);a[:,10:50]=[130,120,180,255];Image.fromarray(a[:40]).save(root/'upper.png');Image.fromarray(a[40:]).save(root/'forearm.png')
            layers={'layers':[{'anatomical_side':'right','rgba_path':name+'.png','x':0,'y':y} for name,y in [('upper',0),('forearm',40)]]}
            proposal={'canvas':[60,80],'layer_manifest_sha256':digest(root/'layer_manifest.json'),'arms':{'right':{'elbow':[.5,.5]}}}
            before=digest(root/'forearm.png')
            with patch('live2d_studio.elbow_overlap.load_validate',return_value=layers):r=prepare(root,proposal,'right',root/'out')
            im=np.array(Image.open(root/'out/sleeve-overlap.png'));x,y,x1,y1=r['bbox'];opaque=im[...,3]>0
            np.testing.assert_array_equal(im[opaque],a[y:y1,x:x1][opaque]);self.assertEqual(before,digest(root/'forearm.png'))
            self.assertFalse(r['new_rgb_inference']);self.assertTrue(r['new_hidden_shape']);self.assertEqual(r['human_review'],'pending')
            with patch('live2d_studio.elbow_overlap.load_validate',return_value=layers):
                with self.assertRaises(ValueError):prepare(root,proposal,'right',root/'out')
                proposal['layer_manifest_sha256']='bad'
                with self.assertRaises(ValueError):prepare(root,proposal,'right',root/'changed')
