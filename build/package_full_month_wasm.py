#!/usr/bin/env python3
"""Proof-gated offline HTML for experimental 589-shift CP-SAT WebAssembly.

Only synthetic fixtures; NEVER a production rostering interface. The bundle
does not accept names, leave records, real duty information or file imports.
A real Node WASM run plus independent audit and matching SHA-256 are mandatory.
Even success here does not establish iPhone Safari hardware compatibility.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re
import sys


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


CASES = {
    "synthetic-full-month-unique-candidates-door": (372, 56, 372),
    "synthetic-full-month-unique-candidates-officer": (217, 50, 217),
    "adjacent-day-fixed-infeasible": (None, None, None),
    "two-legal-same-Sunday-shifts": (None, None, 2),
    "consecutive-Sunday-standby-infeasible": (None, None, None),
}


def verify(js_path, wasm_path, proof_path):
    js = Path(js_path).read_bytes()
    wasm = Path(wasm_path).read_bytes()
    proof = json.loads(Path(proof_path).read_text("utf-8"))
    if not wasm.startswith(b"\x00asm\x01\x00\x00\x00"):
        raise ValueError("Not a genuine WebAssembly v1 binary")
    if b"createMonthModule" not in js:
        raise ValueError("Missing full-calendar Emscripten factory")
    if _sha(js) != proof.get("js_sha256") or _sha(wasm) != proof.get("wasm_sha256"):
        raise ValueError("Full-month Node proof does not match JS/WASM bytes")
    if (proof.get("accepted") is not True or
            proof.get("engine") != "genuine-ORTools-CP-SAT-WASM" or
            proof.get("contract") != "guard-month-v2" or
            proof.get("synthetic_full_month_shifts_tested") != 589 or
            proof.get("synthetic_staff_tested") != 106 or
            proof.get("all_operational_rules_tested") is not False or
            proof.get("dense_full_month_performance_verified") is not False or
            proof.get("real_iphone_safari_verified") is not False):
        raise ValueError("No trusted, correctly scoped full-month Node proof")
    cases = proof.get("cases")
    if not isinstance(cases, list) or len(cases) != len(CASES):
        raise ValueError("Missing or duplicate month test cases")
    checked = {}
    for item in cases:
        if not isinstance(item, dict):
            raise ValueError("Malformed month case")
        key = item.get("name")
        if key not in CASES or key in checked or item.get("accepted") is not True:
            raise ValueError("Unknown or repeated full-month test")
        tasks, staff, filled = CASES[key]
        if filled is None:
            if item.get("status") != "INFEASIBLE":
                raise ValueError("Known impossible case was not rejected")
        else:
            if item.get("status") not in ("OPTIMAL", "FEASIBLE"):
                raise ValueError("Known legal case was not actually solved")
            if item.get("filled") != filled:
                raise ValueError("Wrong independently audited fill count")
        if tasks is not None and (item.get("shifts") != tasks or item.get("staff") != staff):
            raise ValueError("Full-month geometry was not verified")
        checked[key] = True
    return js.decode("utf-8"), base64.b64encode(wasm).decode("ascii"), proof


PAGE = r"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>真正 CP-SAT 589 班 WASM｜離線驗證</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f0f4f8;color:#153248;
font:16px/1.6 -apple-system,BlinkMacSystemFont,system-ui,sans-serif;padding:16px}
main{max-width:680px;margin:16px auto;background:white;padding:22px;border-radius:18px}
h1{font-size:23px;line-height:1.35}label{display:block;margin-top:18px}
select,button{width:100%;padding:14px;border-radius:11px;font-size:16px}
button{background:#0d6589;color:white;border:0;font-weight:700;margin-top:14px}
button:disabled{opacity:.55}.warn{background:#fff0d8;padding:13px;border-radius:10px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf4f8;
border-radius:9px;padding:13px;font-size:12px}small{display:block;overflow-wrap:anywhere}
</style></head><body><main>
<h1>589 班｜真正 CP-SAT WebAssembly 實驗</h1>
<p class="warn">⚠️ <strong>這不是正式軍務排哨系統。</strong>
只能使用完全虛構的固定案例，不能匯入名冊、休假或核定班表。
589 班使用每班只有一名候選人的簡化範例，不能推論真實人力或公平。
手機上求解可能暫時凍結畫面，請勿在重要作業時執行。</p>
<label for="scenario">選擇離線驗證情境</label>
<select id="scenario">
<option value="door">2026/12 大門 372 班／56 名虛構人員</option>
<option value="officer">2026/12 安官 217 班／50 名虛構人員</option>
<option value="adjacent">連續兩日強制值勤：應無解</option>
<option value="same-sunday">同週日合法雙班：應填 2 班</option>
<option value="next-sunday">連續兩週週日留守：應無解</option>
</select>
<button id="run">在本機執行真正 CP-SAT WASM</button>
<p id="status" role="status">尚未執行</p>
<pre id="output">尚無求解結果</pre>
<small>WASM SHA-256：__WASM_SHA__</small>
</main>
<script>__GLUE__</script>
<script>
'use strict';
const RAW=__WASM_PARTS__;
const HOURS={door:[[22,24],[0,2],[2,4],[4,6],[6,8],[8,10],[10,12],
 [12,14],[14,16],[16,18],[18,20],[20,22]],
 officer:[[22,24],[0,2],[2,4],[4,6],[6,12],[12,18],[18,22]]};
const countDays=(y,m)=>new Date(Date.UTC(y,m,0)).getUTCDate();
function monthFixture(pool){
 const slots=HOURS[pool].length,staff=pool==='door'?56:50,
       group=pool==='door'?28:25,days=31;
 let mask='',pins=[],hints=[],reference=[];
 for(let day=1;day<=days;day++){
  const cycle=Math.floor((day-1)/2),parity=(day-1)%2;
  for(let k=0;k<slots;k++){
   const person=parity*group+(k+cycle)%group;
   for(let p=0;p<staff;p++)mask+=p===person?'1':'0';
   pins.push(-2);hints.push(person);reference.push(person);
  }
 }
 return {year:2026,month:12,pool,staff,
         shifts:slots*days,mask,pins,hints,reference};
}
function sparse(pool,items){
 const year=2026,month=11,slots=HOURS[pool].length,
       shifts=slots*countDays(year,month),staff=1;
 let mask=Array(shifts).fill('0'),pins=Array(shifts).fill(-2),
     hints=Array(shifts).fill(-1);
 for(const item of items){
  const slot=(item[0]-1)*slots+(item[1]-1);
  mask[slot]='1';if(item[2])pins[slot]=0;
 }
 return {year,month,pool,staff,shifts,mask:mask.join(''),pins,hints};
}
function fixture(kind){
 if(kind==='door'||kind==='officer')return monthFixture(kind);
 if(kind==='adjacent')return sparse('officer',[[1,5,true],[2,5,true]]);
 if(kind==='same-sunday')return sparse('door',[[1,5,false],[1,9,false]]);
 if(kind==='next-sunday')return sparse('door',[[1,5,true],[8,5,true]]);
 throw Error('不支援此測試情境');
}
function payload(t){
 return ['guard-month-v2',String(t.year)+'-'+String(t.month).padStart(2,'0'),
 t.pool,String(t.shifts)+' '+String(t.staff),
 t.mask,t.pins.join(','),t.hints.join(',')].join('\n')+'\n';
}
function sunday(t,day){
 return new Date(Date.UTC(t.year,t.month-1,day)).getUTCDay()===0;
}
function audit(t,got){
 const a=got.assignments,slots=HOURS[t.pool].length;
 if(!Array.isArray(a)||a.length!==t.shifts)throw Error('輸出班次數錯誤');
 const byPerson=Array.from({length:t.staff},()=>[]);
 for(let i=0;i<t.shifts;i++){
  const p=a[i];
  if(!Number.isInteger(p)||p<-1||p>=t.staff)throw Error('無效人員索引');
  if(p>=0){
   if(t.mask[i*t.staff+p]!=='1')throw Error('違反人員資格');
   byPerson[p].push({day:Math.floor(i/slots)+1,slot:i%slots,
     start:HOURS[t.pool][i%slots][0],end:HOURS[t.pool][i%slots][1]});
  }
  if(t.pins[i]===-1&&p!==-1)throw Error('指定缺班遭覆寫');
  if(t.pins[i]>=0&&p!==t.pins[i])throw Error('指定人員遭覆寫');
 }
 for(const duties of byPerson){
  const daily=new Map();
  for(const x of duties)daily.set(x.day,(daily.get(x.day)||0)+1);
  if([...daily.values()].some(n=>n>(t.pool==='door'?3:1)))
   throw Error('同日排班超過限制');
  for(let i=0;i<duties.length;i++)for(let j=i+1;j<duties.length;j++){
   const x=duties[i],y=duties[j],days=Math.abs(x.day-y.day);
   if(days===1)throw Error('違反站一歇一');
   if(days<=2&&x.slot===y.slot)throw Error('兩日內同班號重複');
   function standby(z){
    return sunday(t,z.day)&&(t.pool==='door'?
      z.start>=6&&z.start<20:z.slot===6);
   }
   if(days===7&&standby(x)&&standby(y))throw Error('連續兩週週日留守');
   if(days===0&&t.pool==='officer')throw Error('安官同日多班');
   if(days===0&&t.pool==='door'&&
      !(x.end+6<=y.start||y.end+6<=x.start))
     throw Error('大門同日間隔不足六小時');
  }
 }
 const filled=a.filter(p=>p>=0).length;
 if(filled!==got.filled||t.shifts-filled!==got.missing)
  throw Error('填班與缺班計算有誤');
 return filled;
}
function wasmBytes(b64){
 const text=atob(b64),out=new Uint8Array(text.length);
 for(let i=0;i<text.length;i++)out[i]=text.charCodeAt(i);
 return out;
}
const button=document.getElementById('run'),
      statusElement=document.getElementById('status'),
      output=document.getElementById('output');
button.addEventListener('click',async()=>{
 button.disabled=true;
 statusElement.textContent='正在本機求解；畫面可能暫時沒有反應…';
 output.textContent='尚待獨立驗證';
 await new Promise(r=>requestAnimationFrame(r));
 const begin=Date.now();
 try{
  if(typeof WebAssembly==='undefined')throw Error('瀏覽器不支援 WASM');
  if(typeof createMonthModule!=='function')throw Error('真正 CP-SAT 入口不存在');
  const binary=wasmBytes(RAW);
  if(!WebAssembly.validate(binary))throw Error('無效 WASM 二進位檔');
  const module=await createMonthModule({wasmBinary:binary,
      print:()=>{},printErr:e=>console.error(String(e))});
  const name=document.getElementById('scenario').value,
        t=fixture(name),got=JSON.parse(module.ccall(
           'solve_guard_month_v2','string',['string'],[payload(t)]));
  let filled=null;
  if(name==='adjacent'||name==='next-sunday'){
   if(got.status!=='INFEASIBLE')throw Error('應為無解，結果卻不是 INFEASIBLE');
  }else{
   if(got.status!=='OPTIMAL'&&got.status!=='FEASIBLE')
    throw Error('CP-SAT 未找到合格結果：'+got.status);
   filled=audit(t,got);
   const expected=name==='same-sunday'?2:t.shifts;
   if(filled!==expected)throw Error('結果與獨立期望不符');
   if(t.reference&&got.assignments.some((v,i)=>v!==t.reference[i]))
    throw Error('完整月份人員與唯一候選人不一致');
  }
  statusElement.textContent='✅ 真正 CP-SAT 離線模型驗證通過（虛構資料）';
  output.textContent=JSON.stringify({accepted:true,scenario:name,
    status:got.status,filled,month:t.year+'-'+String(t.month).padStart(2,'0'),
    shifts:t.shifts,staff:t.staff,elapsed_ms:Date.now()-begin,
    runtime:'this-device',iphone_safari_tested: false,
    operationally_certified:false},null,2);
 }catch(e){
  statusElement.textContent='❌ 本機驗證失敗';
  output.textContent=String(e&&e.stack||e);
 }finally{button.disabled=false;}
});
</script></body></html>"""


def make(js, wasm_b64, proof, out_path):
    js = re.sub(r"</script", r"<\/script", js, flags=re.IGNORECASE)
    parts = [wasm_b64[i:i+4096] for i in range(0, len(wasm_b64), 4096)]
    page = (PAGE.replace("__GLUE__", js)
            .replace("__WASM_PARTS__", " +\n".join(json.dumps(p) for p in parts))
            .replace("__WASM_SHA__", proof["wasm_sha256"]))
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
    print(f"Verified experimental 589-shift WASM HTML: {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("Usage: python build/package_full_month_wasm.py glue.js solver.wasm node_proof.json out.html")
    glue, binary, proof = verify(*sys.argv[1:4])
    make(glue, binary, proof, sys.argv[4])
