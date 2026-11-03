// Actual installed Cubism Core channel audit. No image-quality conclusion.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const [coreFile,modelFile,correspondenceFile]=process.argv.slice(2);
const source=fs.readFileSync(coreFile);const sandbox={console:{...console,log:console.error},require,process,Buffer,__dirname:path.dirname(path.resolve(coreFile)),__filename:path.resolve(coreFile),setTimeout,clearTimeout};
vm.createContext(sandbox);vm.runInContext(source.toString(),sandbox,{timeout:10000});
setTimeout(()=>{let moc,model;const report={status:'running',visual_acceptance:false,samples:[],core_sha256:crypto.createHash('sha256').update(source).digest('hex')};
try{
 const data=JSON.parse(fs.readFileSync(modelFile));const file=path.join(path.dirname(modelFile),data.FileReferences.Moc);const bytes=fs.readFileSync(file);
 const core=sandbox.Live2DCubismCore;moc=core.Moc.fromArrayBuffer(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));model=core.Model.fromMoc(moc);
 const ids=Array.from(model.parameters.ids),defaults=Array.from(model.parameters.defaultValues),drawables=Array.from(model.drawables.ids);
 model.update();
 const areas=index=>{const p=model.drawables.vertexPositions[index],t=model.drawables.indices[index],a=[];for(let j=0;j<t.length;j+=3){const u=t[j]*2,v=t[j+1]*2,w=t[j+2]*2;a.push((p[v]-p[u])*(p[w+1]-p[u+1])-(p[v+1]-p[u+1])*(p[w]-p[u]))}return a};
 const neutralAreas=drawables.map((_,i)=>areas(i));
 for(const eye of JSON.parse(fs.readFileSync(correspondenceFile)).eyes){
  const sourceIndex=drawables.indexOf(eye.source.split(':')[1]),closedIndex=drawables.indexOf(eye.closed.split(':')[1]);
  if(sourceIndex<0||closedIndex<0)throw Error('Missing discovered drawable');
  for(const head of [[0,0,0],[-12,12,-8],[12,-12,8]])for(const value of [0,.05,.1,.15,.2,.25,.35,.5,.65,.75,.9,1]){
   model.parameters.values.set(defaults);model.parameters.values[ids.indexOf(eye.side==='left'?'ParamEyeLOpen':'ParamEyeROpen')]=value;
   for(const [j,id] of ['ParamAngleX','ParamAngleY','ParamAngleZ'].entries())model.parameters.values[ids.indexOf(id)]=head[j];model.update();
   const a=model.drawables.opacities[sourceIndex],b=model.drawables.opacities[closedIndex];
   if(Math.abs(a-Math.max(0,Math.min(1,(value-.1)/.15)))>1e-5||Math.abs(b-Math.max(0,Math.min(1,(.35-value)/.1)))>1e-5)throw Error('Exported opacity differs from authored handoff');
   const triangles={};
   for(const [role,target] of Object.entries({source:eye.source,closed:eye.closed,white:eye.white,iris:eye.iris}).filter(([,t])=>t)){
    const i=drawables.indexOf(target.split(':')[1]);const current=areas(i),before=neutralAreas[i];
    triangles[role]={opacity:model.drawables.opacities[i],reversed_relative_to_open:current.filter((x,j)=>x*before[j]<-1e-12).length,near_zero:current.filter(x=>Math.abs(x)<1e-10).length};
   }
   report.samples.push({side:eye.side,value,head,source_opacity:a,closed_opacity:b,alpha_over_coverage:1-(1-a)*(1-b),triangles});
  }
 }
 report.visible_reversals=report.samples.flatMap(s=>Object.values(s.triangles)).filter(t=>t.opacity>1e-6).reduce((n,t)=>n+t.reversed_relative_to_open,0);
 if(report.visible_reversals)throw Error('Visible eye triangle reverses relative to open pose; keep candidate rejected');
 report.status='pass';
}catch(e){report.status='fail';report.error=String(e);process.exitCode=1}
finally{model?.release();moc?._release();console.log(JSON.stringify(report,null,2))}},1000);
