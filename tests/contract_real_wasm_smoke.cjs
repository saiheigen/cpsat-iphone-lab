'use strict';
// Manual release gate only: genuine C++ WASM + independent JS temporal audit.
// All cases invented; this does not authenticate original operational v7.
const fs=require('node:fs');
const crypto=require('node:crypto');
const path=require('node:path');
const {independentlyAudit}=require('../integration/month_audit.cjs');

const SCENARIOS=[
 ['door','same_day_exact_6h',[[1,5],[1,9]],true],
 ['door','same_day_insufficient_4h',[[1,5],[1,8]],false],
 ['door','same_day_night_then_evening',[[1,3],[1,1]],true],
 ['door','adjacent_day',[[1,1],[2,5]],false],
 ['door','same_shift_two_day_gap',[[1,5],[3,5]],false],
 ['door','same_shift_three_day_gap',[[1,5],[4,5]],true],
 ['door','consecutive_sunday_standby',[[6,5],[13,9]],false],
 ['door','sunday_to_next_sunday_nonstandby',[[6,5],[13,12]],true],
 ['officer','same_day_double',[[1,2],[1,7]],false],
 ['officer','adjacent_day',[[1,2],[2,5]],false],
 ['officer','same_shift_two_day_gap',[[1,7],[3,7]],false],
 ['officer','consecutive_sunday_standby',[[6,7],[13,7]],false],
 ['officer','sunday_nonstandby_then_standby',[[6,6],[13,7]],true],
 ['officer','separated_three_day',[[1,5],[4,5]],true]
];
function scenarioInput(pool,duties){
 const slots=pool==='door'?12:7,n=31*slots;
 const mask=Array(n).fill('0'),pins=Array(n).fill(-2),hints=Array(n).fill(-1);
 for(const [day,slot] of duties){
  const pos=(day-1)*slots+slot-1;
  mask[pos]='1';pins[pos]=0;
 }
 return {pool,n,mask:mask.join(''),pins,hints,
  wire:['guard-month-harsh-v4','2026-12',pool,String(n)+' 1',
    mask.join(''),pins.join(','),hints.join(','),'2'].join('\n')+'\n'};
}
function digest(bytes){return crypto.createHash('sha256').update(bytes).digest('hex');}
async function main(){
 const [modulePath,wasmPath,proofPath,outPath]=process.argv.slice(2);
 if(!modulePath||!wasmPath||!proofPath||!outPath)
  throw Error('Usage: node tests/contract_real_wasm_smoke.cjs module.js module.wasm proof.json out.json');
 const jsBytes=fs.readFileSync(modulePath),wasm=fs.readFileSync(wasmPath);
 const proof=JSON.parse(fs.readFileSync(proofPath,'utf8'));
 if(proof.accepted!==true||proof.contract!=='guard-month-harsh-v4'||
    proof.js_sha256!==digest(jsBytes)||proof.wasm_sha256!==digest(wasm)||
    !WebAssembly.validate(wasm))throw Error('Untrusted or changed genuine WASM artifact');
 const createModule=require(path.resolve(modulePath));
 const engine=await createModule({wasmBinary:new Uint8Array(wasm),print:()=>{},printErr:()=>{}});
 const results=[];
 for(const [pool,name,duties,expectedLegal] of SCENARIOS){
  const f=scenarioInput(pool,duties);
  const response=JSON.parse(engine.ccall('solve_guard_month_harsh_v4','string',['string'],[f.wire]));
  const legal=response.status==='FEASIBLE'||response.status==='OPTIMAL';
  if(legal!==expectedLegal||(!legal&&response.status!=='INFEASIBLE')||
     (legal&&(response.filled!==2||response.missing!==f.n-2)))
   throw Error('C++/WASM temporal mismatch: '+pool+'/'+name+': '+response.status);
  if(legal)independentlyAudit({year:2026,month:12,pool,staff:1,shiftCount:f.n,
    allowed:f.mask,pins:f.pins,hints:f.hints},response);
  results.push({pool,case:name,expected_legal:expectedLegal,status:response.status});
 }
 fs.writeFileSync(outPath,JSON.stringify({synthetic_only:true,verified_real_node_wasm:true,
  source_wasm_sha256:proof.wasm_sha256,verified_original_v7:false,
  operationally_certified:false,checked:results.length,passed:results.length,results},null,2)+'\n');
 console.log('Genuine C++ WASM temporal rule cases: '+results.length+'/'+results.length+' PASS');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
