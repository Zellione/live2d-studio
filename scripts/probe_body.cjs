// Installed Core geometry audit, independent of parameter names or render claims.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const [coreFile,modelFile,inspectionFile,armMode]=process.argv.slice(2);
const source=fs.readFileSync(coreFile),sandbox={console:{...console,log:console.error},require,process,Buffer,__dirname:path.dirname(path.resolve(coreFile)),__filename:path.resolve(coreFile),setTimeout,clearTimeout};
vm.createContext(sandbox);vm.runInContext(source.toString(),sandbox,{timeout:10000});
setTimeout(()=>{let moc,model;const report={status:'running',render_tested:false,core_sha256:crypto.createHash('sha256').update(source).digest('hex'),samples:[]};
try{
 const data=JSON.parse(fs.readFileSync(modelFile)),inspection=JSON.parse(fs.readFileSync(inspectionFile));
 const bytes=fs.readFileSync(path.join(path.dirname(modelFile),data.FileReferences.Moc));
 moc=sandbox.Live2DCubismCore.Moc.fromArrayBuffer(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));model=sandbox.Live2DCubismCore.Model.fromMoc(moc);
 const ids=Array.from(model.parameters.ids),defaults=Array.from(model.parameters.defaultValues),d=model.drawables;
 const roles=Object.fromEntries(inspection.overview.layers.items.map(l=>[l.id,l.role+':'+l.side]));
 const names=Object.fromEntries(inspection.objects.filter(o=>o.layerId).map(o=>[o.target.slice(5),roles[o.layerId]||'generated']));
 const pose=values=>{model.parameters.values.set(defaults);for(const [id,v]of Object.entries(values)){if(!ids.includes(id))throw Error('Missing parameter '+id);model.parameters.values[ids.indexOf(id)]=v}model.update()};
 pose({});const neutral=d.vertexPositions.map(a=>Array.from(a));
 const area=(p,t,j)=>{const a=t[j]*2,b=t[j+1]*2,c=t[j+2]*2;return(p[b]-p[a])*(p[c+1]-p[a+1])-(p[b+1]-p[a+1])*(p[c]-p[a])};
 // Infer the actual rotation pivot from exported face vertices, not the ID.
 const faceIndex=Array.from(d.ids).findIndex(id=>names[id]==='face:none');
 if(faceIndex>=0&&ids.includes('ParamAngleZ')){
  pose({ParamAngleZ:5});const a=neutral[faceIndex],b=d.vertexPositions[faceIndex],count=a.length/2;
  let ax=0,ay=0,bx=0,by=0;for(let j=0;j<a.length;j+=2){ax+=a[j]/count;ay+=a[j+1]/count;bx+=b[j]/count;by+=b[j+1]/count}
  let dot=0,cross=0;for(let j=0;j<a.length;j+=2){const x=a[j]-ax,y=a[j+1]-ay,u=b[j]-bx,v=b[j+1]-by;dot+=x*u+y*v;cross+=x*v-y*u}
  const angle=Math.atan2(cross,dot),co=Math.cos(angle),si=Math.sin(angle),tx=bx-co*ax+si*ay,ty=by-si*ax-co*ay,det=2-2*co;
  if(det>1e-10){const x=((1-co)*tx-si*ty)/det,y=(si*tx+(1-co)*ty)/det,info=model.canvasinfo;let residual=0;
   for(let j=0;j<a.length;j+=2)residual=Math.max(residual,Math.hypot(co*a[j]-si*a[j+1]+tx-b[j],si*a[j]+co*a[j+1]+ty-b[j+1]));
   report.head_tilt_pivot={input:5,actual_degrees:angle*180/Math.PI,canvas:[info.CanvasOriginX+x*info.PixelsPerUnit,info.CanvasOriginY-y*info.PixelsPerUnit],normalized:[(info.CanvasOriginX+x*info.PixelsPerUnit)/info.CanvasWidth,(info.CanvasOriginY-y*info.PixelsPerUnit)/info.CanvasHeight],fit_max_source_pixels:residual*info.PixelsPerUnit};
  }
 }
 const sample=values=>{pose(values);const regions={};let nonfinite=0,visibleReversals=0,invisibleReversals=0;const reversals={};
 for(let i=0;i<d.count;i++){const p=d.vertexPositions[i],n=neutral[i],role=names[d.ids[i]]||'generated';let max=0,sum=0;
 for(let j=0;j<p.length;j+=2){if(!Number.isFinite(p[j])||!Number.isFinite(p[j+1]))nonfinite++;const dist=Math.hypot(p[j]-n[j],p[j+1]-n[j+1]);max=Math.max(max,dist);sum+=dist}
 const prev=regions[role]||{max:0,total:0,vertices:0};regions[role]={max:Math.max(prev.max,max),total:prev.total+sum,vertices:prev.vertices+p.length/2};
 const t=d.indices[i];for(let j=0;j<t.length;j+=3)if(area(p,t,j)*area(n,t,j)<-1e-12){if(d.opacities[i]>1e-6){visibleReversals++;reversals[d.ids[i]]=(reversals[d.ids[i]]||0)+1;}else invisibleReversals++}
 }for(const r of Object.values(regions)){r.mean=r.total/r.vertices;delete r.total}return {values,regions,nonfinite,visibleReversals,invisibleReversals,reversals}};
 for(const [id,v]of Object.entries({ParamAngleX:12,ParamAngleY:8,ParamAngleZ:5,ParamBreath:1,ParamBodyAngleX:2,ParamBodyAngleZ:1,ParamHairFront:1,ParamHairBack:1}))if(ids.includes(id))for(const sign of id==='ParamBreath'?[1]:[-1,1])report.samples.push(sample({[id]:v*sign}));
 for(let i=0;i<=480;i++){const t=i/30;report.samples.push(sample({ParamAngleX:10*Math.sin(t*Math.PI/8),ParamAngleY:6*Math.sin(t*Math.PI/4),ParamAngleZ:4*Math.sin(t*Math.PI/8),ParamBreath:.5-.5*Math.cos(t*Math.PI/2),ParamHairFront:.6*Math.sin(t*Math.PI/8-.4),ParamHairBack:.7*Math.sin(t*Math.PI/8-.7),ParamBodyAngleX:1.5*Math.sin(t*Math.PI/8+.5),ParamBodyAngleZ:.6*Math.sin(t*Math.PI/4),ParamEyeLOpen:Math.cos(t*Math.PI)**2,ParamEyeROpen:Math.cos(t*Math.PI+.1)**2,ParamMouthOpenY:.5+.5*Math.sin(t*7)}))}
 if(armMode==='--arms'){for(const id of ['ParamArmRightOpen','ParamArmLeftOpen'])if(!ids.includes(id))throw Error('Missing arm parameter '+id);for(let i=0;i<=100;i++){const t=i/100;report.samples.push(sample({ParamArmRightOpen:Math.sin(t*Math.PI)**2,ParamArmLeftOpen:Math.sin(t*2*Math.PI)**2,ParamAngleX:10*Math.sin(t*2*Math.PI),ParamAngleY:6*Math.cos(t*2*Math.PI),ParamAngleZ:4*Math.sin(t*Math.PI),ParamBodyAngleX:1.5*Math.sin(t*Math.PI),ParamBodyAngleZ:.6*Math.cos(t*Math.PI),ParamBreath:t,ParamEyeLOpen:Math.cos(t*Math.PI)**2,ParamEyeROpen:Math.cos(t*Math.PI)**2,ParamMouthOpenY:t}));}report.arm_combination_samples=101;}
 report.nonfinite=report.samples.reduce((s,v)=>s+v.nonfinite,0);report.visible_reversals=report.samples.reduce((s,v)=>s+v.visibleReversals,0);pose({});report.exact_neutral_return=d.vertexPositions.every((a,i)=>a.every((v,j)=>v===neutral[i][j]));
 report.status=!report.nonfinite&&!report.visible_reversals&&report.exact_neutral_return?'pass':'fail';if(report.status==='fail')process.exitCode=1;
}catch(e){report.status='fail';report.error=String(e);process.exitCode=1}finally{model?.release();moc?._release();console.log(JSON.stringify(report,null,2))}},1000);
