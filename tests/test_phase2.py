"""Observable quality and safety gates; the inference API receives only a raster."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import numpy as np
from PIL import Image

from live2d_studio.benchmark import flatten, evaluate
from live2d_studio.manifest import load_validate, artwork_request, digest, write_json
from live2d_studio.pipeline import prepare, reconstruct_project
from live2d_studio.reconstruction import reconstruct

ROOT=Path(__file__).resolve().parents[1]


class ImagePipelineTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.input=flatten(ROOT/'tests/fixtures/phase1/final/art',self.root/'truth')
        self.project=self.root/'project'
        self.metrics=prepare(self.input,self.project,'original-repository-artwork')

    def test_synthetic_quality_and_visible_pixels(self):
        report=evaluate(self.project,self.root/'truth')
        self.assertEqual(report['mean_visible_iou'],1)
        self.assertGreater(report['mean_full_iou'],.88)
        self.assertLess(report['layers']['neck']['full_iou'],.5)  # Known missing hidden contour.
        self.assertEqual(self.metrics['composite_changed_pixels'],0)
        self.assertEqual(self.metrics['unknown_foreground_pixels'],0)
        self.assertEqual(self.metrics['missing_regions'],[])
        data=load_validate(self.project)
        self.assertEqual(len(data['layers']),16)
        self.assertEqual(sum(not l['default_visible'] for l in data['layers']),3)
        order={l['id']:l['z_order'] for l in data['layers']}
        for behind,front in [('neck','face'),('face','eyewhite_left'),
                             ('eyewhite_left','irides_left'),('irides_left','eyelash_left')]:
            self.assertLess(order[behind],order[front])

    def test_deterministic_without_ground_truth_available(self):
        # Move raster away from metadata and hide the truth before inference.
        independent=self.root/'independent.png'
        shutil.copyfile(self.input,independent)
        shutil.rmtree(self.root/'truth')
        prepare(independent,self.root/'repeat','original-repository-artwork')
        self.assertEqual((self.project/'layer_manifest.json').read_bytes(),
                         (self.root/'repeat/layer_manifest.json').read_bytes())

    def test_refuses_overwrite_and_keeps_input(self):
        before=digest(self.input)
        manifest=(self.project/'layer_manifest.json').read_bytes()
        with self.assertRaises(FileExistsError):
            prepare(self.input,self.project)
        self.assertEqual(digest(self.input),before)
        self.assertEqual(manifest,(self.project/'layer_manifest.json').read_bytes())

    def test_scale_translation_and_colour_variation(self):
        image=Image.open(self.input).resize((384,450),Image.Resampling.NEAREST)
        pixels=np.array(image)
        pixels[...,:3]=np.clip(pixels[...,:3].astype(int)-3,0,255)
        placed=Image.new('RGBA',(440,500))
        placed.alpha_composite(Image.fromarray(pixels),(19,23))
        source=self.root/'varied.png'
        placed.save(source)
        metrics=prepare(source,self.root/'varied')
        self.assertEqual(metrics['missing_regions'],[])
        self.assertEqual(metrics['composite_changed_pixels'],0)

    def test_opaque_webp_and_jpeg_decode(self):
        original=Image.open(self.input)
        white=Image.new('RGBA',original.size,'white')
        white.alpha_composite(original)
        for extension in ('png','webp','jpg'):
            source=self.root/f'opaque.{extension}'
            white.convert('RGB').save(source,lossless=True)
            metrics=prepare(source,self.root/extension)
            load_validate(self.root/extension)
            self.assertGreater(metrics['foreground_pixels'],0)
            if extension!='jpg':
                self.assertEqual(metrics['missing_regions'],[])

    def test_fractional_alpha_and_zero_transparent_rgb(self):
        rgba=np.zeros((60,60,4),np.uint8)
        rgba[10:50,10:50]=(30,100,200,128)
        source=self.root/'alpha.png'
        Image.fromarray(rgba).save(source)
        metrics=prepare(source,self.root/'alpha')
        self.assertEqual(metrics['composite_changed_pixels'],0)
        self.assertTrue(metrics['missing_regions'])
        load_validate(self.root/'alpha')

    def test_bounded_fill_preserves_visible_values(self):
        rgba=np.full((20,20,4),(100,150,200,255),np.uint8)
        mask=np.ones((20,20),bool)
        mask[9:11,9:11]=False
        out,filled=reconstruct(rgba,mask,'face')
        self.assertEqual(int(filled.sum()),4)
        np.testing.assert_array_equal(out[mask],rgba[mask])
        mask[2:18,2:18]=False
        _,filled=reconstruct(rgba,mask,'face')
        self.assertFalse(filled.any())

    def test_reconstruction_can_replay_separately(self):
        reconstruct_project(self.project,self.root/'reconstructed')
        replay=load_validate(self.root/'reconstructed')
        self.assertEqual(replay,load_validate(self.project))
        with self.assertRaises(FileExistsError):
            reconstruct_project(self.project,self.root/'reconstructed')

    def test_manifest_adapter_and_integrity_failures(self):
        request=artwork_request(self.project)
        self.assertEqual((request['width'],request['height']),(256,300))
        self.assertEqual(len(request['layers']),16)
        data=load_validate(self.project)
        mutations=[lambda d:d.update(schema_version=99),
                   lambda d:d['layers'][0].update(rgba_path='../outside.png'),
                   lambda d:d['layers'][0].update(x=-1),
                   lambda d:d['layers'][1].update(id=d['layers'][0]['id']),
                   lambda d:d['layers'][1].update(z_order=-1)]
        for mutate in mutations:
            bad=copy.deepcopy(data)
            mutate(bad)
            write_json(self.project/'layer_manifest.json',bad)
            with self.assertRaises(ValueError):
                load_validate(self.project)
        write_json(self.project/'layer_manifest.json',data)
        (self.project/data['layers'][0]['rgba_path']).unlink()
        with self.assertRaises(ValueError):
            load_validate(self.project)

    def test_symlink_escape_and_original_tampering(self):
        data=load_validate(self.project)
        path=self.project/data['layers'][0]['rgba_path']
        saved=path.read_bytes()
        path.unlink()
        external=self.root/'external.png'
        external.write_bytes(saved)
        path.symlink_to(external)
        with self.assertRaises(ValueError):
            load_validate(self.project)
        path.unlink()
        path.write_bytes(saved)
        (self.project/data['sources'][0]['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError):
            load_validate(self.project)

    def test_alpha_integrity_not_just_checksum(self):
        data=load_validate(self.project)
        layer=data['layers'][0]
        path=self.project/layer['rgba_path']
        pixels=np.array(Image.open(path))
        y,x=np.argwhere(pixels[...,3]>0)[0]
        pixels[y,x,3]=1
        Image.fromarray(pixels).save(path)
        layer['sha256']['rgba_path']=digest(path)
        write_json(self.project/'layer_manifest.json',data)
        with self.assertRaisesRegex(ValueError,'Alpha differs'):
            load_validate(self.project)

    def test_artifact_policy_allows_goldens_and_ignores_runs(self):
        for name in ('tests/fixtures/phase1/final/runtime/new.model3.json',
                     'tests/fixtures/phase0/export/new.moc3'):
            result=subprocess.run(['git','check-ignore','--no-index','-q',name],cwd=ROOT)
            self.assertEqual(result.returncode,1)
        for name in ('runs/new/texture.png','models/example.safetensors',
                     '.env','exports/new/model.moc3','docs/evidence/phase2/transcript.json'):
            result=subprocess.run(['git','check-ignore','--no-index','-q',name],cwd=ROOT)
            self.assertEqual(result.returncode,0)
