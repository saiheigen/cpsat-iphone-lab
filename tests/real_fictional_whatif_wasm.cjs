'use strict';
// Manual genuine-WASM release smoke, NEVER a mock solver or regular CI test.
// All inputs are the sealed, fictional in-page snapshot. No network or real rosters.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {independentlyAudit}=require('../integration/month_audit.cjs');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function requireTruthy(x,reason){if(!x)throw Error(reason);}
function srcFrames(html){
 const match=html.match(/const SPEC=(\{.*?\});\nconst section=/s);
 requireTruthy(match,'No sealed fictional page source');
 const obj=JSON.parse(match[1]);
 requireTruthy(obj.synthetic_only===true&&obj.operationally_certified===false&&
   obj.month==='2026-12','Non-fictional page source');
 return obj;
}
function extract(pool,source){
 const wire=source.frames[pool].wire;
 requireTruthy(sha(Buffer.from(wire,'ascii'))===source.frames[pool].sha256,
   'Frame source bytes changed');
 const lines=wire.split('\n');
 requireTruthy(lines.length===9&&lines[8]===''&&lines[0]==='guard-month-harsh-v4'&&
   lines[2]===pool,'Wrong frame structure');
 const [count,staff]=lines[3].split(' ').map(Number);
 return {pool,year:2026,month:12,shifts:count,staff,mask:lines[4],
   pins:lines[5].split(',').map(Number),hints:lines[6].split(',').map(Number),
   targets:lines[7].split(',').map(Number),wire};
}
function edited(original){
 const r={...original,pins:[...original.pins],hints:[...original.hints]};
 const mask=[...original.mask];const slots=12;
 // Only a provable RESTRICTION of ten preexisting optional eligible rows.
 // Keep original pinned slot 6 and optional slot 12 available.
 for(const slot of [1,2,3,4,5,7,8,9,10,11]){
  const index=(7-1)*slots+slot-1,p=48;
  requireTruthy(r.pins[index]===-2&&mask[index*r.staff+p]==='1'&&
      r.hints[index]===-1,'Trying to alter fixed duty or unavailable candidate');
  mask[index*r.staff+p]='0';
 }
 r.mask=mask.join('');
 r.wire=['guard-month-harsh-v4','2026-12',r.pool,
   r.shifts+' '+r.staff,r.mask,r.pins.join(','),r.hints.join(','),r.targets.join(',')].join('\n')+'\n';
 requireTruthy(original.mask.length===r.mask.length &&
  [...r.mask].every((bit,i)=>bit==='0'||original.mask[i]==='1'),
  'An ineligible person became eligible');
 return r;
}
async function main(){
 const [jsFile,wasmFile,proofFile,htmlFile,outFile]=process.argv.slice(2);
 if(!jsFile||!wasmFile||!proofFile||!htmlFile||!outFile)
  throw Error('Usage: node tests/real_fictional_whatif_wasm.cjs module.js module.wasm proof.json page.html report.json');
 const proof=JSON.parse(fs.readFileSync(proofFile,'utf8'));
 const js=fs.readFileSync(jsFile),wasm=fs.readFileSync(wasmFile);
 const source=srcFrames(fs.readFileSync(htmlFile,'utf8'));
 requireTruthy(proof.accepted===true&&proof.contract==='guard-month-harsh-v4'&&
   proof.js_sha256===sha(js)&&proof.wasm_sha256===sha(wasm)&&
   source.wasm_sha256===sha(wasm)&&WebAssembly.validate(wasm),
  'Original WASM provenance or content mismatch');
 const create=require(path.resolve(jsFile));
 const wasmModule=await create({wasmBinary:new Uint8Array(wasm),print:()=>{},printErr:()=>{}});
 const results=[];
 for(const whatif of [false,true]){
  for(const pool of ['door','officer']){
   const original=extract(pool,source),t=whatif&&pool==='door'?edited(original):original;
   const got=JSON.parse(wasmModule.ccall('solve_guard_month_harsh_v4','string',['string'],[t.wire]));
   requireTruthy(['FEASIBLE','OPTIMAL'].includes(got.status),
      'Genuine C++ rejected '+pool+' modified='+whatif+' status='+got.status);
   const filled=independentlyAudit({year:t.year,month:t.month,pool:t.pool,
     staff:t.staff,shiftCount:t.shifts,allowed:t.mask,pins:t.pins,hints:t.hints},got);
   requireTruthy(got.filled===filled&&
      got.missing===t.shifts-filled&&filled>=1&&filled<=(pool==='door'?3:1),
      'Genuine C++ solved an illegal or count-inflated roster');
   if(whatif&&pool==='door')requireTruthy(filled===2,
     'Restrictive synthetic edit should leave only two guarded shifts');
   results.push({pool,whatif,status:got.status,filled,missing:got.missing});
  }
 }
 const record={synthetic_only:true,real_wasm_invoked:true,
   wasm_sha256:sha(wasm),cases:results,original_v7_parity_verified:false,
   operationally_certified:false,real_iphone_safari_verified:false};
 fs.writeFileSync(outFile,JSON.stringify(record,null,2)+'\n');
 console.log('Genuine WASM fictional what-if '+results.length+'/'+results.length+' PASS',results);
}
main().catch(e=>{console.error(e);process.exitCode=1;});
