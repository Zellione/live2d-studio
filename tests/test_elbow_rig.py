"""Physical rotation and conservative fallback; no GPU or editor required."""
import unittest
import numpy as np
from live2d_studio.elbow_rig import rotation_landmarks, rotation_keys

class ElbowTests(unittest.TestCase):
    def test_rectangular_bounds_do_not_stretch_rotation(self):
        b=np.array([10,20,110,420]);p=np.array([42,24]);r=rotation_landmarks(b,p,120)
        before=np.array(r['from'])*(b[2:]-b[:2])+b[:2]
        after=np.array(r['to'])*(b[2:]-b[:2])+b[:2]
        np.testing.assert_allclose(np.linalg.norm(before-p,axis=1),np.linalg.norm(after-p,axis=1),atol=1e-12)
        self.assertGreater(np.linalg.det(np.stack((after[1]-after[0],after[2]-after[0]))),0)
    def test_normalized_rotation_is_translation_scale_equivariant(self):
        a=rotation_landmarks([10,20,110,420],[42,24],-110)
        b=rotation_landmarks([120,240,320,1040],[184,248],-110)
        np.testing.assert_allclose(a['to'],b['to'],atol=1e-12)
    def test_rest_exact_and_invalid_inputs_rejected(self):
        r=rotation_landmarks([0,0,100,400],[50,0],0)
        self.assertEqual(r['from'],r['to'])
        for bounds,p,d in [([0,0,0,1],[0,0],10),([0,0,1,1],[0,0],151),([0,0,1,1],[float('nan'),0],10)]:
            with self.assertRaises(ValueError):rotation_landmarks(bounds,p,d)
    def test_intermediate_linear_forms_have_bounded_length_loss(self):
        # 16 keys across 120 degrees: worst interpolation shrink <0.3%, no inversion.
        for step in range(16):
            a=rotation_landmarks([0,0,100,400],[50,0],120*step/16)
            b=rotation_landmarks([0,0,100,400],[50,0],120*(step+1)/16)
            m=(np.array(a['to'])+np.array(b['to']))/2*np.array([100,400])
            self.assertGreater(np.linalg.norm(m[2]-m[0])/400,.997)
            self.assertGreater(np.linalg.det(np.stack((m[1]-m[0],m[2]-m[0]))),0)

    def test_native_rotation_preserves_pivot_scale_and_rest(self):
        for side,sign in [('right',-1),('left',1)]:
            keys=rotation_keys('rotation:inspected','ParamTest',side,120)
            self.assertEqual(keys[0]['op'],'seed')
            self.assertEqual(keys[0]['key'],{'ParamTest':0})
            self.assertEqual(keys[1]['geometry'],{'angle':sign*120})
    def test_native_rejects_unsupported_ownership_and_range(self):
        for side,angle in [('unknown',20),('right',136),('left',float('nan')),('right',0)]:
            with self.assertRaises(ValueError):rotation_keys('rotation:x','ParamTest',side,angle)
