// Evaluated via CDP in a fresh, isolated SillyTavern test instance.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const report = {stage:'sillytavern-extension', status:'running', visual_character_rig_tested:false};
  try {
    for(let i=0;i<100 && !document.querySelector('#live2d_enabled_checkbox');i++) await wait(200);
    if(!document.querySelector('#live2d_enabled_checkbox')) throw Error('Live2D extension UI not initialized');
    // Finish first-run onboarding in this disposable profile only.
    await wait(2000);
    const onboarding = Array.from(document.querySelectorAll('.popup')).find(p=>p.querySelector('.onboarding'));
    if(onboarding) {
      const input=onboarding.querySelector('.popup-input');
      if(input){input.value='Phase0 Tester';input.dispatchEvent(new Event('input',{bubbles:true}));}
      onboarding.querySelector('.popup-button-ok')?.click();
      await wait(1000);
    }
    const st=await import('/script.js');
    const {getContext, extension_settings}=await import('/scripts/extensions.js');
    const base='/scripts/extensions/third-party/Extension-Live2d/';
    const ui=await import(base+'ui.js'), live=await import(base+'live2d.js');
    const name='Phase0 Tile';
    if(!getContext().characters.some(c=>c.name===name)) {
      const response=await fetch('/api/characters/create',{method:'POST',headers:st.getRequestHeaders(),
        body:JSON.stringify({ch_name:name,description:'Original geometric compatibility fixture; not a character rig.',first_mes:'Phase 0 local test.'})});
      if(!response.ok)throw Error('Test character creation failed: '+response.status);
      await st.getCharacters();
    }
    await st.selectCharacterById(getContext().characters.findIndex(c=>c.name===name));
    await wait(1000);
    report.character=getContext().name2;
    if(report.character!==name)throw Error('Test character not active');
    const assets=await ui.getAssetsLive2dFiles();
    const model=assets.live2d?.find(p=>p.endsWith('/phase0/Generated_artwork.model3.json'));
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
    async function canvasEvidence() {
      return new Promise(resolve=>requestAnimationFrame(()=>{
        const canvas=document.querySelector('#live2d-canvas');
        if(!canvas)return resolve({present:false});
        const copy=document.createElement('canvas');copy.width=canvas.width;copy.height=canvas.height;
        const ctx=copy.getContext('2d');ctx.drawImage(canvas,0,0);
        const pixels=ctx.getImageData(0,0,copy.width,copy.height).data;
        let visible=0,turquoise=0;
        for(let i=0;i<pixels.length;i+=4){
          if(pixels[i+3]>0)visible++;
          if(Math.abs(pixels[i]-40)<8 && Math.abs(pixels[i+1]-180)<8 && Math.abs(pixels[i+2]-220)<8 && pixels[i+3]>200)turquoise++;
        }
        resolve({present:true,width:canvas.width,height:canvas.height,visible_pixels:visible,turquoise_pixels:turquoise});
      }));
    }
    report.first_render=await canvasEvidence();
    // Exercise the extension's own expression/motion entry points, without
    // claiming a visible facial expression from this geometric fixture.
    report.expression_loads=[];
    for(const expression of ['Smile','Sad','Angry','Surprised']) {
      await live.playExpression(name,expression);
      report.expression_loads.push(expression);
    }
    await live.playMotion(name,'Nod_id=0');
    report.motion_invoked='Nod_id=0';
    await live.loadLive2d();
    await wait(2000);
    report.reload_render=await canvasEvidence();
    if(!report.first_render.turquoise_pixels || !report.reload_render.turquoise_pixels)throw Error('Expected fixture pixels missing');
    if(document.querySelector('.popup[open]'))throw Error('Modal still obscures screenshot');
    report.status='pass';
    await st.saveSettings();
  } catch(error) {report.status='fail';report.error=String(error);report.stack=error.stack;}
  return report;
})()
