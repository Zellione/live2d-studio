"""Disposable browser QA server; explicitly synthetic and never a real review run."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from test_pose_reviewer import ReviewerTests,synthetic_worker
from live2d_studio.pose_review import Store
from live2d_studio.pose_review_server import make_server

fixture=ReviewerTests();fixture.setUp();store=fixture.store
store.execute=lambda batch,fd:Store.execute(store,batch,fd,synthetic_worker)
server=make_server(store,8796)
print('SYNTHETIC browser fixture: http://127.0.0.1:8796/',flush=True)
try:server.serve_forever()
finally:server.server_close();fixture.tearDown()
