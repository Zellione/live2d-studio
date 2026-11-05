(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const report={stage:'generic-creation-preview',status:'running',frames:{},checks:[],control_noise_pixels:0,samples:{}};
 const check=(ok,name)=>{report.checks.push({name,pass:!!ok});if(!ok)throw Error(name)};
 try{
  for(let i=0;i<120&&!window.preview&&!window.previewError;i++)await wait(250);
  check(!!window.preview,'Actual Cubism model loaded');
  const p=window.preview,c=p.model.internalModel.coreModel;
  const pixels=()=>Array.from(p.app.renderer.extract.pixels(p.app.stage));
  const equal=reference=>{const current=pixels();return reference.every((v,i)=>v===current[i])};
  const capture=n=>{p.app.renderer.render(p.app.stage);report.frames[n]=p.app.view.toDataURL().split(',')[1];report.samples[n]={time:performance.now(),values:{...p.state.values},idle:p.state.idle,talking:p.state.talking,blinks:{...p.state.blinks}}};
  report.geometry={nonfinite:0,invalid_opacity:0,strict_opacity_excursions:0,raw_opacity_min:1,raw_opacity_max:0};
  p.app.ticker.add(()=>{const g=report.geometry;for(const a of c._model.drawables.vertexPositions)for(const v of a)if(!Number.isFinite(v))g.nonfinite++;
   for(const v of c._model.drawables.opacities){g.raw_opacity_min=Math.min(g.raw_opacity_min,v);g.raw_opacity_max=Math.max(g.raw_opacity_max,v);if(v<0||v>1)g.strict_opacity_excursions++;if(!Number.isFinite(v)||v < -8*2**-23||v > 1+8*2**-23)g.invalid_opacity++}});
  const mode=document.querySelector('#compare');mode.checked=true;mode.dispatchEvent(new Event('change'));await wait(1600);
  document.querySelector('[data-expression="angry"]').click();await wait(80);document.querySelector('[data-expression="confused"]').click();await wait(1600);
  check(p.state.expression==='confused','Comparison mode keeps latest click');
  check(['idle','talk','blink-left','blink-right','ParamAngleX','ParamAngleY','ParamAngleZ'].every(id=>document.getElementById(id).disabled),'Comparison mode locks moving controls');
  document.querySelector('[data-expression="angry"]').click();await wait(80);document.querySelector('#reset').click();await wait(1600);
  check(p.state.expression==='neutral','Neutral button cancels pending comparison');
  mode.checked=false;mode.dispatchEvent(new Event('change'));
  await p.compare('neutral');const neutral=pixels();capture('neutral');
  const names=['neutral','angry','confused','embarrassed','happy','sad','surprised'];
  for(const name of names){
   await p.compare(name);capture('face-'+name);
   const s=p.state;
   check(!s.idle&&!s.talking&&!s.talkWeight&&!Object.keys(s.blinks).length&&['ParamAngleX','ParamAngleY','ParamAngleZ'].every(k=>s.values[k]===0),'Controlled still '+name);
   // Browser layout is identical; all images come from the same canvas transform.
   const still=pixels();await wait(100);check(equal(still),'Stable settled '+name);
   for(const v of [0,.05,.1,.15,.2,.25,.35,.5,.65,.75,.9,1]){
    p.state.manual={ParamEyeLOpen:v*s.values.ParamEyeLOpen,ParamEyeROpen:v*s.values.ParamEyeROpen,ParamMouthOpenY:v};
    // Use expression resting eye factors, never an accumulated previous override.
    const base=report.samples['face-'+name].values;
    p.state.manual.ParamEyeLOpen=v*base.ParamEyeLOpen;p.state.manual.ParamEyeROpen=v*base.ParamEyeROpen;
    await wait(60);capture('blink-talk-'+name+'-'+String(v).replace('.','_'));
    check(Math.abs(p.state.values.ParamEyeLOpen-v*base.ParamEyeLOpen)<1e-5&&Math.abs(p.state.values.ParamEyeROpen-v*base.ParamEyeROpen)<1e-5&&Math.abs(p.state.values.ParamMouthOpenY-v)<1e-5,'Independent blink and talk '+name+' '+v);
   }
   p.state.manual={};p.talk(true);p.idle(true);
   for(let i=0;i<4;i++){await wait(100);capture('idle-expression-'+name+'-'+i)}
   await p.compare('neutral');capture('return-'+name);check(equal(neutral),'Exact neutral '+name);
  }
  for(let i=0;i<21;i++){await p.expression(names[i%names.length]);await wait(55);capture('switch-'+i)}
  await p.compare('neutral');capture('reset');check(equal(neutral),'Rapid switching returns exactly');
  check(!report.geometry.nonfinite&&!report.geometry.invalid_opacity,'Finite geometry and bounded opacity');
  check(performance.getEntriesByType('resource').every(e=>new URL(e.name).origin===location.origin),'Only local assets');report.status='pass';
 }catch(e){report.status='fail';report.error=String(e)}
 window.phase4b3Frames=report.frames;report.frames=Object.keys(report.frames);report.remote_frames=true;
 return report;
})()
