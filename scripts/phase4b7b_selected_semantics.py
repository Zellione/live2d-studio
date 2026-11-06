"""Selected-only SAM comparison. Components are proposals, never verified joints."""
import argparse
import html
import json
import os
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image
from scipy import ndimage
from live2d_studio.pose_guides import fit
from live2d_studio.pose_review import REPO,Store,digest,write
from phase4b7b_analyze_selected import analyze


def components(mask):
    labels,count=ndimage.label(mask)
    minimum=max(32,int(mask.sum()*.05));regions=[]
    for index,area in enumerate(np.bincount(labels.ravel())[1:],1):
        if area<minimum:continue
        yy,xx=np.where(labels==index)
        regions.append({'label':index,'pixels':int(area),'centroid':[float(xx.mean()),float(yy.mean())],
                        'bbox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]})
    return labels,sorted(regions,key=lambda r:r['centroid'][0])


def summarize(folder,input_file,overlay_file):
    metadata=json.loads((folder/'sam.json').read_text())
    if metadata['input_sha256']!=digest(input_file):raise ValueError('SAM input mismatch')
    rgb=np.asarray(Image.open(input_file).convert('RGB')).copy()
    arm=np.asarray(Image.open(folder/'handwear.png').convert('L'))>0
    torso=np.asarray(Image.open(folder/'topwear.png').convert('L'))>0
    if arm.shape!=rgb.shape[:2] or torso.shape!=arm.shape:raise ValueError('SAM grid mismatch')
    labels,regions=components(arm)
    overlay=rgb.copy();colors=[np.array([235,75,80]),np.array([55,135,245])]
    for i,row in enumerate(regions):
        m=labels==row['label'];overlay[m]=(.45*overlay[m]+.55*colors[i%2]).astype('uint8')
    Image.fromarray(overlay).save(overlay_file)
    return {'image_sha256':digest(input_file),'sam_metadata_sha256':digest(folder/'sam.json'),
            'arm_mask_sha256':digest(folder/'handwear.png'),'torso_mask_sha256':digest(folder/'topwear.png'),
            'arm_pixels':int(arm.sum()),'substantial_arm_components':len(regions),'components':regions,
            'arm_torso_overlap_pixels':int((arm&torso).sum()),
            'minimum_component_pixels':max(32,int(arm.sum()*.05)),
            'side_assignment':'image-space ordering only; not verified anatomical ownership',
            'joints':'SAM does not separate shoulder, upper arm, elbow, forearm, wrist or hand',
            'hidden_anatomy_verified':False}


def evaluate(run,selection,output,runner=subprocess.run):
    store=Store(run);fd=store.gpu_lock()
    try:
        analyze(run,selection,output)  # Validates the saved human selection before any inference.
        output=output.resolve();state=store.state()
        selection_file=store.safe('selections/'+selection+'/selection.json')
        selected=json.loads(selection_file.read_text())['selected']
        source=Image.open(store.safe(state['source']['path']));baselines={};results={};cards=[]
        baseline_label='Canonical synthetic base' if state.get('canonical_origin') else 'Original'
        if state.get('canonical_origin'):
            store.verify_pins(state,producer=False)
        def infer(file,folder):
            with (output/(folder.name+'.log')).open('x') as log:
                runner([str(REPO/'backends/see-through/.venv/bin/python'),str(REPO/'backends/see-through/worker.py'),
                        '--input',str(file),'--output',str(folder),'--sam'],cwd=REPO,stdout=log,
                       stderr=subprocess.STDOUT,check=True,timeout=600,pass_fds=(fd,))
        for pose,row in selected.items():
            edge=row['config']['long_edge'];name='source-'+str(edge)
            if edge not in baselines:
                file=output/(name+'.png');fit(source,edge).save(file)
                infer(file,output/name)
                baselines[edge]=summarize(output/name,file,output/(name+'-arms.png'))
            file=store.safe('selections/'+selection+'/'+row['image'])
            if digest(file)!=row['sha256']:raise ValueError('Selected image changed before inference')
            folder=output/(pose+'-sam');infer(file,folder)
            result=summarize(folder,file,output/(pose+'-arms.png'))
            result['baseline_long_edge']=edge;result['human_approval_sha256']=row['approval']['image_sha256']
            results[pose]=result
            cards.append(f'<section><h2>{html.escape(pose)}</h2><p>{baseline_label} SAM / selected SAM. Colours identify disconnected arm-category components, not verified limb ownership.</p><div><img src="{name}-arms.png"><img src="{pose}-arms.png"></div><p><a href="{pose}.png">{baseline_label} / selected / unregistered difference panel</a></p></section>')
        report={'selection_sha256':digest(selection_file),'parser_lock_sha256':digest(REPO/'backends/see-through/models.lock.json'),
                'source_sha256':state['source']['sha256'],'baseline':baselines,'selected':results,
                'baseline_role':baseline_label,'identity_reference':state.get('identity_reference'),
                'canonical_origin':state.get('canonical_origin'),
                'scope':'Selected-only exploratory segmentation; generated pixels and mask labels are not anatomy truth',
                'threshold':'positive SAM logits; components >= max(32 pixels, 5 percent of arm mask)',
                'correspondence':'No pixel registration or hidden-clothing area measurement; generated pose proportions differ.'}
        write(output/'semantics.json',report)
        (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Selected auxiliary pose assessment</title><style>body{font:16px system-ui;margin:30px;background:#f3f2ed;color:#243c33}div{display:flex;gap:20px}img{width:48%;max-height:800px;object-fit:contain}p{max-width:1000px}</style><h1>Human-selected pose: exploratory semantic comparison</h1><p>Only approved auxiliary images were parsed. Disconnected components are not joints, depth or recovered source anatomy.</p>'+''.join(cards)+'<p><a href="semantics.json">Exact measurements and hashes</a></p>')
        return report
    finally:os.close(fd)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--selection',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();evaluate(a.run,a.selection,a.output)
