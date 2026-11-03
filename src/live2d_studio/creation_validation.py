"""Actual installed Core and standalone browser validation; no production server."""
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import threading
import time
import urllib.request

from .bundle import validate
from .manifest import write_json, digest
from .preview_live import assets, Handler

REPO = Path(__file__).resolve().parents[2]


def validate_runtime(model, output, extension, scenario=None):
    scenario = scenario or REPO/'scripts/phase4b_browser_scenario.js'
    report = validate(model)
    write_json(output/'integrity.json',report)
    if report['status'] != 'pass':
        raise ValueError('Runtime references failed')
    data = json.loads(model.read_text())
    result = subprocess.run(['node',str(REPO/'scripts/probe_core.cjs'),
        str(extension/'lib/live2dcubismcore.min.js'),str(model.parent/data['FileReferences']['Moc'])],
        text=True,capture_output=True,timeout=30)
    (output/'core.json').write_text(result.stdout)
    (output/'core.log').write_text(result.stderr)
    if result.returncode:
        raise RuntimeError('Installed Cubism Core rejected candidate; inspect core.json')
    chrome = Path('/opt/google/chrome/chrome')
    if not chrome.is_file():
        raise RuntimeError('Browser validation needs /opt/google/chrome/chrome')
    profile = output.parent/(output.name+'-browser-profile')
    with (output/'chrome.log').open('w') as log:
        browser = subprocess.Popen([str(chrome),'--headless=new',f'--user-data-dir={profile}',
            '--remote-debugging-address=127.0.0.1','--remote-debugging-port=0',
            '--no-first-run','--no-default-browser-check','--disable-background-networking',
            '--disable-component-update','--disable-sync','--enable-unsafe-swiftshader',
            '--use-angle=swiftshader','--window-size=1280,1000','about:blank'],stdout=log,stderr=subprocess.STDOUT)
        try:
            portfile = profile/'DevToolsActivePort'
            for _ in range(100):
                if browser.poll() is not None:
                    raise RuntimeError('Dedicated validation browser exited; inspect chrome.log')
                if portfile.is_file():break
                time.sleep(.1)
            else:raise TimeoutError('Browser debugging endpoint unavailable')
            port = int(portfile.read_text().splitlines()[0])
            endpoint = f'http://127.0.0.1:{port}'
            urllib.request.urlopen(endpoint+'/json/version',timeout=3).close()
            with ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,files=assets(model,extension))) as server:
                thread = threading.Thread(target=server.serve_forever,daemon=True)
                thread.start()
                try:
                    with (output/'browser.log').open('w') as stream:
                        result = subprocess.run(['node',str(REPO/'scripts/cdp_smoke.mjs'),endpoint,
                            f'http://127.0.0.1:{server.server_port}/',str(scenario),
                            str(output/'frames')],cwd=REPO,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
                    if result.returncode:
                        raise RuntimeError('Browser validation failed; inspect frames/result.json and browser.log')
                finally:
                    server.shutdown();thread.join()
        finally:
            browser.terminate()
            try:browser.wait(timeout=10)
            except subprocess.TimeoutExpired:browser.kill();browser.wait()
    from .visual_qa import review
    report = review(output/'frames',output/'review')
    browser_result = json.loads((output/'frames/result.json').read_text())['result']['value']
    if browser_result['status'] != 'pass':
        raise RuntimeError('Runtime behavior failed')
    report.update(decision='needs-visual-review',model_sha256=digest(model),
        geometry=browser_result['geometry'],required_review=[
            'blink','mouth','head_overlap','expressions','holes_contours','visible_limbs'])
    write_json(output/'quality.json',report)
