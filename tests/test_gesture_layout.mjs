// Local integration test: actual Chrome page zoom, layout bounds and Core motion.
import fs from 'node:fs/promises';
const [endpoint,single,comparison,old,output]=process.argv.slice(2);
for(const url of [endpoint,single,comparison,old])if(new URL(url).hostname!=='127.0.0.1')throw Error('Loopback only');
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const report={status:'running',layouts:[],clicks:[]},connections=[];
async function connect(url){
 const target=await(await fetch(`${endpoint}/json/new?${encodeURIComponent(url)}`,{method:'PUT'})).json();
 const ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
 let next=0;const pending=new Map();
 ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const [r,j]=pending.get(m.id);pending.delete(m.id);m.error?j(Error(JSON.stringify(m.error))):r(m.result)}};
 const send=(method,params={})=>new Promise((r,j)=>{const id=++next;pending.set(id,[r,j]);ws.send(JSON.stringify({id,method,params}))});
 const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.text);return r.result.value};
 const page={send,evaluate,ws};connections.push(page);return page;
}
function check(ok,message){if(!ok)throw Error(message)}
async function ready(page,expression){for(let i=0;i<150;i++){if(await page.evaluate(expression))return;await wait(200)}throw Error('Page did not become ready')}
const inspect=`(()=>{
 const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};
 const bounds=rect(document.querySelector('aside')),container=rect(document.querySelector('#gestures'));
 const inside=r=>r.x>=bounds.x-.5&&r.right<=bounds.right+.5&&r.y>=bounds.y-.5&&r.bottom<=bounds.bottom+.5;
 const buttons=[...document.querySelectorAll('#gestures>button')].map(b=>({text:b.textContent,...rect(b),scrollWidth:b.scrollWidth,clientWidth:b.clientWidth,inside:inside(rect(b))}));
 return {bounds,container,inside:inside(container),buttons,width:innerWidth,dpr:devicePixelRatio,
 documentOverflow:document.documentElement.scrollWidth>innerWidth,
 columns:getComputedStyle(document.querySelector('#gestures')).gridTemplateColumns,
 otherRows:[...document.querySelectorAll('.row')].filter(e=>e.children.length===2&&e.firstElementChild.tagName==='BUTTON').map(e=>({display:getComputedStyle(e).display,wrap:getComputedStyle(e).flexWrap})),error:window.previewError};
})()`;
try{
 const settings=await connect('chrome://settings/appearance');await ready(settings,'!!chrome.settingsPrivate');
 const zoom=async factor=>{await settings.evaluate(`new Promise((r,j)=>chrome.settingsPrivate.setDefaultZoom(${factor},()=>chrome.runtime.lastError?j(Error(chrome.runtime.lastError.message)):r()))`);await wait(120)};
 async function resize(page,width){const {windowId}=await page.send('Browser.getWindowForTarget');await page.send('Browser.setWindowBounds',{windowId,bounds:{width,height:1000}});await wait(150)}
 const broken=await connect(old);await ready(broken,'!!window.preview');await zoom(1.4);await resize(broken,1440);
 report.negativeControl=await broken.evaluate(inspect);
 check(report.negativeControl.buttons.some(b=>!b.inside),'Old layout must reproduce overflow');
 await fs.writeFile(output+'/before.png',Buffer.from((await broken.send('Page.captureScreenshot',{format:'png'})).data,'base64'));
 for(const [mode,url] of [['single',single],['comparison',comparison]]){
  const page=await connect(url);await ready(page,'!!window.preview');await page.evaluate('window.preview.reset()');
  check(await page.evaluate('window.preview.gestures.length===6'),'Expected all six gestures');
  const labels=await page.evaluate('[...document.querySelectorAll("#gestures>button")].map(b=>b.textContent)');
  for(const factor of [1,1.25,1.4,1.5,2]){
   await zoom(factor);
   for(const width of [1440,960,640]){
    await resize(page,width);
    for(const translated of [false,true]){
     await page.evaluate(`document.querySelectorAll('#gestures>button').forEach((b,i)=>b.textContent=${translated?JSON.stringify(['Rechten Unterarm vorsichtig zur Brust anheben und wieder absenken','LinkerUnterarmMitSehrLangerZusammengesetzterGestenbezeichnungOhneLeerzeichen'.repeat(2),'腕をゆっくり持ち上げて元の位置へ戻す'.repeat(5)]):JSON.stringify(labels)}[i%${translated?3:6}])`);
     const result=await page.evaluate(inspect);report.layouts.push({mode,factor,windowWidth:width,translated,...result});
     check(Math.abs(result.dpr-factor)<.001,'Actual browser zoom must match requested factor');
     check(result.inside&&result.buttons.length===6&&result.buttons.every(b=>b.inside&&b.scrollWidth<=b.clientWidth+1),'Gesture/text overflow: '+JSON.stringify(report.layouts.at(-1)));
     check(!result.documentOverflow,'Horizontal document overflow: '+JSON.stringify(report.layouts.at(-1)));
     check(result.columns.split(' ').length===2,'Two columns required');
     check(result.otherRows.every(r=>r.display==='flex'&&r.wrap==='nowrap'),'Existing two-button rows changed');
     check(!result.error,'Viewer error');
    }
   }
  }
  await zoom(1.4);await resize(page,1440);
  await page.evaluate(`document.querySelectorAll('#gestures>button').forEach((b,i)=>b.textContent=${JSON.stringify(labels)}[i]);document.querySelector('#gestures').scrollIntoView({block:'center'})`);await wait(100);
  await fs.writeFile(output+'/'+mode+'-140.png',Buffer.from((await page.send('Page.captureScreenshot',{format:'png'})).data,'base64'));
  const controls={Nod:'ParamAngleY',Question:'ParamAngleZ',ArmRight:'ParamArmRightOpen',ArmLeft:'ParamArmLeftOpen',ElbowRight:'ParamArmRElbow',ElbowLeft:'ParamArmLElbow'};
  for(const [name,id] of Object.entries(controls)){
   await page.evaluate('window.preview.reset()');await wait(750);
   const point=await page.evaluate(`(()=>{const p=window.preview;window.layoutRest=p.model.internalModel.coreModel._model.drawables.vertexPositions.map(a=>Array.from(a));const b=document.querySelectorAll('#gestures>button')[p.gestures.indexOf(${JSON.stringify(name)})];b.scrollIntoView({block:'center'});const r=b.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,disabled:b.disabled}})()`);
   check(!point.disabled,'Gesture enabled');await page.send('Page.bringToFront');
   await page.send('Input.dispatchMouseEvent',{type:'mousePressed',x:point.x,y:point.y,button:'left',clickCount:1});
   await page.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:point.x,y:point.y,button:'left',clickCount:1});
   const motion=await page.evaluate(`(async()=>{let peak=0,displacement=0;for(let i=0;i<40;i++){await new Promise(r=>setTimeout(r,50));peak=Math.max(peak,Math.abs(window.preview.state.values[${JSON.stringify(id)}]));const d=window.preview.model.internalModel.coreModel._model.drawables;d.vertexPositions.forEach((a,k)=>{if(d.opacities[k]>.001)a.forEach((v,j)=>displacement=Math.max(displacement,Math.abs(v-window.layoutRest[k][j])))})}return {peak,displacement,error:window.previewError}})()`);
   report.clicks.push({mode,name,parameter:id,...motion});check(motion.peak>.2&&motion.displacement>1e-6&&!motion.error,'Intended visible motion did not play: '+name);
  }
 }
 report.status='pass';
}catch(error){report.status='fail';report.error=String(error);process.exitCode=1}
finally{await fs.writeFile(output+'/result.json',JSON.stringify(report,null,2));for(const c of connections)c.ws.close()}
console.log(JSON.stringify({status:report.status,layouts:report.layouts.length,clicks:report.clicks.length,error:report.error}));
