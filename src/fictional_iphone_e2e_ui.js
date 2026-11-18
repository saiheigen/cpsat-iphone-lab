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
// No storage, upload, real identities or relaxation of the sealed source.
const editPool=document.getElementById("fictional-edit-pool");
const editDay=document.getElementById("fictional-edit-day");
const editSlot=document.getElementById("fictional-edit-slot");
const editAction=document.getElementById("fictional-edit-action");
const editPerson=document.getElementById("fictional-edit-person");
const editApply=document.getElementById("fictional-edit-apply");
const editPreset=document.getElementById("fictional-edit-preset");
const editUndo=document.getElementById("fictional-edit-undo");
const editClear=document.getElementById("fictional-edit-clear");
const editStatus=document.getElementById("fictional-edit-status");
const editSummary=document.getElementById("fictional-edit-summary");
const editList=document.getElementById("fictional-edit-list");
const edits=[];
let accepted=null,executing=false,session=0;
function insist(ok,why){if(!ok)throw Error(why);}
function empty(message){
 accepted=null;state.textContent=message;counts.textContent="尚無已完成的雙勤務結果";
 diagnostic.textContent="未產生可用的測試摘要";
 details.hidden=true;details.open=false;dayRows.replaceChildren();reasons.replaceChildren();
}
function readCase(pool,includeEdits=true){
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
 if(includeEdits&&edits.length){
  const bits=t.mask.split("");
  for(const change of edits){
   if(change.pool!==pool)continue;
   const i=change.index;
   insist(Number.isInteger(i)&&i>=0&&i<shifts&&t.pins[i]===-2,
    "修改觸及來源固定班，已拒絕");
   if(change.type==="vacancy"){
    insist(t.hints[i]===-1,"不能將有提示的人直接改成固定空班");
    t.pins[i]=-1;
   }else if(change.type==="block"){
    insist(Number.isInteger(change.person)&&change.person>=0&&
     change.person<staff&&bits[i*staff+change.person]==="1"&&
     t.hints[i]!==change.person,"無法撤銷候選資格");
    bits[i*staff+change.person]="0";
   }else throw Error("不支援的虛構資料修改");
  }
  t.mask=bits.join("");
 }
 t.whatif_edit_count=edits.filter(x=>x.pool===pool).length;
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
 for(const target of [daySelect,editDay]){
  const option=document.createElement("option");option.value=String(d);
  option.textContent="12 月 "+d+" 日";target.appendChild(option);
 }
}
editDay.value="7";
function rowIndex(pool,day,slot){
 const slots=pool==="door"?12:7;
 insist((pool==="door"||pool==="officer")&&Number.isInteger(day)&&
  day>=1&&day<=31&&Number.isInteger(slot)&&slot>=1&&slot<=slots,
  "選擇的勤務日期或時段無效");
 return (day-1)*slots+slot-1;
}
function editLabel(e){
 const slots=e.pool==="door"?12:7;
 const date=Math.floor(e.index/slots)+1,slot=e.index%slots+1;
 return (e.pool==="door"?"大門":"安官")+"｜12/"+date+" 第"+slot+"班｜"+
  (e.type==="vacancy"?"指定空班":"禁排虛構人員 #"+(e.person+1));
}
function updateEditsView(message){
 editList.replaceChildren();
 for(const e of edits){const li=document.createElement("li");
  li.textContent=editLabel(e);editList.appendChild(li);}
 editSummary.textContent="已增加 "+edits.length+" 項模擬限制；只會縮減候選資格。"+
  "不儲存到手機，重新開啟即清空。";
 editPreset.disabled=executing||edits.length!==0;
 editUndo.disabled=executing||edits.length===0;
 editClear.disabled=executing||edits.length===0;
 editStatus.textContent=message||"尚未加入模擬限制";
}
function refreshEditor(){
 const pool=editPool.value==="officer"?"officer":"door";
 const slots=pool==="door"?12:7,previous=Number(editSlot.value);
 editSlot.replaceChildren();
 for(let k=1;k<=slots;k++){
  const option=document.createElement("option");option.value=String(k);
  option.textContent="第"+k+"班";editSlot.appendChild(option);
 }
 editSlot.value=String(previous>=1&&previous<=slots?previous:1);
 const day=Number(editDay.value)||1,index=rowIndex(pool,day,Number(editSlot.value));
 const original=readCase(pool,false);
 const current=readCase(pool,true);
 editPerson.replaceChildren();
 let count=0;
 for(let p=0;p<original.staff;p++)if(current.mask[index*current.staff+p]==="1"){
  const option=document.createElement("option");option.value=String(p);
  option.textContent="虛構人員 #"+(p+1);editPerson.appendChild(option);count++;
 }
 const currentCount=current.mask.slice(index*current.staff,(index+1)*current.staff)
  .split("").filter(bit=>bit==="1").length;
 const immutable=original.pins[index]!==-2;
 const rowEdited=edits.some(e=>e.pool===pool&&e.index===index);
 editPerson.disabled=editAction.value!=="block"||count===0;
 editApply.disabled=executing||immutable||count===0||
  (editAction.value==="vacancy"&&rowEdited)||current.pins[index]===-1;
 const explanation=immutable?(original.pins[index]>=0?
  "此班有人員人工固定，不可修改":"此班原本固定缺班，不可修改"):
  "原本候選 "+count+" 人；模擬後候選 "+currentCount+" 人"+
  (rowEdited?"；已有模擬變更":"");
 editSummary.textContent="已增加 "+edits.length+" 項模擬限制｜"+explanation+
  "。只在本頁記憶體中生效，不會修改來源封存。";
}
function invalidateAccepted(message){
 session++;
 empty("模擬條件已變更；請重新執行兩組求解");
 updateEditsView(message);
 refreshEditor();
}
editPreset.addEventListener("click",()=>{
 if(executing||btn.disabled||edits.length)return;
 try{
  const base=readCase("door",false),batch=[];
  for(const slot of [1,2,3,4,5,7,8,9,10,11]){
   const index=rowIndex("door",7,slot),person=48;
   insist(base.pins[index]===-2&&base.hints[index]!==person&&
    base.mask[index*base.staff+person]==="1","示範情境與原始虛構資料不符");
   batch.push({pool:"door",index,type:"block",person});
  }
  edits.push(...batch);
  invalidateAccepted("✅ 已載入 10 項虛構禁排，重新求解可觀察填班變化");
 }catch(e){editStatus.textContent="❌ "+String(e.message||e);}
});
editPool.addEventListener("change",()=>{editDay.value=editPool.value==="officer"?"5":"7";
 editSlot.value="1";refreshEditor();});
editDay.addEventListener("change",refreshEditor);
editSlot.addEventListener("change",refreshEditor);
editAction.addEventListener("change",refreshEditor);
editApply.addEventListener("click",()=>{
 if(executing||btn.disabled)return;
 try{
  insist(edits.length<40,"最多 40 項模擬限制");
  const pool=editPool.value,day=Number(editDay.value),slot=Number(editSlot.value);
  const index=rowIndex(pool,day,slot),source=readCase(pool,false);
  insist(source.pins[index]===-2,"人工固定班或固定缺班不可更動");
  const already=edits.filter(x=>x.pool===pool&&x.index===index);
  insist(!already.some(x=>x.type==="vacancy"),"此班已被指定空班");
  const next={pool,index,type:editAction.value};
  insist(["block","vacancy"].includes(next.type),"不支援的修改類型");
  if(next.type==="block"){
   next.person=Number(editPerson.value);
   insist(Number.isInteger(next.person)&&next.person>=0&&next.person<source.staff&&
    source.mask[index*source.staff+next.person]==="1"&&
    source.hints[index]!==next.person&&
    !already.some(x=>x.type==="block"&&x.person===next.person),
    "僅能取消目前仍合法的虛構候選，不可重複加入");
  }else{
   insist(already.length===0&&source.hints[index]===-1&&
    source.mask.slice(index*source.staff,(index+1)*source.staff).includes("1"),
    "不能把已修改或無候選的班次設為固定缺班");
  }
  edits.push(next);
  invalidateAccepted("✅ 已加入："+editLabel(next));
 }catch(e){editStatus.textContent="❌ "+String(e.message||e);}
});
editUndo.addEventListener("click",()=>{
 if(executing||btn.disabled||!edits.length)return;
 edits.pop();invalidateAccepted("已撤銷最後一項模擬限制");
});
editClear.addEventListener("click",()=>{
 if(executing||btn.disabled||!edits.length)return;
 edits.length=0;invalidateAccepted("已還原原始虛構測試條件");
});
refreshEditor();
updateEditsView();
function reset(){session++;empty("已清空此輪求解；模擬禁排仍在，須自行按還原");
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
  insist(["OPTIMAL","FEASIBLE"].includes(got.status),"求解器未提供可行解");
  insist(Number.isInteger(got.filled)&&got.filled>=1&&got.filled<=t.expectedFill,
   "新增限制不得增加原始已證實填班數");
  // Original browser audit requires expectedFill==filled. For a stricter
  // in-memory what-if mask, audit the actual C++ result against ALL existing
  // hard rules, but do not mistake that for proof of optimal fill.
  const audited=independentlyAudit({...t,expectedFill:got.filled},got);
  insist(edits.length||audited.filled===t.expectedFill,
   "未修改的虛構來源填班數不符");
   results[pool]={t,got,executionMode,audited};
  }
  const filled=results.door.audited.filled+results.officer.audited.filled;
  const missing=results.door.audited.missing+results.officer.audited.missing;
  insist(filled+missing===589&&filled<=4&&
   (edits.length>0||filled===4),"整月班次數不一致");
  accepted=results;
  counts.textContent="大門："+results.door.audited.filled+"／372 ｜安官："+
   results.officer.audited.filled+"／217 ｜總計已填 "+filled+"，缺班 "+missing;
  state.textContent=edits.length?
   "✅ 新增禁排後取得合法的虛構可行解（不代表最優或正式可用）":
   "✅ 真正 WASM 已求解並通過手機頁面內的部分硬規則稽核（僅虛構資料）";
  diagnostic.textContent=JSON.stringify({synthetic_only:true,preview_only:true,
    operationally_certified:false,importable_as_v7_backup:false,
    real_v7_inputSig_verified:false,full_v7_rule_parity_verified:false,
    real_iphone_safari_verified:false,source_audit_local_only:true,
    independent_source_audit_repeated_on_device:false,
    wasm_binary_sha256:SPEC.wasm_sha256,
    statuses:{door:results.door.got.status,officer:results.officer.got.status},
    execution_modes:{door:results.door.executionMode,officer:results.officer.executionMode},
    month_rows:589,filled,missing,whatif_edits:edits.length,
    whatif_restrictions_only:true,whatif_local_memory_only:true,
    edited_source_original_crossmonth_reaudited_on_device:false,
    optimality_independently_proven:false},null,2);
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
  refreshEditor();updateEditsView(editStatus.textContent);
 }
});
section.hidden=false;
})();
