import json
from pathlib import Path
import tempfile
import unittest

from live2d_studio.stages import Stages
from live2d_studio.creation_quality import validate_review, CHECKS
from live2d_studio.generic_rig import targets, rig_recipe, animation_recipe


class CreationTests(unittest.TestCase):
    def test_resume_checks_pixels_and_preserves_failed_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'run'
            with Stages(output,{'source':'a'}).locked() as s:
                def fail(root):
                    (root/'diagnostic').write_text('failed attempt')
                    raise RuntimeError('interrupted')
                with self.assertRaises(RuntimeError):s.run('inference',{'seed':42},fail)
                old=s.root/s.data['stages']['inference']['directory']
                result=s.run('inference',{'seed':42},lambda p:(p/'pixels').write_bytes(b'RGBA'))
                self.assertTrue((old/'diagnostic').exists())
                self.assertNotEqual(old,result)
            with Stages(output,{'source':'a'}).locked() as s:
                self.assertEqual(result,s.run('inference',{'seed':42},lambda p:self.fail('reran inference')))
                (result/'pixels').write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError,'changed'):
                    s.run('inference',{'seed':42},lambda p:self.fail('silently repaired tampering'))

    def test_input_change_foreign_directory_and_concurrent_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'run'
            with Stages(output,{'source':'a'}).locked():
                with self.assertRaises(RuntimeError):
                    with Stages(output,{'source':'a'}).locked():pass
            with self.assertRaises(ValueError):
                with Stages(output,{'source':'b'}).locked():pass
            with self.assertRaises(ValueError):
                with Stages(Path(tmp),{}).locked():pass

    def test_review_is_bound_and_rejection_is_not_acceptance(self):
        record=dict(evidence_sha256='hash',decision='accept',reviewer='tester',notes='checked',checks=list(CHECKS))
        validate_review(record,'hash',CHECKS)
        for change in [dict(evidence_sha256='old'),dict(decision='reject'),dict(checks=['semantic_ownership']),dict(notes='')]:
            with self.assertRaises(ValueError):validate_review(dict(record,**change),'hash',CHECKS)

    def test_no_girl2_ids_and_complete_axes(self):
        data=dict(layers=dict(items=[]),deformers=dict(items=[]))
        items=[]
        for i,(role,side) in enumerate([('eyebrow','left'),('eyebrow','right'),('mouth','none')]):
            data['layers']['items'].append(dict(id=f'new-layer-{i}',role=role,side=side))
            data['deformers']['items'].append(dict(target=f'warp:random-{i}'))
            items.append(dict(target=f'mesh:unrelated-{i}',parentId=f'random-{i}',layerId=f'new-layer-{i}'))
        bindings=targets(data,items)
        details={v:dict(axes={'X':[-3,0,3],'Y':[-2,0,2]}) for v in bindings.values()}
        steps=rig_recipe(bindings,details)
        self.assertEqual(54,sum(len(s['request']['shapes']) for s in steps))
        for step in steps:
            for shape in step['request']['shapes']:
                self.assertIn(shape['target'],bindings.values())
                self.assertEqual({'X','Y'},set(shape['key']))
        items[0]['parentId']='missing'
        with self.assertRaises(ValueError):targets(data,items)

    def test_refuse_ambiguous_semantics_and_unbounded_axes(self):
        with self.assertRaises(ValueError):targets(dict(layers=dict(items=[]),deformers=dict(items=[])),[])
        bindings={'mouth:none':'warp:a','eyebrow:left':'warp:b','eyebrow:right':'warp:c'}
        with self.assertRaises(ValueError):
            rig_recipe(bindings,{t:dict(axes={'X':list(range(257))}) for t in bindings.values()})

    def test_motion_uses_real_ranges(self):
        ids='ParamMouthCurve ParamBrowEmotion ParamEyeLOpen ParamEyeROpen ParamMouthOpenY ParamAngleX ParamAngleY ParamAngleZ ParamBreath'.split()
        params=[dict(id=k,min=-30,max=30,default=0) for k in ids]
        steps=animation_recipe(params)
        self.assertEqual(7,sum(s['operation']=='expression_put' for s in steps))
        params[5]['max']=.1
        with self.assertRaises(ValueError):animation_recipe(params)


if __name__=='__main__':unittest.main()
