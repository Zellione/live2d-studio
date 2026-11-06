"""Export selected-only visual diagnostics; differences are not exposed anatomy."""
import argparse
import html
import json
from pathlib import Path
import numpy as np
from PIL import Image
from live2d_studio.pose_guides import fit
from live2d_studio.pose_review import Store,digest,write


def analyze(run,selection,output):
    store=Store(run);state=store.state();store.verify_pins(state,producer=False)
    record=next((r for r in state['exports'] if r['id']==selection),None)
    if record is None:raise ValueError('Unknown selected-set ID')
    manifest_file=store.safe('selections/'+selection+'/selection.json')
    if digest(manifest_file)!=record['sha256']:raise ValueError('Selection manifest changed')
    manifest=json.loads(manifest_file.read_text())
    if not manifest['selected']:raise ValueError('No human-selected images; no anatomical analysis is permitted')
    output=output.resolve()
    if not output.is_relative_to(store.root):raise ValueError('Diagnostics must stay in this review run')
    # Validate all selected evidence before creating an output directory.
    for pose,row in manifest['selected'].items():
        file=store.safe('selections/'+selection+'/'+row['image'])
        if digest(file)!=row['sha256'] or state['poses'][pose]['approval']!=row['approval']:
            raise ValueError('Selected evidence/approval changed')
    output.mkdir(parents=True,exist_ok=False)
    source=Image.open(store.safe(state['source']['path']));sections=[];report={}
    for pose,row in manifest['selected'].items():
        candidate=Image.open(manifest_file.parent/row['image']).convert('RGB')
        original=fit(source,row['config']['long_edge'])
        if candidate.size!=original.size:raise ValueError('Unexpected selected image dimensions')
        a=np.asarray(original).astype(float);b=np.asarray(candidate).astype(float)
        delta=np.max(abs(a-b),axis=2)/255
        overlay=(.65*b+.35*np.stack([255*delta,np.zeros_like(delta),255*(1-delta)],axis=2)).astype('uint8')
        panel=Image.new('RGB',(original.width*3,original.height),'white')
        panel.paste(original,(0,0));panel.paste(candidate,(original.width,0));panel.paste(Image.fromarray(overlay),(original.width*2,0));panel.save(output/(pose+'.png'))
        report[pose]={'image_sha256':row['sha256'],'visually_approved':True,'reviewer':row['approval'],
            'anatomically_plausible':'requires independent review','useful_articulation_evidence':'not established by pixel differences',
            'independently_verified_source_pixels':False,
            'checklist':['bilateral arm ownership','shoulders and elbows','wrists and fingers','sleeve boundaries',
                         'new torso coverage','occlusion/draw order','cross-pose anatomical contradictions'],
            'limitation':'Overlay detects repainting, displacement and exposure together; it cannot label hidden-region truth.'}
        sections.append(f'<h2>{html.escape(pose)}</h2><p>Original / selected synthetic image / difference overlay</p><img src="{pose}.png" style="max-width:100%">')
    write(output/'analysis.json',{'selection_sha256':record['sha256'],'poses':report})
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Selected pose diagnostics</title><h1>Human-selected auxiliary poses</h1><p>Generated anatomy remains unverified. Colour differences are not segmentation labels.</p>'+''.join(sections))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--selection',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();analyze(a.run,a.selection,a.output)
