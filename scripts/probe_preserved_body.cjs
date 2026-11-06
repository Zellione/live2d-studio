// Compare actual Core vertices at identical body/eye parameters, independently of
// expression recipes. All drawables except explicitly authored mouth/brow surfaces
// must remain bit-identical. Raw deltas are retained, never thresholded away.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const [coreFile,beforeFile,afterFile,inspectionFile]=process.argv.slice(2);
const context={console:{...console,log:console.error},require,process,Buffer,__dirname:path.dirname(path.resolve(coreFile)),setTimeout,clearTimeout};vm.createContext(context);vm.runInContext(fs.readFileSync(coreFile,'utf8'),context);
setTimeout(()=>{const pairs=[];try{
 const core=context.Live2DCubismCore;
 for(const file of [beforeFile,afterFile]){const d=JSON.parse(fs.readFileSync(file)),b=fs.readFileSync(path.join(path.dirname(file),d.FileReferences.Moc));const moc=core.Moc.fromArrayBuffer(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));pairs.push({moc,m:core.Model.fromMoc(moc)})}
 const inspection=JSON.parse(fs.readFileSync(inspectionFile)),layers=Object.fromEntries(inspection.overview.layers.items.map(l=>[l.id,l]));
 const authored=new Set(inspection.objects.filter(o=>['mouth','eyebrow'].includes(layers[o.layerId]?.role)||layers[o.layerId]?.name.startsWith('facial-mouth-')||layers[o.layerId]?.name==='Generated cheek tint').map(o=>o.target.split(':')[1]));
 const maxima={},frames=[];for(let n=0;n<=480;n++){
 const t=n/480*2*Math.PI;const values={ParamAngleX:12*Math.sin(t),ParamAngleY:8*Math.sin(2*t),ParamAngleZ:5*Math.sin(t+.4),ParamBreath:(1-Math.cos(4*t))/2,ParamBodyAngleX:2*Math.sin(3*t),ParamBodyAngleZ:Math.sin(t),ParamHairFront:.6*Math.sin(5*t),ParamHairBack:.8*Math.sin(5*t-.4),ParamEyeLOpen:(1+Math.cos(7*t))/2,ParamEyeROpen:(1+Math.cos(7*t))/2};
 for(const {m} of pairs){m.parameters.values.set(m.parameters.defaultValues);const ids=Array.from(m.parameters.ids);for(const [id,v]of Object.entries(values))m.parameters.values[ids.indexOf(id)]=v;m.update()}
 const [a,b]=pairs.map(p=>p.m);let changed=0;for(let i=0;i<a.drawables.ids.length;i++){const id=a.drawables.ids[i];if(authored.has(id))continue;const j=Array.from(b.drawables.ids).indexOf(id);if(j<0)throw Error('Lost drawable '+id);const x=a.drawables.vertexPositions[i],y=b.drawables.vertexPositions[j];if(x.length!==y.length)throw Error('Changed topology '+id);let delta=0;for(let k=0;k<x.length;k++)delta=Math.max(delta,Math.abs(x[k]-y[k]));maxima[id]=Math.max(maxima[id]||0,delta);if(delta!==0)changed++}frames.push({n,changed});
 }
 const pass=Object.values(maxima).every(v=>v===0);console.log(JSON.stringify({status:pass?'pass':'fail',samples:frames.length,maxima,excluded_authored_surfaces:[...authored]},null,2));if(!pass)process.exitCode=1;
 }catch(e){console.error(e);process.exitCode=1}finally{for(const p of pairs){p.m.release();p.moc._release()}}},1000);
