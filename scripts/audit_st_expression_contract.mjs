// Exact pinned ST export, synthetic dependencies only. No network/model calls.
import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const source=fs.readFileSync(process.argv[2],'utf8');
const hash=crypto.createHash('sha256').update(source).digest('hex');
assert.equal(hash,'42ef6cf85ee459d821eda3b10c9b589bccfbb2946bb743c3f5137a614836609c');
const block=source.slice(source.indexOf('export async function getExpressionLabel('),source.indexOf('\nfunction getLastCharacterMessage()',source.indexOf('export async function getExpressionLabel('))).replace('export ','');
let calls=[], response='joy', fail=false;
const sandbox={extension_settings:{expressions:{api:2,fallback_expression:'joy',promptType:'raw',filterAvailable:false}},
  modules:[],EXPRESSION_API:{local:0,extras:1,llm:2,none:99},PROMPT_TYPE:{raw:'raw',full:'full'},online_status:'connected',inApiCall:false,
  sampleClassifyText:t=>t,getExpressionsList:async()=>['joy','sadness','anger','surprise','confusion','embarrassment','neutral'],
  substituteParamsExtended:p=>p,getLlmPrompt:async()=> 'synthetic prompt',
  eventSource:{once:()=>{}},event_types:{TEXT_COMPLETION_SETTINGS_READY:'settings'},onTextGenSettingsReady:()=>{},
  waitUntilCondition:async()=>{},getRequestHeaders:()=>({}),
  generateRaw:async args=>{calls.push({kind:'raw',args}); if(fail)throw Error('mock failure');return response;},
  generateQuietPrompt:async args=>{calls.push({kind:'full',args});return response;},
  parseLlmResponse:(text,labels)=>{if(!labels.includes(text))throw Error('unknown');return text;},
  fetch:async()=>{calls.push({kind:'local'});return {ok:!fail,json:async()=>({classification:[{label:response}]})};},
  toastr:{error:()=>{}},console:{error:()=>{},debug:()=>{},warn:()=>{}}};
vm.createContext(sandbox);vm.runInContext(block,sandbox,{timeout:1000});
const f=sandbox.getExpressionLabel;
const labels=[];
for(response of ['joy','sadness','anger','surprise','confusion','embarrassment','neutral']) labels.push(await f('Synthetic text'));
assert.equal(labels.length,7);
response='joy';const success=await f('Synthetic text');fail=true;const error=await f('Synthetic text');fail=false;
assert.equal(success,error);assert.equal(error,'joy');
response='unknown';assert.equal(await f('Synthetic text'),'joy');response='joy';
calls=[];await Promise.all([f('same message'),f('same message')]);assert.equal(calls.length,2);
sandbox.extension_settings.expressions.promptType='full';calls=[];await f('ONLY_THIS_TEXT');
assert(!JSON.stringify(calls).includes('ONLY_THIS_TEXT'));
sandbox.extension_settings.expressions.api=0;response='anger';assert.equal(await f('synthetic local'),'anger');
fail=true;assert.equal(await f('synthetic local'),undefined);
assert(source.includes('export let lastExpression = {}'));
assert(source.includes("lastExpression[spriteFolderName.split('/')[0]] = expression;"));
console.log(JSON.stringify({status:'pass',source_sha256:hash,simulated_llm_labels:labels,
  real_inference:false,network_requests:0,reliable_direct_integration:false,
  findings:{success_and_error_indistinguishable:true,duplicate_same_text_calls:2,
    full_mode_omits_supplied_text:true,unknown_returns_configured_non_neutral_fallback:true,
    local_http_error_returns_undefined:true,lastExpression_has_no_message_id_or_error_status:true},
  decision:'Retain existing neutral fallback; do not patch built-in expressions or install unsafe direct bridge'},null,2));
