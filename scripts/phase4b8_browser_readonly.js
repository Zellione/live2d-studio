(async()=>{
 const wait=async f=>{for(let n=0;n<80;n++){if(f())return;await new Promise(r=>setTimeout(r,100))}throw Error('Canonical reviewer did not load')};
 await wait(()=>document.querySelectorAll('.card').length>=5);
 await wait(()=>[...document.querySelectorAll('.card img')].every(i=>i.complete&&i.naturalWidth>0));
 const response=await fetch('/api/state'),s=await response.json();
 if(s.workflow!=='canonical'||Object.keys(s.poses).join()!=='canonical')throw Error('Wrong workflow');
 if(s.source.sha256!=='98589fb8750ccfc3664935985fc42810381b2e09f22e1ae8cf4cd6dd45d39a2d')throw Error('Wrong original');
 if(!document.querySelector('#page-title').textContent.includes('front-facing'))throw Error('Missing canonical title');
 document.querySelector('.card .image-button').click();
 if(!document.querySelector('#viewer').open)throw Error('No compare dialog');
 document.querySelector('#close-view').click();
 return {stage:'canonical-reviewer',status:'pass',mode:'read-only real Codel review',pose:s.poses.canonical.status,
   batches:s.batches.map(b=>({status:b.status,count:b.candidates.length})),freeze:s.canonical_reference||null};
})()
