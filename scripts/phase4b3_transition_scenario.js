(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const values=[0,.05,.10,.15,.20,.25,.35,.50,.65,.75,.90,1];
 const report={stage:'generic-creation-preview',status:'running',frames:{},checks:[],control_noise_pixels:0,samples:{},sequences:{}};
 const check=(ok,name)=>{report.checks.push({name,pass:!!ok});if(!ok)throw Error(name)};
 try{
  for(let i=0;i<120&&!window.preview&&!window.previewError;i++)await wait(250);
  check(!!window.preview,'Actual Cubism model loaded');
  const p=window.preview,c=p.model.internalModel.coreModel;
  const pixels=()=>Array.from(p.app.renderer.extract.pixels(p.app.stage));
  const equalsNeutral=()=>{const current=pixels();return neutral.every((v,i)=>v===current[i])};
  const capture=n=>{p.app.renderer.render(p.app.stage);report.frames[n]=p.app.view.toDataURL().split(',')[1];report.samples[n]={time:performance.now(),values:{...p.state.values}}};
  const reset=async()=>{await p.reset();await wait(850)};
  report.geometry={nonfinite:0,invalid_opacity:0,strict_opacity_excursions:0,raw_opacity_min:1,raw_opacity_max:0};
  p.app.ticker.add(()=>{const g=report.geometry;for(const a of c._model.drawables.vertexPositions)for(const v of a)if(!Number.isFinite(v))g.nonfinite++;
   for(const v of c._model.drawables.opacities){g.raw_opacity_min=Math.min(g.raw_opacity_min,v);g.raw_opacity_max=Math.max(g.raw_opacity_max,v);if(v<0||v>1)g.strict_opacity_excursions++;if(!Number.isFinite(v)||v < -8*2**-23||v > 1+8*2**-23)g.invalid_opacity++}});
  await reset();const neutral=pixels();capture('neutral');await wait(100);check(equalsNeutral(),'Stable neutral');
  for(const [label,ids,curve] of [['left',['ParamEyeLOpen'],0],['right',['ParamEyeROpen'],0],['both',['ParamEyeLOpen','ParamEyeROpen'],0],['mouth',['ParamMouthOpenY'],0],['smile',['ParamMouthOpenY'],1],['frown',['ParamMouthOpenY'],-1]]){
   await reset();for(const v of values){p.state.manual={ParamMouthCurve:curve,...Object.fromEntries(ids.map(id=>[id,v]))};await wait(55);capture(label+'-'+String(v).replace('.','_'))}
  }
  // Continuous parameter trajectories pass through Cubism's actual keyform
  // interpolation at each rendered frame. Their parameter samples are retained.
  for(const [label,ids] of [['left',['ParamEyeLOpen']],['right',['ParamEyeROpen']],['both',['ParamEyeLOpen','ParamEyeROpen']],['mouth',['ParamMouthOpenY']]]){
   await reset();const names=[];
   for(let i=0;i<=40;i++){const v=label==='mouth'?Math.sin(Math.PI*i/40)**2:Math.cos(Math.PI*i/40)**2;
    p.state.manual=Object.fromEntries(ids.map(id=>[id,v]));await wait(30);const name='cycle-'+label+'-'+i;capture(name);names.push(name)}report.sequences['cycle-'+label]=names;
  }
  for(const name of ['neutral','happy','sad','angry','surprised','confused','embarrassed']){
   await reset();await p.expression(name);await wait(500);capture('face-'+name);p.talk(true);
   const names=[];for(let i=0;i<12;i++){p.state.manual={ParamAngleX:12*Math.sin(i/11*Math.PI*2),ParamAngleY:-8,ParamAngleZ:5,ParamEyeLOpen:Math.cos(i/11*Math.PI)**2,ParamEyeROpen:Math.cos(i/11*Math.PI)**2};await wait(65);const n='combined-'+name+'-'+i;capture(n);names.push(n)}report.sequences['combined-'+name]=names;
   await reset();capture('return-'+name);check(equalsNeutral(),'Exact neutral return '+name);
  }
  await reset();p.idle(true);p.talk(true);const names=[];
  for(let i=0;i<65;i++){await wait(50);const n='idle-talk-'+i;capture(n);names.push(n)}report.sequences['idle-talk']=names;
  const eye=names.map(n=>report.samples[n].values.ParamEyeLOpen);check(Math.min(...eye)<.2&&Math.max(...eye)>.9,'Authored idle blink coexists with talking');
  await reset();capture('reset');check(equalsNeutral(),'Exact final neutral');
  check(!report.geometry.nonfinite&&!report.geometry.invalid_opacity,'Finite geometry and bounded opacity');
  check(performance.getEntriesByType('resource').every(e=>new URL(e.name).origin===location.origin),'Only local assets');report.status='pass';
 }catch(e){report.status='fail';report.error=String(e)}
 // Transfer dense evidence in bounded chunks; a single CDP response containing
 // hundreds of full PNGs can exceed the WebSocket message-size limit.
 window.phase4b3Frames=report.frames;report.frames=Object.keys(report.frames);report.remote_frames=true;
 return report;
})()
