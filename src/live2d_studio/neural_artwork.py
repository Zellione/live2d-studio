"""Optional offline facial inpainting with exact hard-mask compositing.

Deterministic ownership stays authoritative. Inpainting can only replace generated
alternatives; no source layer or observed mask is rewritten by this module.
"""
import json
from pathlib import Path
import shutil
import subprocess
import os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from .manifest import digest, local_file, write_json, load_validate
from .facial_artwork import bounds

REPO = Path(__file__).resolve().parents[2]


def composite(source, prediction, mask):
    if source.shape != prediction.shape or mask.shape != source.shape[:2]:
        raise ValueError('Mismatched inpainting image/mask')
    result = source.copy()
    result[mask,:3] = prediction[mask,:3]
    return result


def crop_box(mask, context=1.5):
    x,y,x1,y1 = bounds(mask)
    margin = max(12,round(max(x1-x,y1-y)*context))
    return max(0,x-margin),max(0,y-margin),min(mask.shape[1],x1+margin),min(mask.shape[0],y1+margin)


def tasks(layers, output, *, scale=2, seed=1729, targets=None):
    """Use only the current single-image layer manifest, never benchmark tiles."""
    layers,output=Path(layers),Path(output)
    data=load_validate(layers)
    report=json.loads((layers/'facial-artwork.json').read_text())
    source=np.array(Image.open(local_file(layers,data['sources'][0]['normalized_path'])).convert('RGBA'))
    holes=np.array(Image.open(layers/'preview/reconstructed-skin.png'))>0
    variants={Path(v['path']).stem:v for v in report['alternatives']}
    output.mkdir(parents=True,exist_ok=False)
    requests=[];bindings=[]
    for name,v in variants.items():
        if v['source_pixels'] or v['kind'] not in ('skin','interior','closed-lash'):
            continue
        if targets is not None and name not in targets:
            continue
        original=np.array(Image.open(local_file(layers,v['path'])).convert('RGBA'))
        mask=(original[...,3]>0)
        context=source.copy()
        if v['kind']=='skin':
            mask &= holes
            prompt='Remove the eye or mouth line inside the edited area. Fill it with smooth continuous skin matching the surrounding anime face, same colors and shading. No new features, no lines, no texture.'
        else:
            skin_name=v['feature']+'-skin'
            backing=np.array(Image.open(layers/variants[skin_name]['path']).convert('RGBA'))
            support=backing[...,3]>0
            context[support]=backing[support]
            context=np.array(Image.alpha_composite(Image.fromarray(context),Image.fromarray(original)))
            if v['kind']=='closed-lash':
                mask=holes & support
                prompt='Refine this closed anime eyelid into one clean gently curved natural closed lash. Keep the eye completely closed. Preserve the exact character identity, thin linework, skin shading and art style. No extra contours.'
            else:
                prompt='Refine the small open anime mouth with subtle dark interior shading and natural lip transitions. Preserve the same mouth shape, size, character and drawn art style. No teeth, no tongue, no extra lines.'
        if not mask.any():
            continue
        box=crop_box(mask);x,y,x1,y1=box
        # Inference uses RGB, with the original alpha retained separately on output.
        rgb=np.array(Image.alpha_composite(Image.new('RGBA',(source.shape[1],source.shape[0]),'white'),Image.fromarray(context)))
        Image.fromarray(rgb[y:y1,x:x1]).save(output/(name+'.png'))
        Image.fromarray(mask[y:y1,x:x1].astype(np.uint8)*255).save(output/(name+'-mask.png'))
        boundary=ndi.binary_dilation(mask)&~ndi.binary_erosion(mask)
        Image.fromarray(boundary[y:y1,x:x1].astype(np.uint8)*255).save(output/(name+'-uncertain-boundary.png'))
        requests.append(dict(id=name,image=name+'.png',mask=name+'-mask.png',scale=scale,seed=seed,prompt=prompt,steps=20,cfg=4.0))
        bindings.append(dict(id=name,variant=v['path'],kind=v['kind'],box=list(box),
            baseline_sha256=digest(layers/v['path']),mask_sha256=digest(output/(name+'-mask.png'))))
    if not requests:
        raise ValueError('No supported generated facial alternatives to inpaint')
    if targets is not None and set(targets)-{r['id'] for r in requests}:
        raise ValueError('Requested alternatives unavailable; do not force an unsupported feature')
    write_json(output/'tasks.json',requests)
    write_json(output/'bindings.json',dict(single_image=True,source_sha256=digest(layers/data['sources'][0]['normalized_path']),
        facial_report_sha256=digest(layers/'facial-artwork.json'),bindings=bindings))
    return requests


def infer(requests, output, model):
    python=REPO/('backends/inpainting/.venv/bin/python' if model=='lama' else 'backends/inpainting/qwen-env/.venv/bin/python')
    if not python.is_file():
        raise RuntimeError('Missing isolated inpainting environment; see backends/inpainting/README.md')
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1')
    with Path(output).with_suffix('.log').open('w') as log:
        result=subprocess.run([str(python),str(REPO/'backends/inpainting/worker.py'),
            '--tasks',str(Path(requests).resolve()),'--output',str(Path(output).resolve()),'--model',model],
            env=env,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Inpainting failed; inspect '+str(log.name))


def reuse_predictions(request_dir,output,cache,model):
    """Copy an exact, pinned producer record; never claim a new inference execution."""
    cache=Path(cache).resolve()
    record=json.loads((cache/'report.json').read_text())
    if record['model']!=model or record['model_lock_sha256']!=digest(REPO/'backends/inpainting/models.lock.json'):
        raise ValueError('Cached model provenance mismatch')
    by_id={r['task']['id']:r for r in record['tasks']}
    for task in json.loads((request_dir/'tasks.json').read_text()):
        r=by_id[task['id']]
        if r['task']!=task:raise ValueError('Cached inference parameters changed')
        if r['image_sha256']!=digest(request_dir/task['image']) or r['mask_sha256']!=digest(request_dir/task['mask']):
            raise ValueError('Cached inference input changed')
        for key,file in [('raw_sha256','raw.png'),('composite_sha256','composite.png')]:
            if digest(local_file(cache,task['id']+'/'+file))!=r[key]:raise ValueError('Cached output changed')
        generated=np.array(Image.open(local_file(cache,task['id']+'/generated.png')).convert('L'))>0
        expected=np.array(Image.open(request_dir/task['mask']).convert('L'))>0
        if not np.array_equal(generated,expected):raise ValueError('Cached generated mask changed')
    output.mkdir()
    shutil.copyfile(cache/'report.json',output/'producer-report.json')
    requested={t['id'] for t in json.loads((request_dir/'tasks.json').read_text())}
    write_json(output/'report.json',dict(record,tasks=[r for r in record['tasks'] if r['task']['id'] in requested],
        reused=True,producer_report_sha256=digest(cache/'report.json')))
    for task in json.loads((request_dir/'tasks.json').read_text()):
        folder=output/task['id'];folder.mkdir()
        for file in ['raw.png','composite.png','generated.png']:
            shutil.copyfile(local_file(cache,task['id']+'/'+file),folder/file)
    write_json(output/'cache-reuse.json',dict(producer_report_sha256=digest(cache/'report.json'),
        inference_executed=False,producer_code_sha256=record.get('code_sha256')))


def install(layers, request_dir, prediction_dir, *, selected=None, blend=False):
    """Install only into a fresh deterministic stage; caller owns that directory."""
    layers,request_dir,prediction_dir=map(Path,(layers,request_dir,prediction_dir))
    bindings=json.loads((request_dir/'bindings.json').read_text())
    report=json.loads((layers/'facial-artwork.json').read_text())
    if digest(layers/'facial-artwork.json')!=bindings['facial_report_sha256']:
        raise ValueError('Neural results belong to different deterministic artwork')
    inference=json.loads((prediction_dir/'report.json').read_text())
    by_id={r['task']['id']:r for r in inference['tasks']}
    installed=[]
    for binding in bindings['bindings']:
        name=binding['id']
        if selected is not None and name not in selected:
            continue
        evidence=by_id[name]
        for field,filename in [('image_sha256',name+'.png'),('mask_sha256',name+'-mask.png')]:
            if evidence[field]!=digest(request_dir/filename):raise ValueError('Changed inpainting input')
        candidate=local_file(prediction_dir,name+'/composite.png')
        if evidence['composite_sha256']!=digest(candidate):raise ValueError('Changed neural prediction')
        if evidence['outside_mask_changed'] or evidence['alpha_changed']:raise ValueError('Inpainting changed protected pixels')
        path=local_file(layers,binding['variant'])
        if digest(path)!=binding['baseline_sha256']:raise ValueError('Changed baseline alternative')
        old=np.array(Image.open(path).convert('RGBA'));new=old.copy()
        x,y,x1,y1=binding['box'];mask=np.array(Image.open(request_dir/(name+'-mask.png')))>0
        rgb=np.array(Image.open(candidate).convert('RGBA'))
        input_pixels=np.array(Image.open(request_dir/(name+'.png')).convert('RGBA'))
        if rgb.shape!=input_pixels.shape or not np.array_equal(rgb[~mask],input_pixels[~mask]):
            raise ValueError('Neural prediction changed pixels outside its mask')
        if not np.array_equal(rgb[...,3],input_pixels[...,3]):raise ValueError('Neural prediction changed alpha')
        section=new[y:y1,x:x1]
        if blend:
            # Keep the deterministic boundary and use neural RGB only in the interior.
            alpha=np.clip((ndi.distance_transform_edt(mask)-1)/2,0,1)[...,None]
            background=section[...,:3]
            if binding['kind']=='closed-lash':
                # Transparent lash pixels have no skin RGB: use the separately
                # generated deterministic backing, never blend against black RGB.
                skin_path='alternatives/'+name.removesuffix('-closed')+'-skin.png'
                skin=np.array(Image.open(local_file(layers,skin_path)).convert('RGBA'))[y:y1,x:x1]
                background=np.array(Image.alpha_composite(Image.fromarray(skin),Image.fromarray(section)))[...,:3]
            rgb[...,:3]=np.rint(background*(1-alpha)+rgb[...,:3]*alpha).astype(np.uint8)
            mask &= alpha[...,0]>0
        section[mask,:3]=rgb[mask,:3]
        if binding['kind']=='closed-lash':
            # Closed artwork includes its generated skin patch, never copied source.
            section[mask,3]=255
        if np.any(new[y:y1,x:x1][~mask]!=old[y:y1,x:x1][~mask]):raise ValueError('Protected boundary changed')
        Image.fromarray(new).save(path)
        generated=np.zeros(old.shape[:2],np.uint8);generated[y:y1,x:x1]=mask.astype(np.uint8)*255
        mask_path='alternatives/'+name+'-neural-mask.png'
        boundary_path='alternatives/'+name+'-neural-boundary.png'
        Image.fromarray(generated).save(layers/mask_path)
        Image.fromarray((ndi.binary_dilation(generated>0)&~ndi.binary_erosion(generated>0)).astype(np.uint8)*255).save(layers/boundary_path)
        variant=next(v for v in report['alternatives'] if v['path']==binding['variant'])
        variant.update(sha256=digest(path),provenance='Local '+inference['model']+' masked inference; '+('deterministic boundary blend' if blend else 'hard composite'),
            uncertainty='Generated appearance, including boundary; not known anatomy',source_pixels=False,
            neural_mask_path=mask_path,neural_mask_sha256=digest(layers/mask_path),
            uncertain_boundary_path=boundary_path,uncertain_boundary_sha256=digest(layers/boundary_path))
        installed.append(dict(id=name,sha256=digest(path),generated_pixels=int(mask.sum())))
    if selected is not None and set(selected)-{v['id'] for v in installed}:
        raise ValueError('Reviewed selection contains unavailable features')
    report['neural']=dict(model=inference['model'],report_sha256=digest(prediction_dir/'report.json'),installed=installed,
        review_required=True,original_layers_unchanged=True,hybrid=blend)
    write_json(layers/'facial-artwork.json',report)
    return report


def reconstruct(layers, output, mode, config, review=None):
    config=json.loads(Path(config).read_text())
    if config.get('model') not in ('lama','qwen'):raise ValueError('Unsupported local inpainting model')
    selected=None
    if mode=='hybrid':
        if review is None:raise ValueError('Hybrid needs an exact-evidence review file')
        reviewed=json.loads(Path(review).read_text())
        if not reviewed.get('reviewer') or reviewed.get('decision')!='accept-selected':raise ValueError('Invalid hybrid review')
        selected=reviewed['selected']
        if not isinstance(selected,list) or len(set(selected))!=len(selected):raise ValueError('Invalid selected feature list')
        if not selected:
            write_json(output/'inpainting-fallback.json',dict(mode='deterministic',inference_executed=False,
                review_sha256=digest(review),reason='Review selected no neural features'))
            return json.loads((layers/'facial-artwork.json').read_text())
    tasks(layers,output/'requests',scale=config.get('scale',2),seed=config.get('seed',1729),targets=config.get('targets'))
    if config.get('prediction_cache'):
        reuse_predictions(output/'requests',output/'predictions',config['prediction_cache'],config['model'])
    else:
        infer(output/'requests/tasks.json',output/'predictions',config['model'])
    if mode=='hybrid' and reviewed.get('report_sha256')!=digest(output/'predictions/report.json'):
        # Timing is variable; bind to deterministic input and output image hashes instead.
        actual={r['task']['id']:{k:r[k] for k in ('image_sha256','mask_sha256','composite_sha256')} for r in json.loads((output/'predictions/report.json').read_text())['tasks']}
        if reviewed.get('images')!={k:actual[k] for k in selected}:raise ValueError('Hybrid review does not match exact regenerated evidence')
    return install(layers,output/'requests',output/'predictions',selected=selected,blend=mode=='hybrid')
