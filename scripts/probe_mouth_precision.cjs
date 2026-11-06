// Isolate opening/eye dependencies and quantify float32 interpolation noise.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const [coreFile,modelFile,inspectionFile]=process.argv.slice(2);
const sandbox={console:{...console,log:console.error},require,process,Buffer,__dirname:path.dirname(path.resolve(coreFile)),setTimeout,clearTimeout};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync(coreFile,'utf8'),sandbox);
setTimeout(()=>{let moc,m;try{
 const data=JSON.parse(fs.readFileSync(modelFile)),bytes=fs.readFileSync(path.join(path.dirname(modelFile),data.FileReferences.Moc));
 moc=sandbox.Live2DCubismCore.Moc.fromArrayBuffer(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));m=sandbox.Live2DCubismCore.Model.fromMoc(moc);
 const inspection=JSON.parse(fs.readFileSync(inspectionFile));const surface=inspection.surfaces.find(s=>s.kind==='source-neutral');const target=surface.target.split(':')[1],index=Array.from(m.drawables.ids).indexOf(target);
 const ids=Array.from(m.parameters.ids),defs=Array.from(m.parameters.defaultValues),set=(k,v)=>{m.parameters.values[ids.indexOf(k)]=v};
 const report={target,canvas:m.canvasinfo,expressions:{}};
 for(const e of data.FileReferences.Expressions){const exp=JSON.parse(fs.readFileSync(path.join(path.dirname(modelFile),e.File)));const groups={};
 for(const mode of ['opening','eyes','both','repeat']){let rest;const samples=[];
 for(let j=0;j<=100;j++){m.parameters.values.set(defs);for(const p of exp.Parameters){const i=ids.indexOf(p.Id);set(p.Id,p.Blend==='Multiply'?defs[i]*p.Value:p.Blend==='Overwrite'?p.Value:defs[i]+p.Value)}
 const v=j/100;if(mode==='opening'||mode==='both')set('ParamMouthOpenY',v);if(mode==='eyes'||mode==='both'){set('ParamEyeLOpen',v);set('ParamEyeROpen',v)}
 m.update();const a=Array.from(m.drawables.vertexPositions[index]);rest??=a;
 let max=0,ulps=0;for(let i=0;i<a.length;i++){const d=Math.abs(a[i]-rest[i]);max=Math.max(max,d);const step=2**(Math.floor(Math.log2(Math.max(Math.abs(a[i]),Math.abs(rest[i]),2**-126)))-23);ulps=Math.max(ulps,d/step)}samples.push({opening:v,max,ulps});}
 groups[mode]={max:Math.max(...samples.map(s=>s.max)),ulps:Math.max(...samples.map(s=>s.ulps)),samples};}
 report.expressions[e.Name]=groups;}
 console.log(JSON.stringify(report,null,2));
 }catch(e){console.error(e);process.exitCode=1}finally{m?.release();moc?._release()}},1000);
