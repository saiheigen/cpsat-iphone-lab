#!/usr/bin/env python3
"""Fail-closed offline dynamic-assignment CP-SAT packaging.

Consumes only outputs from a *genuinely executed* Node+WASM test, checked
against independent enumerations and SHA-256 digests. Never input real duty
data. This makes a 64-shift prototype browser test, NOT a 589-shift product.
"""
import base64
import hashlib
import json
from pathlib import Path
import re
import sys

SCENARIOS = {
    "four-shifts-two-people": ("OPTIMAL", 4),
    "one-person-all-conflicts": ("OPTIMAL", 1),
    "eligibility-and-forced-blank": ("OPTIMAL", 2),
    "conflicting-fixed-shifts": ("INFEASIBLE", None),
}
HASH = lambda data: hashlib.sha256(data).hexdigest()


def verify(js_path, wasm_path, proof_path):
    js = Path(js_path).read_bytes()
    wasm = Path(wasm_path).read_bytes()
    report = json.loads(Path(proof_path).read_text("utf-8"))
    if not wasm.startswith(b"\x00asm\x01\x00\x00\x00"):
        raise ValueError("Not a WebAssembly v1 binary")
    if b"createAssignmentModule" not in js:
        raise ValueError("No dynamic assignment module factory found")
    if not (report.get("accepted") is True and
            report.get("engine") == "genuine-ORTools-CP-SAT-in-WASM" and
            report.get("contract") == "bounded-dynamic-assignment-v1" and
            report.get("invalid_input_cases", 0) >= 4):
        raise ValueError("Genuine dynamic solver proof missing")
    if report.get("operationally_certified") is not False or report.get("full_589_shift_model") is not False:
        raise ValueError("Untrue production certification flag")
    if HASH(js) != report.get("js_sha256") or HASH(wasm) != report.get("wasm_sha256"):
        raise ValueError("Dynamic Node proof SHA-256 mismatches supplied binaries")
    seen = {}
    if not isinstance(report.get("tests"), list):
        raise ValueError("Missing scenario proof")
    for test in report["tests"]:
        if not isinstance(test, dict):
            raise ValueError("Malformed scenario proof")
        name = test.get("name")
        if name in seen or name not in SCENARIOS or test.get("accepted") is not True:
            raise ValueError("Unknown or duplicated scenario result")
        expected_status, expected_fill = SCENARIOS[name]
        if test.get("status") != expected_status:
            raise ValueError("Wrong solver status in scenario proof")
        if test.get("got_filled") != expected_fill:
            raise ValueError("Wrong maximum fill in scenario proof")
        if test.get("oracle_max_fill") != (-1 if expected_fill is None else expected_fill):
            raise ValueError("Independent oracle mismatch")
        seen[name] = True
    if set(seen) != set(SCENARIOS):
        raise ValueError("Missing independent oracle scenarios")
    return js.decode("utf-8"), base64.b64encode(wasm).decode("ascii"), report


TEMPLATE = r"""<!doctype html><html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>真正 CP-SAT WASM 動態班次測試</title>
<style>
*{box-sizing:border-box}body{margin:0;padding:16px;color:#183047;background:#f0f4f7;
font:16px/1.65 -apple-system,BlinkMacSystemFont,sans-serif}
main{max-width:620px;margin:12px auto;background:#fff;border-radius:16px;padding:20px}
h1{font-size:22px;line-height:1.4}p{margin:10px 0}label{display:block;margin:14px 0 8px}
select,button{width:100%;padding:14px;border-radius:10px;font-size:16px}
button{background:#126683;color:white;font-weight:bold;border:0;margin-top:12px}
button:disabled{opacity:.55}.caution{background:#fff1dc;border-radius:9px;padding:12px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf3f7;border-radius:8px;
padding:12px;font-size:12px}small{overflow-wrap:anywhere;display:block;color:#667985}
</style></head><body><main>
<h1>真正 CP-SAT WASM｜動態班次驗證</h1>
<p class="caution">只提供<strong>虛構、匿名、限量</strong>的班次例題。
這不是完整軍務排哨系統；最多 64 班／24 人的求解接口，
不能上傳真實名冊、不能匯入或覆寫已核定班表。</p>
<label for="scenario">選擇虛構指派問題</label>
<select id="scenario">
<option value="four">4 班／2 人：衝突限制</option>
<option value="single">3 班／1 人：強制空白</option>
<option value="elig">3 班／2 人：資格與指定人員</option>
<option value="infeasible">2 班／1 人：固定勤務互相衝突</option>
</select>
<button id="run">在本機執行真正 CP-SAT 求解</button>
<p id="status" role="status">尚未執行</p><pre id="output">沒有結果</pre>
<small>JS SHA-256: __JS_HASH__</small>
<small>WASM SHA-256: __WASM_HASH__</small>
</main><script>__GLUE__</script><script>
'use strict';
const BASE64=__B64__;
const TESTS={
 four:{tasks:4,staff:2,allowed:[1,1,1,1,1,1,1,1],
       conflicts:[[0,1],[2,3]],pins:[-2,-2,-2,-2]},
 single:{tasks:3,staff:1,allowed:[1,1,1],
       conflicts:[[0,1],[0,2],[1,2]],pins:[0,-2,-1]},
 elig:{tasks:3,staff:2,allowed:[1,0,0,1,1,1],
       conflicts:[[0,2]],pins:[0,-2,-1]},
 infeasible:{tasks:2,staff:1,allowed:[1,1],
       conflicts:[[0,1]],pins:[0,0]}
};
function serialize(t){
 return ['assignment-v1',t.tasks+' '+t.staff,
         t.allowed.join(''),t.conflicts.map(p=>p.join(':')).join(';'),
         t.pins.join(',')].join('\n')+'\n';
}
function oracle(t){
 let best=-1,a=Array(t.tasks).fill(-1);
 function search(i){
  if(i===t.tasks){
   if(t.conflicts.some(([x,y])=>a[x]>=0&&a[x]===a[y]))return;
   best=Math.max(best,a.filter(x=>x>=0).length);return;
  }
  for(let p=-1;p<t.staff;p++){
   if(p>=0&&!t.allowed[i*t.staff+p])continue;
   if(t.pins[i]===-1&&p!==-1)continue;
   if(t.pins[i]>=0&&p!==t.pins[i])continue;
   a[i]=p;search(i+1);
  }
 }
 search(0);return best;
}
function independentlyAudit(t,got){
 if(!Array.isArray(got.assignments)||got.assignments.length!==t.tasks)
  throw Error('求解器未回傳完整班表');
 let count=0;
 for(let i=0;i<t.tasks;i++){
  const p=got.assignments[i];
  if(!Number.isInteger(p)||p<-1||p>=t.staff)throw Error('人員編號無效');
  if(p>=0){
   count++;
   if(!t.allowed[i*t.staff+p])throw Error('排入沒有資格的人員');
  }
  if(t.pins[i]===-1&&p!==-1)throw Error('強制空白被改動');
  if(t.pins[i]>=0&&p!==t.pins[i])throw Error('指定人員被改動');
 }
 for(const [x,y] of t.conflicts)
  if(got.assignments[x]>=0&&got.assignments[x]===got.assignments[y])
   throw Error('同一人排入衝突班次');
 if(got.filled!==count||got.missing!==t.tasks-count)
  throw Error('填班數量錯誤');
 return count;
}
function decode(s){
 const raw=atob(s),bytes=new Uint8Array(raw.length);
 for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);
 return bytes;
}
document.getElementById('run').addEventListener('click',async()=>{
 const btn=document.getElementById('run'),status=document.getElementById('status'),
       output=document.getElementById('output');
 btn.disabled=true;status.textContent='正在本機求解…';output.textContent='尚未驗證';
 await new Promise(ok=>requestAnimationFrame(ok));
 const start=Date.now();
 try{
  if(typeof WebAssembly==='undefined')throw Error('此瀏覽器不支援 WASM');
  if(typeof createAssignmentModule!=='function')throw Error('缺少真正 CP-SAT 入口');
  const wasm=decode(BASE64);
  if(!WebAssembly.validate(wasm))throw Error('WASM 格式驗證失敗');
  const mod=await createAssignmentModule({wasmBinary:wasm,
      print:()=>{},printErr:x=>console.error(String(x))});
  const t=TESTS[document.getElementById('scenario').value];
  const got=JSON.parse(mod.ccall('solve_assignment_v1','string',['string'],[serialize(t)]));
  const best=oracle(t);
  if(got.status!==(best<0?'INFEASIBLE':'OPTIMAL'))
    throw Error('CP-SAT 結果不符合獨立窮舉');
  if(best>=0&&independentlyAudit(t,got)!==best)
    throw Error('CP-SAT 填班數不是最佳');
  status.textContent='✅ 本機動態 CP-SAT 指派驗證通過（僅虛構小題）';
  output.textContent=JSON.stringify({accepted:true,status:got.status,
    filled:got.filled??null,oracle_max_fill:best,scenario:
    document.getElementById('scenario').value,elapsed_ms:Date.now()-start,
    runtime:'this-device',real_iphone_verified:false},null,2);
 }catch(e){
  status.textContent='❌ 本機測試失敗';
  output.textContent=String(e&&e.stack||e);
 }finally{btn.disabled=false}
});
</script></body></html>"""


def package(js_file, wasm_file, proof_file, output_file):
    js, b64, proof = verify(js_file, wasm_file, proof_file)
    # JS comments or strings may contain a script terminator. Never let
    # generated Emscripten glue break out of its inline script element.
    js = re.sub(r"</script", r"<\/script", js, flags=re.IGNORECASE)
    chunks = [b64[i:i + 4096] for i in range(0, len(b64), 4096)]
    page = (TEMPLATE.replace("__GLUE__", js)
            .replace("__B64__", " +\n".join(json.dumps(x) for x in chunks))
            .replace("__JS_HASH__", proof["js_sha256"])
            .replace("__WASM_HASH__", proof["wasm_sha256"]))
    out = Path(output_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"Dynamic offline CP-SAT page: {out} ({out.stat().st_size:,} bytes)")
    print("Genuine Node WASM: VERIFIED. Safari iPhone hardware: NOT TESTED.")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("Usage: python build/package_dynamic_assignment.py glue.js solver.wasm proof.json out.html")
    package(*sys.argv[1:])
