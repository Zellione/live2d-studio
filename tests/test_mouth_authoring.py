"""Direction, scale and reset contracts, separate from human emotion recognition."""
import unittest
import numpy as np
from live2d_studio.mouth_authoring import pose_geometry,surface_operations,expression_entries,POSES
from live2d_studio.transition_authoring import bernstein

class MouthTests(unittest.TestCase):
    def test_target_corner_direction_is_not_source_smile(self):
        source=np.array([45,55,55,45.]);w=40;center=50
        def contrast(p):return (p[0]+p[-1])/2-float(bernstein(np.array([.5]))[0]@p)
        happy,_=pose_geometry(source,w,center,1,0,0)
        sad,_=pose_geometry(source,w,center,-1,0,0)
        angry,_=pose_geometry(source,w,center,0,0,1)
        rounded,_=pose_geometry(source,w,center,0,1,0)
        self.assertLess(contrast(happy),-3)
        self.assertGreater(contrast(sad),3)
        self.assertLess(abs(contrast(angry)),abs(contrast(sad))/4)
        self.assertAlmostEqual(contrast(rounded),0)
        # A source frown still reaches the same intended smile/sad target.
        np.testing.assert_equal(happy,pose_geometry(100-source,w,center,1,0,0)[0])
        np.testing.assert_equal(sad,pose_geometry(100-source,w,center,-1,0,0)[0])

    def test_source_relative_operations_are_scale_translation_invariant(self):
        b=np.array([18,40,62,62.]);mb=np.array([20,42,60,60.]);fit=np.array([45,55,55,45.])
        for kind in ['source-neutral','interior']:
            for c,r,t in [(0,0,0),(1,0,0),(-1,0,0),(0,1,0),(0,0,1)]:
                a=surface_operations(kind,b,mb,fit,50,c,r,t,.5)
                z=surface_operations(kind,b*2+30,mb*2+30,fit*2+30,130,c,r,t,.5)
                np.testing.assert_allclose(a[0]['factors'],z[0]['factors'])
                np.testing.assert_allclose(a[0]['pivot'],z[0]['pivot'])
                np.testing.assert_allclose(a[1]['controls'],z[1]['controls'],atol=1e-12)
                self.assertGreater(min(a[0]['factors']),0)

    def test_emotion_channels_reset_without_changing_brows(self):
        old=[dict(parameter='ParamMouthCurve',value=.9,blend='ADD'),dict(parameter='ParamMouthDispleasure',value=1,blend='ADD'),
             dict(parameter='ParamBrowEmotion',value=.8,blend='ADD'),dict(parameter='ParamEyeLOpen',value=.85,blend='MULTIPLY')]
        for name in POSES:
            new=expression_entries(name,old);values={e['parameter']:e['value'] for e in new}
            self.assertNotIn('ParamMouthDispleasure',values)
            self.assertEqual(values['ParamBrowEmotion'],.8)
            self.assertEqual(next(e for e in new if e['parameter']=='ParamEyeLOpen'),old[-1])
            self.assertLessEqual(values['ParamMouthOpenY'],1)
            self.assertGreaterEqual(values['ParamMouthOpenY'],0)
        values={e['parameter']:e['value'] for e in expression_entries('neutral',old)}
        self.assertTrue(all(v==0 for k,v in values.items() if k.startswith('ParamMouth')))
        self.assertEqual(POSES['confused'][1],POSES['surprised'][1])
        self.assertLess(POSES['confused'][4],POSES['surprised'][4])
