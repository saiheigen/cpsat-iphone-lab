/* Appended inside the existing proof-gated offline page's main script.
 * Reuses the existing genuine WASM Worker, cancellation and independent
 * same-month JS audit. Only embedded, source-anchored fictional frames.
 * Does not independently verify the original archived v7 inputs on iPhone.
 */
(function(){
"use strict";
const SPEC=__FICTIONAL_E2E_SPEC__;
const section=document.getElementById("fictional-e2e-workspace");
const startBtn=document.getElementById("fictional-e2e-start");
const state=document.getElementById("fictional-e2e-status");
const counts=document.getElementById("fictional-e2e-counts");
const details=document.getElementById("fictional-e2e-preview");
const daySelect=document.getElementById("fictional-e2e-day");
const poolSelect=document.getElementById("fictional-e2e-pool");
const dayRows=document.getElementById("fictional-e2e-day-rows");
const reasons=document.getElementById("fictional-e2e-reasons");
const diagnostic=document.getElementById("fictional-e2e-report");
let accepted=null,executing=false,session=0;
function insist(ok,why){if(!ok)throw Error(why);}
function empty(message){
 accepted=null;state.textContent=message;counts.textContent="尚無已完成的雙勤務結果";
 diagnostic.textContent="未產生可用的測試摘要";
 details.hidden=true;details.open=false;dayRows.replaceChildren();reasons.replaceChildren();
}
function readCase(pool){
 const item=SPEC.frames[pool];
 insist(item&&typeof item.wire==="string", "缺少完整虛構資料");
 const lines=item.wire.split("\n");
 insist(lines.length===9&&lines[8]===""&&lines[0]==="guard-month-harsh-v4"&&
  lines[1]==="2026-12"&&lines[2]===pool,"虛構資料協議不一致");
 const fields=lines[3].split(" ").map(Number);
 const shifts=pool==="door"?372:217,staff=pool==="door"?56:50;
 insist(fields.length===2&&fields[0]===shifts&&fields[1]===staff,
  "班次或人員數量不一致");
 const pins=lines[5].split(",").map(Number);
 const hints=lines[6].split(",").map(Number);
 const targets=lines[7].split(",").map(Number);
 insist(pins.length===shifts&&hints.length===shifts&&targets.length===staff,
  "固定班或目標被截斷");
 const t={id:"fictional-cross-month-"+pool,synthetic_only:true,
  name:pool==="door"?"虛構大門":"虛構安官",
  year:2026,month:12,pool,shifts,staff,mask:lines[4],pins,hints,targets,
  expectedFill:pool==="door"?3:1};
 insist(serialize(t)===item.wire,"求解器資料被改寫");
 return t;
}
function classify(t,answer,index){
 if(t.pins[index]===-1)return "固定缺班";
 const row=t.mask.slice(index*t.staff,(index+1)*t.staff);
 if(!row.includes("1"))return "候選人數為 0（來源限制；詳細原因未提供）";
 return answer.assignments[index]<0?
  "未填班（仍有候選；原因需進一步分析）":"已填班";
}
function renderDay(){
 dayRows.replaceChildren();
 if(!accepted)return;
 const pool=poolSelect.value,day=Number(daySelect.value),t=accepted[pool].t;
 if(!Number.isInteger(day)||day<1||day>31)return;
 const list=document.createElement("ul");
 const shifts=pool==="door"?12:7;
 for(let k=0;k<shifts;k++){
  const idx=(day-1)*shifts+k,assignee=accepted[pool].got.assignments[idx];
  const times=HOURS[pool][k];
  const li=document.createElement("li");
  li.textContent="第"+(k+1)+"班（"+String(times[0]).padStart(2,"0")+
   ":00–"+String(times[1]).padStart(2,"0")+":00）："+
   (assignee<0?classify(t,accepted[pool].got,idx):"虛構人員 #"+(assignee+1));
  list.appendChild(li);
 }
 dayRows.appendChild(list);
}
function renderReasons(){
 reasons.replaceChildren();
 for(const pool of ["door","officer"]){
  const {t,got}=accepted[pool];
  const total={"固定缺班":0,"候選人數為 0（來源限制；詳細原因未提供）":0,
   "未填班（仍有候選；原因需進一步分析）":0};
  for(let i=0;i<t.shifts;i++)if(got.assignments[i]<0){
   const reason=classify(t,got,i);
   insist(Object.hasOwn(total,reason),"缺班原因分類失敗");total[reason]++;
  }
  const li=document.createElement("li");
  li.textContent=(pool==="door"?"大門衛哨":"安全士官")+"："+
   Object.entries(total).map(([key,value])=>key+" "+value+" 班").join("；");
  reasons.appendChild(li);
 }
}
for(let d=1;d<=31;d++){
 const option=document.createElement("option");option.value=String(d);
 option.textContent="12 月 "+d+" 日";daySelect.appendChild(option);
}
function reset(){session++;empty("已清空此輪驗收；舊結果不可使用");
 if(!executing)startBtn.disabled=false;
}
window.addEventListener("phase5-session-reset",reset);
daySelect.addEventListener("change",renderDay);
poolSelect.addEventListener("change",renderDay);
startBtn.addEventListener("click",async()=>{
 if(executing||btn.disabled)return;
 let generation=++solveGeneration;
 const mine=++session;
 executing=true;startBtn.disabled=true;
 btn.disabled=true;select.disabled=true;resetBtn.disabled=true;combinedBtn.disabled=true;
 cancelBtn.disabled=false;
 empty("正在依序以真正 WASM 求解兩組虛構完整月份…");
 await new Promise(ok=>requestAnimationFrame(ok));
 try{
  insist(SPEC.synthetic_only===true&&SPEC.operationally_certified===false&&
   SPEC.month==="2026-12"&&SPEC.source_audit_local_only===true,
   "未通過虛構來源限定");
  const results={};
  for(const pool of ["door","officer"]){
   insist(generation===solveGeneration&&mine===session,"已取消的舊求解不能採用");
   const t=readCase(pool);
   state.textContent="正在求解"+(pool==="door"?"大門衛哨":"安全士官")+"；尚未核發任何班表…";
   const {got,executionMode}=await solveWithMode(t,generation);
   insist(generation===solveGeneration&&mine===session,"舊求解回覆已失效");
   const audited=independentlyAudit(t,got);
   insist(["OPTIMAL","FEASIBLE"].includes(got.status),"求解器未提供可行解");
   insist(audited.filled===t.expectedFill,"虛構填班數不符合已核對來源");
   results[pool]={t,got,executionMode,audited};
  }
  const filled=results.door.audited.filled+results.officer.audited.filled;
  const missing=results.door.audited.missing+results.officer.audited.missing;
  insist(filled===4&&missing===585,"整月班次數不一致");
  accepted=results;
  counts.textContent="大門："+results.door.audited.filled+"／372 ｜安官："+
   results.officer.audited.filled+"／217 ｜總計已填 "+filled+"，缺班 "+missing;
  state.textContent="✅ 真正 WASM 已求解並通過手機頁面內的部分硬規則稽核（僅虛構資料）";
  diagnostic.textContent=JSON.stringify({synthetic_only:true,preview_only:true,
    operationally_certified:false,importable_as_v7_backup:false,
    real_v7_inputSig_verified:false,full_v7_rule_parity_verified:false,
    real_iphone_safari_verified:false,source_audit_local_only:true,
    independent_source_audit_repeated_on_device:false,
    wasm_binary_sha256:SPEC.wasm_sha256,
    statuses:{door:results.door.got.status,officer:results.officer.got.status},
    execution_modes:{door:results.door.executionMode,officer:results.officer.executionMode},
    month_rows:589,filled,missing},null,2);
  details.hidden=false;details.open=false;
  renderReasons();renderDay();
 }catch(e){
  empty(generation!==solveGeneration||mine!==session?
   "⏹ 已取消；舊求解結果全部作廢":"❌ 求解或規則檢查失敗，沒有可用班表");
  diagnostic.textContent=String(e&&e.message||e);
 }finally{
  executing=false;startBtn.disabled=false;
  btn.disabled=false;select.disabled=false;resetBtn.disabled=false;
  cancelBtn.disabled=true;updateCombinedReadiness();
 }
});
section.hidden=false;
})();
