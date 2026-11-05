"""Build an optional body candidate from a verified creation run, with no inference."""
import argparse,json
from live2d_studio.body_rig import prepare
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 print(json.dumps(prepare(a.baseline,a.output),indent=2))
