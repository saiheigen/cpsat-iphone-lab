#!/usr/bin/env python3
"""Attach one-click *fictional-only* cross-month WASM panel to proven offline page.

Base page must be made by build/package_month_hardship_wasm.py and its embedded
JS/WASM bytes re-hash to a genuine proof. Does not rebuild or modify CP-SAT.
All input source records are invented; no import/upload/network behavior.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SEPARATOR = '</script></body></html>'
HTML_PLACE = '<pre id="output">沒有結果</pre>'
WASM_PATTERN = re.compile(r'const ENCODED=(.*?);\nconst WORKER_BOOTSTRAP=', re.S)
GLUE_PATTERN = re.compile(r'<script id="phase5-wasm-glue">(.*?)</script>', re.S)


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def verify_attested_base(html: str, proof: dict, trusted_digest: str):
    if (proof.get('accepted') is not True or
            proof.get('contract') != 'guard-month-harsh-v4' or
            proof.get('operationally_certified') is not False or
            not re.fullmatch('[0-9a-f]{64}', trusted_digest) or
            proof.get('wasm_sha256') != trusted_digest):
        raise ValueError('Not a trusted synthetic genuine v4 build proof')
    js_match = GLUE_PATTERN.search(html)
    wasm_match = WASM_PATTERN.search(html)
    if not js_match or not wasm_match:
        raise ValueError('Missing existing proof-gated WASM code')
    glue = js_match.group(1)
    chunks = re.findall('"([A-Za-z0-9+/=]+)"', wasm_match.group(1))
    if not chunks or sum(map(len, chunks)) > 15_000_000:
        raise ValueError('Unexpected embedded WASM size')
    try:
        wasm = base64.b64decode(''.join(chunks), validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError('Corrupted embedded WASM') from exc
    if (digest(wasm) != trusted_digest or
            digest(glue.encode('utf-8')) != proof.get('js_sha256') or
            not wasm.startswith(b'\x00asm\x01\x00\x00\x00')):
        raise ValueError('Embedded HTML binary differs from trusted WASM proof')
    if (html.count(SEPARATOR) != 1 or html.count(HTML_PLACE) != 1 or
            'fictional-e2e-workspace' in html or
            html.count('function solveWithMode(') != 1 or
            html.count('function independentlyAudit(') != 1):
        raise ValueError('Base offline UI unexpected or already modified')
    return True


def verify_handoff_and_report(handoff: dict, report: dict, expected_wasm: str):
    if (handoff.get('invented_only') is not True or
            handoff.get('operationally_certified') is not False or
            report.get('synthetic_only') is not True or
            report.get('genuine_local_wasm_runtime_verified') is not True or
            report.get('independent_november_december_audit') is not True or
            report.get('solver_assignments_accepted') is not True or
            report.get('operationally_certified') is not False or
            report.get('real_v7_inputSig_verified') is not False or
            report.get('wasm_sha256') != expected_wasm or
            report.get('staffed') != 4 or report.get('unfilled') != 585 or
            report.get('month_rows') != 589 or
            report.get('pool_staffed') != {'door': 3, 'officer': 1}):
        raise ValueError('Independent local fictional handoff proof is missing')
    frames = {}
    for pool, shifts, staff, ones in [('door',372,56,12),('officer',217,50,7)]:
        raw=handoff['frames'][pool]
        wire=raw['wire']
        if (type(wire) is not str or len(wire)>100_000 or
                not all(ord(x)<128 for x in wire) or
                raw['shift_count']!=shifts or raw['staff_count']!=staff or
                raw['sha256']!=digest(wire.encode('ascii')) or
                report.get('anonymous_input_sha256', {}).get(pool)!=raw['sha256']):
            raise ValueError('Anonymous source and independently audited frame differ')
        lines=wire.splitlines()
        if len(lines)!=8 or lines[0:4]!=['guard-month-harsh-v4','2026-12',pool,f'{shifts} {staff}'] or lines[4].count('1')!=ones:
            raise ValueError('Expected only the built-in deliberately sparse fictional scenario')
        frames[pool]={'wire':wire,'sha256':raw['sha256']}
    return frames


def make(base_html: Path, proof_json: Path, local_report: Path,
         handoff: dict, output_html: Path):
    if base_html.resolve()==output_html.resolve():
        raise ValueError('Do not overwrite the original independently tested UI')
    proof=json.loads(proof_json.read_text('utf-8'))
    report=json.loads(local_report.read_text('utf-8'))
    html=base_html.read_text('utf-8')
    sha=report.get('wasm_sha256','')
    verify_attested_base(html,proof,sha)
    frames=verify_handoff_and_report(handoff,report,sha)
    spec={'synthetic_only':True,'operationally_certified':False,'month':'2026-12',
          'source_audit_local_only':True,'wasm_sha256':sha,'frames':frames}
    safe_json=json.dumps(spec,separators=(',',':'),ensure_ascii=True)
    assert '<' not in safe_json and '&' not in safe_json
    script=(ROOT/'src'/'fictional_iphone_e2e_ui.js').read_text('utf-8')
    if script.count('__FICTIONAL_E2E_SPEC__')!=1 or '<script' in script.lower() or '</script' in script.lower():
        raise ValueError('Unsafe synthetic UI script')
    script=script.replace('__FICTIONAL_E2E_SPEC__',safe_json)
    panel='''<section id="fictional-e2e-workspace" hidden aria-label="跨月虛構整合測試">
<h2>📱 一鍵跨月虛構整合驗收</h2>
<p class="notice">此區只執行內建虛構大門＋安官資料。真正 WASM 在本機求解，手機端再次核對候選資格與休息規則；前月封存與事件的獨立稽核是在產生此頁時完成，並非手機即時重新驗證。不是正式排班。</p>
<details id="fictional-edit-workspace">
<summary>🧪 本機模擬調整：額外禁排與固定空班</summary>
<p>僅可縮減既有虛構候選資格，不得解除原本禁排，也不得變更人工固定班。
修改不會儲存、上傳或改變已核對的原始封存；重新開啟頁面即清空。</p>
<label for="fictional-edit-pool">勤務別</label>
<select id="fictional-edit-pool"><option value="door">大門衛哨</option><option value="officer">安全士官</option></select>
<label for="fictional-edit-day">日期</label><select id="fictional-edit-day"></select>
<label for="fictional-edit-slot">班次</label><select id="fictional-edit-slot"></select>
<label for="fictional-edit-action">模擬操作</label>
<select id="fictional-edit-action"><option value="block">額外禁排一名虛構候選</option><option value="vacancy">指定此班固定空缺</option></select>
<label for="fictional-edit-person">只顯示原本有資格的虛構人員</label>
<select id="fictional-edit-person"></select>
<button id="fictional-edit-preset" type="button">套用示範：10 項禁排，觀察填班變化</button>
<button id="fictional-edit-apply" type="button">新增這項模擬禁排</button>
<button id="fictional-edit-undo" type="button" disabled>撤銷上一項</button>
<button id="fictional-edit-clear" type="button" disabled>全部還原虛構預設資料</button>
<p id="fictional-edit-status" role="status" aria-live="polite">尚未加入模擬限制</p>
<p id="fictional-edit-summary" aria-live="polite">只顯示既有虛構候選，沒有真實資料。</p>
<ol id="fictional-edit-list"></ol>
</details>
<button id="fictional-e2e-start" type="button">一鍵求解目前的虛構條件（兩組 WASM）</button>
<p id="fictional-e2e-status" role="status" aria-live="polite">尚未執行</p>
<p id="fictional-e2e-counts">尚無已完成的雙勤務結果</p>
<details id="fictional-e2e-preview" hidden><summary>查看每日虛構班表與缺班原因</summary>
<label for="fictional-e2e-pool">勤務別</label>
<select id="fictional-e2e-pool"><option value="door">大門衛哨</option><option value="officer">安全士官</option></select>
<label for="fictional-e2e-day">日期</label><select id="fictional-e2e-day"></select>
<div id="fictional-e2e-day-rows"></div>
<h3>缺班原因分類（只有候選矩陣可判斷的資訊）</h3><ul id="fictional-e2e-reasons"></ul>
</details>
<details><summary>驗收證據（僅摘要，不含人員資料）</summary><pre id="fictional-e2e-report">未產生可用的測試摘要</pre></details>
</section>
'''
    style='''\n#fictional-e2e-workspace{margin:24px 0;border-top:2px solid #b7ccd6;padding-top:16px}
#fictional-e2e-workspace h2{font-size:19px}#fictional-e2e-day-rows li{margin:5px 0}
#fictional-edit-workspace{margin:12px 0 20px}#fictional-edit-workspace label{margin:9px 0 4px}
#fictional-edit-workspace button{margin-top:9px}#fictional-edit-list li{font-size:14px;line-height:1.5}
#fictional-edit-summary{font-size:14px;color:#415468}
'''
    if html.count('</style>')!=1:
        raise ValueError('Unexpected base CSS')
    html=html.replace('</style>',style+'</style>')
    html=html.replace(HTML_PLACE,panel+HTML_PLACE)
    html=html.replace(SEPARATOR,script+'\n'+SEPARATOR)
    if (html.count('id="fictional-e2e-workspace"')!=1 or
            html.count('getElementById("fictional-e2e-workspace")')!=1):
        raise ValueError('New offline UI was injected unexpectedly')
    output_html.parent.mkdir(parents=True,exist_ok=True)
    output_html.write_text(html,encoding='utf-8')
    return {'output':str(output_html),'sha256':digest(html.encode('utf-8')),
            'wasm_sha256':sha,'fictional_frames':{x:frames[x]['sha256'] for x in frames}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base_html',type=Path)
    parser.add_argument('wasm_proof',type=Path)
    parser.add_argument('local_audited_report',type=Path)
    parser.add_argument('output_html',type=Path)
    args=parser.parse_args()
    # Deliberately NO arbitrary incoming roster backup or source-file argument.
    from tools.fictional_offline_pipeline import fictional_sparse_handoff
    result=make(args.base_html,args.wasm_proof,args.local_audited_report,
                fictional_sparse_handoff(),args.output_html)
    print(json.dumps(result,ensure_ascii=True))


if __name__=='__main__':
    main()
