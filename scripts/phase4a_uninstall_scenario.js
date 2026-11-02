(async () => {
  const wait=ms=>new Promise(r=>setTimeout(r,ms));
  try {
    for(let i=0;i<100&&!document.querySelector('#live2d_enabled_checkbox');i++)await wait(200);
    if(!document.querySelector('#live2d_enabled_checkbox'))throw Error('Extension did not initialize');
    const ui=await import('/scripts/extensions/third-party/Extension-Live2d/ui.js');
    const assets=await ui.getAssetsLive2dFiles();
    const remaining=assets.live2d||[];
    if(remaining.some(p=>p.includes('/phase3/')))throw Error('Removed Girl2 is still discoverable');
    if(!remaining.some(p=>p.includes('/phase0/')))throw Error('Existing model disappeared');
    return {stage:'phase4a-uninstall',status:'pass',removed_model_discoverable:false,existing_model_preserved:true,models:remaining};
  }catch(error){return {stage:'phase4a-uninstall',status:'fail',error:String(error)};}
})()
