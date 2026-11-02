// Execute the exact installed getExpressionLabel function with synthetic data only.
// No application startup, network, credentials, chats or production writes.
import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const [upstreamFile, candidateFile] = process.argv.slice(2);
const expected=['f6bae7eff0705593403de51062b9dead7a1a5799a8aaa1754c677149fb117c5b',
                '49302ca308e1f06200bda476481e765330ada9531ad57ccea899f2f30754bb3d'];
const results=[];
for(const [index,file] of [upstreamFile,candidateFile].entries()) {
  const source=fs.readFileSync(file,'utf8');
  assert.equal(crypto.createHash('sha256').update(source).digest('hex'),expected[index]);
  const start=source.indexOf('async function getExpressionLabel(');
  const end=source.indexOf('\nfunction moveModel(',start);
  assert(start>=0&&end>start);
  for(const api of [0,2]) {
    let requests=0;
    const sandbox={modules:[],extension_settings:{expressions:{api}},
      EXPRESSION_API:{local:0,extras:1,llm:2},FALLBACK_EXPRESSION:'joy',
      sampleClassifyText:s=>s,getRequestHeaders:()=>({}),
      fetch:async()=>{requests++;return {ok:true,json:async()=>({classification:[{label:'anger'}]})};},
      console:{log:()=>{}}};
    vm.createContext(sandbox);
    vm.runInContext(source.slice(start,end),sandbox,{timeout:1000});
    const label=await sandbox.getExpressionLabel('Synthetic audit sentence.');
    assert.equal(label,api===0?'anger':index===0?'joy':'neutral');
    assert.equal(requests,api===0?1:0);
    results.push({variant:index===0?'upstream':'adapter',expressions_api:api,label,mocked_fetch_calls:requests});
  }
}
console.log(JSON.stringify({status:'pass',classification_inference:false,real_network_requests:0,results},null,2));
