/* Local Cubism viewer. No storage, classifier, or SillyTavern API. */
(async () => {
  const $ = s => document.querySelector(s);
  const fail = error => {$('#status').textContent = `Could not load preview: ${error.message || error}. Check the terminal and installed runtime.`; window.previewError=String(error);};
  window.addEventListener('error', e => fail(e.error || e.message));
  try {
    const config = await (await fetch('/config.json')).json();
    if(config.candidate){
      $('#version-row').hidden=false;
      const candidate=new URL(location.href).searchParams.get('version')==='candidate';
      $('#version').value=candidate?'candidate':'baseline';
      if(candidate)config.model=config.candidate;
      $('#version').onchange=e=>{const url=new URL(location.href);url.searchParams.set('version',e.target.value);location.assign(url);};
    }
    PIXI.live2d.config.preserveExpressionOnMotion=true;
    const app = new PIXI.Application({width:config.comparison?1200:600,height:650,backgroundAlpha:0,preserveDrawingBuffer:true,antialias:true});
    $('#canvas').append(app.view);
    const model = await Promise.race([PIXI.live2d.Live2DModel.from(config.model,{autoInteract:false,autoHitTest:false}),new Promise((_,reject)=>setTimeout(()=>reject(Error('Model load timed out')),30000))]);
    app.stage.addChild(model);
    model.scale.set(570/Math.max(model.width,model.height));
    model.x=(600-model.width)/2+(config.comparison?600:0);model.y=35;
    const peers=[model];
    if(config.comparison){
      const before=await PIXI.live2d.Live2DModel.from(config.comparison,{autoInteract:false,autoHitTest:false});
      app.stage.addChild(before);before.scale.set(model.scale.x);before.x=(600-before.width)/2;before.y=35;peers.push(before);
      document.body.classList.add('comparison');
      const labels=document.createElement('p');labels.textContent='Reference · left / Candidate · right · synchronized start, equal scale';$('#canvas').before(labels);
    }
    const internal=model.internalModel, core=internal.coreModel, manager=internal.motionManager;
    const physics=internal.physics;
    const ids=core._model.parameters.ids, defaults=Array.from(core._model.parameters.defaultValues);
    const set=(id,v)=>core.setParameterValueById(id,v), get=id=>core.getParameterValueById(id);
    // Stable baseline each frame. Motion and expressions compose once, never accumulate.
    internal.on('beforeMotionUpdate',()=>ids.forEach((id,i)=>set(id,defaults[i])));
    internal.eyeBlink=undefined; internal.updateFocus=()=>{};internal.updateNaturalMovements=()=>{};
    const state={head:true,body:true,hair:true,idle:true,talking:false,expression:'neutral',manual:{},blinks:{},values:{},frames:0};
    const sliderDefs=[['ParamMouthOpenY','Mouth open',0,1,.01],['ParamAngleX','Head X',-15,15,.1],['ParamAngleY','Head Y',-15,15,.1],['ParamAngleZ','Head Z',-15,15,.1]];
    sliderDefs.push(...[['ParamBreath','Breathing',0,1,.01],['ParamBodyAngleX','Body turn',-2,2,.05],['ParamBodyAngleZ','Body tilt',-1,1,.05],['ParamHairFront','Front hair',-1,1,.01],['ParamHairBack','Back hair',-1,1,.01]].filter(([id])=>ids.includes(id)));
    for(const [id,label,min,max,step] of sliderDefs){
      const row=document.createElement('label');row.className='slider';row.innerHTML=`<span>${label}</span><input id="${id}" type="range" min="${min}" max="${max}" step="${step}" value="0"><output>0</output>`;
      row.querySelector('input').oninput=e=>{state.manual[id]=Number(e.target.value);row.querySelector('output').value=e.target.value;};$('#sliders').append(row);
    }
    const names=internal.settings.expressions.map(e=>e.Name || e.name);
    async function expression(name){await Promise.all(peers.map(m=>m.expression(name)));state.expression=name;for(const b of $('#expressions').children)b.setAttribute('aria-pressed',String(b.dataset.expression===name));}
    for(const name of names){const b=document.createElement('button');b.textContent=name[0].toUpperCase()+name.slice(1);b.dataset.expression=name;b.onclick=()=>selectExpression(name).catch(fail);$('#expressions').append(b);}
    function idle(value){state.idle=value;for(const m of peers){const mm=m.internalModel.motionManager;mm.groups.idle=value?'Idle':'__paused__';if(value)m.motion('Idle',0,3);else mm.stopAllMotions();}internal.physics=value&&state.hair!==false?physics:undefined;$('#idle').textContent=value?'Pause idle':'Play idle';$('#idle').setAttribute('aria-pressed',String(value));}
    function talk(value){state.talking=value;$('#talk').textContent=value?'Stop talking':'Start talking';$('#talk').setAttribute('aria-pressed',String(value));}
    async function reset(){idle(false);talk(false);state.manual={};state.blinks={};state.gestureStarted=0;for(const [id] of sliderDefs){$('#'+id).value=0;$('#'+id).nextElementSibling.value='0';}await expression('neutral');}
    let comparisonGeneration=0;
    async function compare(name){const generation=++comparisonGeneration;await reset();state.talkWeight=0;await new Promise(r=>setTimeout(r,750));if(generation!==comparisonGeneration)return;await expression(name);await new Promise(r=>setTimeout(r,750));}
    async function selectExpression(name){if($('#compare').checked)await compare(name);else await expression(name);}
    $('#compare').onchange=()=>{const locked=$('#compare').checked;for(const selector of ['#idle','#talk','#blink-left','#blink-right','#enable-head','#enable-body','#enable-hair',...sliderDefs.map(([id])=>'#'+id)])$(selector).disabled=locked;for(const button of $('#gestures').children)button.disabled=locked;if(locked)compare(state.expression).catch(fail);else {comparisonGeneration++;state.mouthOnly=false;$('#mouth-only').checked=false;}};
    $('#mouth-only').onchange=()=>{state.mouthOnly=$('#mouth-only').checked;if(state.mouthOnly&&!$('#compare').checked){$('#compare').checked=true;$('#compare').dispatchEvent(new Event('change'));}};
    $('#idle').onclick=()=>idle(!state.idle);$('#talk').onclick=()=>talk(!state.talking);$('#reset').onclick=()=>{comparisonGeneration++;reset().catch(fail);};
    for(const side of ['left','right'])$('#blink-'+side).onclick=()=>{state.blinks[side]=performance.now();};
    internal.on('afterMotionUpdate',()=>{
      // Manual head/body input must reach physics before its evaluation.
      for(const [id,v] of Object.entries(state.manual))if(!id.startsWith('ParamHair'))set(id,v);
      if(!state.head)for(const id of ['ParamAngleX','ParamAngleY','ParamAngleZ'])set(id,0);
      if(!state.body)for(const id of ['ParamBreath','ParamBodyAngleX','ParamBodyAngleY','ParamBodyAngleZ'])set(id,0);
    });
    internal.on('beforeModelUpdate',()=>{
      const now=performance.now();
      const dt=Math.min(.1,(now-(state.lastTime||now))/1000);state.lastTime=now;
      state.talkWeight=(state.talkWeight||0)+((state.talking?1:0)-(state.talkWeight||0))*(1-Math.exp(-18*dt));
      if(state.talkWeight<.00001)state.talkWeight=0;
      if(state.gestureStarted){const t=(now-state.gestureStarted)/1000;if(t>3)state.gestureStarted=0;else if(t>.9&&t<1.24){const u=(t-.9)/.34,open=u<.3?1-u/.3:u<.5?0:(u-.5)/.5;for(const id of ['ParamEyeLOpen','ParamEyeROpen'])set(id,get(id)*open);}}
      if(state.mouthOnly)ids.forEach((id,i)=>{if(!id.startsWith('ParamMouth'))set(id,defaults[i]);});
      for(const [id,v] of Object.entries(state.manual))set(id,v);
      if(!state.head)for(const id of ['ParamAngleX','ParamAngleY','ParamAngleZ'])set(id,0);
      if(!state.body)for(const id of ['ParamBreath','ParamBodyAngleX','ParamBodyAngleY','ParamBodyAngleZ'])set(id,0);
      if(!state.hair)for(const id of ['ParamHairFront','ParamHairBack'])set(id,0);
      if(state.talkWeight){const envelope=Math.pow(.5+.5*Math.sin(now*.014),1.5)*(.7+.3*Math.sin(now*.003)**2);const rest=get('ParamMouthOpenY');set('ParamMouthOpenY',rest+state.talkWeight*(.08+.75*envelope-rest));}
      for(const [side,start] of Object.entries(state.blinks)){
        const t=(now-start)/340; if(t>=1){delete state.blinks[side];continue;}
        const openness=t<.3?1-t/.3:t<.5?0:(t-.5)/.5;
        const id=side==='left'?'ParamEyeLOpen':'ParamEyeROpen';set(id,get(id)*openness);
      }
      state.values=Object.fromEntries(ids.map(id=>[id,get(id)]));state.frames++;
      if(state.frames%10===0)$('#parameters').textContent=JSON.stringify(state.values,null,2);
    });
    $('#capture').onclick=()=>{app.renderer.render(app.stage);const a=document.createElement('a');a.href=app.view.toDataURL('image/png');a.download=`character-${state.expression}.png`;a.click();};
    const motions=internal.settings.motions||{};
    const gestures=Object.keys(motions).filter(g=>g!=='Idle'&&Array.isArray(motions[g])&&motions[g].length);
    async function gesture(name){if(!gestures.includes(name))throw Error('Unavailable gesture');await model.motion(name,0,3);state.gestureStarted=performance.now();}
    for(const name of gestures){const b=document.createElement('button');b.textContent=name==='Nod'?'Head nod':name==='Question'?'Questioning head tilt':name;b.onclick=()=>gesture(name).catch(fail);$('#gestures').append(b);}
    $('#gesture-row').hidden=!gestures.length;
    for(const kind of ['head','body','hair'])$('#enable-'+kind).onchange=e=>{state[kind]=e.target.checked;if(kind==='hair')internal.physics=state.hair?physics:undefined;};
    // The comparison uses the same controls and clock; each model retains its
    // own authored idle and pendulum state.
    if(peers.length>1){const other=peers[1].internalModel,oc=other.coreModel,oi=oc._model.parameters.ids,od=Array.from(oc._model.parameters.defaultValues),op=other.physics;
      other.eyeBlink=undefined;other.updateFocus=()=>{};other.updateNaturalMovements=()=>{};
      other.on('beforeMotionUpdate',()=>{oi.forEach((id,i)=>oc.setParameterValueById(id,od[i]));other.physics=state.idle&&state.hair?op:undefined;});
      other.on('afterMotionUpdate',()=>{
        for(const [id,v]of Object.entries(state.manual))if(oi.includes(id)&&!id.startsWith('ParamHair'))oc.setParameterValueById(id,v);
        if(!state.head)for(const id of ['ParamAngleX','ParamAngleY','ParamAngleZ'])oc.setParameterValueById(id,0);
        if(!state.body)for(const id of ['ParamBreath','ParamBodyAngleX','ParamBodyAngleZ'])oc.setParameterValueById(id,0);
      });
      other.on('beforeModelUpdate',()=>{
        if(state.mouthOnly)oi.forEach((id,i)=>{if(!id.startsWith('ParamMouth'))oc.setParameterValueById(id,od[i]);});
        for(const [id,v]of Object.entries(state.manual))if(oi.includes(id))oc.setParameterValueById(id,v);
        if(state.talkWeight)oc.setParameterValueById('ParamMouthOpenY',state.values.ParamMouthOpenY);
        if(!state.head)for(const id of ['ParamAngleX','ParamAngleY','ParamAngleZ'])oc.setParameterValueById(id,0);
        if(!state.body)for(const id of ['ParamBreath','ParamBodyAngleX','ParamBodyAngleZ'])oc.setParameterValueById(id,0);
        if(!state.hair)for(const id of ['ParamHairFront','ParamHairBack'])oc.setParameterValueById(id,0);
        for(const [side,start]of Object.entries(state.blinks)){const t=(performance.now()-start)/340;if(t<1){const openness=t<.3?1-t/.3:t<.5?0:(t-.5)/.5,id=side==='left'?'ParamEyeLOpen':'ParamEyeROpen';oc.setParameterValueById(id,oc.getParameterValueById(id)*openness);}}
      });
    }
    // Preload motions so synchronized restart never waits on separate fetches.
    await Promise.all(peers.flatMap(m=>Object.keys(m.internalModel.settings.motions||{}).flatMap(g=>m.internalModel.motionManager.loadMotion(g,0))));
    await expression('neutral');idle(true);$('#controls').disabled=false;$('#status').textContent='Live Cubism model · Local only';
    window.preview={app,model,peers,state,reset,expression,idle,talk,compare,gesture,gestures};
  }catch(error){fail(error);}
})();
