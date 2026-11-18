'use strict';
// Two invented month masks compiled from native hard-rule events in CI.
// Real OR-Tools C++/WASM is mandatory; never mock or claim operational parity.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {check}=require('./month_hardship_real_wasm.cjs');
const SOURCE='phase19-hardcoded-fictional-rules-only';
const CONTRACT='guard-month-harsh-v4';

function assert(x,msg){if(!x)throw Error(msg);}
async function main(){
 const [moduleJs,moduleWasm,inputJson,outputJson]=process.argv.slice(2);
 assert(moduleJs&&moduleWasm&&inputJson&&outputJson,'Usage: module.js module.wasm invented_input.json invented_output.json');
 const input=JSON.parse(fs.readFileSync(inputJson,'utf8'));
 assert(input.contract===CONTRACT&&input.source===SOURCE&&
  input.synthetic_only===true&&input.operationally_certified===false&&
  input.full_v7_rule_parity_verified===false&&input.month==='2026-12',
  'Not an attested imaginary v4 month');
 assert(Array.isArray(input.cases)&&input.cases.length===2,
  'Must test both complete invented pools');
 const binary=fs.readFileSync(moduleWasm);
 assert(WebAssembly.validate(binary),'Genuine binary WASM missing');
 let factory=require(path.resolve(moduleJs));
 if(factory&&typeof factory.default==='function')factory=factory.default;
 assert(typeof factory==='function','Real OR-Tools module factory absent');
 const engine=await factory({wasmBinary:new Uint8Array(binary),
  print:()=>{},printErr:()=>{}});
 assert(typeof engine.ccall==='function','Real Emscripten solver missing');
 const results=[];
 for(const item of input.cases){
  assert(item.synthetic_only===true,'Nonfictional case rejected');
  const frame=item.frame;
  assert(typeof frame==='string'&&Buffer.byteLength(frame,'ascii')<200000,
   'Invalid full-month input');
  assert(crypto.createHash('sha256').update(frame,'ascii').digest('hex')===
    item.frame_sha256,'WASM input was modified');
  const rows=frame.trimEnd().split('\n');
  assert(rows.length===8&&rows[0]===CONTRACT&&rows[1]==='2026-12'&&
   rows[2]===item.pool,'Source wire does not match invented month');
  const dims=rows[3].split(' ').map(Number);
  const n= dims[0],staff=dims[1],slots=item.pool==='door'?12:7;
  assert(['door','officer'].includes(item.pool),'Unknown pool');
  assert(n===31*slots&&item.shifts===n&&item.staff===staff,
   'Incomplete duty calendar or staff count');
  assert(rows[4].length===n*staff&&/^[01]+$/.test(rows[4]),
   'Missing/invalid eligibility mask');
  const pins=rows[5].split(',').map(Number),hints=rows[6].split(',').map(Number),
    targets=rows[7].split(',').map(Number);
  assert(pins.length===n&&hints.length===n&&targets.length===staff,
   'Truncated pins/hints/targets');
  const t={pool:item.pool,year:2026,month:12,shiftCount:n,staff,
   allowed:rows[4],pins,hints};
  const begin=Date.now();
  const got=JSON.parse(engine.ccall('solve_guard_month_harsh_v4',
    'string',['string'],[frame]));
  if(!['OPTIMAL','FEASIBLE'].includes(got.status)){
   throw Error('No legal v4 C++/WASM result; fictional pool='+item.pool+
    ', status='+String(got.status)+', elapsed_ms='+(Date.now()-begin));
  }
  const result=check(t,targets,got);
  assert(result.filled===got.filled,'Independent JS audit disagrees with solver');
  results.push({pool:item.pool,frame_sha256:item.frame_sha256,
   shifts:n,staff,elapsed_ms:Date.now()-begin,result:got});
  process.stdout.write(JSON.stringify({pool:item.pool,shifts:n,
   filled:result.filled,missing:n-result.filled,
   independently_audited:true,real_cpp_wasm_executed:true,
   full_v7_rule_parity_verified:false,operationally_certified:false})+'\n');
 }
 const report={contract:CONTRACT,source:SOURCE,synthetic_only:true,
  genuine_cpp_wasm_executed:true,operationally_certified:false,
  full_v7_rule_parity_verified:false,cases:results};
 fs.writeFileSync(outputJson,JSON.stringify(report,null,2)+'\n');
 console.log('PHASE19_GENUINE_FICTIONAL_HARD_RULE_WASM_EXECUTION_PASS');
}
main().catch(error=>{console.error(String(error));process.exitCode=1;});
