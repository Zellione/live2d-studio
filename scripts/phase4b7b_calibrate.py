"""Prepare a one-factor-at-a-time, single-seed right-arm parameter study."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image
from live2d_studio.pose_guides import guide,prompt

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare(output,followup_from=None):
    output.mkdir(parents=True,exist_ok=False)
    source=ROOT/'runs/references/codel-combined-v1/source/original.png'
    shutil.copyfile(source,output/'source.png')
    im=Image.open(source)
    for kind in ('skeleton','silhouette'):
        picture,points=guide(im,'right-lift',kind);picture.save(output/(kind+'.png'))
        (output/(kind+'.json')).write_text(json.dumps({'joints':points,'status':'inferred framing hypothesis, not anatomical truth'},indent=2)+'\n')
    if followup_from:
        old=json.loads((followup_from/'plan.json').read_text())
        parent=next(t for t in old['tasks'] if t['id']=='g-1536')
        tasks=[]
        for name,changes in [('j-face-landmarks',{}),('k-silhouette-1536',{'guidance':'silhouette'}),
                             ('l-denoise-08',{'denoise':.8}),('m-20-steps',{'steps':20})]:
            cfg=dict(parent['config'],**changes)
            tasks.append(dict(parent,id=name,config=cfg,guide=cfg['guidance']+'.png'))
        plan={'source':'source.png','inputs':{n:sha(output/n) for n in ('source.png','skeleton.png','silhouette.png')},
              'model_lock_sha256':sha(ROOT/'backends/inpainting/models.lock.json'),'tasks':tasks,
              'parent_plan_sha256':sha(followup_from/'plan.json'),
              'comparisons':{'j':'g-1536: guide adds face landmarks and moves nose to source-relative facial area',
                             'k':'j: silhouette representation','l':'j: denoise .8','m':'j: 20 steps'}}
        (output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');return
    base=dict(long_edge=1024,steps=40,cfg=4.0,sampler='euler',scheduler='simple',shift=3.0,
              denoise=1.0,latent='source',mask='legacy-body',guidance='none',cfg_norm=False)
    legacy=json.loads((ROOT/'runs/phase4b7a-input/tasks.json').read_text())[1]['prompt']
    tasks=[]
    def add(name,parent,changes,text):
        cfg=dict(parent,**changes);tasks.append(dict(id=name,seed=1729,config=cfg,prompt=text,negative_prompt='',guide=cfg['guidance']+'.png' if cfg['guidance']!='none' else None));return cfg
    a=add('a-masked',base,{},legacy)
    b=add('b-unmasked',a,{'mask':'none'},legacy)
    c=add('c-short-prompt',b,{},prompt('right-lift','none'))
    d=add('d-skeleton',c,{'guidance':'skeleton'},prompt('right-lift'))
    add('e-silhouette',d,{'guidance':'silhouette'},prompt('right-lift'))
    add('f-empty-latent',d,{'latent':'empty'},prompt('right-lift'))
    add('g-1536',d,{'long_edge':1536},prompt('right-lift'))
    add('h-cfg-norm',d,{'cfg_norm':True},prompt('right-lift'))
    add('i-20-steps',d,{'steps':20},prompt('right-lift'))
    plan={'source':'source.png','inputs':{n:sha(output/n) for n in ('source.png','skeleton.png','silhouette.png')},
          'model_lock_sha256':sha(ROOT/'backends/inpainting/models.lock.json'),'tasks':tasks,
          'comparisons':{'b':'a: mask only','c':'b: prompt formulation only','d':'c: add pose reference plus its necessary text reference',
                         'e':'d: guide representation','f':'d: latent initialization','g':'d: resolution','h':'d: guidance normalization','i':'d: step count'}}
    (output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--followup-from',type=Path);a=p.parse_args();prepare(a.output,a.followup_from)
