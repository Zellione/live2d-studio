// A binary32 representation bound is usable only with an independent structural
// contract: the seam and every geometric ancestor must exclude mouth opening.
function openingIndependent(target,details){
 const d=details[target];if(!d)return false;
 const all=[d,...d.inherited.map(a=>details[a.target])];
 return all.every(x=>x&&x.axes&&!Object.hasOwn(x.axes,'ParamMouthOpenY'));
}
function seamBound(reference,pixelsPerUnit){
 const magnitude=Math.max(...reference.map(Math.abs));
 if(!Number.isFinite(magnitude)||!Number.isFinite(pixelsPerUnit)||pixelsPerUnit<=0)throw Error('Invalid geometry scale');
 const ulp=2**(Math.floor(Math.log2(Math.max(magnitude,2**-126)))-23);
 // Eight representable steps at the largest mesh coordinate, independently
 // capped at a thousandth of one source pixel. No large geometric error waiver.
 return Math.min(8*ulp,.001/pixelsPerUnit);
}
function invariant(reference,samples,pixelsPerUnit){
 const bound=seamBound(reference,pixelsPerUnit);
 const max=Math.max(...samples.map(s=>Math.max(...s.map((v,i)=>Math.abs(v-reference[i])))));
 return {pass:Number.isFinite(max)&&max<=bound,max,bound,source_pixels:max*pixelsPerUnit};
}
module.exports={openingIndependent,seamBound,invariant};
