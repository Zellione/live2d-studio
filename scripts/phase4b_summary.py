"""Collect creation evidence and a local review gallery; never infer visual acceptance."""
import argparse
from html import escape
import json
import os
from pathlib import Path
from live2d_studio.manifest import write_json,digest


def collect(root):
    data=json.loads((root/'creation.json').read_text())
    record=dict(status=data['status'],input_sha256=data['identity']['input_sha256'],
                rights=data['identity']['rights'],stages={k:v['status'] for k,v in data['stages'].items()})
    ready=root/data['review_evidence']['semantic']
    q=json.loads(ready.read_text())
    record.update(fidelity=q['fidelity'],structural_semantics=q['structural_semantics'],
                  blocking_reasons=q['blocking_reasons'])
    inf=root/data['stages']['inference']['directory']
    if (inf/'worker/metrics.json').is_file():
        record['inference']=json.loads((inf/'worker/metrics.json').read_text())
    else:
        record['inference']=dict(reused_validated_bridge=True)
    validation=data['stages'].get('validation')
    if validation and validation['status']=='complete':
        v=root/validation['directory'];q=json.loads((v/'quality.json').read_text())
        record['runtime']=dict(geometry=q['geometry'],network=q['network'],render_status=q['render_status'],
            pose_count=len(q['poses']),max_hole_pixels=max(p['enclosed_transparent_pixels'] for p in q['poses'].values()),
            max_detached_pixels=max(p['detached_small_component_pixels'] for p in q['poses'].values()),
            model_sha256=q['model_sha256'])
        record['core']=json.loads((v/'core.json').read_text())
    for stage in ['semantic','visual']:
        review=root/'reviews'/(stage+'.json')
        if review.is_file():record[stage+'_review']=json.loads(review.read_text())
    return record,data


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--benchmark',type=Path,required=True)
    p.add_argument('--girl2',type=Path,default=Path('runs/phase4b-girl2-final'))
    p.add_argument('--sara',type=Path,default=Path('runs/phase4b-sara'))
    p.add_argument('--regressions',type=Path,default=Path('runs/phase4b-regression-eye-order/summary.json'))
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    records={};html=['<!doctype html><meta charset="utf-8"><title>Phase 4B review</title>',
        '<style>body{font:17px system-ui;margin:30px;background:#eee;color:#20332b}img{max-width:100%}section{margin:40px 0}a{color:#285c8c}</style>',
        '<h1>Phase 4B · working orchestration, incomplete independent visual acceptance</h1>',
        '<p>Girl2 is a regression prototype. Sara reached the standalone viewer automatically but is rejected for eye contours and inadequate mouth opening. No production installation. Numerical motion checks do not certify visual quality.</p>']
    for name,root in [('Girl2',a.girl2),('Sara',a.sara),('Boy2',Path('runs/phase4b-boy2')),
                      ('Hachi',Path('runs/phase4b-hachi')),('Hachi portrait',Path('runs/phase4b-hachi-portrait'))]:
        record,data=collect(root);records[name]=record
        def link(file):return escape(os.path.relpath(file,a.output),quote=True)
        restored=root/data['stages']['restore']['directory']/'layers'
        html += [f'<section><h2>{escape(name)} · {escape(record["status"])}</h2>',
            '<p>'+escape(record['rights'])+'</p>',
            '<p>'+escape('; '.join(record['blocking_reasons']))+'</p>',
            f'<a href="{link(restored/"preview/index.html")}">Source / masks / generated layers</a> · ',
            f'<a href="{link(root/data["review_evidence"]["semantic"])}">Semantic quality report</a>']
        validation=data['stages'].get('validation')
        if validation and validation['status']=='complete':
            v=root/validation['directory']
            html += [f'<p><a href="{link(v/"quality.json")}">Runtime quality report</a></p>',
                     f'<img src="{link(v/"review/poses.png")}" alt="Actual rendered poses">']
        else:
            html += [f'<p><img src="{link(restored/"preview/composite.png")}" width="420" alt="Restored candidate"></p>']
        html += ['</section>']
    regressions=json.loads(a.regressions.read_text())
    compact={k:dict(status=v['status'],fidelity=v['quality']['fidelity'],
                blocking_reasons=v['quality']['blocking_reasons'],
                independent_evaluation=v.get('independent_evaluation')) for k,v in regressions.items()}
    write_json(a.benchmark,dict(schema_version=1,base_commit='53ad920',
        primary_acceptance='not-met: independent runtime candidate rejected visually',
        scope='No production deployment; real local offline inference and installed Core/browser',
        characters=records,negative_regressions=compact,
        limitations=['No independently validated fine Sara masks or hidden anatomy',
                     'No new eyelid-skin/teeth/tongue raster generator',
                     'Framing excludes limbs absent from input; not full-body reconstruction']))
    (a.output/'index.html').write_text(''.join(html))
    print(a.output/'index.html')


if __name__=='__main__':main()
