'use strict';
const assert=require('node:assert/strict');
const {previewCombined}=require('../integration/phase5_v7_preview_adapter.cjs');
function pool(name){
 const shifts=name==='door'?372:217;
 const mask='1'+'0'.repeat(shifts-1);
 const assignments=[0,...Array(shifts-1).fill(-1)];
 return {input:{synthetic_only:true,contract:'guard-month-harsh-v4',
  year:2026,month:12,pool:name,shifts,staff:1,mask,
  pins:Array(shifts).fill(-2),hints:Array(shifts).fill(-1),targets:[1]},
  result:{status:'FEASIBLE',assignments,filled:1,missing:shifts-1}};
}
const door=pool('door'),officer=pool('officer');
const out=previewCombined({door,officer});
assert.equal(out.format,'guard-cpsat-synthetic-preview-v1');
assert.equal(out.month,'2026-12');
assert.equal(out.schedule.door.length,372);
assert.equal(out.schedule.officer.length,217);
assert.equal(out.filled,2);
assert.equal(out.missing,587);
assert.equal(out.vacancies.length,587);
assert.deepEqual(out.schedule.door[0],
 [Date.UTC(2026,11,1)/86400000,1,'SIM_D_000']);
assert.deepEqual(out.schedule.officer[0],
 [Date.UTC(2026,11,1)/86400000,1,'SIM_O_000']);
assert.deepEqual(out.schedule.door[1],
 [Date.UTC(2026,11,1)/86400000,2,null]);
assert.equal(out.importable_as_v7_backup,false);
assert.equal(out.operationally_certified,false);
assert.equal(out.source_solver_provenance_verified_by_this_function,false);
assert.equal(JSON.stringify(out).includes('guard-offline-v5'),false);
assert.throws(()=>previewCombined({door}),/Both/);
assert.throws(()=>previewCombined({door,officer:{...officer,input:{...officer.input,month:11,shifts:210}}}),/Cross-month/);
assert.throws(()=>previewCombined({door,officer:{...officer,input:{...officer.input,pool:'door'}}}),/pool boundary/);
assert.throws(()=>previewCombined({door:{...door,input:{...door.input,synthetic_only:false}},officer}),/Synthetic-only/);
assert.throws(()=>previewCombined({door:{...door,result:{...door.result,missing:0}},officer}),/fill counts/);
assert.throws(()=>previewCombined({door:{...door,result:{...door.result,assignments:door.result.assignments.slice(1)}},officer}),/Truncated/);
const badDay=pool('door');badDay.result.assignments[12]=0;
badDay.result.filled=2;badDay.result.missing=370;
badDay.input.mask=badDay.input.mask.slice(0,12)+'1'+badDay.input.mask.slice(13);
assert.throws(()=>previewCombined({door:badDay,officer}),/Next-day rest/);
console.log('Phase 5 combined v7-shape synthetic preview safety PASS');
