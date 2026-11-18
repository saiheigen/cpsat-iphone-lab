'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {independentlyAudit}=require('../integration/month_audit.cjs');
function makeFixture(pool){
 const slots=pool==='door'?12:7,staff=pool==='door'?56:50,n=slots*31;
 const mask=Array(n*staff).fill('0'),pins=Array(n).fill(-2),hints=Array(n).fill(-1);
 const assigned=Array(n).fill(-1);
 const fixed=pool==='door'?(7-1)*12+6-1:(5-1)*7+5-1;
 const blank=pool==='door'?(5-1)*12+8-1:(6-1)*7+4-1;
 pins[blank]=-1;pins[fixed]=48;assigned[fixed]=48;mask[fixed*staff+48]='1';
 if(pool==='door'){
  for(const [day,slot,p] of [[1,5,0],[4,9,1]]){
   const index=(day-1)*slots+slot-1;mask[index*staff+p]='1';assigned[index]=p;
  }
 }
 const required=pool==='door'?12:7;
 for(let i=0,k=0;k<required-(pool==='door'?3:1);i++){
  const day=10+Math.floor(i/slots),slot=i%slots,p=5+(i%5),index=(day-1)*slots+slot;
  if(index>=n||mask[index*staff+p]==='1')continue;
  mask[index*staff+p]='1';k++;
 }
 const wire=['guard-month-harsh-v4','2026-12',pool,n+' '+staff,
  mask.join(''),pins.join(','),hints.join(','),Array(staff).fill(0).join(',')].join('\n')+'\n';
 const filled=assigned.filter(x=>x>=0).length;
 return {wire,got:{status:'FEASIBLE',assignments:assigned,filled,missing:n-filled}};
}
const temp=Object.fromEntries(['door','officer'].map(pool=>[pool,makeFixture(pool)]));
const frames=Object.fromEntries(Object.entries(temp).map(([pool,item])=>[pool,item.wire]));
const results=Object.fromEntries(Object.entries(temp).map(([pool,item])=>[pool,item.got]));
const hours={door:[[22,24],[0,2],[2,4],[4,6],[6,8],[8,10],[10,12],[12,14],[14,16],[16,18],[18,20],[20,22]],officer:[[22,24],[0,2],[2,4],[4,6],[6,12],[12,18],[18,22]]};
const spec={synthetic_only:true,operationally_certified:false,month:'2026-12',source_audit_local_only:true,wasm_sha256:'0'.repeat(64),frames:Object.fromEntries(Object.entries(frames).map(([pool,wire])=>[pool,{wire}]))};
const js=fs.readFileSync(path.join(__dirname,'../src/fictional_iphone_e2e_ui.js'),'utf8').replace('__FICTIONAL_E2E_SPEC__',JSON.stringify(spec));
function setup(solve){
 class Element{
  constructor(id){this.id=id;this.disabled=false;this.hidden=true;this.open=false;this.textContent='';this.value=id==='fictional-e2e-day'?'1':id==='fictional-e2e-pool'?'door':'';this.handlers={};this.children=[];}
  addEventListener(k,fn){this.handlers[k]=fn;}
  appendChild(n){this.children.push(n);}
  replaceChildren(){this.children=[];}
 }
 const els=new Map(),handles={};
 const document={getElementById:id=>{if(!els.has(id))els.set(id,new Element(id));return els.get(id);},createElement:k=>new Element(k)};
 const window={addEventListener:(k,fn)=>{handles[k]=fn;}};
 const e2e=Object.fromEntries(['btn','select','resetBtn','combinedBtn','cancelBtn'].map(id=>[id,document.getElementById(id)]));
 const ctx={document,window,requestAnimationFrame:cb=>setImmediate(cb),solveGeneration:0,...e2e,updateCombinedReadiness:()=>{},
  solveWithMode:solve,independentlyAudit:(t,got)=>{
   const filled=independentlyAudit({year:t.year,month:t.month,pool:t.pool,staff:t.staff,shiftCount:t.shifts,allowed:t.mask,pins:t.pins,hints:t.hints},got);
   return {filled,missing:t.shifts-filled};
  },
  serialize:t=>['guard-month-harsh-v4',t.year+'-'+String(t.month).padStart(2,'0'),t.pool,t.shifts+' '+t.staff,t.mask,t.pins.join(','),t.hints.join(','),t.targets.join(',')].join('\n')+'\n',
  HOURS:hours,Event,console,setImmediate};
 vm.runInNewContext(js,ctx,{filename:'fictional_iphone_e2e_ui.js'});
 return {get:id=>document.getElementById(id),ctx,reset:()=>handles['phase5-session-reset']()};
}
(async()=>{
 const ok=setup(async t=>({got:results[t.pool],executionMode:'dedicated-worker'}));
 assert.equal(ok.get('fictional-e2e-workspace').hidden,false);
 await ok.get('fictional-e2e-start').handlers.click();
 assert.match(ok.get('fictional-e2e-status').textContent,/^✅/);
 assert.match(ok.get('fictional-e2e-counts').textContent,/缺班 585/);
 assert.equal(ok.get('fictional-e2e-preview').hidden,false);
 const report=JSON.parse(ok.get('fictional-e2e-report').textContent);
 assert.equal(report.operationally_certified,false);
 assert.equal(report.independent_source_audit_repeated_on_device,false);
 assert.equal(report.missing,585);
 assert.equal(ok.get('fictional-e2e-reasons').children.length,2);
 assert.equal(ok.get('fictional-e2e-day-rows').children.length,1);
 ok.get('fictional-e2e-day').value='6';ok.get('fictional-e2e-day').handlers.change();
 assert.equal(ok.get('fictional-e2e-day-rows').children[0].children.length,12);
 ok.reset();
 assert.equal(ok.get('fictional-e2e-preview').hidden,true);
 const bad=setup(async t=>({got:t.pool==='door'?results.door:{status:'UNKNOWN'},executionMode:'dedicated-worker'}));
 await bad.get('fictional-e2e-start').handlers.click();
 assert.match(bad.get('fictional-e2e-status').textContent,/^❌/);
 assert.equal(bad.get('fictional-e2e-preview').hidden,true);
 assert.doesNotMatch(bad.get('fictional-e2e-report').textContent,/"month_rows":589/);
 const forged=setup(async t=>({got:t.pool==='door'?{...results.door,filled:500}:results.officer,executionMode:'dedicated-worker'}));
 await forged.get('fictional-e2e-start').handlers.click();
 assert.equal(forged.get('fictional-e2e-preview').hidden,true);
 assert.match(forged.get('fictional-e2e-status').textContent,/^❌/);
 console.log('Synthetic iPhone UI: success, reset, UNKNOWN rejection, forged-count rejection PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});
