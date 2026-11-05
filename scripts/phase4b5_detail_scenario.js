// Render the same exported geometry at higher pixel density, never crop the input.
(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const report={stage:'generic-creation-preview',status:'running',frames:{},checks:[],samples:{},render_resolution:3};
 const check=(pass,name)=>{report.checks.push({name,pass:!!pass});if(!pass)throw Error(name)};
 try{
  for(let i=0;i<120&&!window.preview&&!window.previewError;i++)await wait(250);
  check(!!window.preview,'Actual Cubism loaded');
  const p=window.preview,c=p.model.internalModel.coreModel;
  report.geometry={nonfinite:0,invalid_opacity:0,strict_opacity_excursions:0,raw_opacity_min:1,raw_opacity_max:0};
  p.app.ticker.add(()=>{const g=report.geometry;
   for(const a of c._model.drawables.vertexPositions)for(const v of a)if(!Number.isFinite(v))g.nonfinite++;
   for(const v of c._model.drawables.opacities){g.raw_opacity_min=Math.min(g.raw_opacity_min,v);g.raw_opacity_max=Math.max(g.raw_opacity_max,v);if(v<0||v>1)g.strict_opacity_excursions++;if(!Number.isFinite(v)||v < -8*2**-23||v > 1+8*2**-23)g.invalid_opacity++}
  });
  p.app.renderer.resolution=3;p.app.renderer.resize(600,650);
  const capture=name=>{p.app.renderer.render(p.app.stage);report.frames[name]=p.app.view.toDataURL().split(',')[1];report.samples[name]={values:{...p.state.values}}};
  await p.compare('neutral');capture('neutral');
  const neutral=p.app.view.toDataURL();
  await wait(100);p.app.renderer.render(p.app.stage);
  check(p.app.view.toDataURL()===neutral,'Stable high-resolution neutral');
  report.control_noise_pixels=0;
  const openings=[0,.05,.1,.15,.25,.5,.75,1];
  for(const name of ['neutral','happy','sad','angry','surprised','confused','embarrassed']){
   await p.compare(name);capture('full-'+name);
   const mode=document.querySelector('#mouth-only');mode.checked=true;mode.dispatchEvent(new Event('change'));
   await p.compare(name);capture('mouth-'+name);
   for(const v of openings){p.state.manual={...p.state.manual,ParamMouthOpenY:v};await wait(70);capture('open-'+name+'-'+String(v).replace('.','_'))}
   mode.checked=false;mode.dispatchEvent(new Event('change'));
  }
  for(const [name,ids] of [['left',['ParamEyeLOpen']],['right',['ParamEyeROpen']],['both',['ParamEyeLOpen','ParamEyeROpen']]]){
   await p.compare('neutral');
   for(const v of [0,.05,.1,.15,.2,.25,.35,.5,.65,.75,.9,1]){
    p.state.manual=Object.fromEntries(ids.map(id=>[id,v]));await wait(70);capture(name+'-'+String(v).replace('.','_'));
   }
  }
  for(const id of ['ParamAngleX','ParamAngleY','ParamAngleZ'])for(const v of [-15,15]){
   await p.compare('neutral');p.state.manual={[id]:v};await wait(70);capture(id+'-'+v);
  }
  for(const x of [-12,12])for(const y of [-8,8])for(const z of [-5,5]){
   await p.compare('neutral');p.state.manual={ParamAngleX:x,ParamAngleY:y,ParamAngleZ:z,ParamEyeLOpen:.1,ParamEyeROpen:.5,ParamMouthOpenY:.75};await wait(70);capture('combined-'+[x,y,z].join('_'));
  }
  await p.compare('neutral');capture('reset');check(p.app.view.toDataURL()===neutral,'Exact high-resolution neutral return');
  check(p.app.view.width===1800&&p.app.view.height===1950,'Actual 3x rasterization, not image enlargement');
  check(!report.geometry.nonfinite&&!report.geometry.invalid_opacity,'Finite geometry and bounded opacity');
  report.status='pass';
 }catch(e){report.status='fail';report.error=String(e)}
 window.phase4b3Frames=report.frames;report.frames=Object.keys(report.frames);report.remote_frames=true;
 return report;
})()
