// Evaluated via CDP in a fresh, isolated SillyTavern test instance.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const report = {stage:'phase3-animation', status:'running', visual_character_rig_tested:true};
  try {
    for(let i=0;i<100 && !document.querySelector('#live2d_enabled_checkbox');i++) await wait(200);
    if(!document.querySelector('#live2d_enabled_checkbox')) throw Error('Live2D extension UI not initialized');
    // Finish first-run onboarding in this disposable profile only.
    await wait(2000);
    const onboarding = Array.from(document.querySelectorAll('.popup')).find(p=>p.querySelector('.onboarding'));
    if(onboarding) {
      const input=onboarding.querySelector('.popup-input');
      if(input){input.value='Phase2.5 Tester';input.dispatchEvent(new Event('input',{bubbles:true}));}
      onboarding.querySelector('.popup-button-ok')?.click();
      await wait(1000);
    }
    const st=await import('/script.js');
    const {getContext, extension_settings}=await import('/scripts/extensions.js');
    const base='/scripts/extensions/third-party/Extension-Live2d/';
    const ui=await import(base+'ui.js'), live=await import(base+'live2d.js');
    const asset=new URL(location.href).searchParams.get('qaAsset')||'phase3';
    if(!/^phase3(?:-v[0-9]+)?$/.test(asset))throw Error('Unexpected test asset');
    report.asset_root='/assets/live2d/'+asset+'/';
    const name='Phase3 Girl2 '+asset;
    if(!getContext().characters.some(c=>c.name===name)) {
      const response=await fetch('/api/characters/create',{method:'POST',headers:st.getRequestHeaders(),
        body:JSON.stringify({ch_name:name,description:'Experimental neural CC0 portrait, no animation quality assumed.',first_mes:'Phase 2.5 experimental animation test.'})});
      if(!response.ok)throw Error('Test character creation failed: '+response.status);
      await st.getCharacters();
    }
    await st.selectCharacterById(getContext().characters.findIndex(c=>c.name===name));
    await wait(1000);
    report.character=getContext().name2;
    if(report.character!==name)throw Error('Test character not active');
    const assets=await ui.getAssetsLive2dFiles();
    const model=assets.live2d?.find(p=>p.endsWith('/'+asset+'/Generated_artwork.model3.json'));
    report.discovered_models=assets.live2d;
    if(!model)throw Error('PSD2Live model absent from actual assets API');
    ui.updateCharactersList();
    await ui.updateCharactersModels(true);
    document.querySelector('#live2d_character_select').value=name;
    await ui.onCharacterChange();
    const select=document.querySelector('#live2d_model_select');
    report.model_option_found=Array.from(select.options).some(o=>o.value===model);
    if(!report.model_option_found)throw Error('Model absent from extension dropdown');
    select.value=model;
    document.querySelector('#live2d_enabled_checkbox').checked=true;
    await ui.onEnabledClick();
    await ui.onModelChange();
    // Place the fixture beside the opaque chat panel using existing UI controls.
    document.querySelector('#live2d_model_scale').value='0.4';
    await ui.onModelScaleChange();
    document.querySelector('#live2d_model_x').value='-75';
    document.querySelector('#live2d_model_y').value='0';
    await ui.onModelCoordChange();
    await wait(2000);
    const settings=extension_settings.live2d.characterModelsSettings[name][model];
    report.parameter_mapping={mouth:settings.param_mouth_open_y_id,cursor:settings.cursor_param};
    report.expression_options=Array.from(document.querySelector('#live2d_default_expression_select').options).map(o=>o.value);
    report.motion_options=Array.from(document.querySelector('#live2d_default_motion_select').options).map(o=>o.value);
    // Find the real extension-owned model in PIXI's registered ticker listeners.
    // No loader replacement, mocks, source edits or separate model instance.
    let instance;
    for(let node=PIXI.Ticker.shared._head?.next;node;node=node.next) {
      if(node.context?.internalModel && !node.context.destroyed)instance=node.context;
    }
    if(!instance)throw Error('Extension model missing from PIXI ticker');
    const mode=new URL(location.href).searchParams.get('mode')||'expressions';
    report.mode=mode;report.integration_adapter=new URL(location.href).searchParams.get('adapter')==='1';report.mapping_checks={};report.mouth_pixel_changes={};report.frames={};report.parameters={};report.geometry={};report.samples={};report.control_noise_pixels=0;
    extension_settings.live2d.force_loop=false;extension_settings.live2d.force_animation=false;
    const findModel=()=>{let m;for(let n=PIXI.Ticker.shared._head?.next;n;n=n.next)if(n.context?.internalModel&&!n.context.destroyed)m=n.context;return m;};
    const values=()=>{const c=findModel().internalModel.coreModel;return Object.fromEntries(Array.from(c._model.parameters.ids,(id,i)=>[id,c._model.parameters.values[i]]));};
    let renderedValues={};const observed=new WeakSet();
    function observe(){const m=findModel();if(m&&!observed.has(m)){observed.add(m);m.internalModel.on('beforeModelUpdate',()=>{renderedValues=values();});}}
    observe();
    const snapshots={};let neutralGeometry;
    function geometry(){
      const c=findModel().internalModel.coreModel,d=c._model.drawables,p=c._model.parameters;
      let nonfinite=0,invalidOpacity=0,rawOpacityExcursions=0,outOfRange=0,flips=0,collapsed=0,expanded=0;
      const vertices=Array.from(d.vertexPositions,v=>Array.from(v));
      if(!neutralGeometry)neutralGeometry=vertices;
      for(let i=0;i<vertices.length;i++){
        nonfinite+=vertices[i].filter(x=>!Number.isFinite(x)).length;
        if(d.opacities[i]<0||d.opacities[i]>1)rawOpacityExcursions++;
        // Cubism float32 interpolation can overshoot constant 1 by a few ULPs.
        // Retain the strict count; reject beyond eight float32 ULPs.
        if(!Number.isFinite(d.opacities[i])||d.opacities[i]<-8*2**-23||d.opacities[i]>1+8*2**-23)invalidOpacity++;
        const ix=d.indices[i];const area=(v,j)=>{const a=ix[j]*2,b=ix[j+1]*2,c=ix[j+2]*2;return (v[b]-v[a])*(v[c+1]-v[a+1])-(v[b+1]-v[a+1])*(v[c]-v[a]);};
        for(let j=0;j<ix.length;j+=3){const old=area(neutralGeometry[i],j),now=area(vertices[i],j);if(Math.abs(old)<1e-8)continue;const ratio=now/old;if(ratio<0)flips++;if(Math.abs(ratio)<.01)collapsed++;if(Math.abs(ratio)>10)expanded++;}
      }
      for(let i=0;i<p.count;i++)if(!Number.isFinite(p.values[i])||p.values[i]<p.minimumValues[i]-.001||p.values[i]>p.maximumValues[i]+.001)outOfRange++;
      return {nonfinite,invalidOpacity,outOfRange,rawOpacityExcursions,opacity_min:Math.min(...d.opacities),opacity_max:Math.max(...d.opacities),new_triangle_flips:flips,collapsed_triangles:collapsed,expanded_triangles:expanded};
    }
    function diff(a,b){let n=0;for(let i=0;i<a.length;i+=4)if(Math.max(...[0,1,2,3].map(j=>Math.abs(a[i+j]-b[i+j])))>20)n++;return n;}
    async function capture(label){observe();await wait(40);return new Promise((resolve,reject)=>requestAnimationFrame(()=>{try{
      const canvas=document.querySelector('#live2d-canvas'),copy=document.createElement('canvas');copy.width=canvas.width;copy.height=canvas.height;
      const ctx=copy.getContext('2d');ctx.drawImage(canvas,0,0);snapshots[label]=ctx.getImageData(0,0,copy.width,copy.height).data;
      report.frames[label]=copy.toDataURL('image/png').split(',')[1];report.geometry[label]=geometry();report.parameters[label]=renderedValues;
      if(Object.values(report.geometry[label]).slice(0,3).some(x=>x))throw Error('Invalid numeric runtime: '+label);
      resolve();}catch(e){reject(e);}}));}
    // Observe rendered values BEFORE Core reloads its saved pre-expression state.
    async function sample(label,ms){
      observe();const m=findModel(), rows=[];let next=0;
      const observer=()=>{const now=performance.now();if(now>=next){rows.push({t:now,...values()});next=now+30;}};
      m.internalModel.on('beforeModelUpdate',observer);
      await wait(ms);m.internalModel.off('beforeModelUpdate',observer);
      report.samples[label]=rows;return rows;
    }
    const assert=(condition,message)=>{if(!condition)throw Error(message);};
    if(mode==='expressions'){
      const internal=instance.internalModel,core=internal.coreModel,manager=internal.motionManager;
      manager.stopAllMotions();manager.groups.idle='QA-no-idle';internal.eyeBlink=undefined;internal.physics=undefined;internal.breath=undefined;
      let pose={};const ids=core._model.parameters.ids,defaults=Array.from(core._model.parameters.defaultValues);
      const reset=()=>ids.forEach((id,i)=>core.setParameterValueById(id,pose[id]??defaults[i]));
      internal.on('beforeMotionUpdate',reset);
      await live.playExpression(name,'neutral');await wait(650);await capture('neutral');await capture('neutral-repeat');
      report.control_noise_pixels=diff(snapshots.neutral,snapshots['neutral-repeat']);
      report.expression_changes={};
      for(const expr of ['happy','sad','angry','surprised','confused','embarrassed','neutral']){
        await live.playExpression(name,expr);await wait(650);await capture('expression_'+expr);
        report.expression_changes[expr]=diff(snapshots.neutral,snapshots['expression_'+expr]);
        if(expr!=='neutral')assert(report.expression_changes[expr]>50,'Expression invisible: '+expr);
        pose={ParamEyeLOpen:0,ParamEyeROpen:0,ParamMouthOpenY:.55,ParamAngleX:8,ParamAngleY:-5};
        await wait(60);await capture('combined_'+expr);
        const rows=await sample('combined_'+expr,80),last=rows.at(-1);
        assert(last.ParamEyeLOpen<.02&&last.ParamEyeROpen<.02,'Expression prevents blink: '+expr);
        assert(last.ParamMouthOpenY>.5,'Expression prevents talk: '+expr);pose={};
      }
      await live.playExpression(name,'neutral');await wait(650);
      for(const kind of ['blink','mouth'])for(const v of [0,.25,.5,.75,1]){
        pose=kind==='blink'?{ParamEyeLOpen:v,ParamEyeROpen:v}:{ParamMouthOpenY:v};await wait(60);await capture(kind+'_'+Math.round(v*100));
      }
      for(const side of ['L','R']){pose={['ParamEye'+side+'Open']:0};await wait(60);await capture('closed_'+side);}
      for(const axis of ['X','Y','Z'])for(const sign of [-1,1]){
        pose={['ParamAngle'+axis]:15*sign};await wait(60);await capture('head_'+axis+'_'+(sign<0?'minus':'plus'));
      }
      for(const sign of [-1,1])for(const [label,eye,mouth]of [['blink',0,0],['half',.5,.5],['open',1,1],['wink',0,1]]){
        pose={ParamAngleX:sign*15,ParamAngleY:sign*15,ParamAngleZ:sign*15,ParamEyeLOpen:eye,ParamEyeROpen:label==='wink'?1:eye,ParamMouthOpenY:mouth};await wait(60);await capture('stress_'+label+'_'+(sign<0?'minus':'plus'));
      }
      pose={};await wait(60);await capture('neutral_restored');assert(diff(snapshots.neutral,snapshots.neutral_restored)===0,'Neutral did not restore');
      internal.off('beforeMotionUpdate',reset);
    } else {
      const constants=await import(base+'constants.js');report.classifier_vocabulary=constants.CLASSIFY_EXPRESSIONS;
      assert(constants.CLASSIFY_EXPRESSIONS.every(k=>settings.classify_mapping[k]),'Missing classifier mapping');
      extension_settings.expressions.api=mode==='llm-blocked'?2:0;
      let classifier='joy',requests=[];
      const realFetch=window.fetch;
      window.fetch=async(input,init)=>{
        if(String(input)==='/api/extra/classify'){
          const requested=classifier;requests.push({label:requested,text:JSON.parse(init.body).text});
          if(requested==='slow-joy'){await wait(700);return new Response(JSON.stringify({classification:[{label:'joy',score:1}]}),{status:200});}
          if(classifier==='throw')throw Error('QA classifier offline');
          if(classifier==='http-error')return new Response('{}',{status:503});
          return new Response(JSON.stringify({classification:[{label:classifier,score:1}]}),{status:200,headers:{'Content-Type':'application/json'}});
        }return realFetch(input,init);
      };
      report.classification='deterministic network mock, no classifier inference';
      async function message(label,text){
        classifier=label;
        const context=getContext(),msg={name,is_user:false,is_system:false,mes:text,send_date:new Date().toISOString(),extra:{}};
        context.chat.push(msg);const index=context.chat.length-1;
        st.addOneMessage(msg);await context.eventSource.emit(context.event_types.MESSAGE_RECEIVED,index);
      }
      await live.playExpression(name,'neutral');await live.playMotion(name,'Idle_id=0');await wait(700);await capture('neutral');
      if(mode==='llm-blocked'){
        await message('anger','Synthetic provider contract test.');
        const rows=await sample('llm_fallback',1100);await capture('llm_fallback');
        assert(requests.length===0,'Blocked LLM path unexpectedly made a request');
        const expected=report.integration_adapter?0:.85;
        assert(Math.abs(rows.at(-1).ParamMouthForm-expected)<.03,'Wrong documented LLM fallback');
        report.llm_integration='blocked: pinned export cannot meet error/deduplication contract';
        report.provider_preserved=extension_settings.expressions.api===2;
        report.simulated_requested_label='anger';report.actual_fallback=report.integration_adapter?'neutral':'happy';
        assert(report.provider_preserved,'Provider changed');
      }else if(mode==='rp'){
        for(const label of ['joy','sadness','anger','surprise','confusion','embarrassment','neutral']){
          await message(label,'A short local test reply.');
          const rows=await sample('message_'+label,1100);await capture('message_'+label);
          const mouth=rows.map(x=>x.ParamMouthOpenY);report.parameters['talk_'+label]={min:Math.min(...mouth),max:Math.max(...mouth)};
          assert(Math.max(...mouth)-Math.min(...mouth)>.15,'No message mouth movement: '+label);
          const mapped=settings.classify_mapping[label].expression;
          const modelJSON=await (await fetch(model)).json();
          const ref=modelJSON.FileReferences.Expressions.find(e=>e.Name===mapped);
          const exp=await (await fetch(model.substring(0,model.lastIndexOf('/')+1)+ref.File)).json();
          const last=rows.at(-1);
          const checks=exp.Parameters.filter(e=>['ParamBrowMood','ParamBrowLY','ParamBrowRY','ParamMouthForm'].includes(e.Id)).map(e=>({id:e.Id,expected:e.Value,actual:last[e.Id],accepted:Math.abs(last[e.Id]-e.Value)<.03}));
          report.mapping_checks[label]={expression:mapped,checks};assert(checks.every(c=>c.accepted),'Wrong applied expression: '+label);
          await wait(300);
        }
        await message('throw','Offline classifier test.');const fallbackRows=await sample('fallback_offline',1100);await capture('fallback_offline');
        if(report.integration_adapter)assert(Math.abs(fallbackRows.at(-1).ParamMouthForm)<.03,'Offline fallback not neutral');
        await live.playExpression(name,'neutral');await wait(600);const rest=await sample('rest',500);assert(rest.every(r=>r.ParamMouthOpenY<.02),'Mouth stuck after talk');await capture('rest');
       }else if(mode==='visual'){
        // Actual moving canvas frames; no parameter holding in this mode.
        for(let i=0;i<8;i++){await wait(350);await capture('idle_'+i);}
        await message('joy','Here is a longer roleplay reply to exercise talking and blinking together. '.repeat(3));
        for(let i=0;i<16;i++){await wait(100);await capture('talk_'+i);}
        await message('neutral','Done.');await wait(800);await capture('talk_rest');
        report.mouth_pixel_changes={};
        // Native mouth rectangle from the character manifest, transformed through
        // the actual model's local/world transform, with a modest deformation margin.
        const internal=findModel().internalModel, core=internal.coreModel;
        report.drawable_ids=Array.from(core._model.drawables.ids);
        // Region specified by measured neutral mouth geometry, not whole-image diff.
        const ids=core._model.drawables.ids;
        const mouthIndices=Array.from(ids, (id,i)=>/mouth|lip/i.test(id)?i:-1).filter(i=>i>=0);
        report.mouth_drawable_indices=mouthIndices;
        const xy=[];
        for(const i of mouthIndices){
          const verts=core._model.drawables.vertexPositions[i];
          for(let j=0;j<verts.length;j+=2){
            const local=internal.localTransform.apply({x:verts[j]*internal.pixelsPerUnit+internal.originalWidth/2,y:-verts[j+1]*internal.pixelsPerUnit+internal.originalHeight/2});
            const pt=findModel().worldTransform.apply(local);xy.push(pt);
          }
        }
        assert(xy.length>0,'Mouth geometry could not be localized');
        if(xy.length){
          const canvas=document.querySelector('#live2d-canvas'),scale=canvas.width/innerWidth;
          const b=[Math.max(0,Math.floor((Math.min(...xy.map(p=>p.x))-8)*scale)),Math.max(0,Math.floor((Math.min(...xy.map(p=>p.y))-8)*scale)),Math.min(canvas.width,Math.ceil((Math.max(...xy.map(p=>p.x))+8)*scale)),Math.min(canvas.height,Math.ceil((Math.max(...xy.map(p=>p.y))+8)*scale))];
          assert(b[2]>b[0]&&b[3]>b[1],'Invalid projected mouth rectangle');
          report.mouth_roi=b;
          for(let i=1;i<16;i++){let n=0;const a=snapshots['talk_'+(i-1)],c=snapshots['talk_'+i];for(let y=b[1];y<b[3];y++)for(let x=b[0];x<b[2];x++){const j=(y*canvas.width+x)*4;if(Math.max(...[0,1,2,3].map(k=>Math.abs(a[j+k]-c[j+k])))>20)n++;}report.mouth_pixel_changes[i]=n;}
          assert(Math.max(...Object.values(report.mouth_pixel_changes))>20,'No visible mouth-region movement');
        }
      }else if(mode==='race'){
        const old=message('slow-joy','Old delayed reply. '.repeat(30));await wait(40);
        await message('anger','New.');await old;
        const rows=await sample('latest_reply',1200);await capture('latest_reply');
        assert(rows.at(-1).ParamBrowMood>.98,'Stale classifier overwrote new emotion');
        assert(rows.slice(-8).every(r=>r.ParamMouthOpenY<.02),'Stale delayed reply restarted speech');
      }else if(mode==='failure'){

        await live.playExpression(name,'angry');await wait(600);
        await message('http-error','HTTP classifier failure.');const rows=await sample('http_failure',1100);await capture('http_failure');
        assert(Math.abs(rows.at(-1).ParamBrowMood)<.03,'HTTP failure leaves stale emotion');
      }else if(mode==='lifecycle'){
        const idle=await sample('idle',4500);await capture('idle');
        assert(Math.min(...idle.map(r=>r.ParamEyeLOpen))<.1,'Idle did not blink');
        if(report.integration_adapter)assert(Math.max(...idle.map(r=>Math.abs(r.ParamAngleX)))<2.01,'Unexpected extra idle head motion');
        await message('sadness','A longer assistant response while sad. '.repeat(8));
        await sample('long_talk',1500);await capture('long_talk');
        await message('joy','New reply interrupts.');await sample('interruption',1300);await capture('interruption');
        await live.playExpression(name,'angry');await sample('transition_angry',700);await capture('transition_angry');
        await live.playExpression(name,'neutral');await sample('transition_neutral',700);
        await live.playExpression(name,'happy');await wait(600);
        await live.playMotion(name,'Nod_id=0');const nod=await sample('explicit_motion',3500);await capture('after_nod');
        report.idle_recovered=String(findModel().internalModel.motionManager.state.currentGroup)==='Idle';
        assert(report.idle_recovered,'Idle did not recover after explicit motion');
        if(report.integration_adapter)assert(nod.at(-1).ParamMouthForm>.8,'Motion erased expression');
        await message('joy','Talking through reload. '.repeat(8));await wait(200);await live.loadLive2d();await wait(600);
        await sample('reload_talking',1000);await capture('reload');
        await message('neutral','After reload.');await sample('post_reload',1200);
        const other='Phase3 switch target';
        if(!getContext().characters.some(c=>c.name===other)){
          const r=await fetch('/api/characters/create',{method:'POST',headers:st.getRequestHeaders(),body:JSON.stringify({ch_name:other,first_mes:'Isolated test.'})});assert(r.ok,'Create switch target');await st.getCharacters();
        }
        await message('joy','Switch away while talking. '.repeat(8));await wait(200);
        await st.selectCharacterById(getContext().characters.findIndex(c=>c.name===other));await wait(600);
        report.switch_removed=live.charactersWithModelLoaded().length===0;
        await st.selectCharacterById(getContext().characters.findIndex(c=>c.name===name));await wait(1200);
        await message('neutral','Back again.');await sample('post_switch',1200);await capture('post_switch');
      }else throw Error('Unknown mode');
      report.classifier_requests=requests;window.fetch=realFetch;
    }
    report.status='pass';report.visual_acceptance='requires-independent-frame-review';await st.saveSettings();
  }catch(error){report.status='fail';report.error=String(error);report.stack=error.stack;}
  return report;
})()
