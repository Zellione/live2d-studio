(async()=>{
 const wait=async f=>{for(let n=0;n<100;n++){if(await f())return;await new Promise(r=>setTimeout(r,100))}throw Error('Timed out waiting for reviewer')};
 const state=async()=>await(await fetch('/api/state')).json();
 const clickText=async(selector,text)=>{const find=()=>[...document.querySelectorAll(selector)].find(e=>e.textContent.includes(text));await wait(()=>find()&&!find().disabled);find().click()};
 await wait(()=>document.querySelector('#poses button'));
 const initial=await state();if(initial.workflow!=='canonical-helpers'||initial.source.sha256===initial.identity_reference.sha256)throw Error('Input roles mixed');
 await wait(()=>!document.querySelector('#identity-figure').hidden&&document.querySelector('#identity-image').naturalWidth>0);
 if(!document.querySelector('#primary-caption').textContent.includes('synthetic'))throw Error('Canonical provenance missing');
 document.querySelector('#reviewer').value='Synthetic browser QA';
 await wait(()=>!document.querySelector('#generate').disabled);document.querySelector('#generate').click();
 await wait(async()=>{const s=await state();return s.batches.length===1&&s.batches[0].status==='completed'});
 await wait(()=>document.querySelectorAll('.card').length===5&&document.querySelector('.card .image-button'));
 document.querySelector('.card .image-button').click();if(!document.querySelector('#viewer').open)throw Error('Compare dialog absent');
 document.querySelector('#zoom').value=150;document.querySelector('#zoom').dispatchEvent(new Event('input'));
 document.querySelector('#close-view').click();
 await clickText('.card button','Reject / flag');await wait(async()=>(await state()).events.some(e=>e.action==='reject'));
 await wait(()=>!document.querySelector('#generate').disabled);document.querySelector('#generate').click();
 await wait(async()=>{const s=await state();return s.batches.length===2&&s.batches[1].status==='completed'});
 await wait(()=>document.querySelectorAll('.card').length===10);
 await clickText('.card button','Accept candidate');await wait(async()=>(await state()).poses['right-lift'].status==='approved');
 await wait(()=>document.querySelector('#generate').disabled);
 await wait(()=>!document.querySelector('#finish').disabled);await clickText('#poses button','modest wave');window.prompt=()=> 'Synthetic framing test';document.querySelector('#unsupported').click();
 await wait(async()=>(await state()).poses.wave.status==='unsupported');
 await wait(()=>!document.querySelector('#finish').disabled);document.querySelector('#finish').click();await wait(async()=>(await state()).exports.length===1);
 const s=await state();if(s.batches.some(b=>b.candidates.some(c=>c.result.reference_latent_count!==3)))throw Error('Missing three-reference evidence');const seeds=s.batches.flatMap(b=>b.candidates.map(c=>c.seed));
 if(new Set(seeds).size!==10||s.poses['left-lift'].status!=='pending')throw Error('Batch isolation failed');
 const imgs=[...document.images].filter(i=>i.getAttribute('src'));await wait(()=>imgs.every(i=>i.complete&&i.naturalWidth>0));
 return {stage:'canonical-gesture-reviewer',status:'pass',synthetic:true,candidates:10,unique_seeds:10,selected:s.poses['right-lift'].selected,export_count:s.exports.length,checks:['three-reference-display','canonical-original-separation','generate','five-more','history','reject','accept','unsupported','selected-only-save','zoom','compare','image-loads']};
})()
