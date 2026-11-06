"""Composition protects authored expression channels and resumes independent stages."""
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from live2d_studio.performance import assert_expressions_preserved,compose
from live2d_studio.stages import Stages

class PerformanceTests(unittest.TestCase):
 def test_later_body_stage_must_preserve_every_channel_and_blend(self):
  before=[dict(id='confused',name='confused',fade_in=.35,fade_out=.35,entries=[dict(parameter='ParamMouthRound',value=1,blend='ADD'),dict(parameter='ParamMouthOpenY',value=.35,blend='ADD')])]
  assert_expressions_preserved(before,copy.deepcopy(before))
  for change in ('remove','value','blend'):
   after=copy.deepcopy(before)
   if change=='remove':after[0]['entries'].pop()
   else:after[0]['entries'][1][change]=0 if change=='value' else 'MULTIPLY'
   with self.assertRaises(ValueError):assert_expressions_preserved(before,after)
 def test_optional_order_and_resume_preserve_predecessor(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);base=root/'base';base.mkdir();(base/'character.psd2live').write_text('original');layers=root/'layers';layers.mkdir();(layers/'manifest').write_text('layers')
   calls=[]
   def mouth(client,predecessor,layers,out):
    calls.append('mouth');self.assertEqual((predecessor/'character.psd2live').read_text(),'original');(out/'character.psd2live').write_text('mouths')
   def body(client,predecessor,layers,out):
    calls.append('body');self.assertEqual((predecessor/'character.psd2live').read_text(),'mouths');out.mkdir();(out/'character.psd2live').write_text('mouths+body')
   with patch('live2d_studio.performance.author_mouths',mouth),patch('live2d_studio.body_rig.author',body):
    for _ in range(2):
     stages=Stages(root/'run',{'test':1})
     with stages.locked():
      result=compose(stages,base,layers,lambda:None,'coordinated','calm')
      self.assertEqual((result/'character.psd2live').read_text(),'mouths+body')
    self.assertEqual(calls,['mouth','body'])
    self.assertEqual((base/'character.psd2live').read_text(),'original')
 def test_defaults_do_not_add_stages(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)
   self.assertEqual(compose(None,p,p,lambda:None),p)
 def test_export_checks_every_saved_expression_parameter(self):
  import json
  from live2d_studio.performance import validate_export_expressions
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);ref=[dict(Name='confused',File='confused.json')]
   saved=[dict(id='create_confused',name='confused',fade_in=.35,fade_out=.35,entries=[dict(parameter='ParamMouthRound',value=1,blend='ADD')])]
   actual=dict(FadeInTime=.35,FadeOutTime=.35,Parameters=[dict(Id='ParamMouthRound',Value=1,Blend='Add')])
   (root/'confused.json').write_text(json.dumps(actual));validate_export_expressions(saved,root,ref)
   actual['Parameters']=[];(root/'confused.json').write_text(json.dumps(actual))
   with self.assertRaises(ValueError):validate_export_expressions(saved,root,ref)
