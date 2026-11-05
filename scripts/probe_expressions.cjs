// Exported Core geometry at expression/blink/talk/head combinations. No perception score.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const [coreFile,modelFile,inspectionFile]=process.argv.slice(2);
const source=fs.readFileSync(coreFile);const sandbox={console:{...console,log:console.error},require,process,Buffer,__dirname:path.dirname(path.resolve(coreFile)),__filename:path.resolve(coreFile),setTimeout,clearTimeout};
vm.createContext(sandbox);vm.runInContext(source.toString(),sandbox,{timeout:10000});
setTimeout(()=>{let moc,model;const report={status:'running',visual_acceptance:false,samples:[],core_sha256:crypto.createHash('sha256').update(source).digest('hex'),nonfinite:0,invalid_opacity:0,strict_opacity_excursions:0};
try{
 const data=JSON.parse(fs.readFileSync(modelFile));const bytes=fs.readFileSync(path.join(path.dirname(modelFile),data.FileReferences.Moc));
 const core=sandbox.Live2DCubismCore;moc=core.Moc.fromArrayBuffer(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));model=core.Model.fromMoc(moc);
 const ids=Array.from(model.parameters.ids),defaults=Array.from(model.parameters.defaultValues),drawables=Array.from(model.drawables.ids);
 const set=(k,v)=>{const i=ids.indexOf(k);if(i<0)throw Error('Missing parameter '+k);model.parameters.values[i]=v};
 const get=k=>model.parameters.values[ids.indexOf(k)];
 const areas=index=>{const p=model.drawables.vertexPositions[index],t=model.drawables.indices[index],a=[];for(let j=0;j<t.length;j+=3){const u=t[j]*2,v=t[j+1]*2,w=t[j+2]*2;a.push((p[v]-p[u])*(p[w+1]-p[u+1])-(p[v+1]-p[u+1])*(p[w]-p[u]))}return a};
 const inspection=JSON.parse(fs.readFileSync(inspectionFile));
 const recipe=JSON.parse(fs.readFileSync(path.join(path.dirname(inspectionFile),'expression-rig-recipe.json')));
 const targets=[...new Set([...inspection.brows.map(b=>b.mesh.target),...recipe.filter(s=>s.request.parameter.id==='ParamMouthDispleasure').flatMap(s=>s.request.shapes.map(f=>f.target))])];
 if(inspection.generated_artwork)targets.push(inspection.generated_artwork.target);
 model.update();const neutralAreas=drawables.map((_,i)=>areas(i));
 const neutral=model.drawables.vertexPositions.map(v=>Array.from(v)),neutralAlpha=Array.from(model.drawables.opacities);
 for(const e of data.FileReferences.Expressions){
  const expression=JSON.parse(fs.readFileSync(path.join(path.dirname(modelFile),e.File)));
  for(const head of [[0,0,0],[-12,-8,-5],[-12,-8,5],[-12,8,-5],[-12,8,5],[12,-8,-5],[12,-8,5],[12,8,-5],[12,8,5]])
   for(const v of [0,.05,.1,.15,.2,.25,.35,.5,.65,.75,.9,1]){
    model.parameters.values.set(defaults);
    for(const p of expression.Parameters)set(p.Id,p.Blend==='Multiply'?get(p.Id)*p.Value:p.Blend==='Overwrite'?p.Value:get(p.Id)+p.Value);
    for(const [i,k] of ['ParamAngleX','ParamAngleY','ParamAngleZ'].entries())set(k,head[i]);
    set('ParamEyeLOpen',get('ParamEyeLOpen')*v);set('ParamEyeROpen',get('ParamEyeROpen')*v);set('ParamMouthOpenY',v);model.update();
    for(const vertices of model.drawables.vertexPositions)for(const x of vertices)if(!Number.isFinite(x))report.nonfinite++;
    for(const x of model.drawables.opacities){if(x<0||x>1)report.strict_opacity_excursions++;if(!Number.isFinite(x)||x < -8*2**-23||x>1+8*2**-23)report.invalid_opacity++}
    const triangles={};
    for(const t of targets){const i=drawables.indexOf(t.split(':')[1]);if(i<0)throw Error('Missing drawable '+t);const current=areas(i);triangles[t]={opacity:model.drawables.opacities[i],reversed:current.filter((x,j)=>x*neutralAreas[i][j]<-1e-12).length}}
    report.samples.push({expression:e.Name,head,blink_talk:v,triangles});
   }
 }
 model.parameters.values.set(defaults);model.update();
 report.exact_neutral_geometry=model.drawables.vertexPositions.every((v,i)=>Array.from(v).every((x,j)=>x===neutral[i][j]))&&neutralAlpha.every((v,i)=>v===model.drawables.opacities[i]);
 report.visible_reversals=report.samples.flatMap(s=>Object.values(s.triangles)).filter(t=>t.opacity>1e-6).reduce((n,t)=>n+t.reversed,0);
 if(report.visible_reversals||report.nonfinite||report.invalid_opacity||!report.exact_neutral_geometry)throw Error('Expression geometry gate failed');
 report.status='pass';
}catch(e){report.status='fail';report.error=String(e);process.exitCode=1}
finally{model?.release();moc?._release();console.log(JSON.stringify(report,null,2))}},1000);
