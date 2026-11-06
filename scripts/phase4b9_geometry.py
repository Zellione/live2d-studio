"""Reproducible selected-family arm hypotheses; no rig authoring."""
import argparse
import json
from pathlib import Path
from live2d_studio.pose_family import load
from live2d_studio.pose_review import REPO,digest,write
from live2d_studio.arm_evidence import assess_image,compare


def run(family,sam,output):
 data=load(family);inference=json.loads((sam/'inference.json').read_text())
 if inference['family_sha256']!=digest(family/'family.json'):raise ValueError('Inference belongs to another family')
 output=output.resolve()
 if not output.is_relative_to(REPO/'runs') or output.is_relative_to(REPO/'runs/references'):raise ValueError('Fresh ignored output required')
 output.mkdir(parents=True,exist_ok=False)
 reports={pose:assess_image(family/row['path'],sam/pose,output/pose) for pose,row in data['images'].items()}
 report={'family_sha256':digest(family/'family.json'),'inference_sha256':digest(sam/'inference.json'),
         'algorithm_sha256':digest(REPO/'src/live2d_studio/arm_evidence.py'),'images':reports,'cross_pose':compare(reports)}
 write(output/'assessment.json',report);return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--family',type=Path,required=True);p.add_argument('--sam',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.family,a.sam,a.output)
