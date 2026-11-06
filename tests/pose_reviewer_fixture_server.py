"""Disposable browser QA server; explicitly synthetic and never a real review run."""
import sys
import argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from test_pose_reviewer import ReviewerTests,synthetic_worker,PRESET
from live2d_studio.pose_review import Store,initialize
from live2d_studio.pose_review_server import make_server

parser=argparse.ArgumentParser();parser.add_argument('--canonical',action='store_true');parser.add_argument('--gestures',action='store_true');args=parser.parse_args()
fixture=ReviewerTests();fixture.setUp();store=fixture.store
if args.canonical:store=initialize(fixture.folder/'canonical',fixture.source,{'test':PRESET},'Synthetic browser fixture',workflow='canonical')
if args.gestures:
    from test_canonical_gestures import CanonicalGestureTests,three_reference_worker
    fixture.tearDown();fixture=CanonicalGestureTests();fixture.setUp();store=fixture.store
    synthetic_worker=three_reference_worker
store.execute=lambda batch,fd:Store.execute(store,batch,fd,synthetic_worker)
server=make_server(store,8796)
print('SYNTHETIC browser fixture: http://127.0.0.1:8796/',flush=True)
try:server.serve_forever()
finally:server.server_close();fixture.tearDown()
