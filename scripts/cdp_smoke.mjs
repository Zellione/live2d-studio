// Dependency-free CDP driver for a dedicated local test browser only.
import fs from 'node:fs/promises';
const [endpoint, url, script, output] = process.argv.slice(2);
if (!endpoint || !url || !script || !output) throw Error('Usage: ENDPOINT URL SCRIPT OUTPUT_DIR');
for (const value of [endpoint, url]) {
  if (new URL(value).hostname !== '127.0.0.1') throw Error('Loopback only');
}
const target = await (await fetch(`${endpoint}/json/new?${encodeURIComponent(url)}`, {method:'PUT'})).json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
let next=0;
const pending=new Map(), events=[];
ws.onmessage=({data})=>{
  const message=JSON.parse(data);
  if(message.id) {
    const waiter=pending.get(message.id);
    if(waiter){pending.delete(message.id);message.error?waiter.reject(Error(JSON.stringify(message.error))):waiter.resolve(message.result);}
  } else if(['Runtime.consoleAPICalled','Runtime.exceptionThrown','Network.responseReceived','Network.loadingFailed'].includes(message.method)) {
    events.push(message);
  }
};
function send(method,params={}) {
  return new Promise((resolve,reject)=>{
    const id=++next;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));
  });
}
await fs.mkdir(output,{recursive:true});
const timeout=setTimeout(()=>{console.error('CDP test timed out');process.exit(2);},90000);
try {
  await send('Runtime.enable');await send('Network.enable');await send('Page.enable');
  await send('Page.navigate',{url});
  let ready=false;
  for(let i=0;i<60;i++){
    const r=await send('Runtime.evaluate',{expression:'document.readyState',returnByValue:true});
    if(r.result.value==='complete'){ready=true;break;}
    await new Promise(r=>setTimeout(r,500));
  }
  if(!ready)throw Error('Document not ready');
  const expression=await fs.readFile(script,'utf8');
  const result=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,timeout:60000});
  const frames=result.result.value?.frames;
  if(frames) {
    for(const [name,data] of Object.entries(frames)) {
      if(!/^[a-zA-Z0-9_-]+$/.test(name)) throw Error('Invalid frame name');
      await fs.writeFile(`${output}/${name}.png`,Buffer.from(data,'base64'));
    }
    result.result.value.frames=Object.keys(frames);
  }
  if(['sillytavern-extension','phase1-animation','phase2-basic'].includes(result.result.value?.stage)) {
    const value=result.result.value;
    const phase1=value.stage==='phase1-animation';
    const phase2=value.stage==='phase2-basic';
    const assetRoot=phase2?'/assets/live2d/phase2/':phase1?'/assets/live2d/phase1/':'/assets/live2d/phase0/';
    const responses=events.filter(e=>e.method==='Network.responseReceived').map(e=>e.params.response);
    const expected=phase2?['.model3.json','.moc3','/texture_00.png','.idle.motion3.json']:phase1?['.model3.json','.moc3','/texture_00.png','.phase1Idle.motion3.json',
      '.phase1_neutral.exp3.json','.phase1_happy.exp3.json','.phase1_angry.exp3.json']:
      ['.model3.json','.moc3','/texture_00.png','.idle.motion3.json',
      '.nod.motion3.json','.smile.exp3.json','.sad.exp3.json','.angry.exp3.json','.surprised.exp3.json'];
    const missing=expected.filter(suffix=>!responses.some(r=>r.url.includes(assetRoot) && r.url.endsWith(suffix) && r.status===200));
    const unexpectedHttp=responses.filter(r=>r.url.includes(assetRoot) && r.status>=400 && !r.url.endsWith('/sillytavern_settings.json'));
    const exceptions=events.filter(e=>e.method==='Runtime.exceptionThrown');
    value.network_validation={missing_successful_resources:missing,unexpected_http_errors:unexpectedHttp.map(r=>({url:r.url,status:r.status})),uncaught_exceptions:exceptions.length};
    if(missing.length || unexpectedHttp.length || exceptions.length)value.status='fail';
  }
  await fs.writeFile(`${output}/result.json`,JSON.stringify(result,null,2));
  const screenshot=await send('Page.captureScreenshot',{format:'png'});
  await fs.writeFile(`${output}/screenshot.png`,Buffer.from(screenshot.data,'base64'));
  if(result.exceptionDetails || result.result.value?.status!=='pass')process.exitCode=1;
  console.log(JSON.stringify(result.result.value ?? result.exceptionDetails,null,2));
} finally {
  // Keep only console text, exceptions, response status/URL; never cookies/headers.
  const sanitized=events.map(e=>({method:e.method,
    text:e.params.args?.map(a=>a.value===undefined?a.description:String(a.value)),
    exception:e.params.exceptionDetails?.text,
    url:e.params.response?.url,status:e.params.response?.status,
    error:e.params.errorText}));
  await fs.writeFile(`${output}/browser-events.json`,JSON.stringify(sanitized,null,2));
  clearTimeout(timeout);ws.close();
}
