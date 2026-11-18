// Quick synthetic protocol checks BEFORE expensive OR-Tools C++ compile.
// This is NOT a genuine WASM or fairness-solver execution proof.
'use strict';
const assert=require('node:assert/strict');
const {tiny,wire,targetsFor,score}=require('./month_fair_real_wasm.cjs');
const {createScenario}=require('./wasm_dense_month_benchmark.cjs');

const small=tiny();
const tinyFrame=wire(small,[1,1]);
const lines=tinyFrame.trimEnd().split('\n');
assert.equal(lines.length,8);
assert.equal(lines[0],'guard-month-fair-v3');
assert.equal(lines[3],'372 2');
assert.equal(lines[7],'1,1');
assert.equal(small.allowed.length,372*2);
const tinyAssignment=Array(372).fill(-1);
tinyAssignment[4]=0;
tinyAssignment[8]=1;
assert.equal(score(tinyAssignment,[1,1]).deviation,0);

const cases=[];
for(const [pool,variant] of [['door','blackouts-no-hints'],
                             ['officer','blackouts-no-hints'],
                             ['door','forced-vacancies']]){
 const s=createScenario(pool,variant);
 const goal=targetsFor(s);
 assert.equal(goal.length,s.staff);
 assert(goal.every(x=>Number.isInteger(x)&&x>=0&&x<=s.shiftCount));
 const payload=wire(s,goal);
 const rows=payload.trimEnd().split('\n');
 assert.equal(rows.length,8);
 assert.equal(rows[3],s.shiftCount+' '+s.staff);
 assert.equal(rows[4].length,s.shiftCount*s.staff);
 assert.equal(rows[5].split(',').length,s.shiftCount);
 assert.equal(rows[6].split(',').length,s.shiftCount);
 assert.equal(rows[7].split(',').length,s.staff);
 cases.push({pool,variant,shifts:s.shiftCount,staff:s.staff,
    candidates:s.eligiblePairs,target_sum:goal.reduce((a,b)=>a+b,0)});
}
console.log(JSON.stringify({
 accepted:true,mode:'protocol-preflight-NOT-real-WASM',
 exact_small_oracle_deviation:0,cases
},null,2));
