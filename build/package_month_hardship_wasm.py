#!/usr/bin/env python3
"""Fail-closed SINGLE-FILE 589-shift three-stage hardship WASM browser demo packager.

Requires a genuinely executed Node OR-Tools CP-SAT WASM proof, with exact
small-case oracle + independent full-month legal audit and matching binaries.
Only four baked-in fictional cases are exported. No import, names, or files.
Chromium checks and iPhone Safari are separate, subsequent acceptance steps.
"""
import base64
import hashlib
import json
from pathlib import Path
import re
import sys

EXPECT={
    "exact-four-shift-hardship-oracle":(372,2,4),
    "door-blackouts-no-hints":(372,56,372),
    "officer-blackouts-no-hints":(217,50,217),
    "door-forced-vacancies":(372,56,360),
}
PAGE_EXPECT={
    "tiny":(372,2,4),
    "door-blackouts-no-hints":(372,56,372),
    "officer-blackouts-no-hints":(217,50,217),
    "door-forced-vacancies":(372,56,360),
}
_sha=lambda b:hashlib.sha256(b).hexdigest()

def verify(js_path, wasm_path, proof_path, fixture_path):
    js=Path(js_path).read_bytes()
    wasm=Path(wasm_path).read_bytes()
    proof=json.loads(Path(proof_path).read_text("utf-8"))
    fixture_bytes=Path(fixture_path).read_bytes()
    fixtures=json.loads(fixture_bytes.decode("utf-8"))
    if not wasm.startswith(b"\x00asm\x01\x00\x00\x00"):
        raise ValueError("Expected genuine WebAssembly header")
    if b"createMonthHardshipModule" not in js:
        raise ValueError("Missing Emscripten three-phase hardship module")
    if (proof.get("js_sha256")!=_sha(js) or
            proof.get("wasm_sha256")!=_sha(wasm)):
        raise ValueError("Genuine Node-tested JS/WASM binary hash mismatch")
    expected_flags={
        "accepted":True,
        "engine":"genuine-Google-OR-Tools-CP-SAT-WASM",
        "contract":"guard-month-harsh-v4",
        "three_phases":True,
        "filled_positions_protected":True,
        "count_fairness_protected":True,
        "synthetic_only":True,
        "real_iphone_safari_tested":False,
        "operationally_certified":False,
        "full_hard_rules_verified":False,
        "exact_independent_hardship_oracle_verified":True,
        "tested_full_589_dense_shifts":True,
    }
    if any(proof.get(k)!=v for k,v in expected_flags.items()):
        raise ValueError("Three-stage genuine WASM proof or testing scope missing")
    if (type(proof.get("invalid_frames_rejected")) is not int or
            proof["invalid_frames_rejected"]<3):
        raise ValueError("Failed invalid-frame rejection proof")
    if (not isinstance(proof.get("fixture_sha256"),str) or
            not re.fullmatch(r"[0-9a-f]{64}",proof["fixture_sha256"]) or
            proof["fixture_sha256"]!=_sha(fixture_bytes)):
        raise ValueError("Unattested browser fixtures differ from real Node WASM test")
    cases=proof.get("cases")
    if not isinstance(cases,list) or len(cases)!=len(EXPECT):
        raise ValueError("Missing or repeated actual Node hardship proof cases")
    seen=set()
    for item in cases:
        if not isinstance(item,dict):
            raise ValueError("Invalid actual Node proof object")
        name=item.get("name")
        if name not in EXPECT or name in seen or item.get("accepted") is not True:
            raise ValueError("Unapproved or repeated three-stage proof case")
        shifts,staff,filled=EXPECT[name]
        if item.get("status") not in ("FEASIBLE","OPTIMAL") or item.get("filled")!=filled:
            raise ValueError("Illegal or insufficient proof of preserved fill")
        if name=="exact-four-shift-hardship-oracle":
            if (item.get("status")!="OPTIMAL" or
                    type(item.get("hardship")) is not int or
                    item.get("hardship")!=item.get("oracle")):
                raise ValueError("Tiny independent exact hardship oracle failed")
        else:
            if item.get("shifts")!=shifts or item.get("staff")!=staff:
                raise ValueError("Whole-month hardship case shape mismatch")
            for key in ("phase1_abs_deviation","final_abs_deviation",
                        "hardship_before","hardship_after"):
                if type(item.get(key)) is not int or item[key]<0:
                    raise ValueError("Missing numerical three-stage hardship proof")
            if (item["final_abs_deviation"]>item["phase1_abs_deviation"] or
                    item["hardship_after"]>item["hardship_before"]):
                raise ValueError("Three-stage solver sacrificed a protected objective")
            for phase in ("fill_phase","fair_phase","hardship_phase"):
                if item.get(phase) not in ("OPTIMAL","FEASIBLE","UNKNOWN"):
                    raise ValueError("Invalid phase status in real WASM proof")
            if (item.get("hardship_optimal_proven") is True and
                    item["hardship_phase"]!="OPTIMAL"):
                raise ValueError("Falsely claimed hardship global optimality")
        seen.add(name)
    if (fixtures.get("contract")!="guard-month-harsh-v4" or
            fixtures.get("source")!="synthetic-fixtures-no-real-workforce-data"):
        raise ValueError("Refusing non-synthetic or untrusted data source")
    entries=fixtures.get("cases")
    if not isinstance(entries,list) or len(entries)!=len(PAGE_EXPECT):
        raise ValueError("Missing browser acceptance cases")
    seen=set()
    for item in entries:
        if not isinstance(item,dict):
            raise ValueError("Malformed browser fixture case")
        name=item.get("id")
        if name not in PAGE_EXPECT or name in seen:
            raise ValueError("Unknown or duplicated browser hardship case")
        shifts,staff,fill=PAGE_EXPECT[name]
        pool="officer" if name.startswith("officer") else "door"
        if (item.get("synthetic_only") is not True or
                item.get("year")!=2026 or item.get("month")!=12 or
                item.get("pool")!=pool or
                item.get("shifts")!=shifts or item.get("staff")!=staff or
                item.get("expectedFill")!=fill):
            raise ValueError("Incorrect fictional duty pool or month shape")
        if (not isinstance(item.get("mask"),str) or
                len(item["mask"])!=shifts*staff or
                set(item["mask"])-{"0","1"} or
                len(item.get("pins",[]))!=shifts or
                len(item.get("hints",[]))!=shifts or
                len(item.get("targets",[]))!=staff):
            raise ValueError("Anonymous eligibility, pin, hint or target truncated")
        if any(type(v) is not int or v<0 or v>shifts for v in item["targets"]):
            raise ValueError("Invalid individual fairness target")
        if any(type(v) is not int or v<-2 or v>=staff for v in item["pins"]):
            raise ValueError("Invalid artificial fixed assignment")
        if any(type(v) is not int or v<-1 or v>=staff for v in item["hints"]):
            raise ValueError("Invalid synthetic warm-start")
        if name=="tiny":
            tiny=next(x for x in cases if x["name"]=="exact-four-shift-hardship-oracle")
            if (type(item.get("oracleBest")) is not int or
                    item["oracleBest"]!=tiny["oracle"]):
                raise ValueError("Tiny independent oracle not bound to exact fixture")
        elif item.get("oracleBest") is not None:
            raise ValueError("Unexpected unproven month-wide hardship oracle")
        seen.add(name)
    return js.decode("utf-8"),base64.b64encode(wasm).decode("ascii"),proof,fixtures


HTML = r"""<!doctype html><html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>真正 CP-SAT｜整月填班與公平離線實驗</title>
<style>
*{box-sizing:border-box}body{margin:0;padding:15px;background:#eef3f7;color:#19364d;
font:16px/1.6 -apple-system,BlinkMacSystemFont,system-ui,sans-serif}
main{max-width:680px;margin:14px auto;background:white;padding:20px;border-radius:16px}
h1{font-size:22px;line-height:1.35}.notice{background:#fff2dc;padding:12px;border-radius:9px}
select,button{display:block;width:100%;padding:14px;border-radius:10px;font-size:16px}
button{background:#0d6888;color:white;font-weight:700;border:0;margin-top:14px}
button:disabled{opacity:.55}label{display:block;margin:15px 0 7px}
details{padding:9px 11px;border:1px solid #c7d8e4;border-radius:9px;margin:12px 0}
details summary{cursor:pointer;font-weight:700}details ol{margin:9px 0;padding-left:24px}
details li{margin:5px 0}.roster-day{padding:8px 0;border-bottom:1px solid #dce5ed}
.roster-day strong{display:block}.roster-day ul{margin:4px 0 8px;padding-left:22px}
.roster-day li{font-size:14px;line-height:1.5}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf3f8;border-radius:9px;
padding:13px;font-size:12px}small{display:block;color:#647586;overflow-wrap:anywhere}
</style></head><body><main>
<h1>589 班真正 CP-SAT｜三階段艱苦哨公平測試</h1>
<p class="notice">⚠️ 僅供虛構資料的離線運算驗證，不是正式軍務排班系統。
不接受名冊、休假或勤務資料輸入，不能核定班表。
先合法填班、再平衡總班數，最後在不犧牲既有成果下改善夜哨／午間與長班。
手機上可能短暫卡頓；本頁不代表已在真正 iPhone Safari 驗收。</p>
<label for="scenario">選擇已驗證的虛構情境</label>
<select id="scenario"></select>
<button id="run">在本機執行真正 WASM 三階段求解</button>
<p id="status" role="status">尚未執行</p>
<section id="summary" aria-live="polite">尚無排班摘要</section>
<details id="vacancy-details" hidden><summary id="vacancy-title">查看完整缺班清單</summary>
<ol id="vacancy-list"></ol></details>
<details id="roster-preview" hidden><summary>查看整月虛構班表預覽（不可匯入正式網站）</summary>
<div id="roster-days"></div></details>
<section id="combined-workspace" aria-label="雙勤務虛構整月預覽">
<p>跨勤務完整月預覽：須先分別完成「安官整月」與「大門強制缺班」兩個真正 WASM 測試。</p>
<button id="combined-run" disabled>顯示大門＋安官 589 班預覽</button>
<p id="combined-status" role="status">尚缺兩個已驗證的虛構情境</p>
<details id="combined-preview" hidden><summary>查看雙勤務每日班次（不可匯入正式網站）</summary>
<div id="combined-days"></div></details>
<pre id="combined-output">尚無雙勤務已驗證資料</pre>
</section>
<pre id="output">沒有結果</pre>
<small>WASM SHA-256：__WASM_SHA__</small>
</main><script>__GLUE__</script>
<script>
"use strict";
const CASES=__CASES__;
const ENCODED=__WASM_PARTS__;
const HOURS={
 door:[[22,24],[0,2],[2,4],[4,6],[6,8],[8,10],[10,12],[12,14],[14,16],[16,18],[18,20],[20,22]],
 officer:[[22,24],[0,2],[2,4],[4,6],[6,12],[12,18],[18,22]]
};
const select=document.getElementById("scenario");
for(const item of CASES){
 const option=document.createElement("option");
 option.value=item.id;option.textContent=item.name;select.appendChild(option);
}
function serialize(t){
 return ["guard-month-harsh-v4",String(t.year)+"-"+String(t.month).padStart(2,"0"),
 t.pool,String(t.shifts)+" "+String(t.staff),t.mask,t.pins.join(","),
 t.hints.join(","),t.targets.join(",")].join("\n")+"\n";
}
function toBytes(raw){
 const b64=atob(raw),out=new Uint8Array(b64.length);
 for(let i=0;i<b64.length;i++)out[i]=b64.charCodeAt(i);
 return out;
}
function hardshipScore(t,assignments){
 const categories=t.pool==="door"?
  ["night_22_24","night_00_02","night_02_04","night_04_06","night_total","noon"]:
  ["night_total","noon","officer_six_hour","officer_hours"];
 const weights={night_total:2,night_22_24:1,night_00_02:1,
  night_02_04:1,night_04_06:1,noon:2,officer_six_hour:2,officer_hours:1};
 const counts=Array(t.staff).fill(0),loads=Array.from({length:t.staff},
  ()=>Array(categories.length).fill(0));
 const totals=Array(categories.length).fill(0);
 const slots=t.pool==="door"?12:7;
 let filled=0;
 for(let s=0;s<assignments.length;s++){
  const p=assignments[s];
  if(p<0)continue;
  filled++;counts[p]++;
  const k=s%slots;
  const units=t.pool==="door"?
   [Number(k===0),Number(k===1),Number(k===2),Number(k===3),
    Number(k<4),Number(k===7)]:
   [Number(k<4),Number(k===5),Number(k===4||k===5),[2,2,2,2,6,6,4][k]];
  for(let c=0;c<categories.length;c++){
   totals[c]+=units[c];loads[p][c]+=units[c];
  }
 }
 let score=0;
 for(let c=0;c<categories.length;c++)
  for(let p=0;p<t.staff;p++)
   score+=weights[categories[c]]*
    Math.abs(filled*loads[p][c]-totals[c]*counts[p]);
 return score;
}
function independentlyAudit(t,res){
 if(!["OPTIMAL","FEASIBLE"].includes(res.status))
  throw Error("未取得合法求解結果："+res.status);
 if(!Array.isArray(res.assignments)||res.assignments.length!==t.shifts)
  throw Error("回傳班次被截斷");
 const slots=HOURS[t.pool].length;
 const per=Array.from({length:t.staff},()=>[]);
 const counts=Array(t.staff).fill(0);
 for(let i=0;i<t.shifts;i++){
  const p=res.assignments[i];
  if(!Number.isInteger(p)||p<-1||p>=t.staff)throw Error("人員索引無效");
  if(p>=0){
   if(t.mask[i*t.staff+p]!=="1")throw Error("沒有排班資格");
   counts[p]++;
   per[p].push({day:Math.floor(i/slots)+1,slot:i%slots,
     start:HOURS[t.pool][i%slots][0],end:HOURS[t.pool][i%slots][1]});
  }
  if(t.pins[i]===-1&&p!==-1)throw Error("固定空班遭變更");
  if(t.pins[i]>=0&&p!==t.pins[i])throw Error("人工固定遭變更");
 }
 for(const duties of per){
  const eachDay=new Map();
  for(const d of duties)eachDay.set(d.day,(eachDay.get(d.day)||0)+1);
  if([...eachDay.values()].some(n=>n>(t.pool==="door"?3:1)))
   throw Error("同日超過最多班數");
  for(let i=0;i<duties.length;i++)for(let j=i+1;j<duties.length;j++){
   const a=duties[i],b=duties[j],gap=Math.abs(a.day-b.day);
   if(gap===1)throw Error("違反站一歇一");
   if(gap<=2&&a.slot===b.slot)throw Error("同班號兩日內重複");
   function standby(v){
    const sunday=new Date(Date.UTC(t.year,t.month-1,v.day)).getUTCDay()===0;
    return sunday&&(t.pool==="door"?(v.start>=6&&v.start<20):v.slot===6);
   }
   if(gap===7&&standby(a)&&standby(b))throw Error("連續兩週日留守");
   if(gap===0&&t.pool==="officer")throw Error("安官同日多班");
   if(gap===0&&t.pool==="door"&&
     !(a.end+6<=b.start||b.end+6<=a.start))
    throw Error("大門同日休息不足六小時");
  }
 }
 const filled=res.assignments.filter(v=>v>=0).length;
 if(filled!==t.expectedFill||res.filled!==filled||
    res.missing!==t.shifts-filled)throw Error("破壞原有合法填班數");
 if(!Array.isArray(res.actual_counts)||
    counts.some((v,i)=>v!==res.actual_counts[i]))
   throw Error("每人實站班數不一致");
 const cost=counts.reduce((v,n,i)=>v+Math.abs(n-t.targets[i]),0);
 if(cost!==res.final_abs_deviation||cost>res.phase1_abs_deviation)
   throw Error("公平階段未改善或保持原本偏差");
 if(!["OPTIMAL","FEASIBLE"].includes(res.fill_phase)||
    !["OPTIMAL","FEASIBLE","UNKNOWN"].includes(res.fair_phase))
   throw Error("求解階段標記異常");
 if(res.status==="OPTIMAL"&&
   !(res.fill_optimal_proven===true&&res.fair_optimal_proven_given_fill===true))
   throw Error("錯誤宣稱全域最佳");
 if(t.id==="tiny"&&cost!==0)throw Error("四班精確總班數公平偏差不為零");
 if(res.fixed_occupied_positions!==true)
  throw Error("第三階段未保護既有已填班位");
 if(!["OPTIMAL","FEASIBLE","UNKNOWN"].includes(res.hardship_phase))
  throw Error("第三階段狀態無效");
 if(res.hardship_optimal_proven_given_locked_predecessors===true&&
    res.hardship_phase!=="OPTIMAL")
  throw Error("錯誤宣稱艱苦哨最優");
 const harsh=hardshipScore(t,res.assignments);
 if(harsh!==res.hardship_final_score||
    harsh>res.hardship_initial_score)
  throw Error("獨立艱苦哨負擔核對失敗");
 if(res.hardship_improved!==(harsh<res.hardship_initial_score))
  throw Error("艱苦哨改善狀態不實");
 if(res.status==="OPTIMAL"&&
   !(res.fill_optimal_proven===true&&
     res.fair_optimal_proven_given_fill===true&&
     res.hardship_optimal_proven_given_locked_predecessors===true))
  throw Error("錯誤宣稱三階段皆最優");
 if(t.id==="tiny"&&harsh!==t.oracleBest)
  throw Error("四班獨立窮舉最佳負擔未達成");

 return {filled,missing:t.shifts-filled,final_cost:cost,
         start_cost:res.phase1_abs_deviation,
         fill_phase:res.fill_phase,fair_phase:res.fair_phase,
         fair_optimal_proven:res.fair_optimal_proven_given_fill===true,
         hardship_phase:res.hardship_phase,
         hardship_initial_score:res.hardship_initial_score,
         hardship_final_score:harsh,
         hardship_optimal_proven:res.hardship_optimal_proven_given_locked_predecessors===true};
}
const btn=document.getElementById("run");
const status=document.getElementById("status"),out=document.getElementById("output");
const summary=document.getElementById("summary");
const vacancyDetails=document.getElementById("vacancy-details");
const vacancyTitle=document.getElementById("vacancy-title");
const vacancyList=document.getElementById("vacancy-list");
const rosterDetails=document.getElementById("roster-preview");
const rosterDays=document.getElementById("roster-days");
const combinedBtn=document.getElementById("combined-run");
const combinedStatus=document.getElementById("combined-status");
const combinedDetails=document.getElementById("combined-preview");
const combinedDays=document.getElementById("combined-days");
const combinedOutput=document.getElementById("combined-output");
const combinedCases=["door-forced-vacancies","officer-blackouts-no-hints"];
const acceptedSynthetic=new Map();
function clearCombinedView(){
 combinedDetails.hidden=true;combinedDetails.open=false;combinedDays.replaceChildren();
 combinedOutput.textContent="尚無本次合併預覽";
}
function updateCombinedReadiness(){
 combinedBtn.disabled=!combinedCases.every(id=>acceptedSynthetic.has(id));
 combinedStatus.textContent=combinedBtn.disabled?
  "請先成功求解安官整月與大門強制缺班情境":
  "兩個虛構月份已分別求解與驗證，可建立 589 班合併預覽";
}
let runtime=null;
select.addEventListener("change",()=>{
 clearCombinedView();updateCombinedReadiness();
 status.textContent="已切換情境，請重新執行求解";
 summary.textContent="尚無這個情境的已驗證結果";
 out.textContent="沒有這個情境的求解結果";
 vacancyDetails.hidden=true;vacancyDetails.open=false;vacancyList.replaceChildren();
 rosterDetails.hidden=true;rosterDetails.open=false;rosterDays.replaceChildren();
});
btn.addEventListener("click",async()=>{
 clearCombinedView();
 const selected=select.value;
 if(combinedCases.includes(selected))acceptedSynthetic.delete(selected);
 updateCombinedReadiness();
 btn.disabled=true;status.textContent="正在本機執行三階段求解…";
 out.textContent="尚待獨立驗證";summary.textContent="正在計算，尚無已驗證班表";
 vacancyDetails.hidden=true;vacancyDetails.open=false;vacancyList.replaceChildren();
 rosterDetails.hidden=true;rosterDetails.open=false;rosterDays.replaceChildren();
 await new Promise(ok=>requestAnimationFrame(ok));
 const start=Date.now();
 try{
  if(typeof createMonthHardshipModule!=="function")throw Error("缺少真正 CP-SAT 模組");
  if(!runtime){
   const wasm=toBytes(ENCODED);
   if(!WebAssembly.validate(wasm))throw Error("WASM 驗證失敗");
   runtime=await createMonthHardshipModule({wasmBinary:wasm,
      print:()=>{},printErr:e=>console.error(String(e))});
  }
  const t=CASES.find(t=>t.id===select.value);
  if(!t)throw Error("找不到虛構情境");
  const got=JSON.parse(runtime.ccall("solve_guard_month_harsh_v4",
      "string",["string"],[serialize(t)]));
  const verified=independentlyAudit(t,got);
  const vacancies=got.assignments.flatMap((p,i)=>p===-1?[{day:Math.floor(i/HOURS[t.pool].length)+1,slot:i%HOURS[t.pool].length+1}]:[]);
  if(vacancies.length!==verified.missing)throw Error("缺班清單與獨立驗證不一致");
  summary.textContent="已排 "+verified.filled+" 班｜缺班 "+verified.missing+" 班"+
    (vacancies.length?"｜缺班位置："+vacancies.slice(0,12).map(v=>v.day+"日第"+v.slot+"班").join("、")+(vacancies.length>12?"…（完整清單見下方）":""):"");
  const grouped=new Map();
  for(const v of vacancies){
   if(!grouped.has(v.day))grouped.set(v.day,[]);
   const [start,end]=HOURS[t.pool][v.slot-1];
   grouped.get(v.day).push("第"+v.slot+"班（"+String(start).padStart(2,"0")+":00–"+
     String(end).padStart(2,"0")+":00）");
  }
  vacancyTitle.textContent="查看完整缺班清單（"+vacancies.length+"班／"+grouped.size+"天）";
  for(const [day,slots] of grouped){
   const li=document.createElement("li");
   li.textContent=day+"日："+slots.join("、");
   vacancyList.appendChild(li);
  }
  vacancyDetails.open=false;vacancyDetails.hidden=vacancies.length===0;
  const totalSlots=HOURS[t.pool].length;
  for(let day=1;day<=Math.ceil(t.shifts/totalSlots);day++){
   const section=document.createElement("section");section.className="roster-day";
   const title=document.createElement("strong");
   title.textContent=t.year+"/"+t.month+"/"+day+"（虛構）";
   const list=document.createElement("ul");
   for(let slot=1;slot<=totalSlots;slot++){
    const i=(day-1)*totalSlots+slot-1,p=got.assignments[i];
    const [start,end]=HOURS[t.pool][slot-1];
    const li=document.createElement("li");
    li.textContent="第"+slot+"班 "+String(start).padStart(2,"0")+":00–"+
      String(end).padStart(2,"0")+":00｜"+(p<0?"缺班":"虛構人員 #"+(p+1));
    list.appendChild(li);
   }
   section.append(title,list);rosterDays.appendChild(section);
  }
  rosterDetails.hidden=false;rosterDetails.open=false;
  if(combinedCases.includes(t.id)){
   acceptedSynthetic.set(t.id,{t,got,verified});
   updateCombinedReadiness();
  }
  status.textContent="✅ 真正 WASM 三階段合法填班與艱苦公平檢查通過";
  out.textContent=JSON.stringify({accepted:true,scenario:t.id,
   status:got.status,shifts:t.shifts,staff:t.staff,
   filled:verified.filled,missing:verified.missing,
   vacancies,
   phase1_abs_deviation:verified.start_cost,
   final_abs_deviation:verified.final_cost,
   fill_phase:verified.fill_phase,fair_phase:verified.fair_phase,
   fairness_optimal_proven:verified.fair_optimal_proven,
   hardship_phase:verified.hardship_phase,
   hardship_initial_score:verified.hardship_initial_score,
   hardship_final_score:verified.hardship_final_score,
   hardship_optimal_proven:verified.hardship_optimal_proven,
   elapsed_ms:Date.now()-start,runtime:"this-device",
   real_iphone_safari_verified:false,
   operationally_certified:false},null,2);
 }catch(err){
  status.textContent="❌ 本機三階段求解／獨立驗證失敗";
  summary.textContent="未產生可驗證班表，禁止採用結果";
  vacancyDetails.hidden=true;vacancyDetails.open=false;vacancyList.replaceChildren();
 rosterDetails.hidden=true;rosterDetails.open=false;rosterDays.replaceChildren();
  out.textContent=String(err&&err.stack||err);
 }finally{btn.disabled=false;}
});
combinedBtn.addEventListener("click",()=>{
 clearCombinedView();
 combinedStatus.textContent="正在重新獨立核對兩個虛構勤務…";
 try{
  if(!combinedCases.every(id=>acceptedSynthetic.has(id)))throw Error("缺少已驗證雙勤務結果");
  const door=acceptedSynthetic.get("door-forced-vacancies");
  const officer=acceptedSynthetic.get("officer-blackouts-no-hints");
  const entries=[["door",door],["officer",officer]];
  let year=null,month=null,filled=0,missing=0,total=0;
  const rows={door:[],officer:[]};
  for(const [pool,data] of entries){
   if(!data||data.t.pool!==pool||data.t.synthetic_only!==true)
    throw Error("虛構資料類別驗證失敗");
   const t=data.t,got=data.got;
   if(year===null){year=t.year;month=t.month;}
   if(t.year!==year||t.month!==month)throw Error("不得混合不同月份");
   const count=new Date(Date.UTC(year,month,0)).getUTCDate()*HOURS[pool].length;
   if(t.shifts!==count)throw Error("勤務月份班次不完整");
   const v=independentlyAudit(t,got);
   if(v.filled!==data.verified.filled||v.missing!==data.verified.missing)
    throw Error("與先前已核對結果不同");
   const slots=HOURS[pool].length;
   for(let i=0;i<got.assignments.length;i++){
    const person=got.assignments[i],day=Math.floor(i/slots)+1,slot=i%slots+1;
    const serial=Date.UTC(year,month-1,day)/86400000;
    if(!Number.isInteger(serial))throw Error("預覽日期序號異常");
    const syntheticId=person<0?null:
      "SIM_"+(pool==="door"?"D":"O")+"_"+String(person).padStart(3,"0");
    rows[pool].push([serial,slot,syntheticId]);
   }
   filled+=v.filled;missing+=v.missing;total+=count;
  }
  if(total!==589||filled!==577||missing!==12||
     rows.door.length!==372||rows.officer.length!==217)
   throw Error("雙勤務填班或缺班數與證明不符");
  for(const [pool] of entries){
   const heading=document.createElement("h3");
   heading.textContent=pool==="door"?"大門衛哨（虛構）":"安全士官（虛構）";
   combinedDays.appendChild(heading);
   const slots=HOURS[pool].length;
   for(let day=1;day<=new Date(Date.UTC(year,month,0)).getUTCDate();day++){
    const section=document.createElement("section");section.className="roster-day";
    const title=document.createElement("strong");
    title.textContent=year+"/"+month+"/"+day;
    const list=document.createElement("ul");
    for(let k=0;k<slots;k++){
     const [serial,slot,person]=rows[pool][(day-1)*slots+k];
     const li=document.createElement("li");
     const [start,end]=HOURS[pool][k];
     li.textContent="第"+slot+"班 "+String(start).padStart(2,"0")+":00–"+
      String(end).padStart(2,"0")+":00｜"+(person===null?"缺班":person);
     list.appendChild(li);
    }
    section.append(title,list);combinedDays.appendChild(section);
   }
  }
  if(combinedDays.querySelectorAll("li").length!==total)
   throw Error("合併預覽漏掉班次");
  combinedOutput.textContent=JSON.stringify({
   accepted:true,format:"guard-cpsat-synthetic-preview-v1",
   schema_shape:"v7-month-schedule-rows-v1",
   month:year+"-"+String(month).padStart(2,"0"),rows:total,
   filled,missing,door_rows:rows.door.length,officer_rows:rows.officer.length,
   synthetic_only:true,preview_only:true,importable_as_v7_backup:false,
   operationally_certified:false,full_v7_rule_parity_verified:false,
   real_iphone_safari_verified:false
  },null,2);
  combinedDetails.hidden=false;combinedDetails.open=false;
  combinedStatus.textContent="✅ 589 班虛構合併預覽已通過獨立核對；缺班 "+missing+" 班";
 }catch(e){
  clearCombinedView();combinedStatus.textContent="❌ 合併預覽拒絕使用";
  combinedOutput.textContent=String(e&&e.message||e);
 }
});
</script></body></html>"""


def make(js, wasm_b64, proof, fixtures, out):
    # No user-supplied records; preserve generated glue without script breakout.
    js = re.sub(r"</script", r"<\/script", js, flags=re.IGNORECASE)
    chunks = [wasm_b64[i:i+4096] for i in range(0, len(wasm_b64), 4096)]
    text = (HTML.replace("__GLUE__", js)
            .replace("__WASM_PARTS__", " +\n".join(json.dumps(x) for x in chunks))
            # JSON is inside a script element: escape HTML/script breakers
            # even when the fixture is tied to a genuine Node proof digest.
            .replace("__CASES__", json.dumps(fixtures["cases"], ensure_ascii=False)
                     .replace("&", r"\u0026")
                     .replace("<", r"\u003c")
                     .replace(">", r"\u003e"))
            .replace("__WASM_SHA__", proof["wasm_sha256"]))
    target = Path(out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"Verified synthetic three-stage hardship offline HTML: {target} ({target.stat().st_size:,} bytes)")


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit("Usage: python build/package_month_hardship_wasm.py module.js module.wasm node_proof.json synthetic_fixtures.json out.html")
    glue, binary, proof, fixtures = verify(*sys.argv[1:5])
    make(glue, binary, proof, fixtures, sys.argv[5])
