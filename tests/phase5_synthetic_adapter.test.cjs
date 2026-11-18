'use strict';
const assert=require('node:assert/strict');
const {normalize,project}=require('../integration/phase5_synthetic_adapter.cjs');
const s={synthetic_only:true,contract:'guard-month-harsh-v4',year:2026,month:12,
 pool:'door',shifts:372,staff:2,mask:'1'.repeat(744),
 pins:Array(372).fill(-2),hints:Array(372).fill(-1),targets:[2,2]};
assert.equal(normalize(s).split('\n').length,9);
const a=Array(372).fill(-1);a[0]=0;a[1]=1;
const r={status:'FEASIBLE',assignments:a,filled:2,missing:370};
assert.equal(project(s,r).shifts.filter(x=>x.unfilled).length,370);
assert.equal(project(s,r).shifts[0].slot,1);
assert.throws(()=>normalize({...s,synthetic_only:false}),/Synthetic-only/);
assert.throws(()=>normalize({...s,mask:'1'}),/mask/);
assert.throws(()=>normalize({...s,shifts:371}),/calendar/);
assert.throws(()=>project(s,{...r,missing:0}),/fill counts/);
assert.throws(()=>project(s,{...r,assignments:a.slice(1)}),/Truncated/);
const pinned={...s,pins:[0,...s.pins.slice(1)]};
assert.throws(()=>project(pinned,{...r,assignments:[1,...a.slice(1)]}),/Pinned/);
const forbidden={...s,mask:'0'+s.mask.slice(1)};
assert.throws(()=>project(forbidden,r),/Ineligible/);
const fixedVacant={...s,pins:[-1,...s.pins.slice(1)]};
assert.throws(()=>project(fixedVacant,r),/Fixed vacancy/);
console.log('Phase 5 synthetic adapter boundary regression PASS');
