import json
import tempfile
import unittest
from pathlib import Path
from live2d_studio.animation import EXPRESSIONS, LABELS, expression, recipe, settings, package

class AnimationTests(unittest.TestCase):
    def test_expression_channels_compose_with_blink_and_talk(self):
        for name,values in EXPRESSIONS.items():
            entries={e['parameter']:e for e in expression(name,values)['entries']}
            for id in ['ParamEyeLOpen','ParamEyeROpen']:
                self.assertEqual(entries[id]['blend'],'MULTIPLY')
                self.assertGreater(entries[id]['value'],0)
                self.assertLessEqual(entries[id]['value'],1)
                self.assertEqual(0*entries[id]['value'],0)
            self.assertEqual(entries['ParamMouthOpenY']['blend'],'ADD')
            self.assertLessEqual(entries['ParamMouthOpenY']['value'],.35)
        self.assertEqual(expression('neutral',EXPRESSIONS['neutral'])['entries'][3]['value'],1)

    def test_mapping_uses_installed_vocabulary_and_keeps_motion_free(self):
        s=settings();self.assertEqual(len(s['classify_mapping']),28)
        self.assertEqual(set(s['classify_mapping']),set(LABELS))
        self.assertEqual(s['classify_mapping']['joy']['expression'],'happy')
        for mapping in s['classify_mapping'].values():
            self.assertIn(mapping['expression'],EXPRESSIONS)
            self.assertEqual(mapping['motion'],'none')
        self.assertEqual(s['param_mouth_open_y_id'],'ParamMouthOpenY')

    def test_recipe_matches_reviewed_rig_and_loop_is_closed(self):
        steps=json.loads(Path('recipes/girl2-animation.json').read_text())
        axes={s['request']['shapes'][0]['target'][-1]:{
            k:sorted({shape['key'][k] for shape in s['request']['shapes']})
            for k in s['request']['shapes'][0]['key']}
            for s in steps if s['operation']=='author_axis'}
        self.assertEqual(steps,recipe(axes))
        curves={}
        for step in steps:
            if step['operation']=='motion_pose' and step['request']['id']=='rpIdle':
                for p,v in step['request']['values'].items():curves.setdefault(p,[]).append((step['request']['time'],v))
        self.assertNotIn('ParamMouthOpenY',curves)
        for p,keys in curves.items():
            self.assertEqual(keys[0][1],keys[-1][1],p)
        self.assertEqual(min(v for t,v in curves['ParamEyeLOpen']),0)
        self.assertLessEqual(max(abs(v) for t,v in curves['ParamAngleX']),2)

    def test_packaging_rejects_existing_output_and_missing_authoring(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileExistsError):package('tests/fixtures/phase1/final/runtime',d)
            with self.assertRaises(ValueError):package('tests/fixtures/phase1/final/runtime',Path(d)/'new')
            self.assertFalse((Path(d)/'new').exists())
