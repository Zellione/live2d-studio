(async()=>{
 const wait=async f=>{for(let n=0;n<150;n++){if(await f())return;await new Promise(r=>setTimeout(r,100))}throw Error('Canonical reviewer timed out')};
 const state=async()=>await(await fetch('/api/state')).json();
 const click=async(selector,text)=>{const find=()=>[...document.querySelectorAll(selector)].find(e=>e.textContent.includes(text));await wait(()=>find()&&!find().disabled);find().click()};
 await wait(()=>document.querySelector('#title')?.textContent==='Front-facing neutral base');
 if(!document.querySelector('#page-title').textContent.includes('front-facing'))throw Error('Wrong workflow copy');
 if(document.querySelectorAll('#poses button').length!==1)throw Error('Auxiliary poses leaked into canonical review');
 document.querySelector('#reviewer').value='Synthetic canonical browser test';
 await click('#generate','Generate');
 await wait(async()=>{const s=await state();return s.batches.length===1&&s.batches[0].status==='completed'});
 await click('.card button','Reject / flag');await wait(async()=>(await state()).events.some(e=>e.action==='reject'));
 await click('#generate','Generate five more');
 await wait(async()=>{const s=await state();return s.batches.length===2&&s.batches[1].status==='completed'});
 await wait(()=>document.querySelectorAll('.card').length===10);
 document.querySelector('.card .image-button').click();if(!document.querySelector('#viewer').open)throw Error('Comparison failed');document.querySelector('#close-view').click();
 await click('.card button','Approve canonical base');
 await wait(async()=>Boolean((await state()).canonical_reference));
 await click('#finish','Save canonical selection');await wait(async()=>(await state()).exports.length===1);
 const s=await state();if(s.poses.canonical.status!=='approved'||!s.canonical_reference)throw Error('No frozen base');
 await wait(()=>document.querySelector('#generate').disabled);
 const seeds=s.batches.flatMap(b=>b.candidates.map(c=>c.seed));if(new Set(seeds).size!==10)throw Error('Repeated seeds');
 return {stage:'canonical-reviewer',status:'pass',synthetic:true,checks:['canonical-only view','five candidates','reject','five fresh seeds','history','comparison','approve','automatic freeze','selected export','approved generation blocked'],frozen:s.canonical_reference.sha256};
})()
