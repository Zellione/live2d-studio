"""Guarded loopback-only reviewer with a fixed asset allowlist."""
import json
import secrets
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from .pose_review import Store,REASONS

STATIC=Path(__file__).with_name('pose_review_web')


def make_server(store,port=8795):
    token=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup();self.connection.settimeout(10)
        def log_message(self,*args):pass
        def guard(self,post=False):
            allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
            host=self.headers.get('Host','')
            if host not in allowed:raise ValueError('Invalid Host')
            origin=self.headers.get('Origin')
            if (origin is not None and origin!='http://'+host) or (post and origin!='http://'+host):raise ValueError('Invalid Origin')
            if self.headers.get('Sec-Fetch-Site')=='cross-site':raise ValueError('Cross-site request refused')
            if post and not secrets.compare_digest(self.headers.get('X-Review-CSRF',''),token):raise ValueError('Missing request token')
        def send(self,status,data,kind='application/json'):
            body=json.dumps(data).encode() if kind=='application/json' else data
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers();self.wfile.write(body)
        def do_GET(self):
            try:
                self.guard()
                if self.path=='/api/state':
                    data=store.state();data['csrf']=token
                    data['reasons']=REASONS+(['not frontal','shoulders hidden','arms overlap','non-neutral expression'] if data.get('workflow')=='canonical' else [])
                    self.send(200,data)
                elif self.path in ('/','/app.js','/style.css'):
                    name={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[self.path]
                    kind={'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8'}[self.path]
                    self.send(200,(STATIC/name).read_bytes(),kind)
                elif self.path.startswith('/asset/') and '%' not in self.path and '?' not in self.path:
                    self.send(200,store.asset(self.path[7:]).read_bytes(),'image/png')
                else:self.send(404,{'error':'Not found'})
            except (ValueError,KeyError,OSError,json.JSONDecodeError) as exc:self.send(400,{'error':str(exc)})
        def do_POST(self):
            try:
                self.guard(post=True)
                if self.path!='/api/action':raise ValueError('Unknown endpoint')
                if self.headers.get('Content-Type')!='application/json':raise ValueError('JSON required')
                length=int(self.headers.get('Content-Length','0'))
                if not 1<=length<=16384:raise ValueError('Invalid request size')
                data=json.loads(self.rfile.read(length))
                if not isinstance(data,dict):raise ValueError('Expected object')
                action=data.get('action')
                if action=='generate':result={'batch':store.generate(data['pose'],data['preset'])}
                elif action=='resume':result={'batch':store.resume(data['batch'])}
                elif action in ('accept','reject','unsupported'):
                    result=store.decide(action,data['pose'],data.get('candidate'),str(data.get('reason','')),str(data.get('reviewer','local user')))
                elif action=='finish':result=store.finish(str(data.get('reviewer','local user')))
                else:raise ValueError('Invalid action')
                self.send(200,result)
            except (ValueError,KeyError,OSError,TypeError,json.JSONDecodeError) as exc:self.send(400,{'error':str(exc)})
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)
