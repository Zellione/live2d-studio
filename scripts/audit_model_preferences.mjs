// Exercise the installed preset initialization block with synthetic preferences.
import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const [uiFile, packageDirectory]=process.argv.slice(2);
const source=fs.readFileSync(uiFile,'utf8');
const policy=JSON.parse(fs.readFileSync(new URL('../recipes/girl2-package.json',import.meta.url),'utf8'));
assert.equal(crypto.createHash('sha256').update(source).digest('hex'),policy.compatibility.target_sha256['data/default-user/extensions/Extension-Live2d/ui.js']);
const preset=JSON.parse(fs.readFileSync(`${packageDirectory}/sillytavern_settings.json`,'utf8'));
const start=source.indexOf('    // Initialize new model');
const end=source.indexOf("    $('#live2d_model_scale').val",start);
assert(start>=0&&end>start);
const model='/assets/live2d/girl2-phase3-portrait-v1/Generated_artwork.model3.json';
const results=[];
for(const variant of ['new','existing','partial-existing']) {
  const other={scale:.65,x:32,classify_mapping:{joy:{expression:'custom',motion:'none'}}};
  const map={OtherCharacter:{other:structuredClone(other)}};
  if(variant==='existing')map.SyntheticCharacter={[model]:structuredClone(other)};
  if(variant==='partial-existing')map.SyntheticCharacter={[model]:{scale:.8}};
  const before=JSON.stringify(map);
  let fetches=0,saves=0;
  const sandbox={character:'SyntheticCharacter',model_path:model,
    extension_settings:{live2d:{characterModelsSettings:map}},user_settings_exists:true,
    CLASSIFY_EXPRESSIONS:policy.classifier_labels,model_hit_areas:{},DEBUG_PREFIX:'test',
    console:{debug:()=>{}},saveSettingsDebounced:()=>saves++,
    fetch:async url=>{assert.equal(url,model.replace('Generated_artwork.model3.json','sillytavern_settings.json'));fetches++;return {ok:true,json:async()=>structuredClone(preset)};}};
  vm.createContext(sandbox);
  await vm.runInContext(`(async()=>{${source.slice(start,end)}})()`,sandbox,{timeout:1000});
  assert.equal(JSON.stringify(map.OtherCharacter.other),JSON.stringify(other));
  if(variant==='new') {
    assert.equal(JSON.stringify(map.SyntheticCharacter[model]),JSON.stringify(preset));
    assert.equal(fetches,1);assert.equal(saves,1);
  } else {
    assert.equal(JSON.stringify(map),before);assert.equal(fetches,0);assert.equal(saves,0);
  }
  results.push({variant,preset_fetches:fetches,synthetic_saves:saves,other_preferences_preserved:true,
    existing_record_preserved:variant!=='new',missing_fields_automatically_merged:false});
}
console.log(JSON.stringify({status:'pass',production_settings_modified:false,synthetic_preferences_only:true,results},null,2));
