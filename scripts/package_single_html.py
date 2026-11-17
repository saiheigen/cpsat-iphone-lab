#!/usr/bin/env python3
"""Make a file://-friendly, single HTML WASM baseline test (NOT CP-SAT)."""
from pathlib import Path
import html
import re
import sys

def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: package_single_html.py JS_OUTPUT HTML_OUTPUT")
    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    js = source.read_text(encoding="utf-8")
    if "createSmokeModule" not in js:
        raise SystemExit("Wrong JS factory: missing createSmokeModule")
    # Prevent an accidental closing tag if the generated JS contains it.
    js = re.sub(r"</script", r"<\\/script", js, flags=re.IGNORECASE)
    page = """<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>iPhone WebAssembly 單檔驗收</title>
<style>
body{font:16px/1.7 -apple-system,BlinkMacSystemFont,sans-serif;max-width:650px;margin:40px auto;padding:0 20px;color:#172b40;background:#f5f8fc}
main{background:white;border-radius:20px;padding:28px;box-shadow:0 6px 30px #22304713}
h1{font-size:23px} #status{font-weight:700;overflow-wrap:anywhere}
.warning{color:#8c4e13;background:#fff4e4;padding:14px;border-radius:10px}
</style></head>
<body><main><h1>iPhone WASM 單檔測試</h1>
<p id="status">正在啟動真正的 WASM 程式…</p>
<p class="warning">這只是 Emscripten／WASM 基礎相容性測試，不是 OR-Tools 或 CP-SAT 排班求解測試。</p>
<p id="detail"></p></main>
<script>
""" + js + """
</script>
<script>
(async () => {
  const status=document.getElementById('status');
  const detail=document.getElementById('detail');
  try {
    if(typeof WebAssembly==='undefined') throw new Error('WebAssembly 不可用');
    if(typeof createSmokeModule!=='function') throw new Error('缺少 WASM 模組工廠');
    const instance=await createSmokeModule();
    const value=instance._smoke_add(17,25);
    if(value!==42) throw new Error('WASM 結果錯誤：'+value);
    status.textContent='✅ 基礎 WASM 實際運行成功：17 + 25 = 42';
    detail.textContent='實際執行環境：'+navigator.userAgent;
  } catch(err) {
    status.textContent='❌ WASM 測試失敗：'+String(err&&err.message||err);
    detail.textContent='請回報完整錯誤訊息，不能視為成功';
  }
})();
</script></body></html>"""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    assert "<html" in target.read_text(encoding="utf-8")
    print(f"Packaged: {target} ({target.stat().st_size:,} bytes)")
    print("NOT A CP-SAT BUILD")

if __name__ == "__main__":
    main()
