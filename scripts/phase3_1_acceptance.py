"""Standalone browser acceptance and matched comparison gallery; no ST server."""
import argparse
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import threading
import time
import urllib.request
from PIL import Image, ImageDraw
import numpy as np
from live2d_studio.preview_live import assets, Handler, DEFAULT_MODEL, DEFAULT_EXTENSION
from live2d_studio.manifest import write_json

REPO=Path(__file__).resolve().parents[1]
NAMES=['neutral','happy','sad','angry','surprised','confused','embarrassed']


def gallery(output):
    sheet=Image.new('RGB',(280*7,600),'#eee');draw=ImageDraw.Draw(sheet)
    metrics={}
    for row,variant in enumerate(['baseline','revised']):
        for col,name in enumerate(NAMES):
            im=Image.open(output/variant/f'face-{name}.png').convert('RGBA')
            crop=im.crop((190,115,430,355)).resize((280,280))
            sheet.paste(crop,(280*col,300*row+20),crop)
            draw.text((280*col+5,300*row+3),variant+' / '+name,fill='black')
            if row:
                old=np.array(Image.open(output/'baseline'/f'face-{name}.png'))
                new=np.array(im)
                metrics[name]=dict(face_changed_pixels=int(np.any(old[115:355,190:430]!=new[115:355,190:430],axis=2).sum()),head_locked=True)
    sheet.save(output/'faces.png')
    a=np.array(Image.open(output/'baseline/neutral.png'));b=np.array(Image.open(output/'revised/neutral.png'))
    metrics['neutral_full_frame_changed_pixels']=int(np.any(a!=b,axis=2).sum())
    html='''<!doctype html><meta charset="utf-8"><title>Girl2 expression review</title>
<style>body{font:16px system-ui;background:#f5f2eb;color:#273a33;margin:32px}img{max-width:100%}.pair{display:flex;gap:20px;flex-wrap:wrap}figure{margin:0}figure img{width:240px;background:#e8ece7}section{margin:24px 0}video{max-width:95%}</style>
<h1>Girl2 · Phase 3 / Phase 3.1</h1><p>Top: accepted baseline. Bottom: revised candidate. Facial comparison locks head X/Y/Z at zero, idle and physics paused; identical camera, scale and crop. Pixel differences are diagnostics, not emotion recognition scores. Human visual gate: requires review.</p><img src="faces.png"><h2>Portrait-size comparison</h2>'''
    for name in NAMES:
        html+=f'<section><h3>{name}</h3><div class="pair">'
        for variant in ['baseline','revised']:
            html+=f'<figure><img src="{variant}/face-{name}.png"><figcaption>{variant} · 240 px canvas</figcaption></figure>'
        html+='</div></section>'
    animation=[]
    for file in sorted((output/'revised').glob('transition-clip-*.png')):
        rgba=Image.open(file).convert('RGBA');bg=Image.new('RGBA',rgba.size,'#e8ece7');bg.alpha_composite(rgba)
        animation.append(bg.convert('RGB'))
    if animation:
        animation[0].save(output/'transitions.gif',save_all=True,append_images=animation[1:],duration=70,loop=0)
        html+='<h2>Live transition recording</h2><img src="transitions.gif" width="360"><p>Real browser frames, neutral → happy → angry. Capture timing is approximate.</p>'
    html+='<h2>Transitions and combined blink / talk</h2><p>Captured from continuous rendering; the live viewer supports further interactive inspection.</p><div class="pair">'
    for name in ['transition-1','transition-2','transition-3']+['combined-'+n for n in NAMES]:
        html+=f'<figure><img src="revised/{name}.png"><figcaption>{name}</figcaption></figure>'
    html+='</div>'
    (output/'index.html').write_text(html)
    write_json(output/'comparison.json',metrics)
    return metrics


def run(output, revised, chrome, cdp_port):
    output.mkdir(parents=True,exist_ok=False)
    log=(output/'chrome.log').open('w')
    browser=subprocess.Popen([chrome,'--headless=new',f'--user-data-dir={output}/chrome',
        '--remote-debugging-address=127.0.0.1',f'--remote-debugging-port={cdp_port}',
        '--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update',
        '--disable-sync','--enable-unsafe-swiftshader','--use-angle=swiftshader','--window-size=1280,1000','about:blank'],stdout=log,stderr=subprocess.STDOUT)
    try:
        endpoint=f'http://127.0.0.1:{cdp_port}'
        for _ in range(100):
            if browser.poll() is not None:raise RuntimeError('Dedicated browser exited; inspect chrome.log')
            try:
                urllib.request.urlopen(endpoint+'/json/version',timeout=1).close();break
            except OSError:time.sleep(.1)
        else:raise TimeoutError('Browser debugging endpoint unavailable')
        for name,model in [('baseline',DEFAULT_MODEL),('revised',revised)]:
            with ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,files=assets(model,DEFAULT_EXTENSION))) as server:
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                try:
                    with (output/(name+'.log')).open('w') as stream:
                        subprocess.run(['node','scripts/cdp_smoke.mjs',endpoint,f'http://127.0.0.1:{server.server_port}/',
                            'scripts/phase3_1_browser_scenario.js',str(output/name)],cwd=REPO,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=160)
                finally:server.shutdown();thread.join()
        metrics=gallery(output)
        if metrics['neutral_full_frame_changed_pixels']:
            raise RuntimeError('Candidate neutral differs from baseline; inspect comparison.json')
        print(json.dumps(metrics,indent=2))
    finally:
        browser.terminate()
        try:browser.wait(timeout=10)
        except subprocess.TimeoutExpired:browser.kill();browser.wait()
        log.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--revised',type=Path,default=Path('runs/phase3-1-final-v2/runtime/Generated_artwork.model3.json'))
    p.add_argument('--chrome',default='/opt/google/chrome/chrome')
    p.add_argument('--cdp-port',type=int,default=9232)
    a=p.parse_args();run(a.output.resolve(),a.revised.resolve(),a.chrome,a.cdp_port)
