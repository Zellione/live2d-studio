import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from live2d_studio.manifest import digest, load_validate, write_json
from live2d_studio.seethrough import import_decomposition, PINNED_SOURCE, MODEL_REVISIONS
from live2d_studio.refinement import refine, neck_repair, structural_review


class RefinementTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);b=self.root/'bridge';b.mkdir()
        src=np.zeros((24,24,4),np.uint8);src[3:21,3:21]=[220,180,150,255]
        src[8:15,8:15]=[20,40,80,255];src[3,3]=[220,180,150,90]
        Image.fromarray(src).save(self.root/'input.png');Image.fromarray(src).save(b/'normalized.png')
        base=np.zeros_like(src);base[3:21,3:21]=[190,140,100,255]
        front=np.zeros_like(src);front[8:15,8:15]=[10,20,60,255]
        layers=[]
        for i,(a,name) in enumerate([(base,'face'),(front,'front hair')]):
            Image.fromarray(a).save(b/f'{i}.png')
            layers.append(dict(name=name,path=f'{i}.png',x=0,y=0,z_order=i,opacity=255,blend_mode='BlendMode.NORMAL'))
        write_json(b/'decomposition.json',dict(format_version=1,order='back-to-front',canvas=dict(width=24,height=24),
            source_revision=PINNED_SOURCE,models=MODEL_REVISIONS,input_sha256=digest(self.root/'input.png'),
            normalized_path='normalized.png',transform=dict(kind='center-square-pad-resize',resolution=24),layers=layers))
        self.project=self.root/'parent'
        import_decomposition(self.root/'input.png',self.project,'test-owned',b)

    def test_exact_unique_copy_and_hidden_retention(self):
        out=self.root/'result';r=refine(self.project,out)
        self.assertEqual(r['fidelity']['exact_fraction'],1)
        data=load_validate(out);observed=np.zeros((24,24),int)
        for l in data['layers']:
            x,y,w,h=[l[k] for k in ('x','y','width','height')]
            observed[y:y+h,x:x+w]+=np.array(Image.open(out/l['mask_path']))>0
        self.assertEqual(observed.max(),1)
        face=data['layers'][0];a=np.array(Image.open(out/face['rgba_path']))
        self.assertEqual(a[10-face['y'],10-face['x']].tolist(),[190,140,100,255])
        self.assertEqual(a[3-face['y'],3-face['x']].tolist(),[220,180,150,90])
        self.assertFalse(data['rig_ready'])
        self.assertEqual(r['gates']['visual_animation'],'not-tested')
        self.assertGreater(r['uncertain_copied_samples'],0)

    def test_replay_no_overwrite_and_parent_immutable(self):
        before={str(p):digest(p) for p in self.project.rglob('*') if p.is_file()}
        refine(self.project,self.root/'a');refine(self.project,self.root/'b')
        self.assertEqual((self.root/'a/layer_manifest.json').read_bytes(),(self.root/'b/layer_manifest.json').read_bytes())
        self.assertEqual(before,{str(p):digest(p) for p in self.project.rglob('*') if p.is_file()})
        with self.assertRaises(FileExistsError):refine(self.project,self.root/'a')

    def test_sam_wrong_source_rejected_before_output(self):
        sam=self.root/'sam';sam.mkdir();write_json(sam/'sam.json',dict(input_sha256='wrong'))
        with self.assertRaisesRegex(ValueError,'different original'):refine(self.project,self.root/'out',sam)
        self.assertFalse((self.root/'out').exists())

    def test_unsupported_transform_rejected(self):
        data=load_validate(self.project);data['sources'][0]['normalization_transform']={'kind':'unknown'}
        write_json(self.project/'layer_manifest.json',data)
        with self.assertRaises(ValueError):refine(self.project,self.root/'out')

    def test_neck_repair_needs_connection_and_parser_support(self):
        a=np.zeros((40,40,4),np.uint8);a[:]=[130,70,200,255]
        a[3:12,12:25]=[230,190,160,255];a[12:17,17:21]=[230,190,160,255]
        a[17:23,13:26]=[230,190,160,255];a[30:34,10:15]=[230,190,160,255]
        owner=np.full((40,40),2,np.int16);owner[3:12,12:25]=0;owner[12:17,17:21]=1
        sam={'face':owner==0,'neck':owner==1};ls=[{'role':r} for r in ('face','neck','topwear')]
        changed=neck_repair(a,[],ls,owner,sam)
        self.assertTrue(changed[20,18]);self.assertFalse(changed[31,12]);self.assertFalse(changed[25,18])
        self.assertEqual(neck_repair(a,[],ls,owner,{}).sum(),0)

    def test_structural_face_failure_is_not_fixed_by_rgb(self):
        arrays=[np.zeros((20,20,4),np.uint8) for _ in range(2)]
        arrays[0][1:3,1:3,3]=255;arrays[1][10:12,10:12,3]=255
        r=structural_review(arrays,[{'role':'face'},{'role':'irides'}],np.zeros((20,20),int),{})
        self.assertEqual(r['status'],'rejected')
