// Real two-phase OR-Tools C++/WASM acceptance. No mock solver.
// Synthetic dense 589-shift examples plus small exact fairness oracle.
// If the full fairness stage times out, mark FEASIBLE instead of OPTIMAL.
// The original proven guard-month-v2 module remains unchanged.
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {createScenario}=require('./wasm_dense_month_benchmark.cjs');
const {sparseFixture,independentlyAudit}=require('./month_real_wasm.cjs');

function targetsFor(s){
 const counts=Array(s.staff).fill(0);
 for(let slot=0;slot<s.shiftCount;slot++)
  for(let person=0;person<s.staff;person++)
   if(s.allowed[slot*s.staff+person]==='1')counts[person]++;
 const weights=counts.map((v,p)=>v*(p%9===2?1/3:1));
 const sum=weights.reduce((a,b)=>a+b,0);
 const total=s.shiftCount-s.pins.filter(x=>x===-1).length;
 const exact=weights.map(w=>sum?total*w/sum:0);
 const target=exact.map(Math.floor);
 const remainder=total-target.reduce((a,b)=>a+b,0);
 const ranked=exact.map((v,i)=>({i,fract:v-target[i]}))
   .sort((a,b)=>b.fract-a.fract||a.i-b.i);
 for(let i=0;i<remainder;i++)target[ranked[i].i]++;
 // Synthetic cross-month credit: reduce one positive target; follow-on
 // rebalance is not claimed to be the exact user-facing v7 calculation.
 const credited=target.findIndex(x=>x>=3);
 if(credited>=0)target[credited]-=2;
 return target;
}
function wire(s,targets){
 if(!Array.isArray(targets)||targets.length!==s.staff)
  throw Error('Wrong target vector shape');
 return ['guard-month-fair-v3',
  String(s.year)+'-'+String(s.month).padStart(2,'0'),
  s.pool,String(s.shiftCount)+' '+String(s.staff),
  s.allowed,s.pins.join(','),s.hints.join(','),targets.join(',')
 ].join('\n')+'\n';
}
function score(assign,targets){
 const actual=Array(targets.length).fill(0);
 for(const p of assign){if(p>=0)actual[p]++;}
 return {counts:actual,deviation:actual.reduce(
   (n,v,i)=>n+Math.abs(v-targets[i]),0)};
}
function check(s,targets,r){
 if(r.status!=='OPTIMAL'&&r.status!=='FEASIBLE')
  throw Error('No feasible two-stage result '+r.status);
 const filled=independentlyAudit(s,r);
 const counted=score(r.assignments,targets);
 if(JSON.stringify(counted.counts)!==JSON.stringify(r.actual_counts))
  throw Error('Wrong reported per-person counts');
 if(counted.deviation!==r.final_abs_deviation)
  throw Error('Wrong reported fairness objective');
 if(r.final_abs_deviation>r.phase1_abs_deviation)
  throw Error('Fairness worsened the original valid schedule');
 if(!['OPTIMAL','FEASIBLE'].includes(r.fill_phase))
  throw Error('No proven first-stage legal roster');
 if(!['OPTIMAL','FEASIBLE','UNKNOWN'].includes(r.fair_phase))
  throw Error('Invalid second-stage solver status');
 if(r.fair_optimal_proven_given_fill && r.fair_phase!=='OPTIMAL')
  throw Error('Fake fairness optimality status');
 if(r.status==='OPTIMAL'&&
    !(r.fill_optimal_proven && r.fair_optimal_proven_given_fill))
  throw Error('Fake overall OPTIMAL');
 return {filled,counts:counted.counts,absDeviation:counted.deviation};
}
function tiny(){
 const s=sparseFixture('door',12,2,[
  [1,5,0,false],[1,5,1,false],[1,9,0,false],[1,9,1,false]]);
 return s;
}
async function main(){
 const [jsfile,wasmfile,outfile]=process.argv.slice(2);
 if(!jsfile||!wasmfile||!outfile)
  throw Error('Usage: node tests/month_fair_real_wasm.cjs module.js module.wasm proof.json');
 const binary=fs.readFileSync(wasmfile);
 if(!WebAssembly.validate(binary))throw Error('Not genuine WASM');
 let factory=require(path.resolve(jsfile));
 if(factory&&typeof factory.default==='function')factory=factory.default;
 if(typeof factory!=='function')throw Error('Missing actual Emscripten factory');
 const started=Date.now();
 const module=await factory({wasmBinary:new Uint8Array(binary),
  print:()=>{},printErr:s=>process.stderr.write(String(s)+'\n')});
 const call=(payload)=>JSON.parse(module.ccall(
  'solve_guard_month_fair_v3','string',['string'],[payload]));
 const cases=[];
 const s=tiny();
 const targets=[1,1];
 const tinyResult=call(wire(s,targets));
 const tinyCheck=check(s,targets,tinyResult);
 // Independent exhaustive optimum: two duties, two eligible people,
 // both 2h shifts spaced >=6h, desired counts [1,1].
 if(tinyCheck.filled!==2||tinyCheck.absDeviation!==0||
    tinyResult.fair_phase!=='OPTIMAL')
  throw Error('Failed independent small exact count-fairness oracle');
 cases.push({name:'two-shift-exact-fairness-oracle',accepted:true,
  status:tinyResult.status,filled:2,optimal_fairness:0});
 for(const [pool,variant] of [['door','blackouts-no-hints'],
                               ['officer','blackouts-no-hints'],
                               ['door','forced-vacancies']]){
  const roster=createScenario(pool,variant);
  const goals=targetsFor(roster);
  const begin=Date.now();
  const got=call(wire(roster,goals));
  const audit=check(roster,goals,got);
  const referenceFill=roster.witness.filter(x=>x>=0).length;
  if(audit.filled!==referenceFill)
    throw Error('Two-stage fairness sacrificed legal coverage');
  cases.push({name:'dense-full-month-'+pool+'-'+variant,
   status:got.status,fill_phase:got.fill_phase,fair_phase:got.fair_phase,
   tasks:roster.shiftCount,staff:roster.staff,
   candidate_pairs:roster.eligiblePairs,filled:audit.filled,
   phase1_cost:got.phase1_abs_deviation,final_cost:audit.absDeviation,
   fair_optimal_proven:got.fair_optimal_proven_given_fill,
   elapsed_ms:Date.now()-begin,accepted:true});
 }
 const impossible=sparseFixture('officer',12,1,
   [[1,5,0,true],[2,5,0,true]]);
 const infeasible=call(wire(impossible,[0]));
 if(infeasible.status!=='INFEASIBLE'||infeasible.fair_phase!=='NOT_RUN'||
   infeasible.assignments!==undefined)
  throw Error('Infeasible hard constraints silently relaxed to improve fairness');
 cases.push({name:'pinned-adjacent-day-conflict',status:'INFEASIBLE',
             fair_phase:'NOT_RUN',accepted:true});
 const badCases=[
  wire(tiny(),[1]),wire(tiny(),[-1,3]),wire(tiny(),[999,1]),
  wire(tiny(),[1,1]).replace('guard-month-fair-v3','guard-month-v2'),
  wire(tiny(),[1,1]).replace(/\n1,1\n$/,'\n'),
 ];
 for(const invalid of badCases)
  if(call(invalid).status!=='INVALID_INPUT')throw Error('Invalid fairness data accepted');
 const proof={
  accepted:true,
  engine:'genuine-Google-OR-Tools-CP-SAT-WASM',
  contract:'guard-month-fair-v3',
  two_phases:true,first_stage:'maximize-legal-fill',
  second_stage:'lock-achieved-fill-and-minimize-absolute-person-count-deviations',
  exactly_optimal_for_real_duties:false,
  actual_iphone_safari_tested:false,
  operationally_certified:false,
  full_hard_rules_verified:false,
  full_589_dense_model_tested:true,
  exact_small_fairness_oracle_verified:true,
  rejected_bad_input_cases:badCases.length,
  cases,elapsed_ms:Date.now()-started,
  js_sha256:crypto.createHash('sha256').update(fs.readFileSync(jsfile)).digest('hex'),
  wasm_sha256:crypto.createHash('sha256').update(binary).digest('hex')
 };
 fs.writeFileSync(outfile,JSON.stringify(proof,null,2)+'\n');
 console.log(JSON.stringify(proof,null,2));
}
if(require.main===module)main().catch(e=>{
 console.error('GENUINE FAIRNESS WASM FAILED:',e);process.exitCode=1;});
module.exports={wire,score,targetsFor,tiny};
