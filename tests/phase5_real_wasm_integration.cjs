'use strict';
// Genuine OR-Tools C++/WASM integration, never a mock or operational roster.
const fs=require('node:fs'),path=require('node:path');
const {normalize,project}=require('../integration/phase5_synthetic_adapter.cjs');
const {toy,check,wire}=require('./month_hardship_real_wasm.cjs');
const {createScenario}=require('./wasm_dense_month_benchmark.cjs');
const {targetsFor}=require('./month_fair_real_wasm.cjs');
async function main(){
 const [jsfile,wasmfile]=process.argv.slice(2);
 if(!jsfile||!wasmfile)throw Error('Usage: node tests/phase5_real_wasm_integration.cjs module.js module.wasm');
 const bytes=fs.readFileSync(wasmfile);
 if(!WebAssembly.validate(bytes))throw Error('Not a valid WebAssembly binary');
 let factory=require(path.resolve(jsfile));
 if(factory&&typeof factory.default==='function')factory=factory.default;
 if(typeof factory!=='function')throw Error('Genuine module factory absent');
 const engine=await factory({wasmBinary:new Uint8Array(bytes),print:()=>{},printErr:()=>{}});
 const cases=[toy(),createScenario('door','blackouts-no-hints'),
  createScenario('officer','blackouts-no-hints'),
  createScenario('door','forced-vacancies')];
 for(const source of cases){
  const targets=source.staff===2?[2,2]:targetsFor(source);
  const t={synthetic_only:true,contract:'guard-month-harsh-v4',
   year:source.year,month:source.month,pool:source.pool,
   shifts:source.shiftCount,staff:source.staff,
   mask:source.allowed,pins:source.pins,hints:source.hints,targets};
  const frame=normalize(t);
  if(frame!==wire(source,targets))throw Error('Adapter wire differs from genuine oracle');
  const got=JSON.parse(engine.ccall('solve_guard_month_harsh_v4','string',['string'],[frame]));
  const verified=check(source,targets,got);
  const projected=project(t,got);
  if(projected.filled!==verified.filled||projected.missing!==source.shiftCount-verified.filled)
   throw Error('Adapter lost filled or unfilled duties');
  console.log(JSON.stringify({pool:t.pool,shifts:t.shifts,filled:projected.filled,
   missing:projected.missing,hardship:verified.hardship,status:got.status}));
 }
 console.log('PHASE5_GENUINE_WASM_INTEGRATION_PASS');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
