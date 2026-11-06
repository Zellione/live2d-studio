"""Standalone local pose reviewer. No coding agent, editor, ST or API dependency."""
import argparse
import fcntl
import json
from pathlib import Path
from live2d_studio.pose_review import initialize,Store
from live2d_studio.pose_review_server import make_server

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('init');a.add_argument('--input',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--presets',type=Path,required=True);a.add_argument('--rights',required=True)
    a=sub.add_parser('serve');a.add_argument('--run',type=Path,required=True);a.add_argument('--port',type=int,default=8795)
    a=sub.add_parser('generate');a.add_argument('--run',type=Path,required=True);a.add_argument('--pose',required=True);a.add_argument('--preset',required=True)
    a=sub.add_parser('add-preset');a.add_argument('--run',type=Path,required=True);a.add_argument('--name',required=True);a.add_argument('--config',type=Path,required=True)
    a=sub.add_parser('init-canonical');a.add_argument('--input',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--presets',type=Path,required=True);a.add_argument('--rights',required=True)
    a=sub.add_parser('init-from-canonical');a.add_argument('--canonical-run',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--presets',type=Path,required=True)
    args=p.parse_args()
    if args.command=='init':initialize(args.output,args.input,json.loads(args.presets.read_text()),args.rights)
    elif args.command=='init-canonical':initialize(args.output,args.input,json.loads(args.presets.read_text()),args.rights,workflow='canonical')
    elif args.command=='init-from-canonical':
        from live2d_studio.canonical_reference import initialize_helpers
        initialize_helpers(args.canonical_run,args.output,json.loads(args.presets.read_text()))
    elif args.command=='add-preset':Store(args.run).add_preset(args.name,json.loads(args.config.read_text()))
    elif args.command=='generate':
        store=Store(args.run);batch,fd=store.reserve(args.pose,args.preset)
        if not store.execute(batch,fd):raise SystemExit('Generation failed; inspect the retained batch worker.log')
    else:
        store=Store(args.run)
        with (store.root/'.server.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            server=make_server(store,args.port);print(f'Pose reviewer: http://127.0.0.1:{server.server_port}/',flush=True)
            try:server.serve_forever()
            finally:server.server_close()
if __name__=='__main__':main()
