// Frame-aligned text animation, not phonemes or audio/TTS synchronization.
export function mouthValue(elapsed, duration, speed=3) {
  if(elapsed<=0 || elapsed>=duration)return 0;
  const attack=Math.min(1,elapsed/100),release=Math.min(1,(duration-elapsed)/150);
  const frequency=Math.max(1,Math.min(6,Number(speed)||3))*1.2;
  const wave=(1-Math.cos(elapsed/1000*Math.PI*2*frequency))/2;
  return .85*wave*wave*attack*release;
}
export class TalkController {
  constructor(now=()=>performance.now()){this.now=now;this.active=new Map();}
  cancel(character){this.active.get(character)?.finish();}
  cancelAll(){for(const item of [...this.active.values()])item.finish();}
  play(character,model,text,settings){
    this.cancel(character);
    const internal=model?.internalModel,core=internal?.coreModel,id=settings.param_mouth_open_y_id;
    if(!core||!id||id==='none')return Promise.resolve();
    const duration=Math.min(60000,Math.max(0,String(text).length*(Number(settings.mouth_time_per_character)||30)));
    if(!duration)return Promise.resolve();
    const start=this.now();
    return new Promise(resolve=>{
      const item={};
      item.finish=()=>{
        if(this.active.get(character)!==item)return;
        clearTimeout(item.timer);internal.off('afterMotionUpdate',item.update);
        if(!model.destroyed&&model.internalModel?.coreModel===core)core.setParameterValueById(id,0);
        this.active.delete(character);resolve();
      };
      item.update=()=>{
        const elapsed=this.now()-start;
        if(model.destroyed||model.internalModel?.coreModel!==core||elapsed>=duration){item.finish();return;}
        // Before saveParameters/expressions: emotional offsets remain composable.
        core.setParameterValueById(id,mouthValue(elapsed,duration,settings.mouth_open_speed));
      };
      this.active.set(character,item);internal.on('afterMotionUpdate',item.update);
      item.timer=setTimeout(item.finish,duration+50); // hidden/suspended tab cleanup
    });
  }
}
