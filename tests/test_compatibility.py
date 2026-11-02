import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validator', ROOT / 'scripts/validate_bundle.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name) / 'bundle'
        shutil.copytree(ROOT / 'tests/fixtures/phase0/export', self.bundle)
        self.model = self.bundle / 'Generated_artwork.model3.json'

    def edit(self, change):
        data = json.loads(self.model.read_text())
        change(data)
        self.model.write_text(json.dumps(data))

    def fails(self):
        self.assertEqual(validator.validate(self.model)['status'], 'fail')

    def test_real_export(self):
        self.assertEqual(validator.validate(self.model)['status'], 'pass')

    def test_case_mismatch(self):
        self.edit(lambda d: d['FileReferences'].__setitem__('Moc', 'generated_artwork.moc3'))
        self.fails()

    def test_escape(self):
        self.edit(lambda d: d['FileReferences'].__setitem__('Moc', '../outside.moc3'))
        self.fails()

    def test_symlink_escape(self):
        (self.bundle / 'outside.moc3').symlink_to(self.model.parent.parent / 'secret')
        self.edit(lambda d: d['FileReferences'].__setitem__('Moc', 'outside.moc3'))
        self.fails()

    def test_missing_expression(self):
        (self.bundle / 'Generated_artwork.smile.exp3.json').unlink()
        self.fails()

    def test_invalid_motion(self):
        (self.bundle / 'Generated_artwork.idle.motion3.json').write_text('{')
        self.fails()

    def test_invalid_binary(self):
        (self.bundle / 'Generated_artwork.moc3').write_bytes(b'bad')
        self.fails()

    def test_wrong_schema(self):
        self.edit(lambda d: d.__setitem__('Version', 2))
        self.fails()

    def test_missing_sound(self):
        self.edit(lambda d: d['FileReferences']['Motions']['Idle'][0].__setitem__('Sound','absent.wav'))
        self.fails()

    def test_missing_file(self):
        self.assertEqual(validator.validate(self.bundle / 'absent.json')['status'], 'fail')


if __name__ == '__main__':
    unittest.main()
