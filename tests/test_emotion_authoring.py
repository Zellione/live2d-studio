import unittest
import numpy as np
from PIL import Image, ImageDraw
from live2d_studio.emotion_authoring import brow_shapes, cheek_tint, expression_entries, CHANNELS

class EmotionTests(unittest.TestCase):
    def test_inner_tip_follows_geometry_and_scales(self):
        mouth=np.array([45,70,55,75]); left=np.array([10,30,35,35]);right=np.array([65,30,90,35])
        for b,sign in [(left,1),(right,-1)]:
            tilt,raise_=brow_shapes(b,mouth)
            self.assertEqual((tilt,raise_),brow_shapes(b*2+40,mouth*2+40))
            controls=tilt[1][1][0]['controls']
            self.assertGreater(sign*(controls[-1]-controls[0]),0)
            self.assertLess(raise_[1][1][0]['delta'][1],0)
        with self.assertRaises(ValueError):brow_shapes(np.array([40,30,60,35]),mouth)

    def test_explicit_resets_and_unaffected_poses(self):
        old=[dict(parameter='ParamBrowEmotion',blend='ADD',value=.7),dict(parameter='ParamEyeLOpen',blend='MULTIPLY',value=.85)]
        for name in ['neutral','happy','sad','surprised']:
            new=expression_entries(name,old,True)
            self.assertEqual(new[:2],old)
            self.assertTrue(all(e['value']==0 for e in new[2:]))
        by_name={n:{e['parameter']:e['value'] for e in expression_entries(n,old,True)} for n in ['angry','confused','embarrassed']}
        self.assertEqual(by_name['angry']['ParamMouthOpenY'],0)
        self.assertEqual(by_name['angry']['ParamBrowLIncline'],by_name['angry']['ParamBrowRIncline'])
        self.assertNotEqual(by_name['confused']['ParamBrowLRaise'],by_name['confused']['ParamBrowRRaise'])
        self.assertLess(by_name['embarrassed']['ParamBrowLIncline'],0)
        for n in by_name:self.assertEqual(by_name[n]['ParamBrowEmotion'],0)
        self.assertEqual(by_name['embarrassed']['ParamBlush'],1)

    def test_tint_translation_transparency_and_support_gate(self):
        def parts(offset=0):
            face=Image.new('RGBA',(180,180));ImageDraw.Draw(face).ellipse((20+offset,10+offset,140+offset,150+offset),fill=(150,100,80,255))
            eyes=[]
            for x in (45,95):
                eye=Image.new('RGBA',face.size);ImageDraw.Draw(eye).rectangle((x+offset,45+offset,x+20+offset,65+offset),fill='black');eyes.append(eye)
            mouth=Image.new('RGBA',face.size);ImageDraw.Draw(mouth).rectangle((70+offset,100+offset,90+offset,104+offset),fill='black')
            return face,eyes,mouth
        a,landmarks=cheek_tint(*parts());b,shifted=cheek_tint(*parts(10))
        self.assertGreater(np.asarray(a)[...,3].max(),60)
        self.assertLessEqual(np.asarray(a)[...,3].max(),64)
        self.assertTrue(np.array_equal(np.asarray(a)[:160,:160,3],np.asarray(b)[10:170,10:170,3]))
        self.assertTrue(all(s['x']==p['x']+10 and s['y']==p['y']+10 for p,s in zip(landmarks,shifted)))
        self.assertFalse(np.asarray(a)[0,:,3].any())
        face,eyes,mouth=parts()
        with self.assertRaises(ValueError):cheek_tint(Image.new('RGBA',face.size),eyes,mouth)

    def test_disconnected_mouth_uses_both_sides(self):
        from live2d_studio.emotion_authoring import mouth_baseline
        from live2d_studio.transition_authoring import bernstein
        a=np.zeros((80,100,4),dtype=np.uint8)
        for x in list(range(20,43))+list(range(58,81)):
            y=round(40+8*(1-((x-50)/30)**2))
            a[y-1:y+2,x]=[40,20,30,255]
            a[y-2,x]=[200,150,130,255]
        fit,width,center=mouth_baseline(a)
        self.assertAlmostEqual(fit[0],fit[-1],delta=1)
        self.assertGreater(float(bernstein(np.array([.5]))[0]@fit),fit[0]+5)
        a[:,:78]=0
        with self.assertRaises(ValueError):
            # Insufficient horizontal evidence must fail rather than extrapolate.
            mouth_baseline(a)
