let state,pose='right-lift',busy=false,lastSignature='';
const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e};
const asset=id=>'/asset/'+id;
async function action(data){
  if(busy)return;busy=true;render();let message='';
  try{const res=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-Review-CSRF':state.csrf},body:JSON.stringify({...data,reviewer:$('reviewer').value})});
    const out=await res.json();if(!res.ok)throw Error(out.error);lastSignature='';await refresh();
    if(data.action==='finish')message='Reviewed set saved locally. Selected poses: '+Object.keys(out.selected).join(', ');
  }catch(e){message=e.message}finally{busy=false;render();if(message)$('notice').textContent=message}
}
function inspect(id,label){$('view-image').src=asset(id);$('view-title').textContent=label;$('view-caption').textContent=label;$('viewer').showModal()}
function render(){
  if(!state.poses[pose])pose=Object.keys(state.poses)[0];
  const canonical=state.workflow==='canonical',helpers=state.workflow==='canonical-helpers';
  $('page-title').textContent=canonical?'Choose a front-facing base.':'Find the right gesture.';
  $('page-description').textContent=canonical?'Compare five frontal candidates, approve one, or try again. Your original artwork remains untouched.':'Compare five variations, keep one, or try again.';
  $('target-heading').textContent=canonical?'Canonical working base':'Target poses';
  $('scope-note').textContent=canonical?'Approval freezes a synthetic canonical working base. Original artwork and verified anatomy remain separate.':'Selections approve synthetic helper images only. Anatomy and usefulness for rigging are evaluated separately.';
  $('finish').textContent=canonical?'Save canonical selection':'Save reviewed pose set';
  $('unsupported').textContent=canonical?'Mark canonicalization unsuccessful':'Mark unsupported';
  $('primary-caption').textContent=helpers?'Canonical · synthetic geometry':'Original · unchanged';
  document.querySelector('[data-view="source"] img').alt=helpers?'Frozen synthetic canonical base':'Original unchanged artwork';
  $('compare-reference-caption').textContent=helpers?'Canonical synthetic base':'Original';
  $('identity-figure').hidden=!helpers;if(helpers)$('identity-image').src=asset('identity');
  document.querySelector('.references').classList.toggle('three-references',helpers);
  $('review-heading').textContent=canonical?'Check the frontal view and character identity.':'Inspect the pose, then the details.';
  $('review-instructions').textContent=canonical?'Check a forward-facing head, chest and hips, level visible shoulders, separated arms, neutral expression, and the same face, hairstyle and outfit. Approval freezes a synthetic working base; it does not replace the original.':'Look at hand placement, sleeve boundaries, shoulder and elbow shape, costume, face and hair. Generated pixels may differ from the original.';
  if(state.gesture_profile)$('review-instructions').textContent=state.poses[pose].prompt+' Both arms down does not satisfy a raised-forearm target.';
  const p=state.poses[pose],active=busy||state.batches.some(b=>b.status==='running');
  const poseActive=busy||state.batches.some(b=>b.pose===pose&&b.status==='running'),frozen=['approved','unsupported'].includes(p.status);
  $('poses').replaceChildren();for(const [key,v] of Object.entries(state.poses)){const b=el('button',v.title,key===pose?'active':'');b.append(el('small',v.status));b.onclick=()=>{pose=key;lastSignature='';render()};$('poses').append(b)}
  $('title').textContent=p.title;$('status').textContent=p.status.toUpperCase();
  const preset=$('preset').value||Object.keys(state.presets)[0];$('preset').replaceChildren();
  for(const name of Object.keys(state.presets)){const o=el('option',name);o.value=name;$('preset').append(o)}$('preset').value=preset;
  const cfg=state.presets[preset];$('settings').textContent=JSON.stringify(cfg,null,2);
  const guideKey='guide/'+pose+'/'+cfg.guidance;$('guide').src=p.guides[cfg.guidance]?asset(guideKey):'';$('guide-button').onclick=()=>inspect(guideKey,'Target guide');
  $('generate').disabled=active||['approved','unsupported'].includes(p.status);$('unsupported').disabled=frozen||poseActive;$('finish').disabled=active;
  $('generate').textContent=state.batches.some(b=>b.pose===pose)?'Generate five more':'Generate five candidates';
  $('notice').textContent=active?'A batch is generating. Completed candidates appear as they finish.':p.status==='approved'?(canonical?'Canonical working base frozen. Original and synthetic provenance are stored separately.':'Selected pose saved. This pose will not be regenerated.'):p.status==='unsupported'?(canonical?'Canonicalization marked unsuccessful; no working base will be used.':'This pose is marked unsupported.'):'Choose a candidate only after inspecting the full image. No selection is automatic.';
  $('batches').replaceChildren();
  for(const b of [...state.batches].reverse().filter(b=>b.pose===pose)){
    const section=el('section',undefined,'batch'),bar=el('div',undefined,'batch-title');bar.append(el('h3',b.preset+' · '+new Date(b.created*1000).toLocaleString()),el('span',b.status,'badge'));
    if(['failed','interrupted'].includes(b.status)){const retry=el('button','Resume unfinished candidates','secondary');retry.disabled=active||frozen;retry.onclick=()=>action({action:'resume',batch:b.id});bar.append(retry)}
    section.append(bar);const grid=el('div',undefined,'candidates');
    for(const c of b.candidates){const card=el('article',undefined,'card'+(p.selected===c.id?' selected':'')+(c.decision?.action==='reject'?' rejected':''));
      if(c.status==='ready'){const view=el('button',undefined,'image-button'),img=el('img');img.src=asset(c.id);img.alt=p.title+' seed '+c.seed;view.append(img);view.onclick=()=>inspect(c.id,p.title+' · seed '+c.seed);card.append(view)}else card.append(el('div','Waiting for generation','pending'));
      card.append(el('div','Seed '+c.seed,'meta'));
      if(c.result)card.append(el('div',c.result.output_size.join(' × ')+' · '+c.result.seconds.toFixed(1)+' s','meta'));
      if(c.decision)card.append(el('div',c.decision.action+(c.decision.reason?': '+c.decision.reason:''),'meta'));
      const accept=el('button',p.selected===c.id?'Selected ✓':canonical?'Approve canonical base':'Accept candidate');accept.disabled=c.status!=='ready'||frozen||poseActive;accept.onclick=()=>action({action:'accept',pose,candidate:c.id});card.append(accept);
      const reasons=el('select');for(const reason of state.reasons){const o=el('option',reason);o.value=reason;reasons.append(o)}card.append(reasons);
      const reject=el('button','Reject / flag','secondary');reject.disabled=accept.disabled;reject.onclick=()=>action({action:'reject',pose,candidate:c.id,reason:reasons.value});card.append(reject);
      const details=el('details'),summary=el('summary','Exact generation metadata');details.append(summary,el('pre',JSON.stringify(c.result||{seed:c.seed,config:b.config},null,2)));card.append(details);grid.append(card)
    }section.append(grid);$('batches').append(section)
  }
  $('exports').textContent=(state.canonical_reference?'Frozen canonical manifest: '+state.canonical_reference.manifest+' · ':'')+(state.exports.length?state.exports.length+' reviewed set(s) saved under this run’s selections/ directory.':'');
}
async function refresh(){try{const res=await fetch('/api/state');const next=await res.json();if(!res.ok)throw Error(next.error);const sig=JSON.stringify(next);state=next;if(sig!==lastSignature){lastSignature=sig;render()}}catch(e){$('notice').textContent=e.message}}
$('generate').onclick=()=>action({action:'generate',pose,preset:$('preset').value});
$('unsupported').onclick=()=>{const reason=window.prompt('Why is this pose unsupported?','Cannot produce a suitable pose in this framing');if(reason!==null)action({action:'unsupported',pose,reason})};
$('finish').onclick=()=>action({action:'finish'});$('preset').onchange=()=>render();
document.querySelector('[data-view="source"]').onclick=()=>inspect('source',state.workflow==='canonical-helpers'?'Canonical synthetic base':'Original reference');
document.querySelector('[data-view="identity"]').onclick=()=>inspect('identity','Original identity/style reference');
$('close-view').onclick=()=>{$('viewer').close();if(document.fullscreenElement)document.exitFullscreen()};$('fullscreen').onclick=()=>$('viewer').requestFullscreen();
$('zoom').oninput=()=>document.querySelectorAll('#compare img').forEach(img=>img.style.height=$('zoom').value+'%');
refresh();setInterval(refresh,2500);
