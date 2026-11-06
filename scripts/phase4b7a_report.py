"""Collect the two pose-study galleries and compact, hash-bound benchmark."""
import argparse
import html
import json
from pathlib import Path

from phase4b7a_poses import digest, dump


def collect(root, primary, lower, benchmark, audit=None):
    records=[]
    batches=[]
    hashes={}
    for label,run,subdir in [('primary',primary,'primary'),('lower-strength',lower,'lower')]:
        report_file=run/'report.json'
        analysis_file=root/subdir/'analysis.json'
        generation=json.loads(report_file.read_text())
        analysis=json.loads(analysis_file.read_text())
        if analysis['generation_report_sha256'] != digest(report_file):
            raise ValueError('Analysis belongs to a different generation report')
        decisions={r['id']:r for r in analysis['poses']}
        hashes[str(report_file)]=digest(report_file)
        hashes[str(analysis_file)]=digest(analysis_file)
        batches.append(dict(label=label,run=str(run),load_seconds=generation['load_seconds'],
                            batch_wall_seconds=generation['total_seconds'],
                            neutral_control_accepted=analysis['neutral_control_accepted']))
        for task in generation['tasks']:
            name=task['task']['id'];review=decisions[name]['decision']
            records.append(dict(batch=label,id=name,decision=review['decision'],
                visually_plausible=review['visually_plausible_pose_edit'],
                segmentation_helpful=review['segmentation_helpful_accepted'],
                reliable_articulation_evidence=review['reliable_articulation_evidence'],
                summary=review['summary'],usefulness=review['usefulness'],
                seconds=task['seconds'],max_allocated_bytes=task['max_allocated_bytes'],
                max_reserved_bytes=task['max_reserved_bytes'],
                composite_sha256=task['composite_sha256'],raw_sha256=task['raw_sha256'],
                reused_from=task.get('reused_from'),
                outside_composite_changed=task['outside_composite_changed'],
                raw_outside_mae=task['raw_outside_mae'],
                delta=decisions[name]['delta'],semantic=decisions[name]['semantic']))
    base=json.loads((root/'primary/analysis.json').read_text())
    result=dict(schema_version=1,phase='4B.7a',baseline_commit='6205158',
        status='feasibility-study-complete-no-promotion',source_reference='codel-combined-v1',
        source_sha256='98589fb8750ccfc3664935985fc42810381b2e09f22e1ae8cf4cd6dd45d39a2d',
        model_lock_sha256=digest(Path('backends/inpainting/models.lock.json')),
        model=generation['model'],encoder=generation['encoder'],gpu=generation['gpu'],
        torch=generation['torch'],cuda=generation['cuda'],
        baseline_semantic=base['baseline_semantic'],
        frozen_decomposition_arms=base.get('frozen_decomposition_arms'),
        original_source_copy_matches=(digest(root/'primary/original.png') ==
            '98589fb8750ccfc3664935985fc42810381b2e09f22e1ae8cf4cd6dd45d39a2d'),
        default_changes=False,training=False,downloads=False,
        production_access=False,arm_rig_built=False,user_approval=False,
        batches=batches,poses=records,evidence_sha256=hashes,
        accepted_exploratory=sum(r['decision']=='accept-exploratory' for r in records),
        segmentation_helpful=sum(r['segmentation_helpful'] for r in records),
        articulation_reliable=sum(r['reliable_articulation_evidence'] for r in records),
        measurements='Torch allocation/reservation peaks; no whole-device peak claim. Reused timings belong to original producers.',
        limitations=['one character, one seed, one quantization, 528x1024, two strengths',
            'body envelope clips some hands and produces visible composite seams',
            'protected face is not evidence of model identity preservation',
            'no independent hidden anatomy or pose ground truth',
            'same-grid voting cannot establish trustworthy hidden reconstruction'])
    if audit:
        names=['python-tests-recovered.log','pose-tests-final.log','reference-before.log',
               'reference-after.log','js-tests.log','sealed-baseline-preservation.json',
               'gallery-links.json','interruption.json','evidence-inventory.json']
        result['validation_evidence_sha256']={str(audit/name):digest(audit/name) for name in names}
    dump(benchmark,result)
    dump(root/'benchmark.json',result)
    rows=[]
    for r in records:
        rows.append('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in
            [r['batch']+'/'+r['id'],r['decision'],r['visually_plausible'],r['segmentation_helpful'],
             r['reliable_articulation_evidence'],r['summary'],r['usefulness']])+'</tr>')
    assessment=(f"{result['accepted_exploratory']} of {len(records)} images pass limited consistency screening; "
                f"{result['segmentation_helpful']} are judged segmentation-helpful; "
                f"{result['articulation_reliable']} supply reliable articulation evidence.")
    conclusion=('No demonstrated articulation benefit in this configuration.'
                if not result['segmentation_helpful'] else
                'Exploratory helper structures require further validation before articulation.')
    (root/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Phase 4B.7a — Codel Qwen pose study</title>
    <style>body{font:16px system-ui;max-width:1400px;margin:30px auto;padding:0 20px;background:#20232b;color:#eee}a{color:#aadeff}table{border-collapse:collapse}td,th{padding:10px;text-align:left;border:1px solid #606570}img{max-width:100%}p{max-width:1000px}</style>
    <h1>Codel: can auxiliary Qwen poses help arm articulation?</h1>
    <p><b>'''+html.escape(conclusion)+'''</b> '''+html.escape(assessment)+'''
    Next: evaluate explicit pose guidance and better edit-mask coverage before attempting an arm rig.</p>
    <p><b>Exploratory evidence only.</b> Each image is screened for consistency before segmentation.
    A plausible pose, useful segmentation and reliable articulation evidence are separate gates.
    The frozen Codel reference and default creation behavior remain unchanged.</p>
    <p>Original artwork: LisadiKaprio, <a href="https://opengameart.org/content/codel-visual-novel-sprite">Codel Visual Novel Sprite</a>, CC BY 4.0.
    All generated images are uncertain derivatives. The original flat image is the sole generation reference.</p>
    <p><a href="primary/index.html">Six required poses: source / composite / raw / change overlays</a> ·
    <a href="lower/index.html">Lower-strength controls</a> · <a href="primary/frozen-arm-layer.png">Frozen unsided arm layer</a> ·
    <a href="primary/reviewed-runtime-neutral.png">Frozen reviewed runtime capture</a> · <a href="benchmark.json">Full measurements</a></p>
    <p>Face equality is imposed by the mask. Magenta change is not recovered anatomy. Rejected images do not contribute downstream proposals.
    Proposed hidden clothing remains generated; no arm rig or user acceptance follows from this study.</p>
    <table><tr><th>Pose</th><th>Screening</th><th>Plausible</th><th>Segmentation helpful</th><th>Articulation reliable</th><th>Finding</th><th>Contribution</th></tr>'''+''.join(rows)+'''</table>
    <h2>Required family</h2><a href="primary/index.html"><img src="primary/contact-sheet.jpg"></a>
    <h2>Lower-strength controls</h2><a href="lower/index.html"><img src="lower/contact-sheet.jpg"></a>''')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','primary','lower','benchmark'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--audit',type=Path)
    a=p.parse_args();collect(a.root,a.primary,a.lower,a.benchmark,a.audit)
