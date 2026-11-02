import {test} from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {TalkController,mouthValue} from '../integrations/sillytavern/rp-talk.mjs';
const settings={param_mouth_open_y_id:'ParamMouthOpenY',mouth_time_per_character:30,mouth_open_speed:3};
function fixture(){const internal=new EventEmitter();let value=0;internal.coreModel={setParameterValueById:(id,v)=>{value=v;}};return {model:{internalModel:internal},internal,value:()=>value};}
test('bounded smooth envelope and exact resting endpoints',()=>{
 const values=Array.from({length:2001},(_,i)=>mouthValue(i,2000));
 assert.equal(values[0],0);assert.equal(values.at(-1),0);assert(Math.max(...values)<=.85);
 assert(Math.max(...values)> .8);assert(Math.min(...values)>=0);
 assert(Math.max(...values.slice(1).map((v,i)=>Math.abs(v-values[i])))<.02);
});
test('new reply replaces old callback without closing the new generation',async()=>{
 let now=0;const c=new TalkController(()=>now),f=fixture();
 const first=c.play('girl',f.model,'long message',settings);now=150;f.internal.emit('afterMotionUpdate');assert(f.value()>0);
 const second=c.play('girl',f.model,'new message',settings);await first;
 assert.equal(f.internal.listenerCount('afterMotionUpdate'),1);now=300;f.internal.emit('afterMotionUpdate');assert(f.value()>0);
 c.cancel('girl');await second;assert.equal(f.value(),0);assert.equal(f.internal.listenerCount('afterMotionUpdate'),0);
});
test('reload and character switch clean all callbacks and mouth values',async()=>{
 const c=new TalkController(()=>200),a=fixture(),b=fixture();
 const promises=[c.play('a',a.model,'hello',settings),c.play('b',b.model,'hello',settings)];
 c.cancelAll();await Promise.all(promises);assert.equal(c.active.size,0);
 assert.equal(a.internal.listenerCount('afterMotionUpdate'),0);assert.equal(b.value(),0);
});
test('destroyed models and completed duration release sessions',async()=>{
 let now=0;const c=new TalkController(()=>now),a=fixture();
 const done=c.play('a',a.model,'hi',settings);now=61;a.internal.emit('afterMotionUpdate');await done;assert.equal(c.active.size,0);
 const destroyed=c.play('a',a.model,'hi',settings);a.model.destroyed=true;a.internal.emit('afterMotionUpdate');await destroyed;assert.equal(c.active.size,0);
});
test('disabled mouth creates no animation or timer',async()=>{
 const c=new TalkController(),a=fixture();await c.play('a',a.model,'hi',{...settings,param_mouth_open_y_id:'none'});assert.equal(c.active.size,0);
});
