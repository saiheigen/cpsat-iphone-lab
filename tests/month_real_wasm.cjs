// Genuine OR-Tools CP-SAT WASM guard-month-v2 tests, synthetic only.
// 589 shifts (372 door and 217 officer) and 106 fictional staff in
// separate pools. Candidate matrices are deliberately SPARSE for a
// reproducible first geometry/protocol proof; not a dense performance test.
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const HOURS={
 door:[[22,24],[0,2],[2,4],[4,6],[6,8],[8,10],[10,12],[12,14],[14,16],[16,18],[18,20],[20,22]],
 officer:[[22,24],[0,2],[2,4],[4,6],[6,12],[12,18],[18,22]]
};
function daysInMonth(y,m){return new Date(Date.UTC(y,m,0)).getUTCDate();}
function serialize(t){
 return ['guard-month-v2',String(t.year)+'-'+String(t.month).padStart(2,'0'),
   t.pool,String(t.shiftCount)+' '+String(t.staff),
   t.allowed,t.pins.join(','),t.hints.join(',')].join('\n')+'\n';
}
function monthFixture(pool){
 const year=2026,month=12,slots=HOURS[pool].length,days=daysInMonth(year,month);
 const staff=pool==='door'?56:50,group=pool==='door'?28:25;
 let mask='',pins=[],hints=[],witness=[];
 for(let d=1;d<=days;d++){
  const cycle=Math.floor((d-1)/2),parity=(d-1)%2;
  for(let k=0;k<slots;k++){
   const who=parity*group+(k+cycle)%group;
   for(let p=0;p<staff;p++)mask+=p===who?'1':'0';
   pins.push(-2);hints.push(who);witness.push(who);
  }
 }
 return {year,month,pool,staff,shiftCount:slots*days,
         allowed:mask,pins,hints,witness};
}
function sparseFixture(pool,month,staff,items){
 const year=2026,slots=HOURS[pool].length;
 const n=slots*daysInMonth(year,month);
 const mask=Array(n*staff).fill('0');
 const pins=Array(n).fill(-2),hints=Array(n).fill(-1);
 for(const [day,slot,person,pin] of items){
  const i=(day-1)*slots+(slot-1);
  mask[i*staff+person]='1';
  if(pin)pins[i]=person;
 }
 return {year,month,pool,staff,shiftCount:n,
         allowed:mask.join(''),pins,hints};
}
function sunday(t,day){
 return new Date(Date.UTC(t.year,t.month-1,day)).getUTCDay()===0;
}
function independentlyAudit(t,got){
 const a=got.assignments;
 if(!Array.isArray(a)||a.length!==t.shiftCount)
  throw Error('Missing full calendar of assignment indices');
 const slots=HOURS[t.pool].length;
 const personJobs=Array.from({length:t.staff},()=>[]);
 for(let i=0;i<a.length;i++){
  const p=a[i];
  if(!Number.isInteger(p)||p<-1||p>=t.staff)throw Error('Bad staff index');
  if(p>=0){
   if(t.allowed[i*t.staff+p]!=='1')throw Error('Assigned an ineligible person');
   personJobs[p].push({day:Math.floor(i/slots)+1,slot:i%slots,
    start:HOURS[t.pool][i%slots][0],end:HOURS[t.pool][i%slots][1]});
  }
  if(t.pins[i]===-1&&p!==-1)throw Error('Fixed vacancy overwritten');
  if(t.pins[i]>=0&&p!==t.pins[i])throw Error('Pinned shift overwritten');
 }
 for(const duties of personJobs){
  const byDay=new Map();
  for(const duty of duties)byDay.set(duty.day,(byDay.get(duty.day)||0)+1);
  if([...byDay.values()].some(n=>n>(t.pool==='door'?3:1)))
    throw Error('Daily shift cap exceeded');
  for(let i=0;i<duties.length;i++)for(let j=i+1;j<duties.length;j++){
   const a=duties[i],b=duties[j],gap=Math.abs(a.day-b.day);
   if(gap===1)throw Error('Next-day rest violated');
   if(gap<=2&&a.slot===b.slot)throw Error('Same slot repeated too soon');
   function standby(x){
    return sunday(t,x.day) &&
      (t.pool==='door'?(x.start>=6&&x.start<20):x.slot===6);
   }
   if(gap===7&&standby(a)&&standby(b))
     throw Error('Consecutive Sunday standby');
   if(gap===0&&t.pool==='officer')throw Error('Officer twice in day');
   if(gap===0&&t.pool==='door'&&
       !(a.end+6<=b.start||b.end+6<=a.start))
     throw Error('Insufficient guard rest');
  }
 }
 const filled=a.filter(p=>p>=0).length;
 if(got.filled!==filled||got.missing!==t.shiftCount-filled)
   throw Error('Wrong shift counts');
 return filled;
}
async function main(){
 const [jsfile,wasmfile,outfile]=process.argv.slice(2);
 if(!jsfile||!wasmfile||!outfile)throw Error('Usage: node tests/month_real_wasm.cjs module.js module.wasm proof.json');
 const wasm=fs.readFileSync(wasmfile);
 if(!WebAssembly.validate(wasm))throw Error('Invalid WebAssembly bytes');
 let factory=require(path.resolve(jsfile));
 if(factory&&typeof factory.default==='function')factory=factory.default;
 if(typeof factory!=='function')throw Error('No Emscripten factory function');
 const module=await factory({wasmBinary:new Uint8Array(wasm),
  print:()=>{},printErr:s=>process.stderr.write(String(s)+'\n')});
 const call=t=>JSON.parse(module.ccall('solve_guard_month_v2','string',['string'],[t]));
 const cases=[];
 for(const pool of ['door','officer']){
  const t=monthFixture(pool),got=call(serialize(t));
  if(!['OPTIMAL','FEASIBLE'].includes(got.status))
    throw Error(pool+' sparse full-month test got '+got.status);
  const filled=independentlyAudit(t,got);
  if(filled!==t.shiftCount)throw Error(pool+' did not fill all eligible shifts');
  if(got.assignments.some((v,i)=>v!==t.witness[i]))
    throw Error('Solver did not return uniquely eligible witness');
  cases.push({name:'synthetic-full-month-unique-candidates-'+pool,
    shifts:t.shiftCount,staff:t.staff,status:got.status,filled,accepted:true});
 }
 const forced=sparseFixture('officer',11,1,
    [[1,5,0,true],[2,5,0,true]]);
 const result=call(serialize(forced));
 if(result.status!=='INFEASIBLE')
    throw Error('Adjacent-day fixed officer shifts not refused');
 cases.push({name:'adjacent-day-fixed-infeasible',status:result.status,accepted:true});
 const legal=sparseFixture('door',11,1,
    [[1,5,0,false],[1,9,0,false]]);
 const check=call(serialize(legal));
 if(!['OPTIMAL','FEASIBLE'].includes(check.status)||
    independentlyAudit(legal,check)!==2)
    throw Error('Two well-spaced Sunday shifts were wrongly forbidden');
 cases.push({name:'two-legal-same-Sunday-shifts',status:check.status,
    filled:2,accepted:true});
 const impossible=sparseFixture('door',11,1,
    [[1,5,0,true],[8,5,0,true]]);
 const blocked=call(serialize(impossible));
 if(blocked.status!=='INFEASIBLE')
   throw Error('Consecutive Sunday standby should be infeasible');
 cases.push({name:'consecutive-Sunday-standby-infeasible',status:blocked.status,
    accepted:true});
 for(const invalid of ['bad',
     'guard-month-v2\n2026-11\ndoor\n1 1\n1\n-2\n-1\n']){
   if(call(invalid).status!=='INVALID_INPUT')
     throw Error('Invalid month protocol was accepted');
 }
 const proof={accepted:true,engine:'genuine-ORTools-CP-SAT-WASM',
    contract:'guard-month-v2',
    synthetic_full_month_shifts_tested:589,
    synthetic_staff_tested:106,
    all_operational_rules_tested:false,
    dense_full_month_performance_verified:false,
    rich_absences_tested:false,
    real_iphone_safari_verified:false,
    cases,
    js_sha256:crypto.createHash('sha256').update(fs.readFileSync(jsfile)).digest('hex'),
    wasm_sha256:crypto.createHash('sha256').update(wasm).digest('hex')};
 fs.writeFileSync(outfile,JSON.stringify(proof,null,2)+'\n');
 console.log(JSON.stringify(proof,null,2));
}
// Export pure synthetic fixture/auditor helpers so CI can inspect the
// complete 589-shift reference BEFORE a costly Emscripten build.
module.exports={monthFixture,sparseFixture,serialize,independentlyAudit,daysInMonth};
if(require.main===module){
 main().catch(e=>{console.error('Genuine full-month WASM acceptance FAILED:',e);
  process.exitCode=1;});
}
