(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const report={stage:'body-runtime',status:'running',frames:{},samples:{},sequences:{},checks:[],control_noise_pixels:0,geometry:{nonfinite:0,invalid_opacity:0,strict_opacity_excursions:0,raw_opacity_min:1,raw_opacity_max:0}};
 const check=(v,n)=>{report.checks.push({name:n,pass:!!v});if(!v)throw Error(n)};
 try{
 for(let i=0;i<120&&!window.preview&&!window.previewError;i++)await wait(250);
 check(window.preview,'Model loaded');const p=window.preview,c=p.model.internalModel.coreModel,d=c._model.drawables;
 let neutralVertices;
 const capture=name=>{p.app.renderer.render(p.app.stage);report.frames[name]=p.app.view.toDataURL().split(',')[1];report.samples[name]={time:performance.now(),values:{...p.state.values},displacement:d.vertexPositions.map((a,i)=>{let max=0,sum=0,dx=0,dy=0;const n=neutralVertices[i];for(let j=0;j<a.length;j+=2){const x=a[j]-n[j],y=a[j+1]-n[j+1],v=Math.hypot(x,y);max=Math.max(max,v);sum+=v;dx+=x;dy+=y}return {id:d.ids[i],max,mean:sum/(a.length/2),dx:dx/(a.length/2),dy:dy/(a.length/2)}}),canvas:c._model.canvasinfo}};
 const reset=async()=>{await p.reset();await wait(800)};
 p.app.ticker.add(()=>{const g=report.geometry;for(const a of d.vertexPositions)for(const v of a)if(!Number.isFinite(v))g.nonfinite++;for(const v of d.opacities){g.raw_opacity_min=Math.min(g.raw_opacity_min,v);g.raw_opacity_max=Math.max(g.raw_opacity_max,v);if(v<0||v>1)g.strict_opacity_excursions++;if(!Number.isFinite(v)||v < -8*2**-23||v>1+8*2**-23)g.invalid_opacity++}});
 await reset();neutralVertices=d.vertexPositions.map(a=>Array.from(a));capture('neutral');
 report.pixels_per_core_unit=Math.abs(p.model.internalModel.localTransform.a*p.model.scale.x)*c._model.canvasinfo.PixelsPerUnit;
 if(p.peers.length>1)check(p.peers.every(m=>m.scale.x===p.model.scale.x),'Comparison equal scale');
 for(const [id,max]of Object.entries({ParamAngleX:12,ParamAngleY:8,ParamAngleZ:5,ParamBreath:1,ParamBodyAngleX:2,ParamHairFront:1,ParamHairBack:1})){
  const names=[];for(let i=0;i<=16;i++){p.state.manual={[id]:id==='ParamBreath'?Math.sin(i*Math.PI/16)**2:max*Math.sin(i*Math.PI/8)};await wait(35);const n=id+'-'+i;capture(n);names.push(n)}report.sequences[id]=names;
 }
 await reset();p.idle(true);const names=[];for(let i=0;i<=128;i++){await wait(125);const n='idle-'+i;capture(n);names.push(n)}report.sequences.idle=names;
 for(const name of ['neutral','happy','sad','angry','surprised','confused','embarrassed']){await p.expression(name);p.talk(true);const names=[];for(let i=0;i<16;i++){await wait(65);const n='talk-'+name+'-'+i;capture(n);names.push(n)}report.sequences['talk-'+name]=names}
 if(p.gesture)for(const name of p.gestures){const emotion=p.state.expression;await p.gesture(name);const names=[];for(let i=0;i<32;i++){await wait(100);const n='gesture-'+name+'-'+i;capture(n);names.push(n)}report.sequences['gesture-'+name]=names;check(p.state.expression===emotion,'Gesture preserves '+emotion);check(Math.max(...names.map(n=>report.samples[n].values.ParamMouthOpenY))-Math.min(...names.map(n=>report.samples[n].values.ParamMouthOpenY))>.2,'Talk continues in '+name)}
 await reset();p.idle(true);
 for(const kind of ['head','body','hair']){const input=document.querySelector('#enable-'+kind);input.checked=false;input.dispatchEvent(new Event('change'));}
 await wait(200);capture('controls-off');check(['ParamAngleX','ParamAngleY','ParamAngleZ','ParamBreath','ParamBodyAngleX','ParamBodyAngleZ','ParamHairFront','ParamHairBack'].every(id=>p.state.values[id]===0),'Head body hair switches disable actual channels');
 for(const kind of ['head','body','hair']){const input=document.querySelector('#enable-'+kind);input.checked=true;input.dispatchEvent(new Event('change'));}
 await reset();p.idle(true);p.state.manual={ParamAngleX:10,ParamAngleZ:4,ParamBodyAngleX:0,ParamBodyAngleZ:0};await wait(1000);
 const physicsNames=[];p.state.manual={ParamAngleX:0,ParamAngleY:0,ParamAngleZ:0,ParamBodyAngleX:0,ParamBodyAngleZ:0};
 for(let i=0;i<=48;i++){await wait(60);const n='hair-release-'+i;capture(n);physicsNames.push(n)}report.sequences['hair-release']=physicsNames;
 await reset();capture('reset');check(report.frames.reset===report.frames.neutral,'Exact neutral image return');
 check(!report.geometry.nonfinite&&!report.geometry.invalid_opacity,'Finite geometry and bounded opacity');report.status='pass';
 }catch(e){report.status='fail';report.error=String(e)}
 window.phase4b3Frames=report.frames;report.frames=Object.keys(report.frames);report.remote_frames=true;return report;
})()
