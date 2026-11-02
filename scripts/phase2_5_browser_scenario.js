// Evaluated via CDP in a fresh, isolated SillyTavern test instance.
(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const report = {stage:'phase2-5-experiment', status:'running', visual_character_rig_tested:true};
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
    const name='Phase2.5 CC0 Portrait';
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
    const model=assets.live2d?.find(p=>p.endsWith('/phase2-5/Generated_artwork.model3.json'));
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
    const internal=instance.internalModel, core=internal.coreModel;
    const ids=core._model.parameters.ids;
    const defaults=Array.from(core._model.parameters.defaultValues);
    report.parameter_ids=ids;
    report.drawables=core._model.drawables.count;
    report.frames={};report.parameters={};report.expressions={};
    const snapshots={};
    function pixelDiff(a,b) {
      let count=0;
      for(let i=0;i<a.length;i+=4)if(Math.max(...[0,1,2,3].map(j=>Math.abs(a[i+j]-b[i+j])))>20)count++;
      return count;
    }
    async function capture(label) {
      await wait(100);
      return new Promise(resolve=>requestAnimationFrame(()=>{
        const canvas=document.querySelector('#live2d-canvas');
        const copy=document.createElement('canvas');copy.width=canvas.width;copy.height=canvas.height;
        const ctx=copy.getContext('2d');ctx.drawImage(canvas,0,0);
        const pixels=ctx.getImageData(0,0,copy.width,copy.height).data;
        report.frames[label]=copy.toDataURL('image/png').split(',')[1];
        snapshots[label]=pixels;
        resolve(pixels);
      }));
    }
    let pose={};
    const holdPose=()=>{
      ids.forEach((id,i)=>core.setParameterValueById(id,pose[id]??defaults[i]));
    };
    // Control the full pose immediately before real Core.update. This removes
    // incidental idle/blink/focus motion from parameter-specific pixel tests.
    internal.on('beforeModelUpdate',holdPose);
    await capture('neutral');
    const repeat=await capture('neutral-repeat');
    report.control_noise_pixels=pixelDiff(snapshots.neutral,repeat);
    const cases={left_closed:{ParamEyeLOpen:0},right_closed:{ParamEyeROpen:0},blink_half:{ParamEyeLOpen:.5,ParamEyeROpen:.5},blink:{ParamEyeLOpen:0,ParamEyeROpen:0},mouth_half:{ParamMouthOpenY:.5},mouth_open:{ParamMouthOpenY:1},angle_x_minus:{ParamAngleX:-25},angle_x_plus:{ParamAngleX:25},angle_y_minus:{ParamAngleY:-20},angle_y_plus:{ParamAngleY:20},angle_z_minus:{ParamAngleZ:-20},angle_z_plus:{ParamAngleZ:20}};
    for(const [label,values] of Object.entries(cases)) {
      pose=values;
      const pixels=await capture(label);
      const changed=pixelDiff(snapshots.neutral,pixels);
      report.parameters[label]={values,changed_pixels:changed};
      if(changed<100 || changed<=report.control_noise_pixels*3)throw Error('No visible isolated deformation: '+label);
    }
    internal.off('beforeModelUpdate',holdPose);
    await live.loadLive2d(); await wait(1000);
    await capture('reload');
    report.status='pass';
    await st.saveSettings();
  } catch(error){report.status='fail';report.error=String(error);report.stack=error.stack;}
  return report;
})()
