"""Read-only standalone Cubism preview with a closed, preloaded asset allowlist."""
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from urllib.parse import urlsplit
import webbrowser

from .bundle import validate

REPO = Path(__file__).resolve().parents[2]
LIBS = ('live2dcubismcore.min.js', 'live2d.min.js', 'pixi.min.js', 'index.min.js')
DEFAULT_MODEL = REPO / 'runs/phase3-final/runtime/Generated_artwork.model3.json'
DEFAULT_EXTENSION = REPO / '.cache/phase3-st/data/default-user/extensions/Extension-Live2d'


def assets(model, extension):
    model, extension = Path(model).resolve(), Path(extension).resolve()
    if not model.is_file():
        raise ValueError(f'Missing Girl2 model: {model}. Restore the local Phase 3 bundle or use --model MODEL.model3.json; see docs/phase3-1-preview.md.')
    report = validate(model)
    if report['status'] != 'pass':
        raise ValueError('Invalid preview bundle: ' + '; '.join(report['errors']))
    result = {}
    def add(url, file):
        result[url] = (file.read_bytes(), mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
    add('/model/' + model.name, model)
    for name in report['files_sha256']:
        add('/model/' + name, model.parent / name)
    for name in LIBS:
        file = extension / 'lib' / name
        if not file.is_file():
            raise ValueError(f'Missing installed runtime: {file}. Use --extension DIRECTORY containing lib/; no runtime download is performed.')
        add('/lib/' + name, file)
    ui = Path(__file__).with_name('preview_ui')
    for name in ('index.html', 'viewer.js', 'style.css'):
        add('/' if name == 'index.html' else '/' + name, ui / name)
    result['/config.json'] = (json.dumps(dict(model='/model/' + model.name)).encode(), 'application/json')
    return result


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, files, **kwargs):
        self.files = files
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
            self.send_error(403, 'Use the printed loopback URL')
            return
        entry = self.files.get(urlsplit(self.path).path)
        if entry is None:
            self.send_error(404)
            return
        data, mime = entry
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self' 'unsafe-eval'; style-src 'self'; connect-src 'self'; img-src 'self' data: blob:; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def viewer_assets(model=None, extension=None):
    files = assets(model or DEFAULT_MODEL, extension or DEFAULT_EXTENSION)
    # The default opens the accepted baseline; the separate candidate is one click away.
    if model is None:
        candidate = REPO / 'runs/phase3-1-final-v2/runtime/Generated_artwork.model3.json'
        if candidate.is_file():
            extra = assets(candidate, extension or DEFAULT_EXTENSION)
            files.update({key.replace('/model/', '/candidate/'): value for key, value in extra.items() if key.startswith('/model/')})
            config = dict(model='/model/' + DEFAULT_MODEL.name, candidate='/candidate/' + candidate.name)
            files['/config.json'] = (json.dumps(config).encode(), 'application/json')
    return files


def serve(model=None, extension=None, port=8768, open_browser=True):
    files = viewer_assets(model, extension)
    with ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, files=files)) as server:
        url = f'http://127.0.0.1:{server.server_port}/'
        print(f'Girl2 live preview: {url}\nRead-only local preview. Ctrl+C stops the server.', flush=True)
        if open_browser:
            if not webbrowser.open(url):
                print('Browser could not be opened automatically. Open the URL above.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return dict(status='stopped')
