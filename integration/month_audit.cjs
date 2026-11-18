'use strict';
// Synthetic-only independent feasibility audit; partial v7 rules.
// No solver dependency. Keep an independent Python reverse-auditor.
const HOURS={
 door:[[22,24],[0,2],[2,4],[4,6],[6,8],[8,10],[10,12],[12,14],[14,16],[16,18],[18,20],[20,22]],
 officer:[[22,24],[0,2],[2,4],[4,6],[6,12],[12,18],[18,22]]
};
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
module.exports={HOURS,independentlyAudit};
