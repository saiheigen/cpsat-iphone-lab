#!/usr/bin/env python3
"""Fail-closed SINGLE-FILE 589-shift fair-count WASM browser demo packager.

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

EXPECT = {
    "two-shift-exact-fairness-oracle": (None, None, 2),
    "dense-full-month-door-blackouts-no-hints": (372, 56, 372),
    "dense-full-month-officer-blackouts-no-hints": (217, 50, 217),
    "dense-full-month-door-forced-vacancies": (372, 56, 360),
    "pinned-adjacent-day-conflict": (None, None, None),
}
PAGE_EXPECT = {
    "tiny": (372, 2, 2),
    "door-blackouts-no-hints": (372, 56, 372),
    "officer-blackouts-no-hints": (217, 50, 217),
    "door-forced-vacancies": (372, 56, 360),
}
_sha = lambda b: hashlib.sha256(b).hexdigest()


def verify(js_path, wasm_path, proof_path, fixture_path):
    js = Path(js_path).read_bytes()
    wasm = Path(wasm_path).read_bytes()
    proof = json.loads(Path(proof_path).read_text("utf-8"))
    fixtures = json.loads(Path(fixture_path).read_text("utf-8"))
    if not wasm.startswith(b"\x00asm\x01\x00\x00\x00"):
        raise ValueError("No real WASM binary")
    if b"createMonthFairModule" not in js:
        raise ValueError("Missing actual Emscripten fair-count module")
    if proof.get("js_sha256") != _sha(js) or proof.get("wasm_sha256") != _sha(wasm):
        raise ValueError("WASM/JS bytes do not match genuine Node execution proof")
    expected_flags = {
        "accepted": True,
        "engine": "genuine-Google-OR-Tools-CP-SAT-WASM",
        "contract": "guard-month-fair-v3",
        "two_phases": True,
        "first_stage": "maximize-legal-fill",
        "second_stage": "lock-achieved-fill-and-minimize-absolute-person-count-deviations",
        "full_589_dense_model_tested": True,
        "exact_small_fairness_oracle_verified": True,
        "operationally_certified": False,
        "actual_iphone_safari_tested": False,
        "full_hard_rules_verified": False,
    }
    if any(proof.get(k) != v for k, v in expected_flags.items()):
        raise ValueError("Genuine fair-count CP-SAT proof or scope missing")
    if type(proof.get("rejected_bad_input_cases")) is not int or proof["rejected_bad_input_cases"] < 5:
        raise ValueError("Invalid-input rejection tests missing")
    seen = set()
    cases = proof.get("cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECT):
        raise ValueError("Missing/duplicate real WASM CP-SAT test cases")
    for item in cases:
        if not isinstance(item, dict):
            raise ValueError("Malformed solver proof case")
        name = item.get("name")
        if name not in EXPECT or name in seen or item.get("accepted") is not True:
            raise ValueError("Unknown, fake or repeated solver case")
        tasks, people, filled = EXPECT[name]
        if name == "pinned-adjacent-day-conflict":
            if item.get("status") != "INFEASIBLE" or item.get("fair_phase") != "NOT_RUN":
                raise ValueError("Pinned hard conflict was relaxed")
        elif name == "two-shift-exact-fairness-oracle":
            if (item.get("filled") != 2 or item.get("optimal_fairness") != 0 or
                    item.get("status") != "OPTIMAL"):
                raise ValueError("Small exact fairness optimum was not proved")
        else:
            if item.get("status") not in ("OPTIMAL", "FEASIBLE"):
                raise ValueError("Dense real WASM CP-SAT did not return legal result")
            if (item.get("filled") != filled or
                    item.get("tasks") != tasks or item.get("staff") != people or
                    type(item.get("phase1_cost")) is not int or
                    type(item.get("final_cost")) is not int or
                    item["final_cost"] > item["phase1_cost"]):
                raise ValueError("Dense fair-count solver lost coverage or worsened fairness")
        seen.add(name)
    # A valid JS/WASM SHA alone does not prove the HTML uses the cases
    # the genuine Node solver tested. Bind *exact fixture file bytes* to
    # the independently executed Node acceptance proof.
    manifest_hash = proof.get("fixture_sha256")
    if (not isinstance(manifest_hash, str) or
            not re.fullmatch(r"[0-9a-f]{64}", manifest_hash) or
            _sha(Path(fixture_path).read_bytes()) != manifest_hash):
        raise ValueError("Browser fixtures do not match actual Node WASM proof")
    if (fixtures.get("contract") != "guard-month-fair-v3" or
            fixtures.get("source") != "synthetic-fixtures-no-real-workforce-data"):
        raise ValueError("Untrusted or non-synthetic browser fixtures")
    entries = fixtures.get("cases")
    if not isinstance(entries, list) or len(entries) != len(PAGE_EXPECT):
        raise ValueError("Missing/duplicate browser fixture cases")
    seen = set()
    for item in entries:
        if not isinstance(item, dict) or item.get("id") not in PAGE_EXPECT or item["id"] in seen:
            raise ValueError("Unknown browser fixture")
        name = item["id"]
        shifts, people, fill = PAGE_EXPECT[name]
        if (item.get("synthetic_only") is not True or item.get("shifts") != shifts or
                item.get("staff") != people or item.get("expectedFill") != fill or
                item.get("year") != 2026 or item.get("month") != 12 or
                item.get("pool") not in ("door", "officer")):
            raise ValueError("Incorrect synthetic browser fixture geometry")
        if (not isinstance(item.get("mask"), str) or
                len(item["mask"]) != shifts * people or
                set(item["mask"]) - {"0", "1"} or
                len(item.get("pins", [])) != shifts or
                len(item.get("hints", [])) != shifts or
                len(item.get("targets", [])) != people):
            raise ValueError("Wrong anonymous eligibility or target columns")
        if any(type(x) is not int or x < 0 or x > shifts for x in item["targets"]):
            raise ValueError("Bad fairness integer targets")
        if any(type(x) is not int or x < -2 or x >= people for x in item["pins"]):
            raise ValueError("Bad artificial fixed shifts")
        if any(type(x) is not int or x < -1 or x >= people for x in item["hints"]):
            raise ValueError("Bad artificial hint values")
        seen.add(name)
    return js.decode("utf-8"), base64.b64encode(wasm).decode("ascii"), proof, fixtures


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
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf3f8;border-radius:9px;
padding:13px;font-size:12px}small{display:block;color:#647586;overflow-wrap:anywhere}
</style></head><body><main>
<h1>589 班真正 CP-SAT｜兩階段公平測試</h1>
<p class="notice">⚠️ 僅供虛構資料的離線運算驗證，不是正式軍務排班系統。
不接受名冊、休假或勤務資料輸入，不能核定班表。
先盡量填滿合法班次，再鎖定填班數，才調整每人班數公平。
手機上可能短暫卡頓；本頁不代表已在真正 iPhone Safari 驗收。</p>
<label for="scenario">選擇已驗證的虛構情境</label>
<select id="scenario"></select>
<button id="run">在本機執行真正 WASM 兩階段求解</button>
<p id="status" role="status">尚未執行</p>
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
 return ["guard-month-fair-v3",String(t.year)+"-"+String(t.month).padStart(2,"0"),
 t.pool,String(t.shifts)+" "+String(t.staff),t.mask,t.pins.join(","),
 t.hints.join(","),t.targets.join(",")].join("\n")+"\n";
}
function toBytes(raw){
 const b64=atob(raw),out=new Uint8Array(b64.length);
 for(let i=0;i<b64.length;i++)out[i]=b64.charCodeAt(i);
 return out;
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
 if(t.id==="tiny"&&cost!==0)throw Error("兩班精確公平最佳偏差應為零");
 return {filled,missing:t.shifts-filled,final_cost:cost,
         start_cost:res.phase1_abs_deviation,
         fill_phase:res.fill_phase,fair_phase:res.fair_phase,
         fair_optimal_proven:res.fair_optimal_proven_given_fill===true};
}
const btn=document.getElementById("run");
const status=document.getElementById("status"),out=document.getElementById("output");
let runtime=null;
btn.addEventListener("click",async()=>{
 btn.disabled=true;status.textContent="正在本機執行兩階段求解…";
 out.textContent="尚待獨立驗證";
 await new Promise(ok=>requestAnimationFrame(ok));
 const start=Date.now();
 try{
  if(typeof createMonthFairModule!=="function")throw Error("缺少真正 CP-SAT 模組");
  if(!runtime){
   const wasm=toBytes(ENCODED);
   if(!WebAssembly.validate(wasm))throw Error("WASM 驗證失敗");
   runtime=await createMonthFairModule({wasmBinary:wasm,
      print:()=>{},printErr:e=>console.error(String(e))});
  }
  const t=CASES.find(t=>t.id===select.value);
  if(!t)throw Error("找不到虛構情境");
  const got=JSON.parse(runtime.ccall("solve_guard_month_fair_v3",
      "string",["string"],[serialize(t)]));
  const verified=independentlyAudit(t,got);
  status.textContent="✅ 真正 WASM 兩階段合法填班與公平檢查通過";
  out.textContent=JSON.stringify({accepted:true,scenario:t.id,
   status:got.status,shifts:t.shifts,staff:t.staff,
   filled:verified.filled,missing:verified.missing,
   phase1_abs_deviation:verified.start_cost,
   final_abs_deviation:verified.final_cost,
   fill_phase:verified.fill_phase,fair_phase:verified.fair_phase,
   fairness_optimal_proven:verified.fair_optimal_proven,
   elapsed_ms:Date.now()-start,runtime:"this-device",
   real_iphone_safari_verified:false,
   operationally_certified:false},null,2);
 }catch(err){
  status.textContent="❌ 本機兩階段求解／獨立驗證失敗";
  out.textContent=String(err&&err.stack||err);
 }finally{btn.disabled=false;}
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
    print(f"Verified synthetic fair-count offline HTML: {target} ({target.stat().st_size:,} bytes)")


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit("Usage: python build/package_month_fair_wasm.py module.js module.wasm node_proof.json synthetic_fixtures.json out.html")
    glue, binary, proof, fixtures = verify(*sys.argv[1:5])
    make(glue, binary, proof, fixtures, sys.argv[5])
