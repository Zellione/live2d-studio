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
    const app = new PIXI.Application({width:600,height:650,backgroundAlpha:0,preserveDrawingBuffer:true,antialias:true});
    $('#canvas').append(app.view);
    const model = await Promise.race([PIXI.live2d.Live2DModel.from(config.model,{autoInteract:false,autoHitTest:false}),new Promise((_,reject)=>setTimeout(()=>reject(Error('Model load timed out')),30000))]);
    app.stage.addChild(model);
    model.scale.set(570/Math.max(model.width,model.height));
    model.x=(600-model.width)/2;model.y=35;
    const internal=model.internalModel, core=internal.coreModel, manager=internal.motionManager;
    const physics=internal.physics;
    const ids=core._model.parameters.ids, defaults=Array.from(core._model.parameters.defaultValues);
    const set=(id,v)=>core.setParameterValueById(id,v), get=id=>core.getParameterValueById(id);
    // Stable baseline each frame. Motion and expressions compose once, never accumulate.
    internal.on('beforeMotionUpdate',()=>ids.forEach((id,i)=>set(id,defaults[i])));
    internal.eyeBlink=undefined; internal.updateFocus=()=>{};internal.updateNaturalMovements=()=>{};
    const state={idle:true,talking:false,expression:'neutral',manual:{},blinks:{},values:{},frames:0};
    const sliderDefs=[['ParamMouthOpenY','Mouth open',0,1,.01],['ParamAngleX','Head X',-15,15,.1],['ParamAngleY','Head Y',-15,15,.1],['ParamAngleZ','Head Z',-15,15,.1]];
    for(const [id,label,min,max,step] of sliderDefs){
      const row=document.createElement('label');row.className='slider';row.innerHTML=`<span>${label}</span><input id="${id}" type="range" min="${min}" max="${max}" step="${step}" value="0"><output>0</output>`;
      row.querySelector('input').oninput=e=>{state.manual[id]=Number(e.target.value);row.querySelector('output').value=e.target.value;};$('#sliders').append(row);
    }
    const names=internal.settings.expressions.map(e=>e.Name || e.name);
    async function expression(name){await model.expression(name);state.expression=name;for(const b of $('#expressions').children)b.setAttribute('aria-pressed',String(b.dataset.expression===name));}
    for(const name of names){const b=document.createElement('button');b.textContent=name[0].toUpperCase()+name.slice(1);b.dataset.expression=name;b.onclick=()=>expression(name).catch(fail);$('#expressions').append(b);}
    function idle(value){state.idle=value;internal.physics=value?physics:undefined;manager.groups.idle=value?'Idle':'__paused__';if(value)model.motion('Idle',0,3);else manager.stopAllMotions();$('#idle').textContent=value?'Pause idle':'Play idle';$('#idle').setAttribute('aria-pressed',String(value));}
    function talk(value){state.talking=value;$('#talk').textContent=value?'Stop talking':'Start talking';$('#talk').setAttribute('aria-pressed',String(value));}
    async function reset(){idle(false);talk(false);state.manual={};state.blinks={};for(const [id] of sliderDefs){$('#'+id).value=0;$('#'+id).nextElementSibling.value='0';}await expression('neutral');}
    $('#idle').onclick=()=>idle(!state.idle);$('#talk').onclick=()=>talk(!state.talking);$('#reset').onclick=()=>reset().catch(fail);
    for(const side of ['left','right'])$('#blink-'+side).onclick=()=>{state.blinks[side]=performance.now();};
    internal.on('beforeModelUpdate',()=>{
      const now=performance.now();
      const dt=Math.min(.1,(now-(state.lastTime||now))/1000);state.lastTime=now;
      state.talkWeight=(state.talkWeight||0)+((state.talking?1:0)-(state.talkWeight||0))*(1-Math.exp(-18*dt));
      if(state.talkWeight<.00001)state.talkWeight=0;
      for(const [id,v] of Object.entries(state.manual))set(id,v);
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
    await expression('neutral');idle(true);$('#controls').disabled=false;$('#status').textContent='Live Cubism model · Local only';
    window.preview={app,model,state,reset,expression,idle,talk};
  }catch(error){fail(error);}
})();
