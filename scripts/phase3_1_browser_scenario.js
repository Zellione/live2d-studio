(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms)), report={stage:'phase3-1-standalone',status:'running',frames:{},checks:[]};
 const check=(ok,name)=>{report.checks.push({name,pass:!!ok});if(!ok)throw Error(name);};
 try{
  for(let i=0;i<60&&!window.preview&&!window.previewError;i++)await wait(250);
  check(!!window.preview,'Real model loaded');const p=window.preview,c=p.model.internalModel.coreModel;
  report.geometry={samples:0,nonfinite:0,raw_opacity_min:1,raw_opacity_max:0,strict_opacity_excursions:0,invalid_opacity:0};
  p.model.internalModel.on('beforeModelUpdate',()=>{
    const g=report.geometry;g.samples++;
    for(const v of c._model.drawables.vertexPositions)for(const x of v)if(!Number.isFinite(x))g.nonfinite++;
    for(const o of c._model.drawables.opacities){g.raw_opacity_min=Math.min(g.raw_opacity_min,o);g.raw_opacity_max=Math.max(g.raw_opacity_max,o);if(o<0||o>1)g.strict_opacity_excursions++;if(!Number.isFinite(o)||o < -8*2**-23||o>1+8*2**-23)g.invalid_opacity++;}
  });
  const capture=name=>{p.app.renderer.render(p.app.stage);report.frames[name]=p.app.view.toDataURL().split(',')[1];};
  const verts=pattern=>Array.from(c._model.drawables.ids).flatMap((id,i)=>pattern.test(id)?Array.from(c._model.drawables.vertexPositions[i]):[]);
  const changed=(a,b)=>a.some((v,i)=>Math.abs(v-b[i])>1e-6);
  const pixels=()=>p.app.renderer.extract.pixels(p.app.stage);
  const neutralize=async()=>{await p.reset();await wait(1100);};
  await neutralize();let neutral=pixels();capture('neutral');
  check(neutral.some((v,i)=>i%4===3&&v>0),'Visible raster from real Core drawables');
  report.core_version=Live2DCubismCore.Version.csmGetVersion();report.expressions={};
  for(const b of document.querySelectorAll('[data-expression]')){
   b.click();await wait(1000);check(p.state.expression===b.dataset.expression,`Expression ${b.dataset.expression} selected`);
   // Keep head/body at identical coordinates for recognition evidence.
   p.state.manual={ParamAngleX:0,ParamAngleY:0,ParamAngleZ:0};await wait(250);
   capture('face-'+b.dataset.expression);report.expressions[b.dataset.expression]={...p.state.values};
   if(b.dataset.expression!=='neutral')check(changed(Array.from(neutral),Array.from(pixels())),`Face pixels change: ${b.dataset.expression}`);
   const before=verts(/Mouth/);document.querySelector('#talk').click();await wait(170);check(changed(before,verts(/Mouth/)),`Talk geometry during ${b.dataset.expression}`);
   document.querySelector('#blink-left').click();await wait(115);capture('combined-'+b.dataset.expression);
   check(p.state.values.ParamEyeLOpen<.12&&p.state.values.ParamEyeROpen>.2,`Independent left blink: ${b.dataset.expression}`);
   document.querySelector('#talk').click();await wait(400);
  }
  await neutralize();
  for(const [id,value,pattern] of [['ParamMouthOpenY',.85,/Mouth/],['ParamAngleX',12,/Face|Eye/],['ParamAngleY',12,/Face|Eye/],['ParamAngleZ',12,/Face|Eye/]]){
   const a=verts(pattern),input=document.getElementById(id);input.value=value;input.dispatchEvent(new Event('input'));await wait(400);
   check(Math.abs(p.state.values[id]-value)<.01,`${id} survives runtime reset`);check(changed(a,verts(pattern)),`${id} changes corresponding geometry`);capture('control-'+id);await neutralize();
  }
  document.querySelector('#blink-right').click();await wait(115);check(p.state.values.ParamEyeROpen<.12&&p.state.values.ParamEyeLOpen>.9,'Independent right blink');await wait(400);
  document.querySelector('#idle').click();const a=verts(/Face|Eye/);await wait(900);check(changed(a,verts(/Face|Eye/)),'Authored Idle changes geometry');
  // Manual control must also win while Idle is running.
  const input=document.getElementById('ParamAngleX');input.value=10;input.dispatchEvent(new Event('input'));await wait(300);check(Math.abs(p.state.values.ParamAngleX-10)<.01,'Manual head override during Idle');
  await neutralize();capture('reset');const reset=pixels();report.neutral_reset_changed_channels=Array.from(neutral).filter((v,i)=>v!==reset[i]).length;
  check(report.neutral_reset_changed_channels===0,'Reset restores exact neutral pixels');
  document.querySelector('[data-expression="happy"]').click();await wait(200);capture('transition-1');document.querySelector('[data-expression="angry"]').click();await wait(200);capture('transition-2');await wait(800);capture('transition-3');
  const angry=report.expressions.angry.ParamMouthForm;
  check(Math.abs(p.state.values.ParamMouthForm-angry)<.01,'Transition reaches target without stuck parameters');
  document.querySelector('[data-expression="happy"]').click();await wait(150);
  const mid=p.state.values.ParamMouthForm;
  check(Math.abs(mid-angry)>.01&&Math.abs(mid-report.expressions.happy.ParamMouthForm)>.01,'Expression transition has an intermediate blend');
  await wait(800);
  for(const name of ['happy','sad','angry','surprised','confused','embarrassed']){
    await p.expression(name);await wait(600);
    p.state.manual={ParamAngleX:15,ParamAngleY:-15,ParamAngleZ:15,ParamEyeLOpen:0,ParamEyeROpen:0,ParamMouthOpenY:1};await wait(120);capture('stress-'+name);
    check(p.state.values.ParamEyeLOpen===0&&p.state.values.ParamEyeROpen===0&&p.state.values.ParamMouthOpenY===1,'Combined eyes/head/mouth '+name);
    p.state.manual={};
  }
  check(report.geometry.nonfinite===0&&report.geometry.invalid_opacity===0,'Finite geometry and valid opacity throughout all sampled poses');
  for(const v of c._model.drawables.vertexPositions)check(Array.from(v).every(Number.isFinite),'Finite Core geometry');
  await neutralize();
  document.querySelector('[data-expression="happy"]').click();
  for(let i=0;i<12;i++){await wait(70);capture('transition-clip-'+String(i).padStart(2,'0'));}
  document.querySelector('[data-expression="angry"]').click();
  for(let i=12;i<24;i++){await wait(70);capture('transition-clip-'+String(i).padStart(2,'0'));}
  await neutralize();
  const urls=performance.getEntriesByType('resource').map(e=>e.name);report.resource_urls=urls;
  check(urls.every(u=>new URL(u).origin===location.origin&&!u.includes('/api/')),'Only standalone local assets; no backend/classifier');
  check(!window.previewError,'No renderer errors');report.status='pass';
 }catch(e){report.status='fail';report.error=String(e);}
 return report;
})()
