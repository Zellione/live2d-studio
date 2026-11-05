(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const report={stage:'generic-creation-preview',status:'running',frames:{},checks:[],samples:{},control_noise_pixels:0};
 const check=(ok,name)=>{report.checks.push({name,pass:!!ok});if(!ok)throw Error(name)};
 try{
  for(let i=0;i<120&&!window.preview&&!window.previewError;i++)await wait(250);
  check(!!window.preview,'Actual Cubism loaded');const p=window.preview,c=p.model.internalModel.coreModel;
  const ids=c._model.parameters.ids,defs=c._model.parameters.defaultValues;
  const nonmouth=Object.fromEntries(Array.from(ids).map((id,i)=>[id,defs[i]]).filter(([id])=>!id.startsWith('ParamMouth')));
  const pixels=()=>Array.from(p.app.renderer.extract.pixels(p.app.stage));
  const equal=a=>{const b=pixels();return a.every((x,i)=>x===b[i])};
  report.geometry={nonfinite:0,invalid_opacity:0,strict_opacity_excursions:0,parameter_range_violations:0,raw_opacity_min:1,raw_opacity_max:0};
  p.app.ticker.add(()=>{const g=report.geometry;for(let i=0;i<ids.length;i++)if(ids[i].startsWith('ParamMouth')){const v=c._model.parameters.values[i];if(!Number.isFinite(v)||v<c._model.parameters.minimumValues[i]-1e-6||v>c._model.parameters.maximumValues[i]+1e-6)g.parameter_range_violations++;}for(const a of c._model.drawables.vertexPositions)for(const v of a)if(!Number.isFinite(v))g.nonfinite++;
   for(const v of c._model.drawables.opacities){g.raw_opacity_min=Math.min(g.raw_opacity_min,v);g.raw_opacity_max=Math.max(g.raw_opacity_max,v);if(v<0||v>1)g.strict_opacity_excursions++;if(!Number.isFinite(v)||v < -8*2**-23||v > 1+8*2**-23)g.invalid_opacity++}});
  const capture=n=>{p.app.renderer.render(p.app.stage);report.frames[n]=p.app.view.toDataURL().split(',')[1];report.samples[n]={values:{...p.state.values},idle:p.state.idle,talking:p.state.talking}};
  await p.compare('neutral');capture('neutral');const neutral=pixels();
  const names=['neutral','happy','sad','angry','confused','surprised','embarrassed'];
  for(const name of names){
   p.state.mouthOnly=false;document.querySelector('#mouth-only').checked=false;await p.compare(name);capture('full-'+name);
   const mouthOnly=document.querySelector('#mouth-only');mouthOnly.checked=true;mouthOnly.dispatchEvent(new Event('change'));await wait(1600);capture('mouth-'+name);const rest=pixels();const restValues={...p.state.values};
   check(Object.entries(nonmouth).every(([k,v])=>Math.abs(p.state.values[k]-v)<1e-5),'Identical non-mouth values '+name);
   check(!p.state.idle&&!p.state.talking&&!p.state.talkWeight,'Still mouth '+name);
   for(const v of [0,.05,.1,.15,.25,.5,.75,1]){
    p.state.manual={...nonmouth,ParamMouthOpenY:v};await wait(65);capture('open-'+name+'-'+String(v).replace('.','_'));
    check(Math.abs(p.state.values.ParamMouthOpenY-v)<1e-5,'Bounded explicit opening '+name+' '+v);
   }
   p.state.manual={...nonmouth};p.talk(true);
   for(let i=0;i<10;i++){await wait(80);capture('talk-'+name+'-'+i);check(p.state.values.ParamMouthOpenY>=0&&p.state.values.ParamMouthOpenY<=1,'Bounded talk '+name+' '+i)}
   p.talk(false);await wait(900);capture('talk-return-'+name);check(equal(rest),'Talking restores emotional mouth '+name);
   for(const v of [0,.1,.5,1]){p.state.manual={ParamMouthOpenY:v,ParamEyeLOpen:v,ParamEyeROpen:v,ParamAngleX:12,ParamAngleY:-8,ParamAngleZ:5};await wait(65);capture('combined-'+name+'-'+String(v).replace('.','_'))}
   await p.compare('neutral');check(equal(neutral),'Exact neutral return '+name);
   report.samples['mouth-'+name].rest_values=restValues;
  }
  // Diagnose actual visible effect, including the imported but hidden Form axis.
  for(const id of ['ParamMouthCurve','ParamMouthDispleasure','ParamMouthSkew','ParamMouthForm'])if(Array.from(ids).includes(id)){
   await p.compare('neutral');for(const v of [-1,0,1]){p.state.manual={...nonmouth,[id]:v};await wait(80);capture('axis-'+id+'-'+v)}
  }
  for(let i=0;i<28;i++){await p.expression(names[i%7]);await wait(50);capture('switch-'+i)}
  await p.compare('neutral');check(equal(neutral),'Rapid switching exact neutral');
  check(!report.geometry.nonfinite&&!report.geometry.invalid_opacity&&!report.geometry.parameter_range_violations,'Finite geometry, opacity and bounded mouth parameters throughout');
  const mode=document.querySelector('#compare');mode.checked=false;mode.dispatchEvent(new Event('change'));check(!p.state.mouthOnly&&!document.querySelector('#mouth-only').checked,'Leaving comparison restores normal facial controls');
  check(performance.getEntriesByType('resource').every(e=>new URL(e.name).origin===location.origin),'Only local assets');report.status='pass';
 }catch(e){report.status='fail';report.error=String(e)}
 window.phase4b3Frames=report.frames;report.frames=Object.keys(report.frames);report.remote_frames=true;return report;
})()
