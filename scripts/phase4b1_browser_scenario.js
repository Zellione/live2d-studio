(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const report={stage:'generic-creation-preview',status:'running',frames:{},checks:[],control_noise_pixels:0};
 const check=(ok,name)=>{report.checks.push({name,pass:!!ok});if(!ok)throw Error(name);};
 try{
  for(let i=0;i<120&&!window.preview&&!window.previewError;i++)await wait(250);
  check(!!window.preview,'Actual Cubism model loaded');
  const p=window.preview,c=p.model.internalModel.coreModel;
  const verts=()=>Array.from(c._model.drawables.vertexPositions).flatMap(v=>Array.from(v));
  const changed=(a,b)=>a.some((v,i)=>Math.abs(v-b[i])>1e-6);
  const pixels=()=>Array.from(p.app.renderer.extract.pixels(p.app.stage));
  const capture=name=>{p.app.renderer.render(p.app.stage);report.frames[name]=p.app.view.toDataURL().split(',')[1];};
  const reset=async()=>{await p.reset();await wait(850);};
  report.geometry={nonfinite:0,invalid_opacity:0,strict_opacity_excursions:0,raw_opacity_min:1,raw_opacity_max:0};
  p.app.ticker.add(()=>{
   const g=report.geometry;
   for(const x of verts())if(!Number.isFinite(x))g.nonfinite++;
   for(const v of c._model.drawables.opacities){g.raw_opacity_min=Math.min(g.raw_opacity_min,v);g.raw_opacity_max=Math.max(g.raw_opacity_max,v);if(v<0||v>1)g.strict_opacity_excursions++;if(!Number.isFinite(v)||v < -8*2**-23||v > 1+8*2**-23)g.invalid_opacity++;}
  });
  await reset();const neutral=pixels();capture('neutral');await wait(200);
  const repeat=pixels();report.control_noise_pixels=neutral.filter((v,i)=>v!==repeat[i]).length;
  check(report.control_noise_pixels===0,'Stable paused neutral');
  check(neutral.some((v,i)=>i%4===3&&v>0),'Visible model');
  for(const [id,values] of [['ParamEyeLOpen',[0,.25,.5,.75,1]],['ParamEyeROpen',[0,.25,.5,.75,1]],['ParamMouthOpenY',[0,.25,.5,.75,1]],['ParamMouthCurve',[-1,1]],['ParamAngleX',[-12,12]],['ParamAngleY',[-12,12]],['ParamAngleZ',[-12,12]],['ParamEyeBallX',[-.6,.6]],['ParamEyeBallY',[-.6,.6]]]){
   for(const value of values){await reset();const before=verts();p.state.manual={[id]:value};await wait(180);
    if(!((id.includes('Eye')&&value===1)||(id==='ParamMouthOpenY'&&value===0)))check(changed(before,verts()),id+' changes vertices at '+value);capture('pose-'+id+'-'+String(value).replace('.','_'));}
  }
  report.expressions={};
  for(const name of ['neutral','happy','sad','angry','surprised','confused','embarrassed']){
   await reset();await p.expression(name);p.state.manual={ParamAngleX:0,ParamAngleY:0,ParamAngleZ:0};await wait(850);
   capture('face-'+name);report.expressions[name]={...p.state.values};
   if(name!=='neutral')check(changed(neutral,pixels()),name+' changes facial pixels with head locked');
   const before=verts();p.talk(true);await wait(190);check(changed(before,verts()),'Talking during '+name);capture('talk-'+name);p.talk(false);
   p.state.manual={ParamAngleX:12,ParamAngleY:-12,ParamAngleZ:8,ParamEyeLOpen:0,ParamEyeROpen:0,ParamMouthOpenY:.8};await wait(180);capture('combined-'+name);await reset();capture('return-'+name);check(!changed(neutral,pixels()),'Exact return from '+name);
  }
  await reset();const before=verts();p.idle(true);await wait(1000);check(changed(before,verts()),'Authored idle moves geometry');
  await reset();capture('reset');check(!changed(neutral,pixels()),'Neutral reset is exact');
  check(!report.geometry.nonfinite&&!report.geometry.invalid_opacity,'Finite geometry and bounded opacity');
  const urls=performance.getEntriesByType('resource').map(e=>e.name);report.resource_urls=urls;
  check(urls.every(u=>new URL(u).origin===location.origin&&!u.includes('/api/')),'Only local assets; no backend');
  check(!window.previewError,'No renderer errors');report.status='pass';
 }catch(error){report.status='fail';report.error=String(error);}
 return report;
})()
