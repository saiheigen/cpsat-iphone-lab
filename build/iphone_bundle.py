#!/usr/bin/env python3
"""Package ONLY a Node-tested, authentic Emscripten CP-SAT build into offline HTML."""
import argparse
import base64
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser()
for key in ('glue','wasm','proof','output'): p.add_argument(key,type=Path)
a=p.parse_args()
js=a.glue.read_bytes()
wasm=a.wasm.read_bytes()
proof=json.loads(a.proof.read_text(encoding='utf-8'))
assert proof.get('accepted') is True and proof.get('solver',{}).get('status')=='OPTIMAL', 'No verified OPTIMAL proof'
assert proof.get('solver',{}).get('engine')=='Google OR-Tools CP-SAT', 'Not genuine OR-Tools'
assert proof.get('js_sha256')==hashlib.sha256(js).hexdigest(), 'JS altered after verified smoke test'
assert proof.get('wasm_sha256')==hashlib.sha256(wasm).hexdigest(), 'WASM altered after verified smoke test'
assert wasm[:8]==b'\0asm\x01\0\0\0' and len(wasm)>4096, 'Missing genuine wasm module'
text=js.decode('utf-8')
assert len(text)>10000 and 'createCPSatModule' in text, 'Missing Emscripten JS glue'
assert '</script' not in text.lower(), 'Inline JS terminator is unsafe'

# Audit whether the compiled module declares imported or defined shared WASM memory.
def uleb(buf,i):
    val=0
    for shift in range(0,70,7):
        if i>=len(buf): raise ValueError('Truncated wasm LEB')
        n=buf[i];i+=1;val|=(n&127)<<shift
        if n<128:return val,i
    raise ValueError('Invalid LEB')
def skipname(b,i):
    n,i=uleb(b,i)
    if i+n>len(b):raise ValueError('Truncated name')
    return i+n
def checkmemory(b,i):
    flags,i=uleb(b,i)
    if flags & 2:raise ValueError('Shared WASM memory prohibited for offline iPhone HTML Viewer')
    _,i=uleb(b,i)
    if flags & 1:_,i=uleb(b,i)
    return i
i=8; nmem=0
while i<len(wasm):
    sid=wasm[i];i+=1
    size,i=uleb(wasm,i)
    section=wasm[i:i+size];i+=size
    if len(section)!=size:raise ValueError('Truncated section')
    if sid==5:
        c,k=uleb(section,0)
        for _ in range(c):k=checkmemory(section,k);nmem+=1
    elif sid==2:
        c,k=uleb(section,0)
        for _ in range(c):
            k=skipname(section,skipname(section,k))
            kind=section[k];k+=1
            if kind==0:_,k=uleb(section,k)
            elif kind==1:
                k+=1;f,k=uleb(section,k);_,k=uleb(section,k)
                if f&1:_,k=uleb(section,k)
            elif kind==2:k=checkmemory(section,k);nmem+=1
            elif kind==3:k+=2
            else:raise ValueError('Unrecognized imported item')
assert nmem>=1,'No WASM memory found'
b64=base64.b64encode(wasm).decode('ascii')
page='''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>真正 CP-SAT iPhone 離線求解驗收</title>
<style>:root{font-family:-apple-system,system-ui,sans-serif;background:#f4f6fa;color:#202d3b}body{margin:0;padding:22px 14px}main{max-width:580px;margin:auto}section{background:white;padding:20px;border-radius:18px;margin:16px 0;box-shadow:0 4px 20px #173a4b10}h1{font-size:24px}p{line-height:1.65}button{width:100%;min-height:54px;border:0;border-radius:12px;color:white;background:#145ddf;font-weight:700;font-size:16px}button:disabled{background:#a5afbe}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6fb;border-radius:12px;padding:14px;min-height:80px;font-size:13px}.status{padding:10px;border-radius:12px;background:#fff0da;color:#8a5700;font-weight:700}.ok{background:#e4f8ef;color:#00603b}.fail{background:#fce7e7;color:#8f2929}</style>
</head><body><main><h1>🧠 Google CP-SAT iPhone 本機求解</h1>
<p>這是<b>真正的 C++ CP-SAT 編譯成 WASM</b> 的獨立驗收頁，不是原本的 DFS，也不連線到外部伺服器。尚未與實際排哨資料整合。</p>
<section><div id="status" class="status">編譯產物已嵌入，但尚未在本機完成實際求解</div>
<p>測試問題：總工時 12；桌子每件耗 4、賺 30；書桌每件耗 3、賺 20。最佳值應為 90。</p>
<button id="go">執行真正 CP-SAT 求解</button><pre id="output">尚未執行</pre></section>
<section><p>驗收標準：必須由 OR-Tools 回報 <b>OPTIMAL</b>、desks=0、tables=3、profit=90，並通過本頁獨立枚舉。</p>
<p>此題無人員或哨務資料。若 iPhone 不支援此 WASM，畫面會明確顯示失敗，不會顯示假成功。</p></section></main>
<script>
/*__GLUE__*/
</script><script type="application/octet-stream" id="wasm">/*__B64__*/</script>
<script>
(()=>{'use strict';const btn=document.getElementById('go'),out=document.getElementById('output'),st=document.getElementById('status');
function oracle(){let best=-1,win=[];for(let d=0;d<=4;d++)for(let t=0;t<=3;t++){if(3*d+4*t>12)continue;const p=20*d+30*t;if(p>best){best=p;win=[[d,t]];}else if(p===best){win.push([d,t]);}}return {best,win};}
btn.onclick=async()=>{btn.disabled=true;out.textContent='正在裝置本機載入 CP-SAT WASM …';try{if(typeof createCPSatModule!=='function')throw Error('找不到真正 CP-SAT module factory');
const str=document.getElementById('wasm').textContent.trim(),bin=Uint8Array.from(atob(str),x=>x.charCodeAt(0));
const module=await createCPSatModule({wasmBinary:bin,print:()=>{},printErr:()=>{}});
const s=JSON.parse(module.ccall('run_cp_sat_probe','string',[],[])),o=oracle();
const valid=s.engine==='Google OR-Tools CP-SAT'&&s.status==='OPTIMAL'&&s.desks===0&&s.tables===3&&s.profit===90&&o.best===90&&o.win.length===1&&o.win[0][0]===0&&o.win[0][1]===3;
st.textContent=valid?'✅ iPhone 真正 CP-SAT OPTIMAL 驗收通過':'❌ 求解結果沒有通過驗收';
st.className='status '+(valid?'ok':'fail');
out.textContent=JSON.stringify({solver:s,oracle:o,accepted:valid,crossOriginIsolated:globalThis.crossOriginIsolated===true},null,2);
}catch(e){st.textContent='❌ iPhone 本機執行失敗';st.className='status fail';out.textContent=String(e&&e.message||e);}finally{btn.disabled=false;}};})();
</script></body></html>'''
assert page.count('/*__GLUE__*/')==1 and page.count('/*__B64__*/')==1
page=page.replace('/*__GLUE__*/',text).replace('/*__B64__*/',b64)
a.output.write_text(page,encoding='utf-8')
print('Offline iPhone CP-SAT HTML:',a.output,'bytes:',a.output.stat().st_size)
