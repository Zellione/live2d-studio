"""Reproduce a hash-checked elbow support diagnostic without changing references."""
import argparse
from pathlib import Path
from live2d_studio.elbow_rig import frozen_reference,propose,author,export_candidate
from live2d_studio.manifest import write_json
from live2d_studio.mcp import MCP
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--author',action='store_true');p.add_argument('--method',choices=['rotation','landmarks'],default='rotation');p.add_argument('--side',choices=['right','left'],default='right');p.add_argument('--degrees',type=float,default=120);p.add_argument('--overlap',action='store_true');p.add_argument('--predecessor',type=Path);a=p.parse_args()
root,_=frozen_reference('docs/references/codel-frontal-prototype-v1.json')
proposal=propose(root/'layers',Path('runs/phase4b9-family'),Path('runs/phase4b9-geometry-final/assessment.json'))
a.output.mkdir(parents=True,exist_ok=False);write_json(a.output/'joints.json',proposal)
if a.author:
    client=MCP('http://127.0.0.1:23871/mcp')
    author(client,root,proposal,a.output/'rig',a.side,a.degrees,a.method,a.overlap,a.predecessor)
    print(export_candidate(client,a.output/'rig',a.side,a.degrees))
