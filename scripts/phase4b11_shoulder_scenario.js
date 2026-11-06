(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const report={status:'running',frames:{},samples:{},checks:[],sequences:{},control_noise_pixels:0,geometry:{nonfinite:0,invalid_opacity:0,strict_opacity_excursions:0}};
 const check=(ok,name)=>{report.checks.push({name,pass:!!ok});if(!ok)throw Error(name)};
 try{
  for(let i=0;i<120&&!window.preview&&!window.previewError;i++)await wait(250);
  check(window.preview,'Frontal model loaded');const p=window.preview,c=p.model.internalModel.coreModel,d=c._model.drawables;
  const reset=async()=>{await p.reset();await wait(800)};
  await reset();const rest=d.vertexPositions.map(a=>Array.from(a));
  const capture=name=>{for(const a of d.vertexPositions)for(const v of a)if(!Number.isFinite(v))report.geometry.nonfinite++;for(const v of d.opacities){if(v<0||v>1)report.geometry.strict_opacity_excursions++;if(!Number.isFinite(v)||v < -8*2**-23||v>1+8*2**-23)report.geometry.invalid_opacity++;}p.app.renderer.render(p.app.stage);report.frames[name]=p.app.view.toDataURL().split(',')[1];
   report.samples[name]={values:{...p.state.values},drawables:d.ids.map((id,i)=>{const a=d.vertexPositions[i];let delta=0;for(let j=0;j<a.length;j++)delta=Math.max(delta,Math.abs(a[j]-rest[i][j]));return {id,delta,opacity:d.opacities[i]}})};};
  capture('neutral');await wait(60);capture('neutral-repeat');check(report.frames.neutral===report.frames['neutral-repeat'],'Stable neutral control');
  for(const side of ['Right','Left']){
   const id='ParamArm'+side+'Open';check(c._model.parameters.ids.includes(id),id+' present');
   const names=[];
   for(let i=0;i<=40;i++){p.state.manual={[id]:i<=20?i/20:(40-i)/20};await wait(40);const n=side+'-'+i;capture(n);names.push(n)}
   report.sequences[side]=names;
   const allMoved=report.samples[side+'-20'].drawables.filter(x=>x.delta>1e-6);
   const hidden=allMoved.filter(x=>x.opacity<=1e-6),moved=allMoved.filter(x=>x.opacity>1e-6);
   check(hidden.length===(c._model.parameters.ids.includes('ParamArm'+side[0]+'Elbow')?1:0),'Only the concealed elbow overlap is additionally moved while invisible');
   check(moved.length===3,'Exactly three visible original '+side+' arm meshes move');
   const prefix=side==='Right'?'ArtMeshHandwearL':'ArtMeshHandwearR';
   check(moved.every(x=>x.id.startsWith(prefix)),'Correct anatomical '+side+' ownership; torso/head/opposite arm fixed');
   check(Math.max(...moved.map(x=>x.delta))>.01,side+' visible Core displacement');
   await reset();capture(side+'-reset');check(report.frames[side+'-reset']===report.frames.neutral,side+' exact neutral return');
  }
  for(const side of ['Right','Left']){
   await reset();p.idle(true);p.talk(true);p.state.manual={ParamAngleX:8,ParamAngleY:3};
   await p.gesture('Arm'+side);const names=[];
   for(let i=0;i<38;i++){await wait(100);const n='talk-head-'+side+'-'+i;capture(n);names.push(n)}
   report.sequences['talk-head-'+side]=names;
   const values=names.map(n=>report.samples[n].values);
   check(Math.max(...values.map(x=>x['ParamArm'+side+'Open']))>.9,side+' motion clip reaches gesture');
   check(Math.max(...values.map(x=>x.ParamMouthOpenY))-Math.min(...values.map(x=>x.ParamMouthOpenY))>.2,'Talking continues during '+side);
   check(values.every(x=>x.ParamAngleX===8),'Head movement coexists with '+side);
  }
  await reset();capture('final-reset');check(report.frames['final-reset']===report.frames.neutral,'Final exact neutral return');
  check(d.vertexPositions.every(a=>Array.from(a).every(Number.isFinite)),'Finite final geometry');
  check(!report.geometry.nonfinite&&!report.geometry.invalid_opacity,'Finite sampled geometry and bounded opacity');report.status='pass';
 }catch(e){report.status='fail';report.error=String(e)}
 window.phase4b3Frames=report.frames;report.frames=Object.keys(report.frames);report.remote_frames=true;return report;
})()
