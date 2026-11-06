(async()=>{
 const wait=async f=>{for(let n=0;n<100;n++){if(await f())return;await new Promise(r=>setTimeout(r,100))}throw Error('Gesture reviewer did not load')};
 await wait(()=>document.querySelector('#poses button'));
 const response=await fetch('/api/state'),s=await response.json();
 if(s.workflow!=='canonical-helpers'||s.gesture_profile!=='chest-forearm-v1')throw Error('Wrong workflow');
 if(s.source.sha256!=='ab2a52ae59af22435b1c2595cb7ced24fdcd4ed5056b16496b8d2b482d78da3e')throw Error('Wrong canonical');
 if(s.identity_reference.sha256!=='98589fb8750ccfc3664935985fc42810381b2e09f22e1ae8cf4cd6dd45d39a2d')throw Error('Wrong original');
 await wait(()=>!document.querySelector('#identity-figure').hidden&&[...document.querySelectorAll('.references img')].every(i=>i.complete&&i.naturalWidth>0));
 await wait(()=>document.querySelectorAll('.card img').length>=5&&[...document.querySelectorAll('.card img')].every(i=>i.complete&&i.naturalWidth>0));
 if(s.batches.some(b=>b.candidates.some(c=>c.status!=='ready'||c.result.reference_latent_count!==3)))throw Error('Incomplete three-reference batch');
 document.querySelector('.card .image-button').click();if(!document.querySelector('#viewer').open)throw Error('No comparison');document.querySelector('#close-view').click();
 return {stage:'canonical-gesture-reviewer',status:'pass',mode:'read-only real Codel',reference_roles:['canonical geometry','target guide','original identity/style'],
   poses:Object.fromEntries(Object.entries(s.poses).map(([k,v])=>[k,v.status])),batches:s.batches.map(b=>({id:b.id,status:b.status,count:b.candidates.length})),approvals_created:false};
})()
