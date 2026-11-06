const test=require('node:test'),assert=require('node:assert/strict');
const {openingIndependent,invariant}=require('../scripts/mouth_invariant.cjs');
test('opening geometry dependencies cannot be excused by tiny movement',()=>{
 const d={seam:{axes:{ParamMouthCurve:[-1,0,1]},inherited:[{target:'parent'}]},parent:{axes:{ParamAngleX:[-30,0,30]}}};
 assert(openingIndependent('seam',d));d.parent.axes.ParamMouthOpenY=[0,1];assert(!openingIndependent('seam',d));delete d.parent;assert(!openingIndependent('seam',d));
});
test('float32 bound scales with model units but rejects source-pixel deformation',()=>{
 for(const scale of [.125,.5,1,2,8,32]){
 const ppu=1078/scale,a=[.03125*scale,.6875*scale];
 const rounded=[Math.fround(a[0]+2**-28*scale),Math.fround(a[1]+2**-24*scale)];
 assert(invariant(a,[rounded],ppu).pass);
 const moved=a.map(v=>v+.01/ppu);assert(!invariant(a,[moved],ppu).pass);
 assert(!invariant(a,[[NaN,a[1]]],ppu).pass);
 }
});
test('cap protects against coarse coordinates and malformed scale',()=>{
 assert(!invariant([1e8,1e8],[[1e8+.01,1e8]],100).pass);
 assert.throws(()=>invariant([1],[1],0));
});
