import unittest
import numpy as np
from live2d_studio.transition_authoring import correspondence,bernstein,ink_curve,opacity_schedule,DENSE_VALUES

class TransitionTests(unittest.TestCase):
    def test_shared_curve_resampling_and_interpolation(self):
        x=np.linspace(0,1,41);source=.2+.15*(2*x-1)**2;target=.7+.05*(1-(2*x-1)**2)
        controls,error=correspondence(x,source,x[::2],target[::2],[0,0,1,1])
        aligned=.08*source+bernstein(x)@controls
        self.assertLess(error,.0001);self.assertLess(np.max(abs(aligned-target)),.0002)
        # Two strokes follow the same curve while the source regains thickness.
        for opening in DENSE_VALUES:
            amount=opening
            y=aligned*(1-amount)+source*amount
            replacement=target+amount*(source-target)
            np.testing.assert_allclose(y,replacement,atol=.0002)
            self.assertTrue(np.isfinite(y).all())
            if opening==1:np.testing.assert_array_equal(y,source)

    def test_correspondence_is_translation_and_scale_equivariant(self):
        x=np.linspace(0,1,25);s=.3+.1*x*x;t=.7+.05*x
        expected,_=correspondence(x,s,x,t,[0,0,1,1])
        for scale,shift in [(25,320),(.02,-5),(89,0)]:
            controls,_=correspondence(x*scale+shift,s*scale+shift,x*scale+shift,t*scale+shift,
                [shift,shift,shift+scale,shift+scale])
            np.testing.assert_allclose(controls,expected,atol=1e-11)

    def test_opacity_handoff_and_iris_exclusion(self):
        def value(kind,x):
            k,v=zip(*opacity_schedule(kind));return np.interp(x,k,v)
        for x in np.linspace(0,1,1001):
            self.assertAlmostEqual(1-(1-value('lash',x))*(1-value('closed',x)),1)
            if x<=.15:self.assertEqual(value('interior',x),0)
        self.assertEqual(value('closed',1),0)
        self.assertEqual(value('lash',1),1)
        self.assertEqual(value('interior',0),0)
        # Source-over coverage stays full throughout; this isn't an additive fade.
        self.assertEqual(value('closed',.125),1)

    def test_contours_across_sizes_colours_and_sides(self):
        for width,height,colour in [(64,32,10),(120,70,75),(40,20,110)]:
            a=np.zeros((height,width,4),np.uint8);a[:]=[230,225,220,255]
            for x in range(3,width-3):
                y=int(height*.25+height*.1*((x-width/2)/(width/2))**2)
                a[y:y+2,x]=[colour,colour,colour,255]
            for b in [a,a[:,::-1]]:
                x,y=ink_curve(b,upper=True)
                self.assertGreater(np.ptp(x),width*.7)
                self.assertLess(max(y),height*.5)

    def test_unsupported_correspondence_fails(self):
        with self.assertRaises(ValueError):correspondence([0,.1],[0,0],[.9,1],[1,1],[0,0,1,1])
        with self.assertRaises(ValueError):ink_curve(np.zeros((10,10,4),np.uint8))

class DenseEvidenceTests(unittest.TestCase):
    def record(self):
        from live2d_studio.transition_authoring import DENSE_VALUES
        r=dict(status='pass',samples={},sequences={})
        def sample(n,**kw):r['samples'][n]=dict(values=dict(ParamEyeLOpen=1,ParamEyeROpen=1,ParamMouthOpenY=0,ParamMouthCurve=0,**{}));r['samples'][n]['values'].update(kw)
        for name,ids,curve in [('left',['ParamEyeLOpen'],0),('right',['ParamEyeROpen'],0),('both',['ParamEyeLOpen','ParamEyeROpen'],0),('mouth',['ParamMouthOpenY'],0),('smile',['ParamMouthOpenY'],1),('frown',['ParamMouthOpenY'],-1)]:
            for v in DENSE_VALUES:sample(name+'-'+str(v).replace('.','_'),ParamMouthCurve=curve,**{k:v for k in ids})
        for name,id in [('left','ParamEyeLOpen'),('right','ParamEyeROpen'),('both','ParamEyeLOpen'),('mouth','ParamMouthOpenY')]:
            ns=[]
            for i in range(41):
                n=name+'cycle'+str(i);v=np.sin(np.pi*i/40)**2;sample(n,**{id:v if name=='mouth' else 1-v});ns.append(n)
            r['sequences']['cycle-'+name]=ns
        for name in ['neutral','happy','sad','angry','surprised','confused','embarrassed']:
            ns=[]
            for i in range(12):n=name+str(i);sample(n,ParamMouthOpenY=i/12);ns.append(n)
            r['sequences']['combined-'+name]=ns
        return r

    def test_dense_actual_values_and_round_trips(self):
        from live2d_studio.transition_quality import validate_samples
        self.assertFalse(validate_samples(self.record())['visual_acceptance'])
        r=self.record();r['samples']['left-0_1']['values']['ParamEyeROpen']=.8
        with self.assertRaises(ValueError):validate_samples(r)
        r=self.record();del r['samples']['right-0_05']
        with self.assertRaises(KeyError):validate_samples(r)
        r=self.record();r['sequences']['cycle-left']=r['sequences']['cycle-left'][:20]
        with self.assertRaises(ValueError):validate_samples(r)

if __name__=='__main__':unittest.main()
