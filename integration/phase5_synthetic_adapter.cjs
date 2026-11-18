'use strict';
// Synthetic-only boundary. Never send operational personnel or eligibility records here.
function assert(cond,msg){if(!cond)throw Error(msg);}
function normalize(input){
 assert(input&&input.synthetic_only===true,'Synthetic-only input required');
 assert(input.contract==='guard-month-harsh-v4','Unsupported solver contract');
 assert(input.pool==='door'||input.pool==='officer','Invalid pool');
 const slots=input.pool==='door'?12:7;
 const days=new Date(Date.UTC(input.year,input.month,0)).getUTCDate();
 assert(Number.isInteger(input.year)&&input.year>=2020&&input.year<=2100&&
 Number.isInteger(input.month)&&input.month>=1&&input.month<=12,'Invalid month');
 assert(input.shifts===days*slots,'Incomplete calendar');
 assert(Number.isInteger(input.staff)&&input.staff>0&&input.staff<=100,'Invalid staff count');
 assert(typeof input.mask==='string'&&input.mask.length===input.shifts*input.staff&&
 /^[01]+$/.test(input.mask),'Invalid eligibility mask');
 assert(Array.isArray(input.pins)&&input.pins.length===input.shifts,'Invalid pins');
 assert(Array.isArray(input.hints)&&input.hints.length===input.shifts,'Invalid hints');
 assert(Array.isArray(input.targets)&&input.targets.length===input.staff,'Invalid targets');
 assert(input.pins.every(v=>Number.isInteger(v)&&v>=-2&&v<input.staff),'Invalid pin value');
 assert(input.hints.every(v=>Number.isInteger(v)&&v>=-1&&v<input.staff),'Invalid hint value');
 assert(input.targets.every(v=>Number.isInteger(v)&&v>=0&&v<=input.shifts),'Invalid target');
 return [input.contract,input.year+'-'+String(input.month).padStart(2,'0'),input.pool,
 input.shifts+' '+input.staff,input.mask,input.pins.join(','),input.hints.join(','),
 input.targets.join(',')].join('\n')+'\n';
}
function project(input,result){
 normalize(input);
 assert(result&&['FEASIBLE','OPTIMAL'].includes(result.status),'No accepted solution');
 assert(Array.isArray(result.assignments)&&result.assignments.length===input.shifts,
 'Truncated assignment');
 const slots=input.pool==='door'?12:7;
 const shifts=result.assignments.map((p,i)=>{
  assert(Number.isInteger(p)&&p>=-1&&p<input.staff,'Invalid assignee');
  assert(input.pins[i]!==-1||p===-1,'Fixed vacancy changed');
  assert(input.pins[i]<0||input.pins[i]===p,'Pinned duty changed');
  assert(p<0||input.mask[i*input.staff+p]==='1','Ineligible assignment');
  return {day:Math.floor(i/slots)+1,slot:i%slots+1,person:p,unfilled:p===-1};
 });
 const filled=shifts.filter(x=>!x.unfilled).length;
 assert(result.filled===filled&&result.missing===input.shifts-filled,'Incorrect fill counts');
 return {synthetic_only:true,contract:input.contract,status:result.status,
  filled,missing:input.shifts-filled,shifts};
}
module.exports={normalize,project};
