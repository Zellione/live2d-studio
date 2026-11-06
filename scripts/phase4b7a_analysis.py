"""Exploratory image-grid deltas and semantic proposals, never anatomical evidence."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from phase4b7a_poses import digest, dump, new_run


def load_rgb(file):
    return np.asarray(Image.open(file).convert('RGB'))


def components(mask, minimum=32):
    labels, count = ndimage.label(mask)
    records = []
    for index, area in enumerate(np.bincount(labels.ravel())[1:], 1):
        if area < minimum:
            continue
        yy, xx = np.where(labels == index)
        records.append(dict(label=index, pixels=int(area), bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],
                            centroid=[float(xx.mean()),float(yy.mean())]))
    return labels, sorted(records, key=lambda row: -row['pixels'])


def delta_regions(source, neutral, candidate, editable, threshold=24, excess=16):
    """Same-grid photometric change above control; neither flow nor recovered surfaces."""
    if source.shape != neutral.shape or source.shape != candidate.shape or editable.shape != source.shape[:2]:
        raise ValueError('Mismatched comparison grids')
    control = np.max(np.abs(neutral.astype(float)-source), axis=-1)
    delta = np.max(np.abs(candidate.astype(float)-source), axis=-1)
    changed = (delta > threshold) & (delta > control + excess) & editable
    return changed, dict(threshold=threshold, excess_over_neutral=excess,
                         changed_pixels=int(changed.sum()), control_mae=float(np.abs(neutral.astype(float)-source)[editable].mean()),
                         candidate_mae=float(np.abs(candidate.astype(float)-source)[editable].mean()))


def sam_masks(folder, image_file):
    record = json.loads((folder/'sam.json').read_text())
    if record['input_sha256'] != digest(image_file):
        raise ValueError('SAM result belongs to another image')
    return {name: np.array(Image.open(folder/(name+'.png')).convert('L')) > 0 for name in record['tags']}


def semantic_proposal(source, candidate, baseline, masks, changed):
    """Expose category transitions and disconnected components without naming joints."""
    arm = masks['handwear']
    labels, regions = components(arm)
    # Skin-color hint learned only from predicted source face, restricted to predicted arms.
    face_rgb = source[baseline['face']]
    if len(face_rgb):
        skin = np.median(face_rgb, axis=0)
        hand = arm & (np.max(np.abs(candidate.astype(float)-skin), axis=-1) < 38)
    else:
        hand = np.zeros_like(arm)
    _, hands = components(hand)
    possible_torso = changed & baseline['handwear'] & masks['topwear'] & ~arm
    # Segmentation may overlap; report conflicts, never force a unique anatomical owner.
    overlap = arm & masks['topwear']
    report = dict(arm_components=regions, hand_color_components=hands,
                  substantial_arm_components=sum(r['pixels']>=max(32,int(arm.sum()*.05)) for r in regions),
                  possible_arm_to_topwear_pixels=int(possible_torso.sum()),
                  arm_topwear_overlap_pixels=int(overlap.sum()),
                  side_assignment='image-space components only; anatomical identity unverified',
                  shoulder_elbow_wrist='not provided by this parser',
                  hidden_truth=False, independent_evidence=False)
    colors = np.array([[220,80,80],[60,150,240],[180,90,220],[240,190,40]],dtype=np.uint8)
    overlay = candidate.copy()
    for i, row in enumerate(regions):
        select = labels == row['label']
        overlay[select] = (overlay[select]*.45 + colors[i%len(colors)]*.55).astype(np.uint8)
    overlay[hand] = (30,235,90)
    overlay[possible_torso] = (255,180,0)
    return report, overlay, possible_torso


def review_decisions(review, generated):
    if review.get('reviewer_kind') != 'development-agent' or review.get('user_approval') is not False:
        raise ValueError('Study review must explicitly distinguish development and user approval')
    if len({row['id'] for row in review['poses']}) != len(review['poses']):
        raise ValueError('Duplicate pose review')
    for row in review['poses']:
        if row['decision'] not in ('accept-exploratory', 'reject'):
            raise ValueError('Unknown exploratory decision')
        if digest(generated/row['id']/'composite.png') != row['composite_sha256']:
            raise ValueError('Review does not match exact pose')
    return {row['id']:row for row in review['poses']}


def analyze(prepared, generated, review_file, sam_root, reference, output, layers=None):
    review = json.loads(review_file.read_text())
    decisions = review_decisions(review, generated)
    generation = json.loads((generated/'report.json').read_text())
    if generation['status'] != 'completed':
        raise ValueError('Incomplete generation batch')
    if set(decisions) != {row['task']['id'] for row in generation['tasks']}:
        raise ValueError('Review must cover every generated pose exactly')
    source = load_rgb(prepared/'input.png')
    neutral = load_rgb(generated/'neutral/composite.png')
    editable = np.array(Image.open(prepared/'edit-mask.png')) > 0
    baseline = sam_masks(sam_root/'source', prepared/'input.png')
    output = new_run(output)
    for name in ('input.png','original.png','edit-mask.png','source-alpha.png'):
        shutil.copyfile(prepared/name, output/name)
    shutil.copyfile(reference, output/'reviewed-runtime-neutral.png')
    shutil.copyfile(review_file, output/'development-review.json')
    shutil.copyfile(generated/'report.json', output/'generation.json')
    base_labels, base_regions = components(baseline['handwear'])
    base_overlay = source.copy()
    base_overlay[baseline['handwear']] = (.4*base_overlay[baseline['handwear']] + .6*np.array([230,90,90])).astype(np.uint8)
    Image.fromarray(base_overlay).save(output/'baseline-arms.png')
    decomposition = []
    if layers:
        manifest = json.loads((layers/'layer_manifest.json').read_text())
        canvas = manifest['canvas']
        observed = Image.new('L',(canvas['width'],canvas['height']))
        for row in manifest['layers']:
            if row['role'] != 'handwear':
                continue
            observed.paste(Image.open(layers/row['mask_path']), (row['x'],row['y']))
            decomposition.append({k:row[k] for k in
                ('id','role','side','observed_pixels','generated_pixels','ownership_status')})
        mask = np.array(observed.resize((source.shape[1],source.shape[0]),Image.Resampling.NEAREST))>0
        overlay=source.copy()
        overlay[mask]=(.4*overlay[mask]+.6*np.array([230,90,90])).astype(np.uint8)
        Image.fromarray(overlay).save(output/'frozen-arm-layer.png')
    records = []
    cards = []
    votes = []
    for task in generation['tasks']:
        name = task['task']['id']
        decision = decisions[name]
        folder = output/name
        folder.mkdir()
        for kind in ('raw','composite'):
            src = generated/name/(kind+'.png')
            if digest(src) != task[kind+'_sha256']:
                raise ValueError('Generation artifact changed')
            shutil.copyfile(src, folder/(kind+'.png'))
        candidate = load_rgb(folder/'composite.png')
        changed, metrics = delta_regions(source, neutral, candidate, editable)
        overlay = candidate.copy()
        overlay[changed] = (.35*overlay[changed]+.65*np.array([255,0,170])).astype(np.uint8)
        Image.fromarray(overlay).save(folder/'delta.png')
        record = dict(id=name, decision=decision, delta=metrics, semantic=None,
                      sufficiently_reliable_articulation_evidence=False)
        proposal_link = ''
        if decision['decision'] == 'accept-exploratory':
            masks = sam_masks(sam_root/name, generated/name/'composite.png')
            proposal, overlay, torso = semantic_proposal(source,candidate,baseline,masks,changed)
            record['semantic'] = proposal
            Image.fromarray(overlay).save(folder/'proposal.png')
            Image.fromarray(torso.astype(np.uint8)*255).save(folder/'possible-torso.png')
            if name != 'neutral':
                votes.append(torso)
            proposal_link = f'<figure><a href="{name}/proposal.png"><img src="{name}/proposal.png"></a><figcaption>Exploratory components / skin hints / possible torso</figcaption></figure>'
        records.append(record)
        e = html.escape
        cards.append(f'''<section><h2>{e(name)} — {e(decision['decision'])}</h2>
        <p>{e(decision['summary'])}</p><p><b>Useful structure:</b> {e(decision['usefulness'])}</p>
        <div class="row"><figure><img src="input.png"><figcaption>Canonical source, resized on white</figcaption></figure>
        <figure><a href="{name}/composite.png"><img src="{name}/composite.png"></a><figcaption>Protected composite</figcaption></figure>
        <figure><a href="{name}/raw.png"><img src="{name}/raw.png"></a><figcaption>Raw decode: inspect unrelated drift</figcaption></figure>
        <figure><a href="{name}/delta.png"><img src="{name}/delta.png"></a><figcaption>Magenta: change beyond neutral control</figcaption></figure>{proposal_link}</div>
        <details><summary>Exact prompt and screening</summary><pre>{e(json.dumps(dict(prompt=task['task'],screening=decision,metrics=record),indent=2))}</pre></details></section>''')
    voting = np.sum(votes,axis=0) if votes else np.zeros(editable.shape,dtype=int)
    Image.fromarray((np.minimum(voting,3)/3*255).astype(np.uint8)).save(output/'torso-votes.png')
    result = dict(status='exploratory-only', poses=records,
                  neutral_control_accepted=decisions['neutral']['decision']=='accept-exploratory',
                  nonneutral_proposal_vote_inputs=len(votes),
                  repeated_same_grid_torso_proposals_pixels=int((voting>=2).sum()),
                  voting_limit='Shared model hallucinations and moving surfaces are correlated; no registration or truth claim',
                  generation_report_sha256=digest(generated/'report.json'), review_sha256=digest(review_file),
                  source_sam_sha256=digest(sam_root/'source/sam.json'), code_sha256=digest(__file__),
                  baseline_arm_components=base_regions,
                  baseline_semantic=semantic_proposal(source,source,baseline,baseline,np.zeros_like(editable))[0],
                  user_approval=False, articulation_ready=False)
    dump(output/'analysis.json', result)
    if decomposition:
        result['frozen_decomposition_arms'] = decomposition
        dump(output/'analysis.json',result)
    tiles = [('Canonical source',output/'input.png')]+[(r['id']+' / '+r['decision']['decision'],output/r['id']/'composite.png') for r in records]
    sheet=Image.new('RGB',(264*4,552*((len(tiles)+3)//4)), '#e0e0e0')
    draw=ImageDraw.Draw(sheet)
    for i,(label,file) in enumerate(tiles):
        im=Image.open(file).convert('RGB');im.thumbnail((264,512))
        x=(i%4)*264;y=(i//4)*552
        sheet.paste(im,(x,y+32));draw.text((x+5,y+5),label,fill='black')
    sheet.save(output/'contact-sheet.jpg',quality=95)
    (output/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Codel auxiliary pose feasibility</title>
    <style>body{font:16px system-ui;margin:28px;background:#20232b;color:#eee}a{color:#aadeff}section{border-top:1px solid #555;padding:20px 0}.row{display:flex;gap:12px;overflow:auto}figure{margin:0;min-width:190px;flex:1}img{width:100%;max-height:620px;object-fit:contain;background:white}figcaption{font-size:13px}pre{white-space:pre-wrap}p{max-width:1100px}</style>
    <h1>Qwen auxiliary poses — feasibility only</h1><p>Canonical source: LisadiKaprio, Codel Visual Novel Sprite,
    <a href="https://opengameart.org/content/codel-visual-novel-sprite">CC BY 4.0</a>. Generated derivatives are uncertain inference artifacts.
    Development acceptance below permits exploratory analysis only; user review remains separate. No model was promoted.</p>
    <p><b>Three gates:</b> a plausible still ≠ helpful segmentation ≠ reliable articulation evidence. No pose passes the third gate.
    Face preservation in composites is imposed by the body mask; it is not proof of Qwen identity fidelity.
    Outputs are 528 × 1024 RGB on white; the original RGBA is preserved separately. No generated transparency is claimed.</p>
    <p>Proposal colors: arm connected components = alternating red/blue/purple/yellow; green = skin-color hints inside predicted arms;
    orange = source arm → predicted topwear with strong image change. These are hypotheses, not joints or recovered clothing.
    Magenta deltas include displaced limbs, removed limbs, shading and unrelated redraws. Correlated model outputs cannot vote themselves into ground truth.</p>
    <p><a href="contact-sheet.jpg">All poses at a glance</a> · <a href="original.png">Original full-resolution source</a> · <a href="reviewed-runtime-neutral.png">Frozen reviewed runtime capture</a> ·
    <a href="edit-mask.png">Shared edit mask</a> · <a href="baseline-arms.png">Source unsided arm prediction</a> · <a href="analysis.json">Measured analysis</a> · <a href="generation.json">Exact generation settings/timings</a> ·
    <a href="torso-votes.png">Repeated torso hypotheses</a></p>''' + ''.join(cards))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('prepared','generated','review','sam-root','reference','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--layers',type=Path)
    a=p.parse_args()
    analyze(a.prepared,a.generated,a.review,a.sam_root,a.reference,a.output,a.layers)
