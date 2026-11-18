// Real three-phase Google OR-Tools CP-SAT C++ WebAssembly (NOT mock).
// Clocks, data and 589-shift rosters are strictly synthetic and fictional.
// C++ must preserve every phase-2 occupied position and total count L1,
// then improve v7-inspired night/noon/long-shift category exposure.
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {createScenario}=require('./wasm_dense_month_benchmark.cjs');
const {sparseFixture,independentlyAudit}=require('./month_real_wasm.cjs');
const {wire:fairWire,score:countScore,targetsFor}=require('./month_fair_real_wasm.cjs');

function wire(s,targets){
 return fairWire(s,targets).replace('guard-month-fair-v3\n','guard-month-harsh-v4\n');
}
function categories(pool,k){
 if(pool==='door'){
  if(k<4)return {'night_total':1,
   [['night_22_24','night_00_02','night_02_04','night_04_06'][k]]:1};
  return k===7?{'noon':1}:{};
 }
 const hours=[2,2,2,2,6,6,4][k];
 const out={officer_hours:hours};
 if(k<4)out.night_total=1;
 if(k===5)out.noon=1;
 if(k===4||k===5)out.officer_six_hour=1;
 return out;
}
const weights={night_total:2,night_22_24:1,night_00_02:1,
 night_02_04:1,night_04_06:1,noon:2,officer_hours:1,
 officer_six_hour:2};
function hardshipScore(s,assignment){
 const staff=s.staff,slots=s.pool==='door'?12:7;
 const counts=Array(staff).fill(0);
 const loads=Array.from({length:staff},()=>({}));
 const totals={};let filled=0;
 for(let i=0;i<s.shiftCount;i++){
  const person=assignment[i];
  if(person<0)continue;
  filled++;counts[person]++;
  for(const [c,u] of Object.entries(categories(s.pool,i%slots))){
   loads[person][c]=(loads[person][c]||0)+u;
   totals[c]=(totals[c]||0)+u;
  }
 }
 let total=0;
 for(const [cat,n] of Object.entries(totals)){
  for(let p=0;p<staff;p++)
   total+=weights[cat]*Math.abs(filled*(loads[p][cat]||0)-n*counts[p]);
 }
 return total;
}
function check(s,targets,r){
 if(!['FEASIBLE','OPTIMAL'].includes(r.status))
  throw Error('No legal v4 C++/WASM result');
 const filled=independentlyAudit(s,r);
 const counted=countScore(r.assignments,targets);
 if(JSON.stringify(counted.counts)!==JSON.stringify(r.actual_counts))
  throw Error('Incorrect individual shift counts');
 if(counted.deviation!==r.final_abs_deviation ||
    counted.deviation>r.phase1_abs_deviation)
  throw Error('Lost original fair-count L1 objective');
 if(r.fixed_occupied_positions!==true)
  throw Error('Stage-2 occupied-position protection absent');
 if(!['OPTIMAL','FEASIBLE','UNKNOWN'].includes(r.hardship_phase))
  throw Error('Invalid hardship phase');
 if(r.hardship_optimal_proven_given_locked_predecessors!==(
       r.hardship_phase==='OPTIMAL'))
  throw Error('Misleading hardship optimality status');
 const harsh=hardshipScore(s,r.assignments);
 if(harsh!==r.hardship_final_score ||
    harsh>r.hardship_initial_score)
  throw Error('Wrong hardship objective or worsening');
 if(r.hardship_improved!==(harsh<r.hardship_initial_score))
  throw Error('Incorrect hardship improvement claim');
 if(r.status==='OPTIMAL' &&
    !(r.fill_optimal_proven && r.fair_optimal_proven_given_fill &&
      r.hardship_optimal_proven_given_locked_predecessors))
  throw Error('Fake all-stage proven OPTIMAL');
 return {filled,countDeviation:counted.deviation,
  hardship:harsh,originalHardship:r.hardship_initial_score};
}
function toy(){
 const items=[];
 for(const [day,slot] of [[1,1],[1,8],[4,2],[4,8]])
  for(const person of [0,1])items.push([day,slot,person,false]);
 return sparseFixture('door',12,2,items);
}
function exactToyOracle(s){
 const active=[];
 for(let i=0;i<s.shiftCount;i++)if(
  [...Array(s.staff).keys()].some(p=>s.allowed[i*s.staff+p]==='1'))
   active.push(i);
 if(active.length!==4||s.staff!==2)throw Error('Unexpected exact toy domain');
 let best=Infinity,valid=0;
 for(let bits=0;bits<(1<<active.length);bits++){
  const a=Array(s.shiftCount).fill(-1);
  for(let k=0;k<active.length;k++)a[active[k]]=(bits>>k)&1;
  try{independentlyAudit(s,{
   assignments:a,filled:4,missing:s.shiftCount-4});}
  catch(err){continue;}
  if(countScore(a,[2,2]).deviation!==0)continue;
  best=Math.min(best,hardshipScore(s,a));valid++;
 }
 if(!Number.isFinite(best)||!valid)throw Error('No independently valid oracle');
 return {best,valid};
}
function preflight(){
 const s=toy(),oracle=exactToyOracle(s);
 if(!wire(s,[2,2]).startsWith('guard-month-harsh-v4\n2026-12\ndoor\n'))
  throw Error('Invalid v4 wire');
 const samples=[];
 for(const [pool,variant] of [['door','blackouts-no-hints'],
                               ['officer','blackouts-no-hints'],
                               ['door','forced-vacancies']]){
  const t=createScenario(pool,variant);
  const targets=targetsFor(t);
  if(wire(t,targets).trimEnd().split('\n').length!==8)
   throw Error('Truncated v4 complete-month frame');
  samples.push({pool,variant,shifts:t.shiftCount,staff:t.staff,
                expected_fill:t.witness.filter(x=>x>=0).length});
 }
 return {accepted:true,stage:'JS-fictional-preflight-NOT-WASM',
         exact_toy_oracle:oracle,samples};
}
async function main(){
 const [jsfile,wasmfile,outfile]=process.argv.slice(2);
 if(!jsfile||!wasmfile||!outfile)
  throw Error('Expected genuine module.js module.wasm proof.json');
 const binary=fs.readFileSync(wasmfile);
 if(!WebAssembly.validate(binary))throw Error('Not a genuine WASM binary');
 let factory=require(path.resolve(jsfile));
 if(factory&&typeof factory.default==='function')factory=factory.default;
 if(typeof factory!=='function')throw Error('No actual Emscripten module factory');
 const engine=await factory({wasmBinary:new Uint8Array(binary),
  print:()=>{},printErr:s=>process.stderr.write(String(s)+'\n')});
 const call=(frame)=>JSON.parse(engine.ccall(
  'solve_guard_month_harsh_v4','string',['string'],[frame]));
 const begin=Date.now();
 const cases=[],ref=preflight();
 const s=toy(),oracle=exactToyOracle(s);
 const tiny=call(wire(s,[2,2])),checked=check(s,[2,2],tiny);
 if(checked.filled!==4||checked.countDeviation!==0||
    checked.hardship!==oracle.best||tiny.hardship_phase!=='OPTIMAL')
  throw Error('Genuine 3-stage WASM violates independent exhaustive toy oracle');
 cases.push({name:'exact-four-shift-hardship-oracle',accepted:true,
  status:tiny.status,filled:checked.filled,hardship:checked.hardship,
  oracle:oracle.best});
 for(const [pool,variant] of [['door','blackouts-no-hints'],
                               ['officer','blackouts-no-hints'],
                               ['door','forced-vacancies']]){
  const t=createScenario(pool,variant),goals=targetsFor(t);
  const start=Date.now(),got=call(wire(t,goals)),audit=check(t,goals,got);
  const expected=t.witness.filter(x=>x>=0).length;
  if(audit.filled!==expected)
   throw Error('3rd-stage hardship sacrificed valid filled shifts');
  cases.push({name:pool+'-'+variant,accepted:true,status:got.status,
   fill_phase:got.fill_phase,fair_phase:got.fair_phase,
   hardship_phase:got.hardship_phase,
   shifts:t.shiftCount,staff:t.staff,filled:audit.filled,
   phase1_abs_deviation:got.phase1_abs_deviation,
   final_abs_deviation:audit.countDeviation,
   hardship_before:audit.originalHardship,hardship_after:audit.hardship,
   hardship_optimal_proven:got.hardship_optimal_proven_given_locked_predecessors,
   elapsed_ms:Date.now()-start});
 }
 const infeasible=sparseFixture('officer',12,1,
  [[1,5,0,true],[2,5,0,true]]);
 const bad=call(wire(infeasible,[0]));
 if(bad.status!=='INFEASIBLE'||bad.hardship_phase!=='NOT_RUN')
  throw Error('Hard pinned next-day conflict became relaxed');
 const sample=wire(s,[2,2]);
 const invalidFrames=[
  sample.replace('guard-month-harsh-v4','guard-month-fair-v3'),
  sample.replace(/\n2,2\n$/,'\n2\n'),
  sample.replace(/\n2,2\n$/,'\n-1,3\n')
 ];
 for(const input of invalidFrames)
  if(call(input).status!=='INVALID_INPUT')
   throw Error('Invalid v4 model accepted');
 const proof={
  accepted:true,engine:'genuine-Google-OR-Tools-CP-SAT-WASM',
  contract:'guard-month-harsh-v4',three_phases:true,
  filled_positions_protected:true,count_fairness_protected:true,
  synthetic_only:true,real_iphone_safari_tested:false,
  operationally_certified:false,full_hard_rules_verified:false,
  exact_independent_hardship_oracle_verified:true,
  tested_full_589_dense_shifts:true,
  invalid_frames_rejected:invalidFrames.length,
  cases,
  wasm_sha256:crypto.createHash('sha256').update(binary).digest('hex'),
  js_sha256:crypto.createHash('sha256').update(fs.readFileSync(jsfile)).digest('hex'),
  elapsed_ms:Date.now()-begin
 };
 fs.writeFileSync(outfile,JSON.stringify(proof,null,2)+'\n');
 console.log(JSON.stringify(proof,null,2));
}
if(require.main===module){
 if(process.argv[2]==='--preflight')console.log(JSON.stringify(preflight(),null,2));
 else main().catch(e=>{console.error('GENUINE 3-STAGE WASM FAILED:',e);
   process.exitCode=1;});
}
module.exports={wire,categories,hardshipScore,exactToyOracle,preflight,toy,check};
