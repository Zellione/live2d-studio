(async()=>{
 const wait=ms=>new Promise(r=>setTimeout(r,ms));const report={stage:'body-runtime',status:'running',frames:{},checks:[],control_noise_pixels:0,geometry:{nonfinite:0,invalid_opacity:0}};
 const check=(v,name)=>{report.checks.push({name,pass:!!v});if(!v)throw Error(name)};
 try{for(let i=0;i<120&&!window.preview&&!window.previewError;i++)await wait(250);const p=window.preview;check(p&&p.peers.length===2,'Two actual Cubism models');await p.compare('confused');p.state.mouthOnly=true;await wait(100);
 for(const m of p.peers){const c=m.internalModel.coreModel._model;check(Array.from(c.parameters.ids).every((id,i)=>id.startsWith('ParamMouth')||c.parameters.values[i]===c.parameters.defaultValues[i]),'Mouth-only neutralizes every non-mouth channel on both models')}
 check(p.peers[0].scale.x===p.peers[1].scale.x,'Equal scale');p.app.renderer.render(p.app.stage);report.frames.comparison=p.app.view.toDataURL().split(',')[1];p.state.mouthOnly=false;await p.compare('neutral');p.app.renderer.render(p.app.stage);report.frames.neutral=p.app.view.toDataURL().split(',')[1];report.status='pass';
 }catch(e){report.status='fail';report.error=String(e)}window.phase4b3Frames=report.frames;report.frames=Object.keys(report.frames);report.remote_frames=true;return report;
})()
