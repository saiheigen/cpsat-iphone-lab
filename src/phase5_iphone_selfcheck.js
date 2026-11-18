/* Single-page synthetic-only device handoff and evidence collector.
   This never sends data or certifies iPhone Safari by itself.
   No roster, name, phone identifier, local storage or external request. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const outcomes=Object.create(null);
let combined=null,probe=null,unhandled=0,lastTick=performance.now(),maxGap=0,ticks=0;
const cases=new Set(["tiny","door-blackouts-no-hints",
 "officer-blackouts-no-hints","door-forced-vacancies"]);
window.addEventListener("error",()=>{unhandled++;});
window.addEventListener("unhandledrejection",()=>{unhandled++;});
setInterval(()=>{
 const now=performance.now();
 if(document.visibilityState==="visible"){
  maxGap=Math.max(maxGap,now-lastTick);
  ticks++;
 }
 lastTick=now;
},100);
document.addEventListener("visibilitychange",()=>{
 lastTick=performance.now();
});
function capture(){
 try{
  const result=JSON.parse($("output").textContent);
  if(result.accepted===true&&cases.has(result.scenario)&&
      result.operationally_certified===false&&
      result.real_iphone_safari_verified===false){
   outcomes[result.scenario]={
    scenario:result.scenario,
    shifts:result.shifts,filled:result.filled,missing:result.missing,
    execution_mode:result.execution_mode,elapsed_ms:result.elapsed_ms,
    fill_phase:result.fill_phase,fair_phase:result.fair_phase,
    hardship_phase:result.hardship_phase,
    final_abs_deviation:result.final_abs_deviation
   };
  }
 }catch(_){}
 try{
  const state=JSON.parse($("combined-output").textContent);
  if(state.accepted===true&&state.synthetic_only===true&&
     state.preview_only===true&&state.importable_as_v7_backup===false&&
     state.rows===589&&state.missing===12&&state.filled===577){
   combined={rows:589,filled:577,missing:12,
    importable_as_v7_backup:false,operationally_certified:false};
  }
 }catch(_){}
 $("phone-record-count").textContent=
  Object.keys(outcomes).length+" / 4 情境已記錄"+
  (combined?"；589 班合併預覽已記錄":"");
}
new MutationObserver(capture).observe($("output"),{childList:true,characterData:true,subtree:true});
new MutationObserver(capture).observe($("combined-output"),{childList:true,characterData:true,subtree:true});
function wasmTinyValid(){
 try{return typeof WebAssembly==="object"&&
  WebAssembly.validate(new Uint8Array([0,97,115,109,1,0,0,0]));}
 catch(_){return false;}
}
async function probeWorker(){
 const result={status:"unavailable",wasm_validate:wasmTinyValid()};
 if(typeof Worker!=="function"||typeof Blob!=="function"||
    typeof URL==="undefined"||typeof URL.createObjectURL!=="function")
  return result;
 return await new Promise(resolve=>{
  let worker=null,url=null,finished=false;
  function done(state){
   if(finished)return;
   finished=true;
   if(worker)worker.terminate();
   if(url)URL.revokeObjectURL(url);
   resolve({status:state,wasm_validate:result.wasm_validate});
  }
  try{
   const script='self.postMessage({ready:true,wasm:WebAssembly.validate('+
    'new Uint8Array([0,97,115,109,1,0,0,0]))})';
   url=URL.createObjectURL(new Blob([script],{type:"text/javascript"}));
   worker=new Worker(url);
   worker.onmessage=e=>done(e.data&&e.data.ready===true&&e.data.wasm===true?
    "ready":"invalid_response");
   worker.onerror=e=>{
    if(e&&typeof e.preventDefault==="function")e.preventDefault();
    done("error");
   };
   setTimeout(()=>done("timeout"),5000);
  }catch(_){done("exception");}
 });
}
$("phone-worker-probe").addEventListener("click",async()=>{
 const button=$("phone-worker-probe");
 button.disabled=true;
 $("phone-probe-status").textContent="正在檢查本機 WASM 與 Blob Worker…";
 try{
  probe=await probeWorker();
  $("phone-probe-status").textContent="Worker："+probe.status+
   "｜基礎 WASM："+(probe.wasm_validate?"通過":"未通過");
 }finally{button.disabled=false;}
});
function manualEvidence(){
 capture();
 const choice=$("phone-open-method").value;
 const connectivity=$("phone-network-mode").value;
 return {
  format:"phase5-synthetic-iphone-selfcheck-v1",
  generated_at_utc:new Date().toISOString(),
  source:"local_synthetic_webpage_no_transmission",
  manually_selected_open_method:choice,
  manually_selected_network_state:connectivity,
  manual_physical_iphone_confirmation:$("phone-is-physical").checked,
  navigator_online_hint:navigator.onLine,
  document_scheme:location.protocol,
  document_origin:location.origin,
  browser_hint_from_user_agent:/iPhone|iPad|iPod/.test(navigator.userAgent)?
   "ios_like":"other_or_unknown",
  browser_identity_independently_verified:false,
  physical_iphone_safari_verified:false,
  operationally_certified:false,
  full_v7_rule_parity_verified:false,
  worker_probe:probe||{status:"not_run",wasm_validate:wasmTinyValid()},
  observed_main_thread_max_gap_ms:Math.round(maxGap),
  main_thread_heartbeat_samples:ticks,
  unhandled_script_errors_observed:unhandled,
  synthetic_cases:Object.values(outcomes),
  synthetic_combined_preview:combined,
  all_four_cases_observed:Object.keys(outcomes).length===4,
  warnings:[
   "此檔不會自行傳送資料；必須由使用者自行複製回報",
   "瀏覽器、裝置與斷網狀態均屬手動選擇或提示，並非獨立實機驗證",
   "navigator.onLine 不足以證實真正離線",
   "若瀏覽器切到背景，事件迴圈間隔不是精確手機效能量測",
   "僅為虛構 CP-SAT 測試，不是正式軍務班表"
  ]
 };
}
$("phone-generate-evidence").addEventListener("click",()=>{
 const result=manualEvidence();
 $("phone-evidence-json").value=JSON.stringify(result,null,2);
 $("phone-evidence-status").textContent=
  "本機測試紀錄已產生；請自行複製貼回對話。"+
  (result.all_four_cases_observed?"四個虛構情境已收集。":"尚未收集四個情境。");
});
$("phone-copy-evidence").addEventListener("click",async()=>{
 const textarea=$("phone-evidence-json");
 if(!textarea.value){
  $("phone-evidence-status").textContent="請先按「產生測試紀錄」";
  return;
 }
 try{
  if(!navigator.clipboard||!navigator.clipboard.writeText)
   throw Error("Clipboard API unavailable");
  await navigator.clipboard.writeText(textarea.value);
  $("phone-evidence-status").textContent="已複製測試紀錄；可貼回對話。";
 }catch(_){
  textarea.focus();
  textarea.select();
  $("phone-evidence-status").textContent=
   "此開啟方式不支援一鍵複製；紀錄已全選，請使用「複製」。";
 }
});
})();
