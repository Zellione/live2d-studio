"""Readiness, exact human review and resumable optional authoring without GPU/MCP."""
import contextlib
import inspect
import io
import json
from pathlib import Path
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch, Mock

import numpy as np
from PIL import Image
from live2d_studio import arm_pipeline as arms
from live2d_studio.manifest import digest, write_json
from live2d_studio.stages import inventory


class ArmPlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=arms.REPO/'runs',prefix='test-arms-')
        self.root=Path(self.tmp.name)
        self.layers=self.root/'layers';self.layers.mkdir()
        self.fixture(self.layers)

    def tearDown(self):self.tmp.cleanup()

    def fixture(self,root,scale=1):
        w,h=100*scale,200*scale
        im=Image.new('RGBA',(w,h));parts=[]
        for side,x in [('right',10),('left',70)]:
            for part,y,height in [('upper',20,60),('forearm',80,50),('hand',130,20)]:
                name=side+'-'+part;rgba=Image.new('RGBA',(20*scale,height*scale),'#79638fff')
                rgba.save(root/(name+'.png'));im.paste(rgba,(x*scale,y*scale))
                mask=Image.new('L',rgba.size,255);mask.save(root/(name+'-observed.png'))
                Image.new('L',rgba.size).save(root/(name+'-hidden.png'))
                files=dict(rgba_path=name+'.png',mask_path=name+'-observed.png',reconstructed_mask_path=name+'-hidden.png')
                parts.append(dict(id=name,arm_part=part,anatomical_side=side,role='handwear',side=side,
                    x=x*scale,y=y*scale,width=20*scale,height=height*scale,z_order=len(parts),source_id='fixture',
                    confidence=.5,quality_status='candidate',provenance='synthetic test fixture',**files,
                    sha256={k:digest(root/v) for k,v in files.items()}))
        im.save(root/'source.png')
        write_json(root/'layer_manifest.json',dict(schema_version=1,canvas=dict(width=w,height=h),
            sources=[dict(id='fixture',path='source.png',normalized_path='source.png',sha256=digest(root/'source.png'),normalized_sha256=digest(root/'source.png'))],layers=parts))

    def change(self,fn):
        p=self.layers/'layer_manifest.json';data=json.loads(p.read_text());fn(data);write_json(p,data)

    def plan(self):
        assessment=arms.assess(self.layers)
        plan={**assessment,'source_project_sha256':'a'*64,'degrees':120,'overlaps':{}}
        for side in ('right','left'):
            plan['overlaps'][side]=arms.overlap(self.layers,plan['proposal'],side,self.root/'overlaps'/side)
        plan['files']={k:v for k,v in inventory(self.root).items()}
        write_json(self.root/'plan.json',plan)
        return plan

    def test_separation_only_proposes_unverified_normalized_joints(self):
        a=arms.assess(self.layers)
        self.assertEqual(a['status'],'needs-arm-review');self.assertFalse(a['proposal']['anatomy_verified'])
        self.assertEqual(a['proposal']['arms']['right']['elbow'],[.195,.4])
        self.assertNotEqual(a['proposal']['arms']['left']['elbow'],a['proposal']['arms']['right']['elbow'])
        scaled=self.root/'scaled';scaled.mkdir();self.fixture(scaled,2)
        b=arms.assess(scaled)
        # Pixel centers differ by half a subpixel after scaling; source-relative attachment remains bounded.
        np.testing.assert_allclose(a['proposal']['arms']['right']['elbow'],b['proposal']['arms']['right']['elbow'],atol=.0025)

    def test_missing_or_duplicate_semantics_fall_back(self):
        self.change(lambda d:d['layers'][0].pop('arm_part'))
        self.assertEqual(arms.assess(self.layers)['status'],'shoulder-only-fallback')
        self.change(lambda d:d['layers'][0].update(arm_part='forearm'))
        self.assertEqual(arms.assess(self.layers)['status'],'shoulder-only-fallback')

    def test_disconnected_ownership_does_not_become_safe_from_labels(self):
        # Switch complete, hash-valid slices between sides: cuts no longer share horizontal support.
        self.change(lambda d:[l.update(arm_part='hand' if l['arm_part']=='forearm' else 'forearm') for l in d['layers'] if l['arm_part'] in ('hand','forearm')])
        result=arms.assess(self.layers)
        self.assertEqual(result['status'],'shoulder-only-fallback')
        self.assertTrue(any('disconnected' in x for x in result['reasons']))

    def test_review_persists_but_never_approves_animation(self):
        self.plan();self.assertIsNone(arms.authorize(self.root))
        arms.approve(self.root,'Synthetic reviewer','Synthetic fixture only')
        self.assertEqual(arms.authorize(self.root)['kind'],'explicit-human-plan-review')
        self.assertIn('animation review separate',json.loads((self.root/'review.json').read_text())['scope'])
        with self.assertRaisesRegex(ValueError,'already recorded'):arms.approve(self.root,'X','Y')

    def test_changed_range_or_review_kind_invalidates_review(self):
        p=self.plan();arms.approve(self.root,'Synthetic reviewer','Fixture')
        p['degrees']=110;write_json(self.root/'plan.json',p)
        with self.assertRaisesRegex(ValueError,'Changed'):arms.authorize(self.root)

    def test_changed_hidden_pixels_or_unsafe_paths_rejected(self):
        self.plan();arms.approve(self.root,'Synthetic reviewer','Fixture')
        (self.root/'overlaps/right/sleeve-overlap.png').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'artifact changed'):arms.authorize(self.root)
        with self.assertRaisesRegex(ValueError,'outside ignored'):arms.read_plan('/tmp')

    def test_rejection_is_resumable_without_authoring(self):
        self.plan();arms.approve(self.root,'Synthetic reviewer','Unsupported sleeve',decision='reject')
        self.assertEqual(arms.authorize(self.root),{'kind':'rejected'})
        with patch.object(arms,'frozen_reference',side_effect=AssertionError('Cannot override rejection')):
            self.assertEqual(arms.authorize(self.root,'reference'),{'kind':'rejected'})

    def test_exact_reference_reuse_cannot_generalize_acceptance(self):
        plan=self.plan();ref=self.root/'reference';(ref/'provenance').mkdir(parents=True)
        write_json(ref/'provenance/approved-arm-contract.json',arms.contract(plan))
        write_json(ref/'user-review.json',dict(reviewer_kind='human',decision='accept'))
        write_json(ref/'manifest.json',{})
        with patch.object(arms,'frozen_reference',return_value=(ref,{})):
            self.assertEqual(arms.authorize(self.root,'fixture-pin')['kind'],'explicit-reuse-of-exact-reviewed-reference')
            plan['source_project_sha256']='b'*64;write_json(self.root/'plan.json',plan)
            with self.assertRaisesRegex(ValueError,'exact arm plan'):arms.authorize(self.root,'fixture-pin')

    def test_fallback_never_contacts_editor(self):
        base=self.root/'base';base.mkdir();(base/'character.psd2live').write_bytes(b'fixture')
        out=self.root/'planned';out.mkdir();client=Mock(side_effect=AssertionError('Must not call editor'))
        arms._plan(base,self.layers,out,client,120)
        self.assertEqual(arms.read_plan(out)['status'],'shoulder-only-fallback');client.assert_not_called()

    def test_optional_stage_waits_then_resumes_without_reauthoring(self):
        base=self.root/'base';base.mkdir();(base/'character.psd2live').write_bytes(b'fixture')
        for name in ['body','mouth','composition','arm']:write_json(base/(name+'-inspection.json'),{})
        runtime=self.root/'runtime';runtime.mkdir();model=runtime/'fixture.model3.json';write_json(model,{})
        write_json(runtime/'existing.motion3.json',{'fixture':'unchanged'})
        out=self.root/'run';calls=[]
        def fake_author(client,reference,proposal,output,side,degrees,method,overlap,parent):
            self.assertEqual(method,'rotation');self.assertTrue(overlap);calls.append(side)
            dest=output/'authoring';shutil.copytree(parent,dest)
            patch=arms.overlap(reference/'layers',proposal,side,output/'overlap')
            write_json(dest/'elbow-inspection.json',dict(bindings={side:dict(meshes=['mesh:'+side+p for p in ['upper','forearm','hand']])},surfaces=[dict(target='mesh:'+side+p) for p in ['forearm','hand']]))
            write_json(dest/'overlap-inspection.json',dict(patch=patch,mesh=dict(target='mesh:'+side+'cap')))
        def fake_export(client,output,side,degrees):
            target=output/'exported/runtime';shutil.copytree(runtime,target)
            return target/model.name
        with patch('live2d_studio.bundle.validate',return_value={'status':'pass','files_sha256':{}}),patch.object(arms,'inspect_source'),patch.object(arms,'author',side_effect=fake_author),patch.object(arms,'export_candidate',side_effect=fake_export),patch('live2d_studio.arm_validation.validation_pins',return_value={}),patch('live2d_studio.arm_validation.validate_arms') as validate:
            result=arms.prepare(base,self.layers,model,out,client_factory=lambda:None)
            self.assertEqual(result['status'],'needs-arm-review');self.assertFalse(calls)
            arms.approve(Path(result['plan']),'Synthetic reviewer','Synthetic fixture overlap/range only')
            result=arms.prepare(base,self.layers,model,out,client_factory=lambda:None)
            self.assertEqual(result['status'],'needs-visual-review');self.assertEqual(calls,['right','left'])
            before=inventory(out/'stages')
            again=arms.prepare(base,self.layers,model,out,client_factory=lambda:None)
            self.assertEqual(result,again);self.assertEqual(calls,['right','left']);validate.assert_called_once()
            self.assertEqual(before,inventory(out/'stages'))
            self.assertEqual(digest(Path(result['model']).parent/'existing.motion3.json'),digest(runtime/'existing.motion3.json'))
            self.assertEqual((base/'character.psd2live').read_bytes(),b'fixture')


class ArmOwnerTests(unittest.TestCase):
    def fixture(self):
        meshes=[dict(target='mesh:'+p,parentId='owner') for p in ('upper','lower','hand')]
        objects=meshes+[dict(target='warp:owner',parentId='body')]
        params={'Shoulder':dict(min=0,max=1,default=0),'Body':dict(default=0)}
        return objects,meshes,'Shoulder',params,dict(axes={'Shoulder':[0,1],'Body':[-1,0,1]})

    def test_inspected_owner_and_neutral_keys_required(self):
        args=self.fixture();self.assertEqual(arms.check_owner(*args),'owner')
        args[-1]['axes']['Body']=[-1,1]
        with self.assertRaisesRegex(ValueError,'neutral'):arms.check_owner(*args)

    def test_unrelated_mesh_or_deformer_is_rejected(self):
        for target in ['mesh:torso','warp:unrelated']:
            args=self.fixture();args[0].append(dict(target=target,parentId='owner'))
            with self.assertRaisesRegex(ValueError,'Unrelated'):arms.check_owner(*args)

    def test_missing_parent_and_unbound_shoulder_rejected(self):
        args=self.fixture();args[0].pop()
        with self.assertRaisesRegex(ValueError,'warp'):arms.check_owner(*args)
        args=self.fixture();args[-1]['axes'].pop('Shoulder')
        with self.assertRaisesRegex(ValueError,'shoulder keys'):arms.check_owner(*args)


class ArmWorkflowTests(unittest.TestCase):
    def test_cli_and_api_defaults_preserve_existing_behavior(self):
        from live2d_studio.cli import main
        from live2d_studio.creation import create
        from live2d_studio.performance import prepare
        for method in [create,prepare]:self.assertEqual(inspect.signature(method).parameters['arms'].default,'preserve')
        for command,args,module in [('create',['--input','x.png'],'creation.create'),('prepare-performance',['--baseline','runs/base'],'performance.prepare')]:
            for enabled in (False,True):
                flags=['--arms','native-elbows','--arm-review-reference','reference.json'] if enabled else []
                with patch.object(sys,'argv',['studio',command,*args,'--output','runs/new',*flags]),patch('live2d_studio.'+module,return_value={'status':'needs-arm-review'}) as fn,contextlib.redirect_stdout(io.StringIO()):main()
                self.assertEqual(fn.call_args.kwargs['arms'],'native-elbows' if enabled else 'preserve')

    def test_unsupported_range_and_overlapping_output_fail_before_editor(self):
        for degrees in [0,136,float('nan')]:
            with self.assertRaisesRegex(ValueError,'Unsupported arm range'):
                arms.prepare(arms.REPO/'runs/base/authoring',arms.REPO/'runs/base/layers',arms.REPO/'runs/base/runtime/model.json',arms.REPO/'runs/fixture-output',degrees=degrees)
        with self.assertRaisesRegex(ValueError,'Separate ignored'):
            arms.prepare(arms.REPO/'runs/base',arms.REPO/'runs/layers',arms.REPO/'runs/model.json',arms.REPO/'runs/base/child')


if __name__=='__main__':unittest.main()
