"""Summarize completed matched runs and create a self-contained local gallery."""
import argparse
import html
import json
from pathlib import Path
import shutil
import numpy as np
from PIL import Image
from live2d_studio.pose_review import REPO,digest,write

SCREENING={
 'quality':'Recognizable face, hair, palette and outfit; frontal framing retained. Both arms remain down: fails requested gesture. Hands are present but anatomy is unverified.',
 'lightning8':'Recognizable identity, hair and outfit; frontal framing retained. Anatomical right elbow bends with continuous sleeve, wrist and present hand; other arm stays down. Pointing index and hand above chest depart from relaxed chest-height target. Folded fingers/shoulder geometry still need human review.',
 'lightning4':'Clear right bent arm, present pointing hand and relaxed opposite arm. Outfit, palette and framing remain recognizable. Slight face/proportion change and simpler hand/cloth shading than eight steps. Same excessive hand height and pointing departure; finger topology unverified.',
 'control8':'Reduced-step no-LoRA control has a ghost raised forearm/hand superimposed on the original down arm. Severe limb/hand failure despite recognizable face and outfit. Reject.',
 'control4':'Reduced-step no-LoRA control has a fading duplicated arm and nearly absent raised hand. Severe anatomy/rendering failure. Reject.'}

def build(run,output):
 run=run.resolve();output=output.resolve()
 if not output.is_relative_to(REPO/'runs') or output.is_relative_to(REPO/'runs/references'):raise ValueError('Fresh ignored gallery required')
 source=json.loads((run/'comparison.json').read_text());results={}
 for name in source['cases']:
  folder=run/name;report=json.loads((folder/'report.json').read_text());process=json.loads((folder/'process.json').read_text())
  if report['status']!='completed' or process['returncode']!=0:raise ValueError('Incomplete comparison')
  task=report['tasks'][0];file=folder/task['id']/'image.png'
  if digest(file)!=task['image_sha256']:raise ValueError('Changed output')
  plan=json.loads((folder/'plan.json').read_text())
  if plan['inputs']!=source['inputs'] or task['seed']!=source['seed'] or task['prompt']!=source['prompt'] or task['reference_latent_count']!=3:raise ValueError('Unmatched comparison')
  results[name]={'process_wall_seconds':process['wall_seconds'],'worker_total_seconds':report['total_seconds'],
    'startup_seconds':report['startup_seconds'],'model_loading':report['model_loading'],'model_unloading':report['phases']['model_unloading'],
    'task':task,'development_screening':SCREENING[name],'human_approved':False}
 effects={}
 for count in (8,4):
  a=np.asarray(Image.open(run/f'lightning{count}/c1/image.png')).astype(np.int16)
  b=np.asarray(Image.open(run/f'control{count}/c1/image.png')).astype(np.int16)
  effects[str(count)]={'mean_absolute_rgb_delta_0_255':float(np.abs(a-b).mean()),'changed_pixel_fraction':float(np.any(a!=b,axis=2).mean()),
   'meaning':'Matched steps, CFG, seed, prompt and references; adapter presence is the changed variable. Pixel change proves effect, not anatomical correctness.'}
 summary=dict(source,cases=results,adapter_effect_controls=effects,
    timing_scope='One fresh process per case, warm filesystem cache; CUDA-synchronized wall stages. Sampling includes lazy GPU materialization/patch application; decoding includes VAE transfers. Torch allocator peaks, not whole-board VRAM. No uncertainty interval from n=1.',
    recommendation='Use Balanced for further human review; Fast for quick exploration; Quality retains the historical 40-step reference. No automatic approval or rigging.')
 output.mkdir(parents=True,exist_ok=False);write(output/'measurements.json',summary)
 cards=[]
 def card(title,file,note):
  target=title.replace(' ','-')+'.png';shutil.copyfile(file,output/target)
  return f'<article><h3>{html.escape(title)}</h3><a href="{target}" target="_blank"><img src="{target}" alt="{html.escape(title)}"></a><p>{html.escape(note)}</p></article>'
 for label,name in [('Original identity','identity.png'),('Frozen canonical','source.png'),('Target guide','guide.png')]:
  cards.append(card(label,run/'quality'/name,'Reference only; unchanged.'))
 refs=''.join(cards);cards=[];rows=[]
 for name,r in results.items():
  t=r['task'];tm=t['timings'];wall=r['process_wall_seconds'];speed=results['quality']['process_wall_seconds']/wall
  note=f"{wall:.1f}s process; {t['seconds']:.1f}s image; {speed:.2f}× process speed. "+r['development_screening']
  cards.append(card(name,run/name/'c1/image.png',note))
  rows.append('<tr>'+''.join(f'<td>{v}</td>' for v in [name,f"{r['model_loading']['seconds']:.2f}",f"{tm['reference_encoding']['seconds']:.2f}",f"{tm['lora_loading']['seconds']:.2f}",f"{tm['sampling']['seconds']:.2f}",f"{tm['decoding']['seconds']:.2f}",f'{wall:.2f}',f"{t['peak_allocated_bytes']/2**30:.2f} / {t['peak_reserved_bytes']/2**30:.2f}"] )+'</tr>')
 page='''<!doctype html><meta charset="utf-8"><title>Qwen Lightning comparison</title><style>body{font:16px system-ui;background:#18202a;color:#e8edf4;margin:2rem}a{color:#97c8ff}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1rem}article{background:#263140;padding:1rem}img{width:100%;max-height:75vh;object-fit:contain;background:white}table{border-collapse:collapse}td,th{padding:.6rem;border:1px solid #617087}p{max-width:100ch}</style><h1>Qwen 2509 Lightning: matched comparison</h1><p>Development screening only. No generated image is automatically approved. Click an image for full resolution. All cases use the same seed, prompt, 800 × 1536 framing and three input references.</p><p><a href="http://127.0.0.1:8804/">Open five-candidate reviewer</a> · <a href="measurements.json">Exact settings, hashes and measurements</a></p>'''
 page+='<h2>References</h2><div class="grid">'+refs+'</div><h2>40 / 8 / 4 and matched controls</h2><div class="grid">'+''.join(cards)+'</div>'
 page+='<h2>Timing in seconds; memory in GiB</h2><table><tr><th>Case</th><th>Model load</th><th>References</th><th>LoRA load</th><th>Sampling</th><th>Decode</th><th>Process total</th><th>Allocated / reserved peak</th></tr>'+''.join(rows)+'</table><p>'+html.escape(summary['timing_scope'])+'</p><p>Both Lightning outputs improve arm visibility in this seed, but use a pointing hand above the requested height. This is neither human approval nor anatomical validation. The no-LoRA low-step controls contain ghost limbs. Reduced steps alone are insufficient.</p>'
 (output/'index.html').write_text(page+'<p>Codel artwork: LisadiKaprio, <a href="https://opengameart.org/content/codel-visual-novel-sprite">CC-BY-4.0 source</a>. Generated images are synthetic derivatives.</p>')
 return summary

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.run,a.output)
