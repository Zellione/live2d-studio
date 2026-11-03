import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from PIL import Image
from live2d_studio.manifest import digest,write_json,load_validate
from live2d_studio.facial_artwork import prepare,skin_surface,closed_lash


def fixture(root,colour=(185,150,125),offset=0,alpha=254,open_mouth=False):
    root.mkdir();size=90;source=np.zeros((size,size,4),np.uint8)
    source[8:82,8:82]=[*colour,alpha]
    roles=[('face','none'),('mouth','none')]+[(r,s) for s in ['left','right'] for r in ['eyewhite','irides','eyelash']]
    masks=[np.zeros((size,size),bool) for _ in roles];masks[0][8:82,8:82]=True
    masks[1][65,36+offset:53+offset]=True
    source[65,32+offset:57+offset]=[40,25,32,alpha]  # extra contour belongs to face initially
    if open_mouth:
        masks[1][60:72,32+offset:57+offset]=True;source[masks[1]]=[40,25,32,alpha]
    for side,x in [('left',22+offset),('right',55+offset)]:
        i=roles.index(('eyewhite',side));masks[i][30:42,x:x+15]=True
        source[masks[i]]=[245,240,235,alpha]
        masks[i+1][32:41,x+5:x+11]=True;source[masks[i+1]]=[70,80,95,alpha]
        masks[i+2][29:31,x:x+15]=True;source[masks[i+2]]=[25,25,30,alpha]
    # Last layer is the unique observed owner, as in restoration.
    owner=np.full((size,size),-1)
    for i,m in enumerate(masks):owner[m]=i
    for f in ['source','layers','masks','generated','semantic','uncertain','reconstructed']:(root/f).mkdir()
    Image.fromarray(source).save(root/'source/original.png')
    layers=[]
    for i,(role,side) in enumerate(roles):
        a=np.zeros_like(source);owned=owner==i;a[owned]=source[owned];obs=a[...,3]
        l=dict(id=f'random-{i}',role=role,side=side,name=role,x=0,y=0,width=size,height=size,z_order=i,
            source_id='source-0',default_visible=True,confidence=0,quality_status='generated-review',hidden_reconstruction_status='unlocalized',provenance=['synthetic'],
            observed_pixels=int(owned.sum()),generated_pixels=0)
        files=dict(rgba_path='layers',mask_path='masks',generated_mask_path='generated',semantic_mask_path='semantic',uncertain_mask_path='uncertain',reconstructed_mask_path='reconstructed')
        for key,arr in zip(files,(a,obs,np.zeros_like(obs),obs,(obs>0).astype(np.uint8)*255,np.zeros_like(obs))):
            l[key]=files[key]+f'/{i}.png';Image.fromarray(arr).save(root/l[key])
        l['sha256']={k:digest(root/l[k]) for k in files};layers.append(l)
    sh=digest(root/'source/original.png')
    write_json(root/'layer_manifest.json',dict(schema_version=2,canvas=dict(width=size,height=size),layers=layers,rig_ready=False,warnings=[],
        provenance=dict(unique_source_ownership=True),sources=[dict(rights='Test-owned synthetic artwork',id='source-0',path='source/original.png',normalized_path='source/original.png',sha256=sh,normalized_sha256=sh,
        normalization_transform=dict(kind='native-source-grid'))]))
    return root


class FacialArtworkTests(unittest.TestCase):
    def test_existing_open_mouth_art_is_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=fixture(root/'source',open_mouth=True)
            report=prepare(p,root/'a')
            self.assertEqual(report['changes'][-1]['strategy'],'retain-existing-open-source-mouth')
            self.assertFalse(any(v['feature']=='mouth' for v in report['alternatives']))
            self.assertEqual(report['fidelity']['exact_fraction'],1)

    def test_closed_lash_uses_source_colour_and_refuses_tiny_fragments(self):
        source=np.zeros((40,40,4),np.uint8);lash=np.zeros((40,40),bool)
        lash[12:15,10:30]=True;source[lash]=[24,35,43,254]
        skin=np.full((40,40,3),180,np.uint8)
        closed=closed_lash(source,lash,skin,(9,10,31,30))
        self.assertGreater((closed[...,3]>0).sum(),20)
        np.testing.assert_array_equal(np.unique(closed[closed[...,3]>0,:3],axis=0),[[24,35,43]])
        self.assertFalse((closed[:20,:,3]>0).any())
        lash[:]=False;lash[12:14,12]=True
        with self.assertRaisesRegex(ValueError,'Insufficient'):closed_lash(source,lash,skin,(9,10,31,30))

    def test_source_exact_unique_neutral_replay_and_palette(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=fixture(root/'source',colour=(95,175,125),offset=3)
            before={str(f):digest(f) for f in p.rglob('*') if f.is_file()}
            report=prepare(p,root/'a');prepare(p,root/'b')
            self.assertEqual(report['fidelity']['exact_fraction'],1)
            self.assertEqual(before,{str(f):digest(f) for f in p.rglob('*') if f.is_file()})
            self.assertEqual((root/'a/layer_manifest.json').read_bytes(),(root/'b/layer_manifest.json').read_bytes())
            data=load_validate(root/'a')
            self.assertTrue(data['provenance']['unique_source_ownership'])
            skin=np.array(Image.open(root/'a/alternatives/eye-left-skin.png'))
            np.testing.assert_array_equal(np.unique(skin[skin[...,3]>0,:3],axis=0),[[95,175,125]])
            self.assertFalse(report['additional_references']);self.assertTrue(report['requires_visual_review'])
            with self.assertRaises(FileExistsError):prepare(p,root/'a')

    def test_no_colour_evidence_or_ambiguous_eyes_refuses(self):
        with self.assertRaisesRegex(ValueError,'Insufficient'):
            skin_surface(np.zeros((8,8,4),np.uint8),np.zeros((8,8),bool),np.ones((8,8),bool))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=fixture(root/'source');d=load_validate(p)
            d['layers'][2]['role']='unknown';write_json(p/'layer_manifest.json',d)
            with self.assertRaisesRegex(ValueError,'Ambiguous facial role'):prepare(p,root/'a')
            self.assertFalse((root/'a').exists())

    def test_opaque_source_and_bounds_translate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=prepare(fixture(root/'s1',alpha=255),root/'a')
            b=prepare(fixture(root/'s2',offset=4,alpha=255),root/'b')
            self.assertEqual(a['fidelity']['exact_fraction'],1);self.assertEqual(b['fidelity']['exact_fraction'],1)
            for left,right in zip(a['changes'],b['changes']):self.assertEqual(left['bounds'][0]+4,right['bounds'][0])

if __name__=='__main__':unittest.main()
