import json,tempfile,unittest
from pathlib import Path
import numpy as np
from PIL import Image
from live2d_studio.frontal_face import repair
from live2d_studio.manifest import digest,write_json,load_validate
from live2d_studio.preview import preview
from live2d_studio.pose_review import REPO


class FrontalBrowTests(unittest.TestCase):
    def test_neutral_preserved_while_stationary_brow_ink_is_removed(self):
        with tempfile.TemporaryDirectory(dir=REPO/'runs') as tmp:
            root=Path(tmp);project=root/'before';project.mkdir()
            for folder in ('layers','masks','generated','semantic','uncertain','reconstructed','source','preview'):(project/folder).mkdir()
            source=np.full((90,90,4),[240,220,200,255],np.uint8)
            source[24:27,18:36]=[55,35,25,255];source[24:27,54:72]=[55,35,25,255]
            owner=np.zeros((90,90),int);owner[24:27,22:33]=1;owner[24:27,58:69]=2
            Image.fromarray(source).save(project/'source/original.png');h=digest(project/'source/original.png');layers=[]
            for i,(role,side) in enumerate([('face','none'),('eyebrow','left'),('eyebrow','right')]):
                a=np.zeros_like(source);a[owner==i]=source[owner==i];obs=a[...,3]
                row=dict(id='test-'+str(i),name=role,role=role,side=side,z_order=i,x=0,y=0,width=90,height=90,source_id='s',default_visible=True,confidence=0,quality_status='generated-review',hidden_reconstruction_status='unlocalized',provenance=['synthetic-fixture'])
                for key,folder,arr in [('rgba_path','layers',a),('mask_path','masks',obs),('generated_mask_path','generated',obs*0),('semantic_mask_path','semantic',obs),('uncertain_mask_path','uncertain',obs),('reconstructed_mask_path','reconstructed',obs*0)]:
                    row[key]=folder+'/'+str(i)+'.png';Image.fromarray(arr).save(project/row[key])
                row['sha256']={k:digest(project/v) for k,v in row.items() if k.endswith('_path')};layers.append(row)
            data=dict(schema_version=2,canvas=dict(width=90,height=90),layers=layers,sources=[dict(id='s',path='source/original.png',sha256=h,normalized_path='source/original.png',normalized_sha256=h,rights='synthetic test')],provenance={'unique_source_ownership':True},warnings=[])
            write_json(project/'layer_manifest.json',data);before=preview(project,data,Image.fromarray(source))
            report=repair(project,root/'after');after=load_validate(root/'after')
            np.testing.assert_array_equal(before,np.array(Image.open(root/'after/preview/composite.png')))
            face=after['layers'][0];pixels=np.array(Image.open(root/'after'/face['rgba_path']))
            np.testing.assert_array_equal(pixels[25,20,:3],[240,220,200])
            self.assertGreater(sum(r['source_pixels_transferred'] for r in report),0)
            self.assertEqual(digest(project/'source/original.png'),h)
            with self.assertRaisesRegex(ValueError,'Fresh'):repair(project,root/'after')

if __name__=='__main__':unittest.main()
