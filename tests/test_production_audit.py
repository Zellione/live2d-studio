import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from live2d_studio import production_audit as audit


class ProductionAuditTests(unittest.TestCase):
    def test_projection_omits_credentials_messages_and_character_names(self):
        data = {'password':'PRIVATE-CREDENTIAL', 'chats':['PRIVATE-CHAT'], 'extension_settings':{
            'apiKey':'PRIVATE-API-KEY', 'expressions':{'api':2, 'llmPrompt':'PRIVATE-PROMPT'},
            'live2d':{'enabled':True, 'force_loop':False,
                'characterModelMapping':{'PRIVATE-NAME':'/assets/live2d/other/test.model3.json'},
                'characterModelsSettings':{'PRIVATE-NAME':{'/assets/live2d/other/test.model3.json':{
                    'animation_click':{'message':'PRIVATE-MESSAGE'},'scale':.45,'x':10}}}}}}
        report=audit.summarize_settings(io.StringIO(json.dumps(data)))
        self.assertNotIn('PRIVATE',json.dumps(report))
        self.assertEqual(report['classifier_api'],2)
        self.assertEqual(report['configured_character_model_pairs'],1)
        self.assertEqual(report['flags'],{'enabled':True,'force_loop':False})
        self.assertFalse(report['requires_preference_merge'])

    def test_existing_target_preferences_are_a_conflict_not_a_merge(self):
        prefs={'classify_mapping':{'joy':{'expression':'PRIVATE-EXPRESSION','motion':'none'}}}
        models={'redacted':{audit.MODEL_URL.lstrip('/'):prefs}}
        data={'extension_settings':{'live2d':{'characterModelsSettings':models}}}
        r=audit.summarize_settings(io.StringIO(json.dumps(data)))
        self.assertTrue(r['requires_preference_merge']);self.assertEqual(r['proposed_path_preferences'],1)
        self.assertNotIn('PRIVATE-EXPRESSION',json.dumps(r))

    def test_missing_settings_is_distinct_from_enabled(self):
        r=audit.summarize_settings(io.StringIO('{}'))
        self.assertFalse(r['live2d_settings_present']);self.assertEqual(r['flags'],{})
        self.assertFalse(r['legacy_api_is_llm'])

    def test_escaped_nested_unselected_values_are_skipped(self):
        data={'skip':{'secret':['quote " brace } slash \\',{'more':[1,2,None]}]},
              'extension_settings':{'api':2,'live2d':{'enabled':False}}}
        r=audit.summarize_settings(io.StringIO(json.dumps(data)))
        self.assertTrue(r['legacy_api_is_llm']);self.assertEqual(r['flags'],{'enabled':False})

    def test_malformed_selected_values_fail_without_logging_data(self):
        for text in ['{"extension_settings":{"live2d":"PRIVATE"}}',
                     '{"extension_settings":{"live2d":{"enabled":PRIVATE}}}',
                     '{"extension_settings":{},"extension_settings":{}}']:
            with self.assertRaises(ValueError) as e:audit.summarize_settings(io.StringIO(text))
            self.assertNotIn('PRIVATE',str(e.exception))

    def test_report_output_cannot_target_production_or_traverse(self):
        for dest in [Path('/home/zelli/tools/ai/SillyTavern/audit.json'),audit.REPO/'runs/../../audit.json']:
            with patch.object(audit,'audit') as compute:
                with self.assertRaises(ValueError):audit.save_audit('unused','unused',dest)
                compute.assert_not_called()

    def test_report_output_is_exclusive_and_rejects_links(self):
        with tempfile.TemporaryDirectory(dir=audit.REPO/'runs') as d:
            report=Path(d)/'report.json';report.write_text('keep')
            with self.assertRaises(FileExistsError):audit.save_audit('unused','unused',report)
            link=Path(d)/'link';link.symlink_to('/home/zelli/tools/ai/SillyTavern',target_is_directory=True)
            with self.assertRaises(ValueError):audit.save_audit('unused','unused',link/'report.json')
            self.assertEqual(report.read_text(),'keep')
