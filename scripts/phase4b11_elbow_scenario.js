(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const report={status:'running',frames:{},checks:[],sequences:{},samples:{},control_noise_pixels:0,geometry:{nonfinite:0,invalid_opacity:0,strict_opacity_excursions:0}};
 const check=(ok,name)=>{report.checks.push({name,pass:!!ok});if(!ok)throw Error(name)};
 try{
 for(let i=0;i<120&&!window.preview&&!window.previewError;i++)await wait(250);
 check(window.preview,'Loaded');const p=window.preview,c=p.model.internalModel.coreModel,d=c._model.drawables;const sides=['Right','Left'].filter(side=>c._model.parameters.ids.includes('ParamArm'+side[0]+'Elbow'));check(sides.length,'Elbow parameter present');
 const reset=async()=>{await p.reset();await wait(800)};await reset();const rest=d.vertexPositions.map(a=>Array.from(a));
 const capture=n=>{for(const a of d.vertexPositions)for(const x of a)if(!Number.isFinite(x))report.geometry.nonfinite++;for(const x of d.opacities){if(x<0||x>1)report.geometry.strict_opacity_excursions++;if(!Number.isFinite(x)||x < -8*2**-23||x>1+8*2**-23)report.geometry.invalid_opacity++;}p.app.renderer.render(p.app.stage);report.frames[n]=p.app.view.toDataURL().split(',')[1];report.samples[n]={values:{...p.state.values},moved:d.ids.filter((_,i)=>d.vertexPositions[i].some((v,j)=>Math.abs(v-rest[i][j])>1e-6))};};
 capture('neutral');await wait(80);capture('neutral-repeat');check(report.frames.neutral===report.frames['neutral-repeat'],'Stable neutral');
 for(const side of sides){const id='ParamArm'+side[0]+'Elbow';
 const names=[];for(let i=0;i<=100;i++){p.state.manual={[id]:i<=50?i/50:(100-i)/50};await wait(35);const n=side+'-sweep-'+i;capture(n);names.push(n)}report.sequences[side+'-sweep']=names;
 for(const value of [.1,.25,.5,.75,.9,1]){p.state.manual={[id]:value};await wait(70);capture(side+'-pose-'+Math.round(value*100))}
 check(report.samples[side+'-pose-100'].moved.length===2,'Only forearm and hand move; upper arm/shoulder unchanged');
 await reset();capture('restored');check(report.frames.neutral===report.frames.restored,'Exact neutral return');
 p.idle(true);p.talk(true);await p.expression('happy');p.state.manual={ParamAngleX:8,ParamAngleY:3};await p.gesture('Elbow'+side);const clip=[];
 for(let i=0;i<48;i++){p.state.manual={ParamAngleX:8*Math.sin(i/8),ParamAngleY:3*Math.cos(i/8),ParamBreath:.5-.5*Math.cos(i/6)};await wait(100);capture(side+'-clip-'+i);clip.push(side+'-clip-'+i)}report.sequences[side+'-clip']=clip;
 check(Math.max(...clip.map(n=>report.samples[n].values[id]))>.9,'Cubism clip reaches elbow endpoint');
 check(Math.max(...clip.map(n=>report.samples[n].values.ParamMouthOpenY))-Math.min(...clip.map(n=>report.samples[n].values.ParamMouthOpenY))>.2,'Talking coexists');
 check(Math.max(...clip.map(n=>report.samples[n].values['ParamArm'+side+'Open']))>.1,'Shoulder and elbow coordinated');
 for(let i=0;i<3;i++){await p.gesture('Elbow'+side);await wait(170);capture(side+'-repeat-'+i)}
 await reset();capture('interrupted-reset');check(report.frames.neutral===report.frames['interrupted-reset'],'Interruption resets exactly');
 }
 for(const name of ['Nod','Question']){
   await reset();p.idle(true);p.talk(true);p.state.manual={ParamArmRElbow:.65};await p.gesture(name);
   for(let i=0;i<30;i++){await wait(100);capture(name+'-held-elbow-'+i);check(p.state.values.ParamArmRElbow===.65||Math.abs(p.state.values.ParamArmRElbow-.65)<1e-6,'Head gesture preserves held elbow');}
 }
 await reset();capture('after-head-gestures');check(report.frames.neutral===report.frames['after-head-gestures'],'Neutral after head/talk coexistence');
 const config=await(await fetch('/config.json')).json();const reloaded=await PIXI.live2d.Live2DModel.from(config.model,{autoInteract:false,autoHitTest:false});
 const ri=reloaded.internalModel,rc=ri.coreModel,rd=rc._model.parameters;
 ri.eyeBlink=undefined;ri.physics=undefined;ri.updateFocus=()=>{};ri.updateNaturalMovements=()=>{};ri.motionManager.groups.idle='__paused__';ri.motionManager.stopAllMotions();
 ri.on('beforeModelUpdate',()=>rd.ids.forEach((id,i)=>rc.setParameterValueById(id,rd.defaultValues[i])));
 reloaded.scale.set(p.model.scale.x);reloaded.x=p.model.x;reloaded.y=p.model.y;p.app.stage.removeChild(p.model);p.app.stage.addChild(reloaded);await wait(300);
 p.app.renderer.render(p.app.stage);report.frames['reloaded-neutral']=p.app.view.toDataURL().split(',')[1];check(report.frames.neutral===report.frames['reloaded-neutral'],'Fresh model instance restores exact neutral render');
 check(!report.geometry.nonfinite&&!report.geometry.invalid_opacity,'Finite sampled geometry and bounded opacity');report.status='pass';report.visual_acceptance=false;
 }catch(e){report.status='fail';report.error=String(e)}
 window.phase4b3Frames=report.frames;report.frames=Object.keys(report.frames);report.remote_frames=true;return report;
})()
