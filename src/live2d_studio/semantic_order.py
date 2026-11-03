"""Conservative eye compositing constraints, independent of character coordinates."""
from copy import deepcopy
from pathlib import Path
import shutil
from PIL import Image
from .manifest import load_validate,write_json,digest
from .preview import preview

EYE_ORDER = {'eyewhite':0,'irides':1,'eyelash':2}


def order_layers(layers):
    result=deepcopy(layers)
    changes=[]
    for side in ('left','right'):
        slots=[i for i,l in enumerate(result) if l['side']==side and l['role'] in EYE_ORDER]
        roles=[result[i]['role'] for i in slots]
        if len(roles)!=3 or set(roles)!=set(EYE_ORDER):
            # Incomplete/ambiguous eyes remain for the readiness gate, never guessed.
            continue
        before=[result[i]['id'] for i in slots]
        ordered=sorted([result[i] for i in slots],key=lambda l:EYE_ORDER[l['role']])
        if before!=[l['id'] for l in ordered]:
            changes.append(dict(side=side,before=before,after=[l['id'] for l in ordered]))
        for index,layer in zip(slots,ordered):
            result[index]=layer
    for index,layer in enumerate(result):
        layer['z_order']=index
    return result,changes


def order_eyes(project,output):
    project,output=Path(project),Path(output)
    data=deepcopy(load_validate(project))
    output.mkdir(parents=True,exist_ok=False)
    for folder in ('source','layers','masks','generated','semantic','uncertain','reconstructed'):
        shutil.copytree(project/folder,output/folder)
    (output/'preview').mkdir()
    data['layers'],changes=order_layers(data['layers'])
    data['provenance']['eye_order']='white-iris-lash-v1'
    write_json(output/'layer_manifest.json',data)
    write_json(output/'config.json',dict(algorithm='white-iris-lash-v1',changes=changes,
        parent_manifest_sha256=digest(project/'layer_manifest.json'),
        caveat='Compositing constraint, not independent semantic correctness. Raw model output retained.'))
    preview(output,data,Image.open(output/data['sources'][0]['normalized_path']))
    load_validate(output)
    return changes
