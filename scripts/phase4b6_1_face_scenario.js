(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 const report={stage:'generic-creation-preview',status:'running',frames:{},samples:{},checks:[],control_noise_pixels:0,geometry:{nonfinite:0,invalid_opacity:0},render_resolution:3};
 const check=(v,name)=>{report.checks.push({name,pass:!!v});if(!v)throw Error(name)};
 try{
 for(let i=0;i<120&&!window.preview&&!window.previewError;i++)await wait(250);
 check(!!window.preview,'Actual Core loaded');const p=window.preview;
 p.app.renderer.resolution=3;p.app.renderer.resize(600,650);
 const capture=n=>{p.app.renderer.render(p.app.stage);report.frames[n]=p.app.view.toDataURL().split(',')[1];report.samples[n]={values:{...p.state.values}}};
 await p.compare('neutral');capture('neutral');await wait(100);capture('stable');check(report.frames.neutral===report.frames.stable,'Identical settled control pixels');
 for(const name of ['neutral','happy','sad','angry','confused','surprised','embarrassed']){
 p.state.mouthOnly=false;await p.compare(name);capture('full-'+name);
 p.state.mouthOnly=true;await wait(100);capture('mouth-'+name);
 check(!p.state.idle&&!p.state.talking,'Settled still '+name);
 check(['ParamAngleX','ParamAngleY','ParamAngleZ'].every(id=>p.state.values[id]===0),'Head zero '+name);
 check(p.state.values.ParamEyeLOpen===1&&p.state.values.ParamEyeROpen===1,'Mouth-only identical eyes '+name);
 }
 p.state.mouthOnly=false;await p.compare('neutral');capture('reset');check(report.frames.neutral===report.frames.reset,'Exact neutral reset');report.status='pass';
 }catch(e){report.status='fail';report.error=String(e)}
 window.phase4b3Frames=report.frames;report.frames=Object.keys(report.frames);report.remote_frames=true;return report;
})()
