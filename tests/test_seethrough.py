import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from live2d_studio.backends import prepare
from live2d_studio.manifest import digest, load_validate, artwork_request, write_json
from live2d_studio.seethrough import PINNED_SOURCE, MODEL_REVISIONS, semantics


class SeeThroughTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.bridge=self.root/'bridge'
        self.bridge.mkdir()
        self.source=self.root/'input.png'
        Image.new('RGBA',(12,10),(120,80,60,255)).save(self.source)
        Image.open(self.source).save(self.bridge/'normalized.png')
        image=Image.new('RGBA',(4,5),(10,90,80,127))
        image.save(self.bridge/'eye.png')
        self.data=dict(format_version=1,order='back-to-front',canvas=dict(width=12,height=10),
            input_sha256=digest(self.source),source_revision=PINNED_SOURCE,models=MODEL_REVISIONS,
            normalized_path='normalized.png',transform=dict(kind='test-identity'),
            layers=[dict(name='irides-r',path='eye.png',x=1,y=2,z_order=0,opacity=255,blend_mode='BlendMode.NORMAL')])
        self.save()

    def save(self):
        write_json(self.bridge/'decomposition.json',self.data)

    def run_backend(self,name='out'):
        return prepare(self.source,self.root/name,'test-owned','see-through',self.bridge)

    def test_generated_fractional_alpha_and_unknown_are_honest(self):
        metrics=self.run_backend()
        manifest=load_validate(self.root/'out')
        layer=manifest['layers'][0]
        self.assertEqual(layer['side'],'left')
        self.assertEqual(layer['hidden_reconstruction_status'],'unlocalized')
        self.assertEqual(metrics['observed_pixels'],0)
        self.assertIsNone(metrics['visible_original_pixels_changed'])
        self.assertEqual(metrics['generated_pixels'],20)
        self.assertEqual(metrics['unassigned_foreground_pixels'],100)
        self.assertEqual(np.array(Image.open(self.root/'out'/layer['generated_mask_path'])).max(),127)
        self.assertEqual(layer['reconstructed_pixels'],0)
        self.assertIn('eye_close:left',manifest['missing_regions'])
        self.assertFalse(manifest['rig_ready'])
        self.assertEqual(artwork_request(self.root/'out')['layers'][0]['role'],'irides')

    def test_determinism_and_no_overwrite(self):
        self.run_backend('one')
        self.run_backend('two')
        self.assertEqual((self.root/'one/layer_manifest.json').read_bytes(),(self.root/'two/layer_manifest.json').read_bytes())
        with self.assertRaises(FileExistsError):self.run_backend('one')

    def test_path_escape_and_wrong_source_rejected_before_writes(self):
        self.data['layers'][0]['path']='../input.png'
        self.save()
        with self.assertRaises(ValueError):self.run_backend()
        self.assertFalse((self.root/'out').exists())
        self.data['layers'][0]['path']='eye.png'
        self.data['input_sha256']='0'*64
        self.save()
        with self.assertRaises(ValueError):self.run_backend()

    def test_order_blend_and_revision_gates(self):
        for key,value in [('source_revision','unknown'),('order','front-to-back')]:
            old=self.data[key]
            self.data[key]=value
            self.save()
            with self.assertRaises(ValueError):self.run_backend()
            self.data[key]=old
        self.data['layers'][0]['opacity']=100
        self.save()
        with self.assertRaises(ValueError):self.run_backend()

    def test_forged_observed_pixels_are_rejected(self):
        self.run_backend()
        root=self.root/'out'
        data=load_validate(root)
        layer=data['layers'][0]
        Image.new('L',(4,5),127).save(root/layer['mask_path'])
        Image.new('L',(4,5),0).save(root/layer['generated_mask_path'])
        for key in ['mask_path','generated_mask_path']:layer['sha256'][key]=digest(root/layer[key])
        write_json(root/'layer_manifest.json',data)
        with self.assertRaisesRegex(ValueError,'Visible original pixels changed'):load_validate(root)

    def test_neural_replay_and_build_are_not_silently_baseline(self):
        self.run_backend()
        from live2d_studio.pipeline import reconstruct_project
        from live2d_studio.mcp import build
        with self.assertRaises(ValueError):reconstruct_project(self.root/'out',self.root/'replay')
        with patch('live2d_studio.mcp.MCP') as mcp:
            with self.assertRaises(ValueError):build(self.root/'out',self.root/'build','http://127.0.0.1:23871/mcp')
            mcp.assert_not_called()

    def test_backend_selection_and_side_conventions(self):
        self.assertEqual(semantics('eyelash-l'),('eyelash','right'))
        self.assertEqual(semantics('front hair'),('front_hair','none'))
        self.assertEqual(semantics('eyes'),('unknown','none'))
        with self.assertRaises(ValueError):prepare(self.source,self.root/'x','test','see-through')
        with self.assertRaises(ValueError):prepare(self.source,self.root/'x','test','deterministic',self.bridge)
