// Real 589-shift CP-SAT WASM stress using the PREVIOUSLY COMPILED
// Google OR-Tools WebAssembly binary, not a mock and not a fresh compile.
// Entirely synthetic. Dense availability + leave/training/nightcheck/
// driving/meal-duty analogues are converted to anonymous eligibility bits.
// Source names/dates/real military events must NEVER enter GitHub.
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {monthFixture,serialize,independentlyAudit}=
 require('./month_real_wasm.cjs');

function reason(pool,staff,day,slot) {
  const night=slot<=4;
  const noon=pool==='door'?slot===8:slot===6;
  // Deterministic fictitious restrictions, NOT real personnel data:
  if(staff%23===22)return 'kitchen';
  if(staff%11===4 && night)return 'night-exempt';
  if(staff%13===6 && noon)return 'noon-exempt';
  const leave=2+(staff*7)%24; // two days leave, next day return
  if(day>=leave && day<=leave+2)return 'leave-or-return';
  if(day===leave-1 && night)return 'night-before-leave';
  if(staff%17===5 && day>=9 && day<=12)return 'training-with-prior-day';
  if(staff%19===6 && day>=16 && day<=18)return 'nightcheck-plus-minus-one';
  if(staff%23===12 && day>=22 && day<=23)return 'driver-or-rest';
  if(staff%23===12 && day===21 && night)return 'night-before-driving';
  if(pool==='officer' && staff%13===7 && day>=7 && day<=9)
    return 'meal-and-rest';
  if(pool==='officer' && staff%21===10 && day>=26 && day<=28)
    return 'officer-duty-and-rest';
  return null;
}
function createScenario(pool,variant) {
  if(!['door','officer'].includes(pool))throw Error('Unknown pool');
  if(!['blackouts-hints','blackouts-no-hints','forced-vacancies'].includes(variant))
    throw Error('Unknown synthetic variant');
  const basic=monthFixture(pool);
  const slots=pool==='door'?12:7;
  const group=pool==='door'?28:25;
  const total=basic.shiftCount;
  const mask=Array(total*basic.staff).fill('0');
  const witness=Array(total).fill(-1),pins=Array(total).fill(-2);
  const hints=Array(total).fill(-1);
  const reasonCounts={};
  const chosenTwoDaysBack=Array.from({length:slots},()=>[]);
  const forceBlank=(variant==='forced-vacancies');
  let eligiblePairs=0;
  for(let day=1;day<=31;day++){
    const parity=(day-1)%2;
    const base=parity*group;
    const used=new Set();
    const cycle=Math.floor((day-1)/2);
    for(let slot=1;slot<=slots;slot++){
      const i=(day-1)*slots+(slot-1);
      const intentionalHole=forceBlank && day===16;
      if(intentionalHole){
        pins[i]=-1; // ALL duty slots of this fabricated day stay blank.
        continue;
      }
      let chosen=-1;
      for(let delta=0;delta<group;delta++){
        const person=base+(slot-1+cycle*3+delta)%group;
        if(used.has(person))continue;
        if(reason(pool,person,day,slot))continue;
        if(day>=3 && chosenTwoDaysBack[slot-1].includes(person))continue;
        chosen=person;break;
      }
      if(chosen<0)throw Error('No legal fictitious witness '+pool+'/'+day+'/'+slot);
      witness[i]=chosen;used.add(chosen);
      if(variant!=='blackouts-no-hints')hints[i]=chosen;
      if([14,57,125].includes(i))pins[i]=chosen; // synthetic fixed staff
      for(let person=base;person<base+group;person++){
        const blocked=reason(pool,person,day,slot);
        if(blocked){
          reasonCounts[blocked]=(reasonCounts[blocked]||0)+1;
          continue;
        }
        mask[i*basic.staff+person]='1';eligiblePairs++;
      }
      if(mask[i*basic.staff+chosen]!=='1')
        throw Error('Constructed witness not in allowed matrix');
    }
    for(let slot=1;slot<=slots;slot++){
      const idx=(day-1)*slots+(slot-1);
      chosenTwoDaysBack[slot-1][day%2]=witness[idx];
    }
  }
  if(eligiblePairs<total*8)
    throw Error('Stress matrix is unexpectedly sparse');
  const frame={year:basic.year,month:basic.month,pool,
    staff:basic.staff,shiftCount:total,
    allowed:mask.join(''),pins,hints,witness,
    source:'synthetic-fictional-blackout-matrix',
    variant,eligiblePairs,reasonCounts};
  independentlyAudit(frame,{assignments:witness,
    filled:witness.filter(x=>x>=0).length,
    missing:witness.filter(x=>x<0).length});
  for(let i=0;i<total;i++){
    const p=witness[i];
    if(p>=0 && reason(pool,p,Math.floor(i/slots)+1,(i%slots)+1))
      throw Error('Witness violates fictional event '+pool+'/'+i);
    if(pins[i]>=0 && pins[i]!==p)
      throw Error('Reference witness violates artificial fixed assignment');
  }
  return frame;
}
function preflight(){
  const all=[];
  for(const pool of ['door','officer']){
    for(const variant of ['blackouts-hints','blackouts-no-hints','forced-vacancies']){
      const scenario=createScenario(pool,variant);
      const filled=scenario.witness.filter(x=>x>=0).length;
      const blocked=scenario.witness.length-filled;
      if(filled !== scenario.shiftCount-(variant==='forced-vacancies'?(pool==='door'?12:7):0))
        throw Error('Incorrect reference fill for '+pool+'/'+variant);
      if(scenario.allowed.length!==scenario.shiftCount*scenario.staff)
        throw Error('Matrix shape mismatch');
      if(!serialize(scenario).startsWith('guard-month-v2\n2026-12\n'+pool+'\n'))
        throw Error('Invalid protocol framing');
      all.push({pool,variant,tasks:scenario.shiftCount,staff:scenario.staff,
        eligiblePairs:scenario.eligiblePairs,knownLegalFill:filled,
        forcedMissing:blocked,reasonCounts:scenario.reasonCounts,
        independent_witness_audited:true});
    }
  }
  return {accepted:true,mode:'synthetic-preflight-not-WASM',cases:all};
}
function memory(){
  const m=process.memoryUsage();
  return {rss_mb:Math.round(m.rss/1048576*10)/10,
    heap_mb:Math.round(m.heapUsed/1048576*10)/10,
    external_mb:Math.round(m.external/1048576*10)/10};
}
async function benchmark(jsfile,wasmfile,outfile){
  const pre=preflight();
  const data=fs.readFileSync(wasmfile);
  if(!WebAssembly.validate(data))throw Error('Not valid true WASM');
  let factory=require(path.resolve(jsfile));
  if(typeof factory==='object'&&typeof factory.default==='function')factory=factory.default;
  if(typeof factory!=='function')throw Error('Missing real Emscripten WASM factory');
  const boot=process.hrtime.bigint();
  const mod=await factory({wasmBinary:new Uint8Array(data),
    print:()=>{},printErr:s=>process.stderr.write(String(s)+'\n')});
  const bootMs=Number(process.hrtime.bigint()-boot)/1e6;
  const out=[];
  for(const p of pre.cases){
    const t=createScenario(p.pool,p.variant);
    const begin=process.hrtime.bigint();
    const response=JSON.parse(mod.ccall('solve_guard_month_v2','string',['string'],
      [serialize(t)]));
    const elapsedMs=Number(process.hrtime.bigint()-begin)/1e6;
    const status=response.status;
    if(!['OPTIMAL','FEASIBLE','UNKNOWN','INFEASIBLE'].includes(status))
      throw Error('Unexpected solver status: '+status);
    // The independent, validated constructive witness proves feasible.
    // INFEASIBLE therefore would prove a modelling bug, not manpower shortage.
    if(status==='INFEASIBLE')
      throw Error('CP-SAT falsely declared demonstrably feasible synthetic model INFEASIBLE');
    const referenceFilled=t.witness.filter(x=>x>=0).length;
    let returnedFilled=null;
    let missedBySolver=null;
    let auditValid=false;
    if(status==='OPTIMAL'||status==='FEASIBLE'){
      returnedFilled=independentlyAudit(t,response);
      auditValid=true;
      missedBySolver=referenceFilled-returnedFilled;
      if(missedBySolver<0)
        throw Error('CP-SAT assigned slots intentionally removed from scenario');
      if(status==='OPTIMAL'&&missedBySolver!==0)
        throw Error('Claimed OPTIMAL less than proven independently legal witness');
    }else{
      // UNKNOWN is not zero filled and cannot be used as a published roster.
      if(response.assignments!==undefined)
        throw Error('UNKNOWN response must not contain supposedly valid schedule');
    }
    const record={
      pool:p.pool,variant:p.variant,shifts:t.shiftCount,staff:t.staff,
      candidates:t.eligiblePairs,synthetic_restrictions:p.reasonCounts,
      status,elapsed_ms:Math.round(elapsedMs),
      independent_reference_fill:referenceFilled,
      wasm_returned_fill:returnedFilled,
      gap_to_independent_feasible_reference:missedBySolver,
      returned_schedule_independently_audited:auditValid,
      proof_of_maximum_fill:(auditValid&&missedBySolver===0),
      full_operational_rules_tested:false,real_iphone_safari_tested:false,
      node_memory_after:memory(),
    };
    out.push(record);
    console.log(JSON.stringify(record));
  }
  const report={
    benchmark_executed:true,
    engine:'actual-OR-Tools-CP-SAT-in-Node-WASM',
    contract:'guard-month-v2',
    case_count:out.length,
    real_device_benchmark:false,
    all_operational_rules_tested:false,
    objective_scope:'maximum-legal-fill-under-current-partial-constraints',
    notes:'UNKNOWN means not solved, not zero fill. FEASIBLE means not necessarily optimal.',
    wasm_sha256:crypto.createHash('sha256').update(data).digest('hex'),
    js_sha256:crypto.createHash('sha256').update(fs.readFileSync(jsfile)).digest('hex'),
    initialization_ms:Math.round(bootMs),
    preflight:pre,results:out
  };
  fs.writeFileSync(outfile,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({benchmark_executed:true,
    cases:out.map(({pool,variant,status,wasm_returned_fill,
      independent_reference_fill,elapsed_ms})=>({
        pool,variant,status,wasm_returned_fill,independent_reference_fill,elapsed_ms
      }))},null,2));
}
if(require.main===module){
 if(process.argv[2]==='--preflight'){
  try{console.log(JSON.stringify(preflight(),null,2));}
  catch(e){console.error(e);process.exitCode=1;}
 }else{
  const [js,wasm,result]=process.argv.slice(2);
  if(!js||!wasm||!result)throw Error('Usage: node wasm_dense_month_benchmark.cjs --preflight OR glue.js module.wasm proof.json');
  benchmark(js,wasm,result).catch(e=>{console.error('TRUE WASM DENSE BENCHMARK FAILED:',e);
    process.exitCode=1;});
 }
}
module.exports={createScenario,preflight,reason};
