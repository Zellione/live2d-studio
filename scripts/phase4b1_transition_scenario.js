(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const report={stage:'generic-creation-preview',status:'running',frames:{},checks:[],control_noise_pixels:0,talking:{}};
 const check=(ok,name)=>{report.checks.push({name,pass:!!ok});if(!ok)throw Error(name)};
 try{
  for(let i=0;i<120&&!window.preview&&!window.previewError;i++)await wait(250);
  check(!!window.preview,'Actual Cubism model loaded');
  const p=window.preview,c=p.model.internalModel.coreModel;
  const capture=n=>{p.app.renderer.render(p.app.stage);report.frames[n]=p.app.view.toDataURL().split(',')[1]};
  const pixels=()=>Array.from(p.app.renderer.extract.pixels(p.app.stage));
  const reset=async()=>{await p.reset();await wait(850)};
  report.geometry={nonfinite:0,invalid_opacity:0,strict_opacity_excursions:0,raw_opacity_min:1,raw_opacity_max:0};
  p.app.ticker.add(()=>{const g=report.geometry;for(const a of c._model.drawables.vertexPositions)for(const v of a)if(!Number.isFinite(v))g.nonfinite++;
   for(const v of c._model.drawables.opacities){g.raw_opacity_min=Math.min(g.raw_opacity_min,v);g.raw_opacity_max=Math.max(g.raw_opacity_max,v);if(v<0||v>1)g.strict_opacity_excursions++;if(!Number.isFinite(v)||v < -8*2**-23||v > 1+8*2**-23)g.invalid_opacity++}});
  await reset();const neutral=pixels();capture('neutral');await wait(200);const repeat=pixels();check(neutral.every((v,i)=>v===repeat[i]),'Stable neutral');
  for(const name of ['neutral','happy','sad','angry','surprised','confused','embarrassed']){
   await reset();await p.expression(name);p.state.manual={ParamAngleX:0,ParamAngleY:0,ParamAngleZ:0};await wait(850);p.talk(true);
   const values=[];for(let i=0;i<10;i++){await wait(100);capture('talk-'+name+'-'+i);values.push(p.state.values.ParamMouthOpenY)}
   report.talking[name]=values;check(Math.max(...values)-Math.min(...values)>.03,'Non-frozen talk envelope during '+name);
   p.talk(false);await p.expression('neutral');
   for(let i=0;i<4;i++){await wait(150);capture('fade-'+name+'-'+i)}
   await reset();const restored=pixels();check(neutral.every((v,i)=>v===restored[i]),'Exact neutral restoration from '+name);
  }
  for(const [name,id] of [['blink','ParamEyeLOpen'],['mouth','ParamMouthOpenY']]){
   await reset();for(let i=0;i<=10;i++){p.state.manual={[id]:name==='blink'?1-i/10:i/10};await wait(70);capture(name+'-ramp-'+i)}
  }
  await reset();capture('reset');check(!report.geometry.nonfinite&&!report.geometry.invalid_opacity,'Finite geometry and bounded opacity');
  check(performance.getEntriesByType('resource').every(e=>new URL(e.name).origin===location.origin),'Only local assets');report.status='pass';
 }catch(e){report.status='fail';report.error=String(e)}return report;
})()
