// Fast preflight ONLY: synthetic JS fixtures and independent rule audit.
// Does not execute WebAssembly and must not be reported as proof of WASM.
'use strict';
const assert=require('node:assert/strict');
const {monthFixture,sparseFixture,serialize,independentlyAudit,daysInMonth}=
  require('./month_real_wasm.cjs');

let count=0;
for(const pool of ['door','officer']){
 const t=monthFixture(pool);
 const expected=pool==='door'?372:217;
 const staff=pool==='door'?56:50;
 assert.equal(t.shiftCount,expected);
 assert.equal(t.staff,staff);
 assert.equal(t.allowed.length,expected*staff);
 assert.equal(t.witness.length,expected);
 assert.equal(t.hints.length,expected);
 assert.equal(t.pins.length,expected);
 assert(serialize(t).startsWith('guard-month-v2\n2026-12\n'));
 const got={assignments:t.witness,filled:expected,missing:0};
 assert.equal(independentlyAudit(t,got),expected);
 count+=expected;
}
assert.equal(count,589);
const good=sparseFixture('door',11,1,[[1,5,0,false],[1,9,0,false]]);
const legal=[-1].concat(Array(good.shiftCount-1).fill(-1));
legal[4]=0;legal[8]=0;
assert.equal(independentlyAudit(good,{assignments:legal,filled:2,
                                     missing:good.shiftCount-2}),2);
const bad=sparseFixture('officer',11,1,[[1,5,0,false],[2,5,0,false]]);
const consecutive=Array(bad.shiftCount).fill(-1);
consecutive[4]=0;consecutive[11]=0;
assert.throws(()=>independentlyAudit(bad,{assignments:consecutive,filled:2,
  missing:bad.shiftCount-2}),/Next-day rest/);
const bothSundays=sparseFixture('door',11,1,[[1,5,0,false],[8,5,0,false]]);
const repeated=Array(bothSundays.shiftCount).fill(-1);
repeated[4]=0;repeated[7*12+4]=0;
assert.throws(()=>independentlyAudit(bothSundays,{assignments:repeated,filled:2,
  missing:bothSundays.shiftCount-2}),/Consecutive Sunday standby/);
const eligibility=sparseFixture('door',11,1,[]);
const illegal=Array(eligibility.shiftCount).fill(-1);
illegal[0]=0;
assert.throws(()=>independentlyAudit(eligibility,{assignments:illegal,filled:1,
  missing:eligibility.shiftCount-1}),/ineligible/);
assert.equal(daysInMonth(2028,2),29);
console.log(JSON.stringify({
 accepted:true,tests:'synthetic-fixture-static-preflight-not-real-WASM',
 complete_shift_count:589,staff:106,
 checks:['fully filled independently audited witness',
         'two same-Sunday shifts allowed',
         'adjacent-day conflict rejected',
         'consecutive Sunday standby rejected',
         'ineligible person rejected',
         'leap-day calendar'],
 real_wasm_executed:false,real_iphone_safari:false
},null,2));
