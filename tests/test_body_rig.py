"""Conservative hierarchy binding, motion independence and fallback contracts."""
import tempfile
from pathlib import Path
import unittest
from live2d_studio.body_rig import bindings, motion_clips, geometry_recipe, prepare

class BodyTests(unittest.TestCase):
    def test_no_output_inside_preserved_run(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError,'preserved predecessor'):
                prepare(folder,Path(folder)/'body')
            self.assertFalse((Path(folder)/'body').exists())

    def fixture(self):
        roles=['face','front_hair','back_hair','topwear']
        view={'layers':{'items':[dict(id=r,role=r) for r in roles]}}
        items=[dict(target='mesh:'+r,layerId=r) for r in roles]
        details={m['target']:dict(inherited=[dict(target=t) for t in (['warp:head','rotation:tilt','warp:body'] if m['layerId']!='topwear' else ['warp:body'])]) for m in items}
        details.update({'warp:head':dict(axes={'ParamAngleX':[-45,0,45],'ParamAngleY':[-30,0,30]}),'rotation:tilt':dict(axes={'ParamAngleZ':[-30,0,30]}),'warp:body':dict(axes={'ParamBreath':[0,1]})})
        return view,items,details

    def test_shared_head_required_and_body_excluded(self):
        v,o,d=self.fixture();self.assertEqual(bindings(v,o,d)['head'],'warp:head')
        d['mesh:back_hair']['inherited']=[dict(target='warp:body')]
        with self.assertRaisesRegex(ValueError,'common head'):bindings(v,o,d)
        v,o,d=self.fixture();d['mesh:topwear']['inherited'].insert(0,dict(target='warp:head'))
        with self.assertRaisesRegex(ValueError,'owns body'):bindings(v,o,d)

    def test_head_geometry_leaves_neutral_and_facial_channels_alone(self):
        v,o,d=self.fixture();b=bindings(v,o,d);r=geometry_recipe(b,d)
        self.assertEqual(len(r),8)
        self.assertTrue(all(x['target']=='warp:head' for x in r))
        self.assertFalse(any(all(v==0 for v in x['key'].values()) for x in r))
        upward=next(x for x in r if x['key']=={'ParamAngleX':0,'ParamAngleY':30})
        self.assertLess(upward['operations'][0]['delta'][1],0)

    def test_idle_loop_and_gestures_preserve_face(self):
        params={k:dict(min=-45,max=45) for k in ['ParamAngleX','ParamAngleY','ParamAngleZ','ParamBodyAngleX','ParamBodyAngleZ','ParamBreath','ParamEyeLOpen','ParamEyeROpen']}
        clips=motion_clips(params)
        self.assertEqual(clips[0]['duration'],16)
        for curve in clips[0]['curves']:
            self.assertEqual(curve['keys'][0]['value'],curve['keys'][-1]['value'])
            self.assertEqual(curve['keys'][0]['time'],0)
            self.assertEqual(curve['keys'][-1]['time'],16)
            self.assertTrue(all(k['in'][1]==k['out'][1]==0 for k in curve['keys']))
        for clip in clips[1:]:
            self.assertFalse(clip['loop'])
            self.assertTrue(all(c['parameter'].startswith('ParamAngle') for c in clip['curves']))
            self.assertTrue(all(c['keys'][-1]['value']==0 for c in clip['curves']))
        params['ParamAngleX']['max']=1
        with self.assertRaisesRegex(ValueError,'outside inspected'):motion_clips(params)

if __name__=='__main__':unittest.main()
