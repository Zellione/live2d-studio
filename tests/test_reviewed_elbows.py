"""Exact limited elbow reference; local binaries remain deliberately untracked."""
import json
from pathlib import Path
import unittest
from live2d_studio.manifest import digest
from live2d_studio.stages import inventory,verify
from live2d_studio.elbow_rig import frozen_reference
from live2d_studio.bundle import validate

REPO=Path(__file__).resolve().parents[1]
PIN=REPO/'docs/references/codel-frontal-elbows-v1.json'


class ElbowReferenceMetadataTests(unittest.TestCase):
    def test_limited_acceptance_and_neutral_difference_remain_explicit(self):
        pin=json.loads(PIN.read_text())
        self.assertEqual(pin['status'],'accepted-limited-elbow-reference')
        self.assertFalse(pin['production_deployment'])
        self.assertEqual(pin['neutral_reference_changed_pixels'],880)
        self.assertEqual(len(pin['manifest_sha256']),64)
        self.assertGreater(pin['payload_files'],200)


class ElbowReferenceLocalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pin=json.loads(PIN.read_text());cls.root=REPO/cls.pin['reference_root']
        if not cls.root.exists():raise unittest.SkipTest('Ignored local reference absent')
        _,cls.manifest=frozen_reference(PIN)

    def test_every_payload_and_exact_human_evidence_is_sealed(self):
        self.assertEqual(inventory(self.root),self.manifest['files']|{'manifest.json':self.pin['manifest_sha256']})
        self.assertTrue(all(not(p.stat().st_mode & 0o222) for p in [self.root,*self.root.rglob('*')]))
        self.assertEqual(digest(self.root/'user-review.json'),self.pin['user_review_sha256'])
        user=json.loads((self.root/'user-review.json').read_text())
        self.assertEqual(user['reply'],'Accept as a limited elbow prototype')
        self.assertEqual(user['reviewer_kind'],'human');self.assertEqual(user['decision'],'accept')
        verify(REPO,user['files'])
        self.assertEqual(digest(self.root/self.pin['editable_project']),digest(REPO/'runs/phase4b11-bilateral-v2/rig/authoring/character.psd2live'))
        self.assertEqual(digest(self.root/self.pin['layered_psd']),digest(REPO/'runs/phase4b11-bilateral-v2/rig/exported/character.psd'))

    def test_complete_runtime_preserves_all_previous_expression_physics_motion(self):
        model=self.root/self.pin['model'];self.assertEqual(validate(model)['status'],'pass')
        data=json.loads(model.read_text());refs=data['FileReferences']
        self.assertEqual(len(refs['Expressions']),7)
        self.assertTrue({'Idle','Nod','Question','ArmRight','ArmLeft','ElbowRight','ElbowLeft'}<=set(refs['Motions']))
        parent,_=frozen_reference(REPO/'docs/references/codel-frontal-prototype-v1.json')
        for file in (parent/'runtime').iterdir():
            if file.name.endswith(('.exp3.json','.physics3.json','.motion3.json')):
                self.assertEqual(digest(file),digest(model.parent/file.name))
        for side in ('right','left'):
            cap=json.loads((self.root/'overlaps'/side/'overlap.json').read_text())
            self.assertFalse(cap['new_rgb_inference']);self.assertTrue(cap['new_hidden_shape'])
            self.assertEqual(digest(self.root/'overlaps'/side/cap['path']),cap['sha256'])

    def test_old_failed_method_and_count_gate_remain_failed(self):
        b=json.loads((REPO/'docs/benchmarks/phase4b11.json').read_text())
        self.assertEqual(b['failures_retained']['mesh_transform']['visible_triangle_reversals'],8983)
        self.assertEqual(b['validation']['historical_regression']['status'],'fail')


if __name__=='__main__':unittest.main()
