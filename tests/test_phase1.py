"""Regression checks for portable artifacts and expression/animation composition."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'tests/fixtures/phase1/final/runtime'

class Phase1Tests(unittest.TestCase):
    def test_neutral_does_not_override_blink_or_talk(self):
        expression=json.loads((RUNTIME/'Generated_artwork.phase1_neutral.exp3.json').read_text())
        ids={entry['Id'] for entry in expression['Parameters']}
        self.assertFalse(ids & {'ParamEyeLOpen','ParamEyeROpen','ParamMouthOpenY'})
        self.assertIn('ParamMood',ids)

    def test_expressions_preserve_animation_channels(self):
        for name in ('happy','angry'):
            entries=json.loads((RUNTIME/f'Generated_artwork.phase1_{name}.exp3.json').read_text())['Parameters']
            blends={entry['Id']:entry['Blend'] for entry in entries}
            self.assertEqual(blends['ParamEyeLOpen'],'Multiply')
            self.assertEqual(blends['ParamEyeROpen'],'Multiply')
            self.assertEqual(blends['ParamMouthOpenY'],'Add')

    def test_motion_loop_endpoints_and_blink(self):
        motion=json.loads((RUNTIME/'Generated_artwork.phase1Idle.motion3.json').read_text())
        self.assertTrue(motion['Meta']['Loop'])
        for curve in motion['Curves']:
            segments=curve['Segments']
            self.assertEqual(segments[1],segments[-1])
            self.assertEqual(segments[-2],motion['Meta']['Duration'])
            if curve['Id'] in ('ParamEyeLOpen','ParamEyeROpen'):
                self.assertIn(0,segments[4::3])

    def test_names_unique_and_exact(self):
        settings=json.loads((RUNTIME/'Generated_artwork.model3.json').read_text())
        self.assertEqual([entry['Name'] for entry in settings['FileReferences']['Expressions']],['neutral','happy','angry'])

    def test_art_generation_refuses_existing_destination(self):
        spec=importlib.util.spec_from_file_location('art',ROOT/'scripts/create_phase1_art.py')
        art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)
        with tempfile.TemporaryDirectory() as temp:
            destination=Path(temp)/'art'
            art.create(destination)
            original=(destination/'face.png').read_bytes()
            with self.assertRaises(FileExistsError):
                art.create(destination)
            self.assertEqual(original,(destination/'face.png').read_bytes())

if __name__=='__main__':
    unittest.main()
