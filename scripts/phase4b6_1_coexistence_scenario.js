(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const report={stage:'body-runtime',status:'running',frames:{},samples:{},sequences:{},checks:[],control_noise_pixels:0,geometry:{nonfinite:0,invalid_opacity:0,strict_opacity_excursions:0,raw_opacity_min:1,raw_opacity_max:0}};
 const check=(v,name)=>{report.checks.push({name,pass:!!v});if(!v)throw Error(name)};
 try{
 for(let i=0;i<120&&!window.preview&&!window.previewError;i++)await wait(250);
 check(!!window.preview,'Actual Core loaded');const p=window.preview,d=p.model.internalModel.coreModel._model.drawables;
 const capture=n=>{p.app.renderer.render(p.app.stage);report.frames[n]=p.app.view.toDataURL().split(',')[1];report.samples[n]={time:performance.now(),values:{...p.state.values},talking:p.state.talking,idle:p.state.idle};const g=report.geometry;for(const a of d.vertexPositions)for(const v of a)if(!Number.isFinite(v))g.nonfinite++;for(const v of d.opacities){g.raw_opacity_min=Math.min(g.raw_opacity_min,v);g.raw_opacity_max=Math.max(g.raw_opacity_max,v);if(v<0||v>1)g.strict_opacity_excursions++;if(!Number.isFinite(v)||v < -8*2**-23||v>1+8*2**-23)g.invalid_opacity++}};
 await p.compare('neutral');capture('neutral');await p.compare('confused');capture('confused-rest');
 p.idle(true);const names=[];
 for(let i=0;i<120;i++){
 if(i===20)await p.gesture('Question');if(i===40)p.talk(true);if(i===85)p.talk(false);
 await wait(80);const n='confused-moving-'+i;capture(n);names.push(n);
 check(Math.abs(p.state.values.ParamMouthRound-1)<1e-5&&Math.abs(p.state.values.ParamMouthCurve)<1e-5,'Round questioning shape persists '+i);
 if(i<40||i>103)check(Math.abs(p.state.values.ParamMouthOpenY-.35)<1e-4,'Parted rest while moving '+i);
 }
 report.sequences['confused-moving']=names;
 check(Math.max(...names.map(n=>Math.abs(report.samples[n].values.ParamAngleX)))>1,'Visible head inputs coexist');
 check(Math.max(...names.map(n=>Math.abs(report.samples[n].values.ParamHairBack)))>.01,'Hair dynamics coexist');
 check(Math.max(...names.map(n=>report.samples[n].values.ParamBreath))>.1,'Breathing coexists');
 check(Math.max(...names.slice(40,85).map(n=>report.samples[n].values.ParamMouthOpenY))>.5,'Talking continues');
 await p.compare('confused');capture('confused-return');check(report.frames['confused-rest']===report.frames['confused-return'],'Talking/gesture returns exact confused rest');
 for(const emotion of ['confused','surprised']){await p.compare(emotion);for(let i=0;i<=100;i++){p.state.manual={ParamMouthOpenY:i/100};await wait(18);capture('dense-'+emotion+'-'+i)}}
 p.idle(true);const emotions=['happy','sad','angry','surprised','embarrassed','confused','neutral'];
 for(let i=0;i<28;i++){await p.expression(emotions[i%7]);await wait(40);capture('rapid-'+i)}
 await p.compare('confused');capture('rapid-confused-rest');check(report.frames['confused-rest']===report.frames['rapid-confused-rest'],'Rapid expression changes restore confused');
 await p.compare('neutral');capture('reset');check(report.frames.reset===report.frames.neutral,'Neutral clears expression channels');
 check(!report.geometry.nonfinite&&!report.geometry.invalid_opacity,'Finite geometry, valid opacity');report.status='pass';
 }catch(e){report.status='fail';report.error=String(e)}
 window.phase4b3Frames=report.frames;report.frames=Object.keys(report.frames);report.remote_frames=true;return report;
})()
