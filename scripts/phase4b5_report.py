"""Collect frozen Phase 4B.5 evidence and a self-contained local review gallery."""
import argparse
from collections import Counter
import html
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image, ImageDraw

from live2d_studio.manifest import digest, write_json
from live2d_studio.stages import verify

NAMES = ['neutral', 'happy', 'sad', 'angry', 'surprised', 'confused', 'embarrassed']


def read(file):
    return json.loads(Path(file).read_text())


def render_record(root):
    r = read(root/'frames/result.json')['result']['value']
    q = read(root/'quality.json')
    if r['status'] != 'pass' or not all(c['pass'] for c in r['checks']):
        raise ValueError('Failed render suite: ' + str(root))
    return dict(path=str(root), frames=len(r['frames']), geometry=r['geometry'],
                report_sha256=digest(root/'frames/result.json'), quality_sha256=digest(root/'quality.json'),
                max_holes=max(v['enclosed_transparent_pixels'] for v in q['poses'].values()),
                max_detached=max(v['detached_small_component_pixels'] for v in q['poses'].values()),
                network=q['network'])


def stage(root, state, key):
    s = state['stages'][key]
    directory = root/s['directory']
    verify(directory, s['files'])
    return directory


def creation_record(root):
    state = read(root/'creation.json')
    q = read(stage(root, state, 'readiness')/'quality.json')
    return dict(path=str(root), status=state['status'],
                timings_seconds={k: round(s['finished']-s['started'], 3) for k, s in state['stages'].items()},
                fidelity=q['fidelity'], parser_agreement=q['structural_semantics'],
                available_roles=q['available_roles'])


def face_box(layers, frame, role='face', padding=0):
    m = read(layers/'layer_manifest.json')
    l = next(l for l in m['layers'] if l['role'] == role)
    sb = Image.open(layers/m['sources'][0]['normalized_path']).getbbox()
    rb = Image.open(frame).getbbox()
    sx, sy = (rb[2]-rb[0])/(sb[2]-sb[0]), (rb[3]-rb[1])/(sb[3]-sb[1])
    return tuple(round(v) for v in (rb[0]+(l['x']-padding*l['width']-sb[0])*sx,
        rb[1]+(l['y']-padding*l['height']-sb[1])*sy,
        rb[0]+(l['x']+(1+padding)*l['width']-sb[0])*sx,
        rb[1]+(l['y']+(1+padding)*l['height']-sb[1])*sy))


def sheet(file, rows, size=(260, 300)):
    w, h = size
    out = Image.new('RGB', (w*len(rows[0]), h*len(rows)), '#eee')
    draw = ImageDraw.Draw(out)
    for ri, row in enumerate(rows):
        for ci, (label, file_in, box) in enumerate(row):
            im = Image.open(file_in).convert('RGBA')
            if box:
                im = im.crop(box)
            scale = min((w-12)/im.width, (h-34)/im.height)
            im = im.resize((max(1, round(im.width*scale)), max(1, round(im.height*scale))), Image.Resampling.LANCZOS)
            out.paste(im, (ci*w+(w-im.width)//2, ri*h+30), im)
            draw.text((ci*w+5, ri*h+6), label, fill='black')
    out.save(file)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--benchmark', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    run = Path('runs/phase4b5-codel-full-first')
    candidate = Path('runs/phase4b5-codel-mouths')
    freeze = Path('runs/phase4b5-freeze')
    seal = read(freeze/'first-run-seal.json')
    verify(run, seal['files'])
    verify(Path('.'), read(freeze/'freeze.json')['files'])
    for root, files in read(freeze/'references.json').items():
        verify(Path(root), files)
    state = read(run/'creation.json')
    layers = stage(run, state, 'facial')/'layers'
    restored = stage(run, state, 'restore')/'layers'
    core = read(candidate/'expression-core.json')
    source_target = next(s['target'] for s in read(candidate/'authoring/mouth-inspection.json')['surfaces'] if s['kind'] == 'source-neutral')
    drift = {}
    for name in NAMES:
        samples = [s for s in core['samples'] if s['expression'] == name and s['head'] == [0, 0, 0] and s['blink_talk'] is not None]
        base = samples[0]['mouth_vertices'][source_target]
        drift[name] = max(abs(v-w) for s in samples for v, w in zip(s['mouth_vertices'][source_target], base))
    # Preserve the probe's failed verdict; this merely summarizes its raw data.
    mouth_core = dict(status=core['status'], error=core.get('error'), samples=len(core['samples']),
                     source_seam_opening_invariant=core['source_seam_opening_invariant'],
                     source_seam_max_drift=drift, unchanged_tolerance=1e-7,
                     visible_reversals_recounted=sum(t['reversed'] for s in core['samples'] for t in s['triangles'].values() if t['opacity'] > 1e-6),
                     nonfinite=core['nonfinite'], invalid_opacity=core['invalid_opacity'],
                     strict_opacity_excursions=core['strict_opacity_excursions'], sha256=digest(candidate/'expression-core.json'))
    operations = {}
    for key in ['project', 'rig', 'animation', 'export']:
        rows = read(stage(run, state, key)/'mcp-transcript.json')
        operations[key] = dict(Counter(row['operation'] for row in rows))
    inf = stage(run, state, 'inference')
    sem = stage(run, state, 'semantics')
    report = dict(schema_version=1, phase='4B.5', continued_from=read(freeze/'freeze.json')['head'],
        first_run=creation_record(run), optional_candidate=str(candidate),
        protocol=read(freeze/'protocol.json'), source_provenance=read('benchmarks/phase4b5-art.json'),
        freeze_sha256=digest(freeze/'freeze.json'), first_run_seal_sha256=digest(freeze/'first-run-seal.json'),
        gpu=dict(decomposition=read(inf/'worker/metrics.json'), sam=read(sem/'sam/metrics.json')),
        independent_evaluation=read('runs/phase4b5-evaluation/independent-metrics.json'),
        first_dense=render_record(stage(run, state, 'validation')),
        candidate_dense=render_record(candidate/'dense'), first_mouths=render_record(Path('runs/phase4b5-first-mouths')),
        candidate_mouths=render_record(candidate/'mouth-review'), mouth_core=mouth_core,
        first_details=render_record(Path('runs/phase4b5-first-details-v2')),
        candidate_details=render_record(candidate/'details-v3'),
        successful_mcp_calls_by_operation=operations,
        references={name: creation_record(Path('runs/phase4b1-'+name)) for name in ['girl2', 'sara']},
        reference_timing_caveat='Phase 4B.1 cached inference/SAM replays; not comparable GPU inference speed measurements.',
        source_art=read(candidate/'authoring/source-art.json'),
        tests=dict(python=137, javascript=5, python_log_sha256=digest(freeze/'python-tests.log'), javascript_log_sha256=digest(freeze/'node-tests.log')),
        preservation=dict(first_run_sealed=True, frozen_code_unchanged=True, reference_inventories_unchanged=True),
        completion=dict(first_cli_technical_execution=True, source_art_preservation='passes narrow native-grid and archive checks',
            semantic_decomposition='limited facial ink corroboration; whole-character accuracy unknown',
            functional_rigging='first run passes; optional mouth candidate fails strict source-seam invariant',
            visually_convincing_animation='development-rejected: overlapping near-closed eye contours and residual shading/fragments', user_acceptance=False),
        character_specific_rig_operations=0, runtime_agent_required=False, production_modified=False,
        model_downloads=False, training=False, portrait_experiment='Predeclared, not executed: original framing reached runtime.',
        limitations=['Input selection exposed four numbered PNGs and difference bounds before inference; no expression tuning.',
            'Optional 4B.4/4B.4.1 scripts remain outside create CLI; separate candidate, not silently included in first result.',
            'Original frame ends at upper legs; no feet or complete full-body articulation.',
            'Single unsided arm layer preserves both arms/hands but does not provide independent limb controls.',
            'Plain mouth cavity, simplified closed lashes, residual shading and generated skin/hair boundaries need user review.',
            'No claim of model-pretraining holdout or broad generalization.'],
        retained_failures=['Initial sandbox CUDA denial; retry kept in creation history.',
            'Optional mouth Core invariant: Embarrassed drift 1.1920928955078125e-7 exceeds 1e-7.',
            'Early high-resolution diagnostic collectors omitted required geometry/control-noise fields; captures and tracebacks retained.'])
    first_frame = Path('runs/phase4b5-first-mouths/frames/neutral.png')
    candidate_frame = candidate/'mouth-review/frames/neutral.png'
    report['neutral_changed_pixels_first_vs_optional'] = int(np.any(np.array(Image.open(first_frame)) != np.array(Image.open(candidate_frame)), axis=2).sum())
    for key, root in [('first', stage(run, state, 'validation')), ('optional', candidate/'dense')]:
        t = read(root/'transition-core.json')
        report[key+'_eye_core'] = dict(status=t['status'], samples=len(t['samples']), visible_reversals=t['visible_reversals'])
    historical = {
        'girl2': ('runs/phase2-5-oga-neural/metrics.json', 'runs/phase2-5-oga-sam/metrics.json'),
        'sara': ('runs/phase4b-sara/stages/inference-e894236c7977/worker/metrics.json', 'runs/phase4b-sara/stages/semantics-70ebda41504a/sam/metrics.json')}
    for name, paths in historical.items():
        expected = read(Path('runs/phase4b1-'+name)/'creation.json')['identity']['input_sha256']
        values = {}
        for kind, file in zip(['decomposition', 'sam'], paths):
            m = read(file)
            if m['input_sha256'] != expected:
                raise ValueError('Historical worker belongs to a different reference')
            values[kind] = dict(path=file, sha256=digest(file), seconds=m['seconds'],
                               peak_allocated_bytes=max(v['peak_allocated_bytes'] for v in m['stages']),
                               caveat='Historical source-matched inference, not rerun here')
        report['references'][name]['historical_gpu'] = values
    report['development_review'] = dict(reviewer='development-agent', decision='reject-for-convincing-animation',
        user_acceptance=False, evidence_sha256=report['candidate_details']['report_sha256'],
        defects=['At openness .25, overlapping compressed eye contours and residual skin/shading fragments remain.',
                 'Closed lashes are flat and simpler than the artist reference; original open-eye shading persists.',
                 'First-run mouth expression distinctions are weak; optional mouths retain the failed Core invariant.',
                 'Plain cavity and source lower-lip shading remain stylistic limits.'],
        interpretation='High facial ink recall misses shaded contour ownership and reconstruction around moving eye surfaces; no input-quality blame.')
    write_json(a.benchmark, report)
    write_json(a.output/'benchmark.json', report)
    write_json(a.output/'development-review.json', report['development_review'])
    shutil.copyfile('runs/phase4b5-source/selected/neutral.png', a.output/'original.png')
    for name in ['composite', 'layers', 'segmentation']:
        shutil.copyfile(restored/f'preview/{name}.png', a.output/(name+'.png'))
    for name in ['reference-expressions', 'psd-facial-layers']:
        shutil.copyfile(Path('runs/phase4b5-evaluation')/(name+'.png'), a.output/(name+'.png'))
    shutil.copytree('runs/phase4b5-mouth-comparison', a.output/'mouths')
    for file in (a.output/'mouths').glob('*.html'):
        text = file.read_text().replace('Phase 4B.4.1', 'Codel Phase 4B.5').replace('Previous: Phase 4B.4.', 'Previous: sealed first Codel CLI run.').replace('Candidate: coordinated mouth contour/cavity.', 'Candidate: unchanged optional generic expression and mouth scripts; strict Core invariant FAILED, no promotion.')
        file.write_text(text)
    shutil.copytree('runs/phase4b5-transition-comparison', a.output/'transitions')
    detail_roots = [('First CLI', Path('runs/phase4b5-first-details-v2')), ('Optional mouths', candidate/'details-v3')]
    for prefix in ['full', 'mouth']:
        rows = []
        for label, root in detail_roots:
            box = face_box(layers, root/'frames/neutral.png')
            rows.append([(label+' / '+n, root/f'frames/{prefix}-{n}.png', box) for n in NAMES])
        sheet(a.output/(prefix+'-details.png'), rows)
    rows = []
    for label, root in detail_roots:
        box = face_box(layers, root/'frames/neutral.png')
        rows.append([(label+' / '+str(v), root/f'frames/both-{v}.png', box) for v in ['0', '0_05', '0_1', '0_15', '0_25', '0_5', '1']])
    sheet(a.output/'blink-details.png', rows)
    opening_sections = []
    for name in NAMES:
        rows = []
        for label, root in detail_roots:
            box = face_box(layers, root/'frames/neutral.png', 'mouth', .6)
            rows.append([(label+' / '+v, root/f'frames/open-{name}-{v}.png', box) for v in ['0','0_05','0_1','0_15','0_25','0_5','0_75','1']])
        sheet(a.output/('opening-detail-'+name+'.png'), rows, (220, 140))
        opening_sections.append('<h3>'+name+'</h3><img src="opening-detail-'+name+'.png">')
    shutil.copyfile(candidate/'details-v3/frames/neutral.png', a.output/'runtime-neutral.png')
    # Full body at combined extreme poses, including both hands, with no face crop.
    keys = ['neutral', 'ParamAngleX--15', 'ParamAngleX-15', 'ParamAngleY--15', 'ParamAngleY-15', 'ParamAngleZ--15', 'ParamAngleZ-15', 'combined-12_8_5']
    boxes = [Image.open(candidate/f'details-v3/frames/{k}.png').getbbox() for k in keys]
    union = (min(b[0] for b in boxes)-8, min(b[1] for b in boxes)-8, max(b[2] for b in boxes)+8, max(b[3] for b in boxes)+8)
    sheet(a.output/'whole-character-poses.png', [[(k, candidate/f'details-v3/frames/{k}.png', union) for k in keys]], (250, 650))
    reference_rows = []
    for name in ['girl2', 'sara']:
        root = Path('runs/phase4b1-'+name); rs = read(root/'creation.json')
        ll = stage(root, rs, 'facial')/'layers'; rr = stage(root, rs, 'validation')/'frames'
        box = face_box(ll, rr/'neutral.png')
        # The earlier accepted 4B.1 evidence uses face-* expression names.
        reference_rows.append([(name+' frozen / '+n, rr/f'face-{n}.png', box) for n in NAMES])
    sheet(a.output/'frozen-references.png', reference_rows)
    attribution = html.escape(report['source_provenance']['attribution'])
    page = '''<!doctype html><meta charset="utf-8"><title>Codel — independent Live2D review</title>
<style>body{font:17px system-ui;line-height:1.5;background:#eee;color:#223;max-width:1500px;margin:30px auto;padding:20px}img{max-width:100%;background:#ddd}figure{margin:20px 0}a{color:#164f8a}.pair{display:flex;gap:20px}.pair figure{flex:1}.pair img{max-height:750px}li{margin:7px 0}</style>
<h1>Codel: an interactive candidate, not an accepted conversion</h1>
<p>The original 1078 × 2089 neutral PNG reached a portable Cubism export through the frozen creation CLI. No manually authored character-specific rig operations were used. The original framing includes both hands and ends at the upper legs. No portrait inference experiment was run.</p>
<p><a href="http://127.0.0.1:8786/">Open first-run interactive viewer</a> · <a href="http://127.0.0.1:8787/">Open optional-mouth diagnostic viewer</a> · <a href="mouths/mouth-only.html">Mouth-only opening comparisons</a> · <a href="transitions/index.html">Dense transitions and sampled animation loops</a></p>
<h2>Read this before judging</h2><ul>
<li>First CLI: 401 runtime frames and 72 eye geometry samples pass. Its Happy/Confused/Embarrassed mouths are subtle; Sad and Angry are similar.</li>
<li>Optional expression/mouth scripts: visibly different mouths, but the 819-sample Core audit FAILS its unchanged source-seam tolerance in Embarrassed (1.19e-7 versus 1e-7). No visible triangle reversals were found in those samples. This diagnostic candidate is not promoted.</li>
<li>Development visual rejection: quarter-open eyes show overlapping contours and residual skin/shading fragments. Closed lashes are flatter than the artist references. These defects occur in both candidates despite numerical passes. Plain mouth cavity has no teeth or tongue.</li>
<li>Both arms/hands are retained in one unsided arm layer. Independent arm/hand rigging and complete full-body motion are not established.</li>
<li>Source preservation and narrow facial ink ownership checks pass; whole-character semantic correctness and convincing animation remain unproven. Your visual acceptance is still pending.</li></ul>
<div class="pair"><figure><img src="original.png"><figcaption>Only inference input: original neutral Codel3.png</figcaption></figure><figure><img src="runtime-neutral.png"><figcaption>Optional candidate: actual neutral Core render, 3× diagnostic resolution</figcaption></figure></div>
<h2>Seven complete expressions</h2><p>First CLI above; optional generic mouths below. Actual high-resolution re-renders, identical framing.</p><img src="full-details.png">
<h2>Mouth-only expressions</h2><p>Eyes, brows, blush and head held neutral. Judge mouth shape separately.</p><img src="mouth-details.png">
<h2>Dense blink close-ups — visible defect retained</h2><img src="blink-details.png"><p>Inspect the .25 sample for overlapping contours and residual shading. Use the transition gallery for independent eyes, full cycles, mouth cycles, talking in every expression, idle and exact neutral returns.</p>
<details><summary>High-resolution mouth openings, every expression</summary>'''+''.join(opening_sections)+'''</details>
<h2>Head poses and limb preservation</h2><img src="whole-character-poses.png">
<h2>Source restoration and decomposition</h2><div class="pair"><figure><img src="composite.png"><figcaption>Native-grid restored composite: 911,627 / 911,631 foreground pixels exact; no duplicate source owners</figcaption></figure><figure><img src="layers.png"><figcaption>Candidate layer artwork; generated hidden regions are not known anatomy</figcaption></figure></div>
<details><summary>Candidate semantic coverage overlay</summary><img src="segmentation.png"></details>
<h2>Artist references — evaluation only</h2><p>Opened after sealing the first run, except the disclosed input-selection exposure. These twelve variants are not one-to-one labels for our seven expressions. The PSD contains a fused base and seven facial groups, not a fully separated Live2D model.</p><img src="reference-expressions.png"><details><summary>Artist's original facial color/ink layers</summary><img src="psd-facial-layers.png"></details>
<h2>Frozen Girl2 and Sara comparison</h2><p>Historical Phase 4B.1 captures, not rerun or retuned here. Different source resolution and style; these are visual context, not matched accuracy measurements. Girl2: stevenburrow, CC0. Sara: ZeNeRIA29 / RPG Action, CC BY 3.0. Their earlier limitations remain.</p><img src="frozen-references.png">
<h2>Protocol limits</h2><p>Four numbered PNGs were viewed while selecting neutral; difference bounding boxes were computed before inference. No reference-driven tuning occurred. Only Codel3.png entered creation. No claim is made that this public artwork was absent from model training. Optional mouth scripts are outside the creation CLI, so their result is a separately identified extension experiment.</p>
<p>All numeric evidence is available in <a href="benchmark.json">the benchmark record</a>. It does not grant visual approval.</p><p>'''+attribution+''' <a href="https://opengameart.org/content/codel-visual-novel-sprite">Source and license</a>.</p>'''
    (a.output/'index.html').write_text(page)
    print(a.output/'index.html')


if __name__ == '__main__':
    main()
