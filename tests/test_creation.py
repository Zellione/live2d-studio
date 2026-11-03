import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

from live2d_studio.stages import Stages
from live2d_studio.creation_quality import validate_review, CHECKS
from live2d_studio.generic_rig import targets, rig_recipe, animation_recipe


class CreationTests(unittest.TestCase):
    def test_eye_order_uses_semantics_and_leaves_other_layers_fixed(self):
        from live2d_studio.semantic_order import order_layers
        roles=[('face','none'),('eyelash','left'),('eyebrow','left'),('irides','left'),('eyewhite','left'),('front_hair','none')]
        layers=[dict(id=str(i),role=role,side=side,z_order=i) for i,(role,side) in enumerate(roles)]
        ordered,changes=order_layers(layers)
        self.assertEqual([l['id'] for l in ordered],['0','4','2','3','1','5'])
        self.assertEqual(len(changes),1)
        replay,changes=order_layers(ordered)
        self.assertEqual(replay,ordered);self.assertEqual(changes,[])
        self.assertEqual([l['id'] for l in layers],[str(i) for i in range(6)])
        ambiguous=layers+[dict(layers[3],id='duplicate')]
        self.assertEqual(order_layers(ambiguous)[1],[])

    def test_preview_run_verifies_current_export(self):
        from live2d_studio.creation import preview_model
        from live2d_studio.stages import inventory
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);export=root/'stages/export-test';(export/'runtime').mkdir(parents=True)
            model=export/'runtime/a.model3.json';model.write_text('{}')
            data=dict(model='stages/export-test/runtime/a.model3.json',stages=dict(export=dict(
                status='complete',directory='stages/export-test',files=inventory(export))))
            (root/'creation.json').write_text(json.dumps(data))
            self.assertEqual(preview_model(root),model)
            model.write_text('changed')
            with self.assertRaises(ValueError):preview_model(root)
            model.write_text('{}');data['stages']['export']['status']='failed'
            (root/'creation.json').write_text(json.dumps(data))
            with self.assertRaises(ValueError):preview_model(root)

    def test_real_cli_stages_reuse_validated_bridge_without_worker(self):
        from live2d_studio.creation import create
        from live2d_studio.seethrough import PINNED_SOURCE,MODEL_REVISIONS
        from live2d_studio.manifest import digest,write_json
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'input.png';bridge=root/'bridge';bridge.mkdir()
            Image.new('RGBA',(12,10),(80,60,30,255)).save(source)
            Image.open(source).save(bridge/'normalized.png')
            Image.new('RGBA',(4,5),(20,40,60,255)).save(bridge/'eye.png')
            write_json(bridge/'decomposition.json',dict(format_version=1,order='back-to-front',
                canvas=dict(width=12,height=10),input_sha256=digest(source),source_revision=PINNED_SOURCE,
                models=MODEL_REVISIONS,normalized_path='normalized.png',transform=dict(kind='test'),
                layers=[dict(name='irides-r',path='eye.png',x=1,y=2,z_order=0,opacity=255,blend_mode='BlendMode.NORMAL')]))
            with patch('live2d_studio.creation.worker',side_effect=AssertionError('GPU reran')):
                result=create(source,root/'run',decomposition=bridge,until='inference',preview=False)
                first=json.loads((root/'run/creation.json').read_text())
                # Resume no longer even needs the external bridge path.
                result=create(source,root/'run',until='inference',preview=False)
                second=json.loads((root/'run/creation.json').read_text())
            self.assertEqual(first['stages'],second['stages'])
            self.assertEqual(result['status'],'stopped-after-inference')
            import zipfile
            from live2d_studio.generic_rig import verify_source_art
            project=root/'run'/second['stages']['inference']['directory']/'validated'
            with zipfile.ZipFile(root/'model.psd2live','w') as archive:
                archive.write(bridge/'eye.png','assets/eye.png')
            self.assertEqual(verify_source_art(project,root/'model.psd2live')['exact_source_layers'],1)
            with zipfile.ZipFile(root/'wrong.psd2live','w') as archive:
                archive.write(source,'assets/wrong.png')
            with self.assertRaises(ValueError):verify_source_art(project,root/'wrong.psd2live')
            pixel=root/'run'/second['stages']['inference']['directory']/'bridge/eye.png'
            pixel.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):create(source,root/'run',until='inference',preview=False)

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
