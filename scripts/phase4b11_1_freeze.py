"""Freeze the reviewed elbow experiment; no editor or source mutation."""
from pathlib import Path
import json, shutil
from live2d_studio.elbow_rig import frozen_reference
from live2d_studio.manifest import digest,write_json
from live2d_studio.stages import inventory,verify

REPO=Path(__file__).resolve().parents[1]

def freeze():
    candidate=REPO/'runs/phase4b11-bilateral-v2';rig=candidate/'rig'
    parent,_=frozen_reference(REPO/'docs/references/codel-frontal-prototype-v1.json')
    review=json.loads((candidate/'user-review.json').read_text())
    benchmark=json.loads((REPO/'docs/benchmarks/phase4b11.json').read_text())
    if digest(candidate/'user-review.json')!=benchmark['review']['sha256'] or review['reviewer_kind']!='human' or review['decision']!='accept':
        raise ValueError('Exact human acceptance missing')
    for name,h in review['files'].items():
        p=(REPO/name).resolve()
        if not p.is_relative_to(REPO/'runs') or digest(p)!=h:raise ValueError('Reviewed payload changed')
    root=REPO/'runs/references/codel-frontal-elbows-v1'
    if root.exists():raise ValueError('Reference already exists; never repin')
    root.mkdir(parents=True)
    for src,dst in [(parent/'layers',root/'layers'),(parent/'master',root/'master'),(rig/'exported/runtime',root/'runtime')]:shutil.copytree(src,dst)
    (root/'authoring').mkdir()
    for p in (rig/'authoring').iterdir():
        if p.is_file() and p.name!='editor-snapshot.psd2live':shutil.copyfile(p,root/'authoring'/p.name)
    shutil.copyfile(rig/'exported/character.psd',root/'authoring/character.psd')
    shutil.copyfile(rig/'exported/mouth-contract.json',root/'authoring/mouth-contract.json')
    for side,base in [('right',REPO/'runs/phase4b11-overlap-v2/rig'),('left',rig)]:
        shutil.copytree(base/'overlap',root/'overlaps'/side)
        dest=root/'provenance'/side;dest.mkdir(parents=True)
        for name in ['elbow-inspection.json','rotation-inspection.json','overlap-inspection.json']:
            shutil.copyfile(base/'authoring'/name,dest/name)
    shutil.copyfile(candidate/'joints.json',root/'provenance/joints.json')
    shutil.copyfile(candidate/'user-review.json',root/'user-review.json')
    for name in ['preservation-final.json','user-gap-rejection.json']:
        shutil.copyfile(REPO/'runs/phase4b11-audit'/name,root/'provenance'/name)
    contract={'source_project_sha256':digest(parent/'authoring/character.psd2live'),
              'layer_manifest_sha256':digest(parent/'layers/layer_manifest.json'),
              'method':'native-rotation-v1','degrees':120,'shoulder_fraction':.15,'sides':{}}
    joints=json.loads((candidate/'joints.json').read_text())
    for side in ['right','left']:
        contract['sides'][side]={'elbow':joints['arms'][side]['elbow'],
            'overlap_sha256':digest(root/'overlaps'/side/'sleeve-overlap.png')}
    write_json(root/'provenance/approved-arm-contract.json',contract)
    files=inventory(root)
    manifest={'reference_name':root.name,'kind':'reviewed-limited-frontal-elbow-reference','candidate':str(candidate.relative_to(REPO)),
              'files':files,'user_review':'user-review.json','approved_arm_contract':'provenance/approved-arm-contract.json',
              'limits':['880 changed neutral-render pixels against previous frontal reference','Synthetic joints/hidden shapes are not independently verified anatomy','No wrist/finger articulation or deployment'],
              'production_deployment':False}
    write_json(root/'manifest.json',manifest);verify(root,files)
    pin={'reference_name':root.name,'reference_root':str(root.relative_to(REPO)),'manifest_sha256':digest(root/'manifest.json'),
         'payload_files':len(files),'model':'runtime/Generated_artwork.model3.json','editable_project':'authoring/character.psd2live',
         'layered_psd':'authoring/character.psd','user_review_sha256':digest(root/'user-review.json'),
         'approved_arm_contract_sha256':digest(root/'provenance/approved-arm-contract.json'),
         'neutral_reference_changed_pixels':880,'status':'accepted-limited-elbow-reference','production_deployment':False}
    write_json(REPO/'docs/references/codel-frontal-elbows-v1.json',pin)
    for p in root.rglob('*'):
        if p.is_file():p.chmod(0o444)
    for p in sorted([p for p in root.rglob('*') if p.is_dir()],key=lambda p:len(p.parts),reverse=True):p.chmod(0o555)
    root.chmod(0o555);print(json.dumps(pin,indent=2))

if __name__=='__main__':freeze()
