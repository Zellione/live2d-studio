"""Build a compact metrics record and local visual comparison from completed runs."""
import json
from pathlib import Path
from html import escape

ROOT=Path(__file__).resolve().parents[1]
RUNS=ROOT/'runs'


def read(relative):
    return json.loads((RUNS/relative).read_text())


def main():
    result=dict(schema_version=1,scope='Phase 2.5; two licensed artworks, one with coarse XCF GT',
        model_lock='backends/see-through/models.lock.json',
        input_hashes={name:read(f'phase2-5-{name}-neural/metrics.json')['input_sha256'] for name in ['wikipe','oga']},
        native_comparisons={name:read(f'phase2-5-audit/{name}-comparison'+('-visible' if name=='wikipe' else '')+'.json') for name in ['wikipe','oga']},
        oga_baseline=read('phase2-5-oga-baseline/coarse-evaluation.json'),
        oga_neural=read('phase2-5-oga-layers/coarse-evaluation-reviewed.json'),
        sam={name:read(f'phase2-5-{name}-sam-review/metrics.json') for name in ['wikipe','oga']},
        hardware={name:read(f'phase2-5-{name}-neural/metrics.json') for name in ['wikipe','oga']},
        replay=read('phase2-5-audit/replay.json'),
        rig_import=read('phase2-5-oga-build/import-validation.json'),
        animation=read('phase2-5-oga-browser/result.json')['result']['value']['parameters'],
        recommendation='Keep See-through opt-in; basic Girl2 rig demonstrated, cropped Wikipe-tan rejected.')
    summary=ROOT/'docs/benchmarks/phase2-5.json'
    if summary.exists():raise FileExistsError('Summary exists; review before replacing a measurement record')
    summary.parent.mkdir(exist_ok=True)
    summary.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    output=RUNS/'phase2-5-review'
    output.mkdir(exist_ok=False)
    blocks=[]
    for name,title,rights in [('wikipe','Wikipe-tan — rejected','Kasuga; CC BY-SA 3.0; Wikimedia Commons'),
                              ('oga','Girl2 — animated prototype','stevenburrow; CC0; OpenGameArt')]:
        figures=[]
        for file,label in [(f'../phase2-5-{name}-baseline/source/normalized.png','Original'),
                           (f'../phase2-5-{name}-baseline/preview/composite.png','Baseline composite (includes unknown)'),
                           (f'../phase2-5-{name}-layers/preview/composite.png','See-through composite'),
                           (f'../phase2-5-{name}-layers/preview/layers.png','Generated layer candidates')]:
            figures.append(f'<figure><a href="{file}"><img src="{file}"></a><figcaption>{label}</figcaption></figure>')
        blocks.append('<h2>'+title+'</h2><p>'+rights+'</p>'+''.join(figures))
    html='<!doctype html><meta charset="utf-8"><title>Phase 2.5 comparison</title><style>'\
         'body{font:16px sans-serif;background:#eee;margin:24px}figure{display:inline-block;vertical-align:top;margin:10px}'\
         'img{max-width:350px;max-height:400px;background:repeating-conic-gradient(#ccc 0% 25%,white 0% 50%) 0/16px 16px}'\
         'pre{white-space:pre-wrap}.poses{max-width:100%;max-height:none}</style>'\
         '<h1>Phase 2.5 — local comparison</h1><p>Coverage is not semantic correctness. All neural pixels are generated; '\
         'hidden-only provenance is unavailable. The neutral baseline keeps unknown original pixels.</p>'
    html+=''.join(blocks)+'<h2>Actual isolated SillyTavern poses</h2>'\
          '<img class="poses" src="../phase2-5-oga-browser/pose-review.png">'\
          '<p>Procedural PSD2Live blink/mouth/head prototype; neck seam and simplified facial motion remain.</p>'\
          '<h2>Measured comparison</h2><pre>'+escape(json.dumps(result['native_comparisons'],indent=2))+'</pre>'
    (output/'index.html').write_text(html)


if __name__=='__main__':main()
