'use strict';
// Genuine local OR-Tools CP-SAT WASM invocation. Synthetic-only inputs.
// No network, no device storage, no names in stdout or on disk.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {parseFictionalV4Wire} = require('./v4_frame_contract.cjs');

function sha(bytes) {return crypto.createHash('sha256').update(bytes).digest('hex');}
function insist(ok, message) {if (!ok) throw Error(message);}
async function stdinText() {
  let s='';
  for await (const chunk of process.stdin) {
    s+=chunk;
    insist(s.length<=150000,'Oversize fictional request');
  }
  return s;
}
async function main() {
  const [jsPath,wasmPath,proofPath]=process.argv.slice(2);
  insist(jsPath&&wasmPath&&proofPath,'Three local WASM/proof paths are required');
  const request=JSON.parse(await stdinText());
  insist(request&&request.synthetic_only===true&&
    request.contract==='guard-month-harsh-v4'&&
    request.frames&&Object.keys(request.frames).sort().join(',')==='door,officer',
    'Only both pools of the invented v4 contract are supported');
  insist(typeof request.trusted_wasm_sha256==='string' &&
    /^[a-f0-9]{64}$/.test(request.trusted_wasm_sha256),'Expected independent hash');
  const wires={};
  for(const pool of ['door','officer']){
    const frame=request.frames[pool];
    insist(frame&&typeof frame.wire==='string'&&
      typeof frame.sha256==='string'&&sha(frame.wire)===frame.sha256,
      'Anonymous wire checksum mismatch');
    const parsed=parseFictionalV4Wire(frame.wire,{synthetic_only:true});
    insist(parsed.pool===pool,'Wrong duty pool');
    wires[pool]=frame.wire;
  }
  const jsBytes=fs.readFileSync(jsPath), wasm=fs.readFileSync(wasmPath);
  const proof=JSON.parse(fs.readFileSync(proofPath,'utf8'));
  insist(proof && proof.accepted===true && proof.contract==='guard-month-harsh-v4' &&
    proof.js_sha256===sha(jsBytes) && proof.wasm_sha256===sha(wasm) &&
    proof.wasm_sha256===request.trusted_wasm_sha256,
    'Build proof / independent trust digest disagree');
  insist(WebAssembly.validate(wasm),'Not a valid WebAssembly binary');
  const maker=require(path.resolve(jsPath));
  insist(typeof maker==='function','Genuine WASM module factory missing');
  const engine=await maker({wasmBinary:new Uint8Array(wasm),print:()=>{},printErr:()=>{}});
  insist(engine && typeof engine.ccall==='function','Genuine WASM engine missing');
  const results={};
  for(const pool of ['door','officer']){
    const response=JSON.parse(engine.ccall('solve_guard_month_harsh_v4',
      'string',['string'],[wires[pool]]));
    insist(response && typeof response.status==='string','Invalid WASM response');
    if(response.status==='FEASIBLE'||response.status==='OPTIMAL'){
      results[pool]={status:response.status,assignments:response.assignments,
        filled:response.filled,missing:response.missing};
    }else{
      results[pool]={status:response.status};
    }
  }
  process.stdout.write(JSON.stringify({verified_runtime:true,
    wasm_sha256:sha(wasm),results}));
}
main().catch(error=>{console.error('Synthetic local WASM runner blocked:',error.message);
  process.exitCode=1;});
