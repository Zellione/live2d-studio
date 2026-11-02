"""Serve only the selected bundle and installed runtime libraries on loopback."""
import argparse
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlsplit

LIBS = ['live2dcubismcore.min.js', 'live2d.min.js', 'pixi.min.js', 'index.min.js', 'extra.min.js']


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, extension, model, **kwargs):
        self.extension, self.model = extension, model
        super().__init__(*args, **kwargs)

    def do_GET(self):
        request = unquote(urlsplit(self.path).path)
        if request == '/':
            content = Path(__file__).with_name('runtime_smoke.html').read_text()
            content = content.replace('MODEL_URL', json.dumps('/model/' + self.model.name))
            data, mime = content.encode(), 'text/html; charset=utf-8'
        else:
            if request.startswith('/lib/') and request[5:] in LIBS:
                target = self.extension / 'lib' / request[5:]
            elif request.startswith('/model/'):
                target = (self.model.parent / request[7:]).resolve()
                if not target.is_relative_to(self.model.parent):
                    self.send_error(403)
                    return
            else:
                self.send_error(404)
                return
            if not target.is_file():
                self.send_error(404)
                return
            data = target.read_bytes()
            mime = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extension', required=True, type=Path)
    parser.add_argument('--model', required=True, type=Path)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    for lib in LIBS:
        if not (args.extension / 'lib' / lib).is_file():
            parser.error(f'Missing installed library: {lib}')
    if not args.model.is_file():
        parser.error('Missing model JSON')
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(
        Handler, extension=args.extension.resolve(), model=args.model.resolve()))
    print(f'Runtime-only test: http://127.0.0.1:{server.server_port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
