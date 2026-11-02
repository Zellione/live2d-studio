// Geometry/opacity evidence only; browser pixel tests are a separate gate.
const fs=require('node:fs'), vm=require('node:vm'), path=require('node:path'), crypto=require('node:crypto');
const [coreFile,mocFile,profile='phase1']=process.argv.slice(2);
if(!['phase1','basic'].includes(profile))throw Error('Profile must be phase1 or basic');
if(!coreFile||!mocFile)throw Error('Usage: CORE_JS MOC3');
const sandbox={console:{...console,log:console.error},require,process,Buffer,setTimeout,clearTimeout,
  __dirname:path.dirname(path.resolve(coreFile)),__filename:path.resolve(coreFile)};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync(coreFile,'utf8'),sandbox);
setTimeout(()=>{
  let moc,model;
  const report={stage:'rig-geometry',render_tested:false,checks:{}};
  try {
    const bytes=fs.readFileSync(mocFile);
    report.moc_sha256=crypto.createHash('sha256').update(bytes).digest('hex');
    const core=sandbox.Live2DCubismCore;
    moc=core.Moc.fromArrayBuffer(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));
    model=core.Model.fromMoc(moc);
    const ids=Array.from(model.parameters.ids);
    const capture=(pose={})=>{
      model.parameters.values.set(model.parameters.defaultValues);
      for(const [id,value]of Object.entries(pose)){
        const index=ids.indexOf(id);if(index<0)throw Error('Missing '+id);
        model.parameters.values[index]=value;
      }
      model.update();
      return Array.from(model.drawables.ids,(id,i)=>({id,vertices:Array.from(model.drawables.vertexPositions[i]),opacity:model.drawables.opacities[i]}));
    };
    const baseline=capture();
    const changed=(a,b)=>a.filter((d,i)=>Math.abs(d.opacity-b[i].opacity)>1e-5||d.vertices.some((v,j)=>Math.abs(v-b[i].vertices[j])>1e-5)).map(d=>d.id);
    const cases={ParamEyeLOpen:[0,.5],ParamEyeROpen:[0,.5],ParamMouthOpenY:[.5,1],ParamAngleX:[-25,25],ParamAngleY:[-20,20],ParamAngleZ:[-20,20]};
    if(profile==='phase1')cases.ParamMood=[-1,1];
    report.profile=profile;
    for(const [id,values]of Object.entries(cases)) {
      const samples=values.map(value=>capture({[id]:value}));
      const changes=samples.map(s=>changed(baseline,s));
      if(changes.some(c=>!c.length)||!changed(samples[0],samples[1]).length)throw Error('Unbound/constant parameter '+id);
      report.checks[id]={values,changed_drawables:changes};
    }
    const left=report.checks.ParamEyeLOpen.changed_drawables[0],right=report.checks.ParamEyeROpen.changed_drawables[0];
    if(left.some(id=>right.includes(id)))throw Error('Left/right blink affect shared drawable');
    const repeat=capture();
    if(changed(baseline,repeat).length)throw Error('Default pose did not restore');
    report.status='pass';
  }catch(error){report.status='fail';report.error=String(error);process.exitCode=1;}
  finally{model?.release();moc?._release();console.log(JSON.stringify(report,null,2));}
},1000);
