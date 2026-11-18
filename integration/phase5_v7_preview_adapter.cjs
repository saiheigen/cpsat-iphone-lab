'use strict';
// Preview-only projection into v7's [Unix-day, slot, personID] row shape.
// ONLY anonymous, synthetic scenarios. Not a guard-offline-v5 backup.
// Validation here covers the solver's proven subset of mandatory rules,
// NOT every v7 business, carry, leave, inspection and cross-month behavior.
const {project}=require('./phase5_synthetic_adapter.cjs');
function requireState(ok, message){if(!ok)throw Error(message);}
function previewCombined({door,officer}){
 requireState(door&&officer,'Both door and officer pools are required');
 const pools={door,officer};
 const schedule={door:[],officer:[]};
 const vacancies=[];
 let filled=0,missing=0,year=null,month=null;
 for(const pool of ['door','officer']){
  const entry=pools[pool];
  requireState(entry&&entry.input&&entry.result,'Missing pool input or result');
  const input=entry.input;
  requireState(input.pool===pool,'Incorrect pool boundary');
  requireState(input.synthetic_only===true,'Synthetic-only source required');
  if(year===null){year=input.year;month=input.month;}
  requireState(year===input.year&&month===input.month,'Cross-month merge refused');
  const projected=project(input,entry.result);
  requireState(projected.synthetic_only===true,'Non-synthetic projection refused');
  const days=new Date(Date.UTC(year,month,0)).getUTCDate();
  const expected=days*(pool==='door'?12:7);
  requireState(projected.shifts.length===expected,'Truncated pool');
  for(const row of projected.shifts){
   const serial=Date.UTC(year,month-1,row.day)/86400000;
   requireState(Number.isInteger(serial),'Invalid day serial');
   const person=row.unfilled?null:
    'SIM_'+(pool==='door'?'D':'O')+'_'+String(row.person).padStart(3,'0');
   schedule[pool].push([serial,row.slot,person]);
   if(row.unfilled)vacancies.push({pool,day:row.day,slot:row.slot});
  }
  filled+=projected.filled;missing+=projected.missing;
 }
 requireState(schedule.door.length+schedule.officer.length===filled+missing,
  'A shift disappeared');
 return {
  format:'guard-cpsat-synthetic-preview-v1',
  schema_shape:'v7-month-schedule-rows-v1',
  source_contract:'guard-month-harsh-v4',
  month:year+'-'+String(month).padStart(2,'0'),
  synthetic_only:true,preview_only:true,
  importable_as_v7_backup:false,operationally_certified:false,
  full_v7_rule_parity_verified:false,real_iphone_safari_verified:false,
  source_solver_provenance_verified_by_this_function:false,
  filled,missing,schedule,vacancies,
  warnings:[
   '僅供虛構資料預覽；不可還原為 v7 備份或覆寫核定班表',
   '目前未逐條驗證完整 v7 軍務規則、跨月與補償狀態',
   '真正 iPhone Safari 實機尚未通過'
  ]
 };
}
module.exports={previewCombined};
