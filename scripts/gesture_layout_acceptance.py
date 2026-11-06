"""Real page-zoom/layout/click checks using an isolated Chrome profile and Core."""
import argparse
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import threading
import time

from live2d_studio.preview_live import viewer_assets, Handler, REPO
from live2d_studio.elbow_rig import frozen_reference
from live2d_studio.manifest import write_json,digest
from live2d_studio.stages import inventory,verify


def run(output):
    output=output.resolve()
    if not output.is_relative_to(REPO/'runs'):raise ValueError('Ignored output required')
    output.mkdir(parents=True,exist_ok=False)
    root,_=frozen_reference(REPO/'docs/references/codel-frontal-elbows-v1.json')
    model=root/'runtime/Generated_artwork.model3.json';before=inventory(root)
    single=viewer_assets(model);comparison=viewer_assets(model,comparison=model)
    old=dict(comparison)
    for url,name in [('/','index.html'),('/style.css','style.css')]:
        old[url]=(subprocess.check_output(['git','show','98e7cc3:src/live2d_studio/preview_ui/'+name]),comparison[url][1])
    servers=[];threads=[]
    try:
        for files in [single,comparison,old]:
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,files=files))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            servers.append(server);threads.append(thread)
        profile=output/'browser-profile'
        with (output/'chrome.log').open('w') as log:
            browser=subprocess.Popen(['/opt/google/chrome/chrome','--headless=new',f'--user-data-dir={profile}',
                '--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','--no-first-run',
                '--no-default-browser-check','--disable-background-networking','--disable-component-update',
                '--disable-sync','--enable-unsafe-swiftshader','--use-angle=swiftshader','--window-size=1440,1000',
                'about:blank'],stdout=log,stderr=log)
            try:
                for _ in range(100):
                    if browser.poll() is not None:raise RuntimeError('Dedicated browser exited')
                    if (profile/'DevToolsActivePort').is_file():break
                    time.sleep(.1)
                port=(profile/'DevToolsActivePort').read_text().splitlines()[0]
                with (output/'browser.log').open('w') as stream:
                    subprocess.run(['node',str(REPO/'tests/test_gesture_layout.mjs'),f'http://127.0.0.1:{port}',
                        *[f'http://127.0.0.1:{s.server_port}/' for s in servers],str(output)],
                        stdout=stream,stderr=stream,check=True,timeout=240)
            finally:
                browser.terminate()
                try:browser.wait(timeout=10)
                except subprocess.TimeoutExpired:browser.kill();browser.wait()
        verify(root,before)
        write_json(output/'preservation.json',{'reference_files_verified':len(before),
            'model_sha256':digest(model),'viewer_js_sha256':digest(REPO/'src/live2d_studio/preview_ui/viewer.js'),
            'assets_unchanged':True})
    finally:
        for server,thread in zip(servers,threads):server.shutdown();thread.join();server.server_close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    run(p.parse_args().output)
