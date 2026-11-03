"""Preview exposure boundary and reproducible expression recipe contracts."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from live2d_studio.preview_live import assets, viewer_assets, LIBS
from live2d_studio.expressive import recipe, blush_png
from PIL import Image
import numpy as np

REPO=Path(__file__).resolve().parents[1]
FIXTURE=REPO/'tests/fixtures/phase1/final/runtime/Generated_artwork.model3.json'

class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.extension=Path(self.temp.name)
        (self.extension/'lib').mkdir()
        for name in LIBS:(self.extension/'lib'/name).write_text('// unit-test asset; never a rendering fixture')

    def test_only_runtime_references_and_ui_are_exposed(self):
        files=assets(FIXTURE,self.extension)
        self.assertIn('/model/Generated_artwork.moc3',files)
        self.assertIn('/lib/live2dcubismcore.min.js',files)
        for name in ('sillytavern_settings.json','animation-provenance.json','Generated_artwork.cmo3','Generated_artwork.psd2live.json'):
            self.assertNotIn('/model/'+name,files)
        self.assertFalse(any('..' in name for name in files))
        self.assertNotIn('/model/../character.psd2live',files)

    def test_default_version_selector_keeps_baseline(self):
        with patch('live2d_studio.preview_live.DEFAULT_MODEL',FIXTURE):
            files=viewer_assets(extension=self.extension)
        config=json.loads(files['/config.json'][0])
        self.assertTrue(config['model'].startswith('/model/'))
        if 'candidate' in config:
            self.assertIn(config['candidate'],files)
            self.assertNotIn('/candidate/character.psd2live',files)

    def test_missing_dependencies_fail_before_server(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,'Missing Girl2 model'):
                assets(Path(directory)/'absent.model3.json',self.extension)
            with self.assertRaisesRegex(ValueError,'Missing installed runtime'):
                assets(FIXTURE,Path(directory))

    def test_escaping_model_reference_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            model=Path(directory)/'model.model3.json'
            model.write_text(json.dumps({'Version':3,'FileReferences':{'Moc':'../secret.moc3'}}))
            with self.assertRaisesRegex(ValueError,'Nonportable'):
                assets(model,self.extension)

    def test_reviewed_recipe_matches_generator(self):
        self.assertEqual(recipe(),json.loads((REPO/'recipes/girl2-expressive.json').read_text()))
        expressions=[s['request']['expression'] for s in recipe() if s['operation']=='expression_put']
        self.assertEqual(len(expressions),7)
        neutral=next(e for e in expressions if e['name']=='neutral')
        for e in neutral['entries']:
            self.assertEqual(e['value'],1 if e['blend']=='MULTIPLY' else 0)

    def test_blush_is_deterministic_transparent_and_local(self):
        with tempfile.TemporaryDirectory() as directory:
            a,b=[Path(directory)/n for n in ('a.png','b.png')]
            blush_png(a);blush_png(b)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            alpha=np.array(Image.open(a))[:,:,3]
            self.assertLessEqual(alpha.max(),70)
            self.assertEqual(alpha[0,0],0)
            self.assertLess(np.count_nonzero(alpha),5000)

if __name__=='__main__':unittest.main()
