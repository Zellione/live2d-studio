import importlib.util
import tempfile
import unittest
from pathlib import Path
from live2d_studio.rp_qa import evaluate

spec=importlib.util.spec_from_file_location('st_patch',Path(__file__).resolve().parents[1]/'scripts/patch_st_phase3.py')
patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)

class RPIntegrationTests(unittest.TestCase):
    def test_patcher_refuses_unknown_source_and_nonisolated_destinations(self):
        with self.assertRaises(ValueError):patch.patched('unknown source')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):patch.apply(Path(d))
    def test_pixel_motion_alone_never_grants_rp_acceptance(self):
        r=evaluate({'visual':dict(mode='visual',status='pass',mouth_pixel_changes={'1':500})})
        self.assertEqual(r['rp_integration'],'rejected');self.assertFalse(r['production_ready'])
    def test_caught_event_errors_are_failures(self):
        r=evaluate({m:dict(status='pass',network_validation=dict(caught_event_listener_errors=1)) for m in ['rp','lifecycle','failure','race','visual']})
        self.assertTrue(any('event errors' in s for s in r['failures']))
    def test_complete_event_evidence_keeps_visual_gate_separate(self):
        labels=['joy','sadness','anger','surprise','confusion','embarrassment','neutral']
        runs={m:dict(status='pass',network_validation=dict(caught_event_listener_errors=0)) for m in ['rp','lifecycle','failure','race','visual']}
        runs['rp']['mapping_checks']={label:dict(checks=[dict(accepted=True)]) for label in labels}
        runs['rp']['samples']={'rest':[dict(ParamMouthOpenY=0)],**{'message_'+label:[dict(ParamMouthOpenY=0),dict(ParamMouthOpenY=.8)] for label in labels}}
        runs['lifecycle'].update(idle_recovered=True,switch_removed=True)
        runs['visual']['mouth_pixel_changes']={'1':100}
        report=evaluate(runs)
        self.assertEqual(report['rp_integration'],'accepted-isolated-adapter')
        self.assertEqual(report['visual_animation'],'requires-independent-review')
        self.assertFalse(report['production_ready'])
