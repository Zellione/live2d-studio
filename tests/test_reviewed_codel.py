"""Regression identity for the user-reviewed combined Codel; no inference/editor."""
import contextlib
import inspect
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from live2d_studio.manifest import digest
from live2d_studio.stages import verify, fingerprint
from live2d_studio.bundle import validate

REPO = Path(__file__).resolve().parents[1]
PIN = REPO/'docs/references/codel-combined-v1.json'


class ReviewedCodelMetadataTests(unittest.TestCase):
    def test_acceptance_is_limited_and_configuration_is_explicit(self):
        p=json.loads(PIN.read_text())
        self.assertEqual(p['user_acceptance']['quote'],'Das sieht soweit gut aus jetzt.')
        for key in ['production_approved','professional_quality','full_body_articulation']:
            self.assertIs(p['user_acceptance'][key],False)
        self.assertFalse(p['default_changes'])
        self.assertEqual(p['feature_configuration'],dict(reconstruction='deterministic',facial_motion='aligned',mouths='coordinated',body_motion='calm'))
        self.assertEqual(len(p['manifest_sha256']),64)
        self.assertTrue(any('1716' in item for item in p['limitations']))

    def test_both_cli_workflows_forward_options_and_keep_defaults(self):
        from live2d_studio.cli import main
        from live2d_studio.creation import create
        self.assertEqual(inspect.signature(create).parameters['mouths'].default,'preserve')
        self.assertEqual(inspect.signature(create).parameters['body_motion'].default,'preserve')
        for enabled in [False,True]:
            flags=['--mouths','coordinated','--body-motion','calm'] if enabled else []
            with patch.object(sys,'argv',['live2d-studio','create','--input','input.png','--output','runs/test']+flags),patch('live2d_studio.creation.create',return_value={'status':'stopped-after-export'}) as action,contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(),0)
            self.assertEqual(action.call_args.kwargs['mouths'],'coordinated' if enabled else 'preserve')
            self.assertEqual(action.call_args.kwargs['body_motion'],'calm' if enabled else 'preserve')
            with patch.object(sys,'argv',['live2d-studio','prepare-performance','--baseline','runs/base','--output','runs/test']+flags),patch('live2d_studio.performance.prepare',return_value={}) as action,contextlib.redirect_stdout(io.StringIO()):
                main()
            self.assertEqual(action.call_args.args[2:4],('coordinated','calm') if enabled else ('preserve','preserve'))


class ReviewedCodelLocalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pin=json.loads(PIN.read_text());cls.root=REPO/cls.pin['reference_root']
        if not cls.root.exists():raise unittest.SkipTest('Local third-party/generated reference intentionally excluded from Git')

    def test_full_seal_and_source_candidate_are_unchanged(self):
        p=self.pin;root=self.root
        self.assertEqual(digest(root/p['manifest']),p['manifest_sha256'])
        manifest=json.loads((root/p['manifest']).read_text())
        verify(root,manifest['files'])
        self.assertEqual(set(manifest['files']),{str(f.relative_to(root)) for f in root.rglob('*') if f.is_file() and f.name!='manifest.json'})
        original=REPO/p['candidate']
        verify(original,{n.removeprefix('candidate/'):h for n,h in manifest['files'].items() if n.startswith('candidate/')})
        self.assertTrue(all(not (f.stat().st_mode & 0o222) for f in [root,*root.rglob('*')]))
        self.assertEqual(digest(root/p['user_acceptance']['path']),p['user_acceptance']['sha256'])
        user=json.loads((root/p['user_acceptance']['path']).read_text())
        self.assertEqual(user['runtime_inventory_sha256'],fingerprint(p['runtime_files']))

    def test_seven_expressions_physics_and_body_motion_contract(self):
        p=self.pin;model=self.root/p['paths']['model'];data=json.loads(model.read_text())
        self.assertEqual(validate(model)['status'],'pass');verify(model.parent,p['runtime_files'])
        refs=data['FileReferences'];self.assertEqual({e['Name'] for e in refs['Expressions']},{'neutral','happy','sad','angry','surprised','confused','embarrassed'})
        poses={e['Name']:{v['Id']:v['Value'] for v in json.loads((model.parent/e['File']).read_text())['Parameters']} for e in refs['Expressions']}
        self.assertEqual((poses['confused']['ParamMouthRound'],poses['confused']['ParamMouthOpenY'],poses['confused']['ParamMouthCurve']),(1,.35,0))
        self.assertEqual(poses['surprised']['ParamMouthOpenY'],.85)
        self.assertEqual(set(refs['Motions']),{'Idle','Nod','Question'})
        for name,entries in refs['Motions'].items():
            motion=json.loads((model.parent/entries[0]['File']).read_text())
            self.assertFalse(any(c['Id'].startswith('ParamMouth') for c in motion['Curves']))
            if name=='Idle':
                self.assertEqual(motion['Meta']['Duration'],16)
                self.assertTrue({'ParamAngleX','ParamAngleY','ParamAngleZ','ParamBreath','ParamEyeLOpen','ParamEyeROpen'}<={c['Id'] for c in motion['Curves']})
        physics=json.loads((model.parent/refs['Physics']).read_text())
        self.assertTrue({'ParamHairFront','ParamHairBack'}<={o['Destination']['Id'] for group in physics['PhysicsSettings'] for o in group['Output']})

    def test_unchanged_model_json_cannot_hide_expression_tampering(self):
        model=self.root/self.pin['paths']['model'];data=json.loads(model.read_text())
        name=next(e['File'] for e in data['FileReferences']['Expressions'] if e['Name']=='confused')
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/model.name).write_bytes(model.read_bytes())
            exp=json.loads((model.parent/name).read_text());next(p for p in exp['Parameters'] if p['Id']=='ParamMouthOpenY')['Value']=0
            (folder/name).write_text(json.dumps(exp))
            self.assertEqual(digest(folder/model.name),digest(model))
            with self.assertRaises(ValueError):verify(folder,{name:self.pin['runtime_files'][name]})

    def test_historical_failures_remain_failed(self):
        for label,record in self.pin['retained_failures'].items():
            file=REPO/record['path']
            self.assertEqual(digest(file),record['sha256'])
            report=json.loads(file.read_text());self.assertEqual(report['status'],'fail')
            if label=='girl2_visible_lips':self.assertEqual(report['visible_reversals'],1716)
