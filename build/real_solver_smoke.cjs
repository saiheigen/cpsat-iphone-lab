// The build must truly load the CP-SAT WASM binary, not a mock.
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
async function main(){
 const [jsfile,wasmfile,reportfile]=process.argv.slice(2);
 if(!jsfile||!wasmfile||!reportfile) throw Error('usage: node real_solver_smoke.cjs real.js real.wasm report.json');
 const js=path.resolve(jsfile),wasmPath=path.resolve(wasmfile);
 const wasm=fs.readFileSync(wasmPath);
 if(!WebAssembly.validate(wasm)) throw Error('Invalid WebAssembly binary');
 let factory=require(js);
 if(factory&&typeof factory.default==='function')factory=factory.default;
 if(typeof factory!=='function')throw Error('Emscripten factory missing');
 const started=Date.now();
 const module=await factory({wasmBinary:new Uint8Array(wasm),print:()=>{},printErr:s=>process.stderr.write(String(s)+'\n')});
 if(typeof module.ccall!=='function')throw Error('ccall runtime missing');
 const got=JSON.parse(module.ccall('run_cp_sat_probe','string',[],[]));
 let best=-Infinity, winners=[];
 for(let d=0;d<=4;d++)for(let t=0;t<=3;t++){
   if(3*d+4*t>12)continue;
   const p=20*d+30*t;
   if(p>best){best=p;winners=[{d,t}]}else if(p===best)winners.push({d,t});
 }
 const accepted=got.engine==='Google OR-Tools CP-SAT'&&got.status==='OPTIMAL'&&
   got.desks===0&&got.tables===3&&got.profit===90&&best===90&&
   winners.length===1&&winners[0].d===0&&winners[0].t===3;
 const report={accepted,solver:got,oracle:{profit:best,winners},elapsed_ms:Date.now()-started,
   wasm_sha256:crypto.createHash('sha256').update(wasm).digest('hex'),
   js_sha256:crypto.createHash('sha256').update(fs.readFileSync(js)).digest('hex')};
 fs.writeFileSync(reportfile,JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report,null,2));
 if(!accepted)process.exitCode=1;
}
main().catch(e=>{console.error('REAL CP-SAT TEST FAILED:',e);process.exitCode=1});
