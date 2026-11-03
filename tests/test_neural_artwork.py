import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
from live2d_studio.manifest import digest, write_json
from live2d_studio.facial_artwork import prepare
from live2d_studio.neural_artwork import composite, tasks, install, reconstruct, reuse_predictions, REPO
from test_facial_artwork import fixture


class NeuralArtworkTests(unittest.TestCase):
    def test_empty_review_fallback_loads_no_model_and_keeps_artwork(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);prepare(fixture(root/'source'),root/'layers')
            before=digest(root/'layers/facial-artwork.json')
            write_json(root/'config.json',dict(model='qwen'))
            write_json(root/'review.json',dict(reviewer='test',decision='accept-selected',selected=[]))
            with patch('live2d_studio.neural_artwork.infer') as runner:
                reconstruct(root/'layers',root,'hybrid',root/'config.json',root/'review.json')
                runner.assert_not_called()
            self.assertEqual(before,digest(root/'layers/facial-artwork.json'))
            self.assertFalse((root/'requests').exists())

    def test_cached_predictions_bind_model_inputs_parameters_and_masks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);req=root/'requests';req.mkdir();cache=root/'cache';(cache/'test').mkdir(parents=True)
            pixels=np.full((8,8,4),255,np.uint8);mask=np.zeros((8,8),np.uint8);mask[3:5,3:5]=255
            Image.fromarray(pixels).save(req/'image.png');Image.fromarray(mask).save(req/'mask.png')
            for name in ['raw.png','composite.png']:Image.fromarray(pixels).save(cache/'test'/name)
            Image.fromarray(mask).save(cache/'test/generated.png')
            task=dict(id='test',image='image.png',mask='mask.png',seed=1729)
            write_json(req/'tasks.json',[task])
            record=dict(model='lama',model_lock_sha256=digest(REPO/'backends/inpainting/models.lock.json'),tasks=[dict(task=task,
                image_sha256=digest(req/'image.png'),mask_sha256=digest(req/'mask.png'),raw_sha256=digest(cache/'test/raw.png'),composite_sha256=digest(cache/'test/composite.png'))])
            write_json(cache/'report.json',record)
            reuse_predictions(req,root/'reused',cache,'lama')
            self.assertFalse(json.loads((root/'reused/cache-reuse.json').read_text())['inference_executed'])
            task['seed']=9;write_json(req/'tasks.json',[task])
            with self.assertRaisesRegex(ValueError,'parameters'):reuse_predictions(req,root/'bad',cache,'lama')
            task['seed']=1729;write_json(req/'tasks.json',[task]);Image.fromarray(255-mask).save(cache/'test/generated.png')
            with self.assertRaisesRegex(ValueError,'mask changed'):reuse_predictions(req,root/'bad',cache,'lama')
            self.assertFalse((root/'bad').exists())

    def test_hybrid_requires_review_and_rejects_stale_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);prepare(fixture(root/'source'),root/'layers')
            write_json(root/'config.json',dict(model='lama',targets=['eye-left-skin']))
            with patch('live2d_studio.neural_artwork.infer') as runner:
                with self.assertRaisesRegex(ValueError,'exact-evidence'):
                    reconstruct(root/'layers',root,'hybrid',root/'config.json')
                runner.assert_not_called()
            write_json(root/'review.json',dict(reviewer='test reviewer',decision='accept-selected',selected=['eye-left-skin'],images={}))
            def fake_infer(requests,output,model):
                output.mkdir();write_json(output/'report.json',dict(tasks=[dict(task=dict(id='eye-left-skin'),
                    image_sha256='changed',mask_sha256='changed',composite_sha256='changed')]))
            with patch('live2d_studio.neural_artwork.infer',fake_infer):
                with self.assertRaisesRegex(ValueError,'exact regenerated'):
                    reconstruct(root/'layers',root,'hybrid',root/'config.json',root/'review.json')

    def test_composite_preserves_rgba_outside_and_alpha_everywhere(self):
        rng=np.random.default_rng(6)
        source=rng.integers(0,256,(25,30,4),dtype=np.uint8)
        prediction=255-source;mask=np.zeros((25,30),bool);mask[8:12,9:20]=True
        result=composite(source,prediction,mask)
        np.testing.assert_array_equal(result[~mask],source[~mask])
        np.testing.assert_array_equal(result[...,3],source[...,3])
        np.testing.assert_array_equal(result[mask,:3],prediction[mask,:3])
        with self.assertRaises(ValueError):composite(source,prediction,mask[:-1])

    def test_tasks_use_generated_alternatives_and_preserve_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);prepare(fixture(root/'source',colour=(80,160,120),offset=3),root/'layers')
            before={str(p.relative_to(root/'layers')):digest(p) for p in (root/'layers').rglob('*') if p.is_file()}
            req=tasks(root/'layers',root/'requests')
            self.assertEqual(len(req),6)
            self.assertFalse(any('neutral' in r['id'] for r in req))
            self.assertEqual(before,{str(p.relative_to(root/'layers')):digest(p) for p in (root/'layers').rglob('*') if p.is_file()})
            self.assertTrue(json.loads((root/'requests/bindings.json').read_text())['single_image'])
            with self.assertRaises(FileExistsError):tasks(root/'layers',root/'requests')

    def test_open_mouth_fallback_and_missing_target_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);prepare(fixture(root/'source',open_mouth=True),root/'layers')
            req=tasks(root/'layers',root/'requests')
            self.assertFalse(any(r['id'].startswith('mouth') for r in req))
            with self.assertRaisesRegex(ValueError,'No supported'):
                tasks(root/'layers',root/'unsupported',targets=['mouth-interior'])

    def test_install_only_generated_alternative_and_reject_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);prepare(fixture(root/'source'),root/'layers')
            req=tasks(root/'layers',root/'requests',targets=['eye-left-skin'])
            originals={str(p.relative_to(root/'layers')):digest(p) for folder in ['source','layers','masks','generated'] for p in (root/'layers'/folder).rglob('*') if p.is_file()}
            pred=root/'predictions';(pred/'eye-left-skin').mkdir(parents=True)
            image=np.array(Image.open(root/'requests/eye-left-skin.png'))
            mask=np.array(Image.open(root/'requests/eye-left-skin-mask.png'))>0
            image[mask,:3]=[101,151,121]
            Image.fromarray(image).save(pred/'eye-left-skin/composite.png')
            entry=dict(task=req[0],image_sha256=digest(root/'requests/eye-left-skin.png'),mask_sha256=digest(root/'requests/eye-left-skin-mask.png'),
                composite_sha256=digest(pred/'eye-left-skin/composite.png'),outside_mask_changed=0,alpha_changed=0)
            write_json(pred/'report.json',dict(model='test',tasks=[entry]))
            # A changed result cannot be installed even when the report claims integrity.
            Image.fromarray(255-image).save(pred/'eye-left-skin/composite.png')
            with self.assertRaisesRegex(ValueError,'Changed neural'):install(root/'layers',root/'requests',pred)
            Image.fromarray(image).save(pred/'eye-left-skin/composite.png')
            report=install(root/'layers',root/'requests',pred,blend=True)
            self.assertTrue(report['neural']['review_required'])
            self.assertEqual(originals,{str(p.relative_to(root/'layers')):digest(p) for folder in ['source','layers','masks','generated'] for p in (root/'layers'/folder).rglob('*') if p.is_file()})
            self.assertEqual(report['neural']['installed'][0]['id'],'eye-left-skin')


if __name__=='__main__':unittest.main()
