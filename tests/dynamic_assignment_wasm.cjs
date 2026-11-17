// True Emscripten + CP-SAT WASM assignment contract tests, synthetic only.
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');

function serialize(t){
 const {tasks,staff,allowed,conflicts,pins}=t;
 if(allowed.length!==tasks*staff||pins.length!==tasks)throw Error('Invalid fixture');
 return ['assignment-v1',tasks+' '+staff,
  allowed.map(x=>x?'1':'0').join(''),
  conflicts.map(x=>x[0]+':'+x[1]).join(';'),
  pins.join(',')].join('\n')+'\n';
}
function exactMax(t){
 const {tasks,staff,allowed,conflicts,pins}=t;
 let best=-1;
 const a=Array(tasks).fill(-1);
 function rec(i){
  if(i===tasks){
   if(conflicts.some(e=>a[e[0]]>=0&&a[e[0]]===a[e[1]]))return;
   best=Math.max(best,a.filter(v=>v>=0).length);
   return;
  }
  for(let p=-1;p<staff;p++){
   if(p>=0&&!allowed[i*staff+p])continue;
   if(pins[i]===-1&&p!==-1)continue;
   if(pins[i]>=0&&pins[i]!==p)continue;
   a[i]=p;rec(i+1);
  }
 }
 rec(0);return best;
}
function audit(t,got){
 if(!Array.isArray(got.assignments)||got.assignments.length!==t.tasks)
  throw Error('Assignment array missing/wrong size');
 const a=got.assignments;
 for(let i=0;i<t.tasks;i++){
  const p=a[i];
  if(!Number.isInteger(p)||p<-1||p>=t.staff)throw Error('Invalid person index');
  if(p>=0&&!t.allowed[i*t.staff+p])throw Error('Ineligible person assigned');
  if(t.pins[i]===-1&&p!==-1)throw Error('Forced blank overwritten');
  if(t.pins[i]>=0&&p!==t.pins[i])throw Error('Fixed person overwritten');
 }
 for(const [i,j] of t.conflicts)
  if(a[i]>=0&&a[i]===a[j])throw Error('Conflicting shifts assigned to one person');
 const filled=a.filter(p=>p>=0).length;
 if(got.filled!==filled||got.missing!==t.tasks-filled)
  throw Error('Wrong counters');
 return filled;
}
async function main(){
 const [jsfile,wasmfile,outfile]=process.argv.slice(2);
 if(!jsfile||!wasmfile||!outfile)throw Error('Usage: node tests/dynamic_assignment_wasm.cjs module.js module.wasm proof.json');
 const js=path.resolve(jsfile), wasm=fs.readFileSync(wasmfile);
 if(!WebAssembly.validate(wasm))throw Error('Invalid WebAssembly');
 let factory=require(js);
 if(factory&&typeof factory.default==='function')factory=factory.default;
 if(typeof factory!=='function')throw Error('No actual Emscripten factory');
 const start=Date.now();
 const mod=await factory({wasmBinary:new Uint8Array(wasm),
                          print:()=>{},printErr:s=>process.stderr.write(String(s)+'\n')});
 const call=(s)=>JSON.parse(mod.ccall('solve_assignment_v1','string',['string'],[s]));
 const tests=[
  {name:'four-shifts-two-people',tasks:4,staff:2,
   allowed:Array(8).fill(1),conflicts:[[0,1],[2,3]],pins:[-2,-2,-2,-2]},
  {name:'one-person-all-conflicts',tasks:3,staff:1,
   allowed:[1,1,1],conflicts:[[0,1],[0,2],[1,2]],pins:[0,-2,-1]},
  {name:'eligibility-and-forced-blank',tasks:3,staff:2,
   allowed:[1,0,0,1,1,1],conflicts:[[0,2]],pins:[0,-2,-1]},
  {name:'conflicting-fixed-shifts',tasks:2,staff:1,
   allowed:[1,1],conflicts:[[0,1]],pins:[0,0]},
 ];
 const results=[];
 for(const t of tests){
  const got=call(serialize(t)), optimum=exactMax(t);
  const expected=optimum<0?'INFEASIBLE':'OPTIMAL';
  if(got.status!==expected)throw Error(t.name+': '+got.status+' expected '+expected);
  if(optimum>=0&&audit(t,got)!==optimum)throw Error('Optimum mismatch: '+t.name);
  results.push({name:t.name,status:got.status,
                oracle_max_fill:optimum,got_filled:got.filled??null,accepted:true});
 }
 const bad=['bad','assignment-v1\n0 0\n\n\n\n',
   'assignment-v1\n2 2\n0X01\n0:1\n-2,-2\n',
   'assignment-v1\n1 1\n1\n\n99\n'];
 for(const input of bad)
  if(call(input).status!=='INVALID_INPUT')throw Error('Invalid data accepted');
 const report={
  accepted:true,engine:'genuine-ORTools-CP-SAT-in-WASM',
  contract:'bounded-dynamic-assignment-v1',tests:results,
  invalid_input_cases:bad.length,elapsed_ms:Date.now()-start,
  js_sha256:crypto.createHash('sha256').update(fs.readFileSync(js)).digest('hex'),
  wasm_sha256:crypto.createHash('sha256').update(wasm).digest('hex'),
  operationally_certified:false,iphone_safari_verified:false,
  full_589_shift_model:false
 };
 fs.writeFileSync(outfile,JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report,null,2));
}
main().catch(e=>{console.error('Dynamic WASM CP-SAT FAILED:',e);process.exitCode=1});
