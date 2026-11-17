#!/usr/bin/env python3
"""Fail-closed iPhone packaging for real, Node-verified OR-Tools CP-SAT WASM.

This checks the report from an actual Node invocation, matching file hashes,
and a synthetic optimization's independently established unique optimum.
This page does NOT prove iPhone compatibility or monthly roster correctness.
"""
from pathlib import Path
import base64
import hashlib
import json
import re
import sys

def digest(contents):
    return hashlib.sha256(contents).hexdigest()

def verify(jsfile, wasmfile, reportfile):
    js = Path(jsfile).read_bytes()
    wasm = Path(wasmfile).read_bytes()
    report = json.loads(Path(reportfile).read_text("utf-8"))
    if not wasm.startswith(b"\x00asm\x01\x00\x00\x00"):
        raise ValueError("Not a WebAssembly v1 binary")
    if b"createCPSatModule" not in js:
        raise ValueError("Expected CP-SAT factory missing")
    if report.get("accepted") is not True:
        raise ValueError("Real Node CP-SAT smoke test has not passed")
    actual = report.get("solver") or {}
    oracle = report.get("oracle") or {}
    expected = {"engine":"Google OR-Tools CP-SAT","status":"OPTIMAL",
                "desks":0,"tables":3,"profit":90}
    if not all(actual.get(k)==v for k,v in expected.items()):
        raise ValueError("Solver's OPTIMAL sample result is wrong")
    if oracle.get("profit") != 90 or oracle.get("winners") != [{"d":0,"t":3}]:
        raise ValueError("Independent oracle does not confirm unique optimum")
    if digest(js) != report.get("js_sha256"):
        raise ValueError("JS hash does not match real solver report")
    if digest(wasm) != report.get("wasm_sha256"):
        raise ValueError("WASM hash does not match real solver report")
    return js.decode("utf-8"), base64.b64encode(wasm).decode("ascii"), report

TEMPLATE = r"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>iPhone CP-SAT WASM 實機驗證</title>
<style>
*{box-sizing:border-box}body{font:16px/1.65 -apple-system,BlinkMacSystemFont,sans-serif;
margin:0;background:#f2f6f9;color:#173147;padding:18px}
main{margin:18px auto;max-width:600px;background:white;border-radius:18px;padding:24px}
h1{font-size:24px}button{width:100%;background:#126683;color:white;padding:15px;
border:0;border-radius:12px;font-size:16px;font-weight:bold}
button:disabled{opacity:.5}.warn{padding:12px;border-radius:10px;background:#fff2dc}
pre{overflow-wrap:anywhere;white-space:pre-wrap;font-size:12px;background:#edf2f5;padding:12px}
small{color:#657782;overflow-wrap:anywhere}
</style></head><body><main>
<h1>真正 CP-SAT WASM｜iPhone 驗證</h1>
<p class="warn">僅測試虛構數學小題。不是正式 589 班排哨引擎；
GitHub 的 OPTIMAL 不代表 iPhone 通過，也不代表實際軍務規則已驗收。</p>
<button id="run">在本機執行真正 CP-SAT 求解</button>
<p id="status" role="status">尚未執行手機測試</p><pre id="output">沒有結果</pre>
<small>JS SHA-256: __JS_HASH__</small>
<small>WASM SHA-256: __WASM_HASH__</small>
</main>
<script>
__GLUE__
</script>
<script>
'use strict';
const B64 = __WASM_B64__;
function decode(s){
  const raw=atob(s),bytes=new Uint8Array(raw.length);
  for(let p=0;p<raw.length;p+=65536)
    for(let q=p;q<Math.min(p+65536,raw.length);q++)bytes[q]=raw.charCodeAt(q);
  return bytes;
}
document.getElementById('run').addEventListener('click',async()=>{
  const btn=document.getElementById('run'),status=document.getElementById('status'),
        out=document.getElementById('output');
  btn.disabled=true;status.textContent='正在載入並求解…';out.textContent='尚未通過';
  await new Promise(ok=>requestAnimationFrame(ok));
  const start=Date.now();
  try{
    if(typeof WebAssembly==='undefined')throw Error('不支援 WebAssembly');
    if(typeof createCPSatModule!=='function')throw Error('缺少真正 CP-SAT 模組');
    const wasm=decode(B64);
    if(!WebAssembly.validate(wasm))throw Error('WASM 格式驗證失敗');
    const mod=await createCPSatModule({
      wasmBinary:wasm,print:()=>{},printErr:msg=>console.error(String(msg))
    });
    if(typeof mod.ccall!=='function')throw Error('缺少 ccall');
    const got=JSON.parse(mod.ccall('run_cp_sat_probe','string',[],[]));
    const passed=got.engine==='Google OR-Tools CP-SAT'&&got.status==='OPTIMAL'&&
      got.desks===0&&got.tables===3&&got.profit===90;
    status.textContent=passed ?
      '✅ iPhone 本機 CP-SAT WASM 實測通過（僅虛構小題）' :
      '❌ 求解結果未通過驗收';
    out.textContent=JSON.stringify({passed,got,expected:{desks:0,tables:3,profit:90},
      runtime:'this-device',ms:Date.now()-start,userAgent:navigator.userAgent},null,2);
  }catch(e){status.textContent='❌ 手機實測失敗';out.textContent=String(e&&e.stack||e)}
  finally{btn.disabled=false}
});
</script></body></html>"""

def main(argv):
    if len(argv)!=4:
        raise SystemExit("usage: package_iphone_cp_sat.py solver.js solver.wasm reverified.json out.html")
    js,b64,r=verify(*argv[:3])
    # Prevent the Emscripten source from terminating its inline <script>.
    js=re.sub("</script",r"<\/script",js,flags=re.IGNORECASE)
    chunks=[b64[i:i+4096] for i in range(0,len(b64),4096)]
    page=(TEMPLATE.replace("__GLUE__",js)
          .replace("__WASM_B64__"," +\n".join(json.dumps(c) for c in chunks))
          .replace("__JS_HASH__",r["js_sha256"])
          .replace("__WASM_HASH__",r["wasm_sha256"]))
    out=Path(argv[3]);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(page,encoding="utf-8")
    print(f"Packaged {out} ({out.stat().st_size:,} bytes).")
    print("Node WASM smoke: VERIFIED. iPhone hardware: NOT YET TESTED.")
if __name__=="__main__":main(sys.argv[1:])
