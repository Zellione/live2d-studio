"""Structural temporal evidence gates; these never assert visual naturalness."""
import math
from .transition_authoring import DENSE_VALUES


def validate_samples(report):
    if report.get('status')!='pass':raise ValueError('Failed runtime capture')
    samples=report['samples'];checks=[]
    for name,ids,curve in [('left',['ParamEyeLOpen'],0),('right',['ParamEyeROpen'],0),('both',['ParamEyeLOpen','ParamEyeROpen'],0),('mouth',['ParamMouthOpenY'],0),('smile',['ParamMouthOpenY'],1),('frown',['ParamMouthOpenY'],-1)]:
        for value in DENSE_VALUES:
            label=name+'-'+str(value).replace('.','_');actual=samples[label]['values']
            if any(not math.isclose(actual[k],value,abs_tol=1e-5) for k in ids):raise ValueError('Wrong actual runtime parameter: '+label)
            if not math.isclose(actual['ParamMouthCurve'],curve,abs_tol=1e-5):raise ValueError('Wrong expression curve')
            if name in ('left','right'):
                opposite='ParamEyeROpen' if name=='left' else 'ParamEyeLOpen'
                if not math.isclose(actual[opposite],1,abs_tol=1e-5):raise ValueError('Independent eye changed')
        checks.append(name+' dense samples and actual parameters')
    for name,id in [('left','ParamEyeLOpen'),('right','ParamEyeROpen'),('both','ParamEyeLOpen'),('mouth','ParamMouthOpenY')]:
        names=report['sequences']['cycle-'+name];values=[samples[n]['values'][id] for n in names]
        low,high=(0,1) if name=='mouth' else (1,0)
        if len(values)<25 or abs(values[0]-low)>1e-5 or abs(values[-1]-low)>1e-5 or min(abs(v-high) for v in values)>1e-5:
            raise ValueError('Incomplete closing/reopening cycle')
        midpoint=len(values)//2;sign=1 if name=='mouth' else -1
        if any((b-a)*sign < -1e-5 for a,b in zip(values[:midpoint],values[1:midpoint+1])) or any((b-a)*sign > 1e-5 for a,b in zip(values[midpoint:],values[midpoint+1:])):
            raise ValueError('Unexpected reversal in a closing/reopening trajectory')
        checks.append(name+' complete round trip')
    for name in ['neutral','happy','sad','angry','surprised','confused','embarrassed']:
        values=[samples[n]['values']['ParamMouthOpenY'] for n in report['sequences']['combined-'+name]]
        if max(values)-min(values)<.03:raise ValueError('Frozen talking during '+name)
        checks.append(name+' talking with head and both eyes')
    return dict(status='pass',checks=checks,visual_acceptance=False)
