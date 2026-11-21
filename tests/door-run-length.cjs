'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');

async function main() {
  const [exe,wasm] = process.argv.slice(2);
  const engine = wasm && await require(path.resolve(exe))({wasmBinary:fs.readFileSync(wasm)});
  function test(label, picks, edges, valid, pool='door') {
    const n=pool==='door'?12:7, count=31*n;
    const chosen=new Set(picks.map(([d,k])=>d*n+k));
    const pins=Array.from({length:count},(_,i)=>chosen.has(i)?0:-1);
    const relaxed=edges!==null;
    const frame=[relaxed?'guard-month-harsh-v5':'guard-month-harsh-v4','2026-12',pool,count+' 1',
      '1'.repeat(count),pins.join(','),pins.join(','),String(chosen.size)];
    if(relaxed)frame.push('edges='+edges);
    const wire=frame.concat('limits_ms=100,100,100,100','').join('\n');
    const result=JSON.parse(engine?engine.ccall('solve_guard_month_harsh_v4','string',['string'],[wire]):
      execFileSync(path.resolve(exe),{input:wire,encoding:'utf8'}));
    assert.equal(result.baseline_valid,valid,label);
    assert.ok(!result.failed_stage,label);
    if(valid){assert.equal(result.filled,chosen.size,label);assert.deepEqual(result.assignments,pins,label);}
    else assert.ok(!['OPTIMAL','FEASIBLE'].includes(result.status),label);
  }
  test('two adjacent dates',[[0,5],[1,6]],0,true);
  test('three consecutive dates',[[0,5],[1,6],[2,7]],0,false);
  test('same slot next day',[[0,5],[1,5]],0,false);
  test('same slot two days later',[[0,5],[2,5]],0,false);
  test('short overnight rest',[[0,0],[1,1]],0,false);
  test('exactly six hours',[[0,0],[1,4]],0,true);
  test('break resets run',[[0,5],[1,6],[3,7]],0,true);
  test('two shifts count as one day',[[0,1],[0,7],[1,5]],0,true);
  test('two days before month',[[0,5]],3,false);
  test('one day before month',[[0,5],[1,6]],2,false);
  test('one day after month',[[29,5],[30,6]],4,false);
  test('two days after month',[[30,6]],12,false);
  test('old contract',[[0,5],[1,6]],null,false);
  test('officer adjacent dates',[[0,1],[1,3]],null,false,'officer');
  console.log('14/14 day rule and baseline checks passed');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
