// Dependency-free CDP driver for a dedicated local test browser only.
import fs from 'node:fs/promises';
const [endpoint, url, script, output, startupMock] = process.argv.slice(2);
if(startupMock && startupMock !== '--mock-startup-classifier') throw Error('Unknown option');
if (!endpoint || !url || !script || !output) throw Error('Usage: ENDPOINT URL SCRIPT OUTPUT_DIR');
for (const value of [endpoint, url]) {
  if (new URL(value).hostname !== '127.0.0.1') throw Error('Loopback only');
}
const target = await (await fetch(`${endpoint}/json/new?about:blank`, {method:'PUT'})).json();
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
await fs.mkdir(output,{recursive:false});
const scenarioTimeout=Number(process.env.LIVE2D_SCENARIO_TIMEOUT_MS||120000);
if(!Number.isFinite(scenarioTimeout)||scenarioTimeout<1000||scenarioTimeout>600000)throw Error('Invalid scenario timeout');
const timeout=setTimeout(()=>{console.error('CDP test timed out');process.exit(2);},scenarioTimeout+30000);
try {
  await send('Runtime.enable');await send('Network.enable');await send('Page.enable');
  if(startupMock) await send('Page.addScriptToEvaluateOnNewDocument',{source:`
    const originalFetch = window.fetch;
    window.fetch = function(input, init) {
      if(String(input) === '/api/extra/classify') return Promise.resolve(new Response(
        JSON.stringify({classification:[{label:'neutral',score:1}]}),
        {status:200,headers:{'Content-Type':'application/json'}}));
      return originalFetch.call(this,input,init);
    };
  `});
  await send('Page.navigate',{url});
  await send('Page.bringToFront');
  let ready=false;
  for(let i=0;i<60;i++){
    const r=await send('Runtime.evaluate',{expression:'document.readyState',returnByValue:true});
    if(r.result.value==='complete'){ready=true;break;}
    await new Promise(r=>setTimeout(r,500));
  }
  if(!ready)throw Error('Document not ready');
  const expression=await fs.readFile(script,'utf8');
  const result=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,timeout:scenarioTimeout});
  const frames=result.result.value?.frames;
  if(result.result.value && startupMock) result.result.value.startup_classifier='mock neutral before application startup; no inference';
  if(result.result.value?.remote_frames) {
    if(!Array.isArray(frames)||frames.length>2000||frames.some(n=>!/^[a-zA-Z0-9_-]+$/.test(n)))throw Error('Invalid remote frames');
    for(let start=0;start<frames.length;start+=8){
      const names=frames.slice(start,start+8);
      const chunk=await send('Runtime.evaluate',{expression:`Object.fromEntries(${JSON.stringify(names)}.map(n=>[n,window.phase4b3Frames[n]]))`,returnByValue:true});
      for(const [name,data] of Object.entries(chunk.result.value))await fs.writeFile(`${output}/${name}.png`,Buffer.from(data,'base64'));
    }
    await send('Runtime.evaluate',{expression:'delete window.phase4b3Frames'});
  } else if(frames) {
    for(const [name,data] of Object.entries(frames)) {
      if(!/^[a-zA-Z0-9_-]+$/.test(name)) throw Error('Invalid frame name');
      await fs.writeFile(`${output}/${name}.png`,Buffer.from(data,'base64'));
    }
    result.result.value.frames=Object.keys(frames);
  }
  if(['sillytavern-extension','phase1-animation','phase2-basic','phase2-5-experiment','phase2-6-quality','phase3-animation'].includes(result.result.value?.stage)) {
    const value=result.result.value;
    const phase3=value.stage==='phase3-animation';
    const phase1=value.stage==='phase1-animation';
    const phase25=value.stage==='phase2-5-experiment';
    const phase26=value.stage==='phase2-6-quality';
    const phase2=value.stage==='phase2-basic'||phase25||phase26;
    const assetRoot=phase3?value.asset_root:phase26?value.asset_root:phase25?'/assets/live2d/phase2-5/':phase2?'/assets/live2d/phase2/':phase1?'/assets/live2d/phase1/':'/assets/live2d/phase0/';
    const responses=events.filter(e=>e.method==='Network.responseReceived').map(e=>e.params.response);
    const expected=phase3?['.model3.json','.moc3','/texture_00.png','.rpIdle.motion3.json']:phase2?['.model3.json','.moc3','/texture_00.png','.idle.motion3.json']:phase1?['.model3.json','.moc3','/texture_00.png','.phase1Idle.motion3.json',
      '.phase1_neutral.exp3.json','.phase1_happy.exp3.json','.phase1_angry.exp3.json']:
      ['.model3.json','.moc3','/texture_00.png','.idle.motion3.json',
      '.nod.motion3.json','.smile.exp3.json','.sad.exp3.json','.angry.exp3.json','.surprised.exp3.json'];
    const missing=expected.filter(suffix=>!responses.some(r=>r.url.includes(assetRoot) && r.url.endsWith(suffix) && r.status===200));
    const unexpectedHttp=responses.filter(r=>r.url.includes(assetRoot) && r.status>=400 && !r.url.endsWith('/sillytavern_settings.json'));
    const exceptions=events.filter(e=>e.method==='Runtime.exceptionThrown');
    const listenerErrors=phase3?events.filter(e=>e.method==='Runtime.consoleAPICalled'&&e.params.args?.some(a=>a.value==='Error in event listener')):[];
    value.network_validation={caught_event_listener_errors:listenerErrors.length,missing_successful_resources:missing,unexpected_http_errors:unexpectedHttp.map(r=>({url:r.url,status:r.status})),uncaught_exceptions:exceptions.length};
    if(missing.length || unexpectedHttp.length || exceptions.length || listenerErrors.length)value.status='fail';
  }
  if(['phase3-1-standalone','generic-creation-preview'].includes(result.result.value?.stage)) {
    const failures=events.filter(e=>e.method==='Runtime.exceptionThrown'||e.method==='Network.loadingFailed'||(e.method==='Network.responseReceived'&&e.params.response.status>=400));
    const external=events.filter(e=>e.method==='Network.responseReceived'&&new URL(e.params.response.url).origin!==new URL(url).origin);
    result.result.value.network_validation={failures:failures.length,external_requests:external.length};
    if(failures.length||external.length)result.result.value.status='fail';
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
  clearTimeout(timeout);await send("Target.closeTarget",{targetId:target.id});ws.close();
}
