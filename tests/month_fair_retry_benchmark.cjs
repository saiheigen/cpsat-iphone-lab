// Deterministic paired workload. Seeds change eligibility, never the incumbent
// or the solver seed. Run against each binary and compare identical frame hashes.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {wire, check, hardshipScore} = require('./month_hardship_real_wasm.cjs');
const {independentlyAudit} = require('./month_real_wasm.cjs');

function fixture(seed) {
  const staff=30, shiftCount=360, pool='door';
  const hints=Array.from({length:shiftCount}, (_,s)=>
    (Math.floor(s/12)%2)*15+(s%12+Math.floor(s/24))%13);
  const available=Array(shiftCount*staff).fill('0'), free=[];
  for(let i=0;i<available.length;i++){
    if(i%staff===hints[Math.floor(i/staff)])available[i]='1';
    else free.push(i);
  }
  for(let i=free.length-1;i>0;i--){
    seed=(Math.imul(1664525,seed)+1013904223)>>>0;
    const j=Math.floor((seed/4294967296)*(i+1));
    [free[i],free[j]]=[free[j],free[i]];
  }
  const extras=Math.round(0.28*available.length)-shiftCount;
  for(const i of free.slice(0,extras))available[i]='1';
  const s={year:2026,month:11,pool,shiftCount,staff,pins:Array(shiftCount).fill(-2),
    hints, allowed:available.join('')};
  independentlyAudit(s,{assignments:hints,filled:shiftCount,missing:0});
  return s;
}

function workload(assignments, staff) {
  let triples=0, extra=0;
  for(let d=0;d<assignments.length;d+=12){
    const counts=Array(staff).fill(0);
    for(const p of assignments.slice(d,d+12))if(p>=0)counts[p]++;
    for(const n of counts){triples+=Number(n===3);extra+=Math.max(0,n-1);}
  }
  return {triples,extra};
}

function checkExtraRegression(engine){
  // Only the first shift can move. Reassigning it balances counts but
  // creates a second double-duty day. All unused positions are pinned empty.
  const s={year:2026,month:11,pool:'door',staff:2,shiftCount:360,
    pins:Array(360).fill(-1),hints:Array(360).fill(-1),allowed:'1'.repeat(720)};
  for(const [slot,p] of [[5,0],[9,1],[53,0],[57,0]]){
    s.hints[slot]=p;s.pins[slot]=p;
  }
  s.pins[5]=-2;
  const result=JSON.parse(engine.ccall('solve_guard_month_harsh_v4','string',['string'],[wire(s,[2,2])]));
  check(s,[2,2],result);
  assert.ok(result.baseline_valid && !result.failed_stage);
  assert.deepEqual(result.assignments,s.hints);
  assert.equal(result.final_abs_deviation,2);
  // Moving a daytime shift would improve L1 while worsening the normalized
  // hardship score. Distinct dates ensure the daily guard cannot reject it.
  s.pins.fill(-1);s.hints.fill(-1);
  for(const [slot,p] of [[1,0],[53,0],[101,0],[149,1]]){
    s.hints[slot]=p;s.pins[slot]=p;
  }
  s.pins[53]=-2;
  const worse=s.hints.slice();worse[53]=1;
  assert.ok(hardshipScore(s,worse)>hardshipScore(s,s.hints));
  const guarded=JSON.parse(engine.ccall('solve_guard_month_harsh_v4','string',['string'],[wire(s,[2,2])]));
  check(s,[2,2],guarded);
  assert.ok(guarded.baseline_valid && !guarded.failed_stage);
  assert.deepEqual(guarded.assignments,s.hints);

}

async function benchmark(js, wasm, out) {
  const factory=require(path.resolve(js)), binary=fs.readFileSync(wasm);
  checkExtraRegression(await factory({wasmBinary:binary,print:()=>{},printErr:()=>{}}));
  const records=[];
  for(let seed=20261120;seed<=20261126;seed++){
    const s=fixture(seed), goals=Array(s.staff).fill(12), frame=wire(s,goals);
    const engine=await factory({wasmBinary:binary, print:()=>{}, printErr:()=>{}});
    const start=Date.now();
    const r=JSON.parse(engine.ccall('solve_guard_month_harsh_v4','string',['string'],[frame]));
    const ms=Date.now()-start;
    const audit=check(s,goals,r);
    assert.equal(audit.filled,s.shiftCount);
    assert.ok(!r.failed_stage, 'Exception fallback reached in benchmark');
    const before={...workload(s.hints,s.staff),hardship:hardshipScore(s,s.hints),filled:360,L1:96};
    const after=workload(r.assignments,s.staff);
    assert.ok(after.triples<=before.triples && after.extra<=before.extra);
    assert.ok(audit.hardship<=before.hardship);
    const row={before,...after,seed,input_sha256:crypto.createHash('sha256').update(frame).digest('hex'),
      filled:audit.filled, L1:audit.countDeviation, hardship:audit.hardship,
      warm_status:r.fair_warm_status, warm_L1:r.fair_warm_cost,
      retry_status:r.fair_retry_status, search_L1:r.fair_search_cost, transfers:r.fair_transfers, ms};
    records.push(row);
    console.log(JSON.stringify(row));
  }
  fs.writeFileSync(out,JSON.stringify(records,null,2)+'\n');
}
// Frozen single-run old-WASM measurements from run 44223914115, on these
// exact synthetic inputs. This is a conservative merge check on this panel.
const reference = [
  {
    "seed": 20261120,
    "input_sha256": "40654c8dfad2a820f2b872065324b7ec49da376976f5d041b9a11acc449faec5",
    "filled": 360,
    "L1": 8
  },
  {
    "seed": 20261121,
    "input_sha256": "35500272d227ab8f8b247c66675df05d688faef257259bc7d33898b58aef025a",
    "filled": 360,
    "L1": 12
  },
  {
    "seed": 20261122,
    "input_sha256": "c463721dc914dd5c6586e203c7d694d80f2e2bb181592b9de70f1a499c2ad861",
    "filled": 360,
    "L1": 8
  },
  {
    "seed": 20261123,
    "input_sha256": "e1f24391d753eb05ab3e4a31748788f6c593f3024f0914ae8ee0ec0826b2ac69",
    "filled": 360,
    "L1": 16
  },
  {
    "seed": 20261124,
    "input_sha256": "4ca349b80e3d12332709cefdf37d7a894bf564f729947ebdc9317be95d219f8e",
    "filled": 360,
    "L1": 20
  },
  {
    "seed": 20261125,
    "input_sha256": "09c3603b814a4145509c12ae5f474d886284e35e7c597264b4fd1c71a15b0dd5",
    "filled": 360,
    "L1": 96
  },
  {
    "seed": 20261126,
    "input_sha256": "67995c077cbe7a8896888a64bf5595c2556dd499e79d9dc11364dc445b0e8ed7",
    "filled": 360,
    "L1": 20
  }
];
function checkPanel(filename) {
  const measured=JSON.parse(fs.readFileSync(filename));
  assert.equal(measured.length,reference.length);
  for(const [i,r] of measured.entries()){
    const prior=reference[i];
    assert.equal(r.seed,prior.seed); assert.equal(r.input_sha256,prior.input_sha256);
    assert.equal(r.filled,prior.filled);
    assert.ok(r.L1<=prior.L1, 'Higher L1 on seed '+r.seed+': '+r.L1+' > '+prior.L1);
  }
}
if(require.main===module){
  if(process.argv[2]==='--check')checkPanel(process.argv[3]);
  else benchmark(...process.argv.slice(2)).catch(e=>{console.error(e);process.exitCode=1;});
}
module.exports={fixture};
