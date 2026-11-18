#!/usr/bin/env python3
"""Actual offline browser acceptance of EXPERIMENTAL 589-shift CP-SAT WASM.

The HTML may only exist if a real Emscripten, Node+OR-Tools CP-SAT and
independent synthetic-shift audit all succeeded. Browser checks are also real
(no JS mocks), but Playwright Chromium mobile mode is NOT iPhone Safari.
"""
from pathlib import Path
import argparse
import json
import time

from playwright.sync_api import sync_playwright

SCENARIOS = {
    "door": ("OPTIMAL", 372, 372, 56),
    "officer": ("OPTIMAL", 217, 217, 50),
    "adjacent": ("INFEASIBLE", None, 210, 1),
    "same-sunday": ("OPTIMAL", 2, 360, 1),
    "next-sunday": ("INFEASIBLE", None, 360, 1),
}


def check_profile(browser, html_path, mobile):
    kind="mobile-chromium" if mobile else "desktop-chromium"
    context=browser.new_context(
        viewport={"width":390,"height":844} if mobile else
                 {"width":1280,"height":800},
        device_scale_factor=3 if mobile else 1,
        has_touch=mobile,is_mobile=mobile,offline=True)
    page=context.new_page()
    web_requests=[]
    js_errors=[]
    page.on("request",lambda r:web_requests.append(r.url)
            if r.url.startswith(("http://","https://")) else None)
    page.on("pageerror",lambda e:js_errors.append(str(e)))
    start=time.monotonic()
    report={"profile":kind,"accepted":False,"real_iphone_safari":False,
            "offline":True,"cases":[]}
    try:
        page.goto(html_path.resolve().as_uri(),wait_until="domcontentloaded",
                  timeout=90000)
        for scenario,(expected_status,expected_fill,shift_count,staff) in SCENARIOS.items():
            page.locator("#scenario").select_option(scenario)
            page.locator("#run").click(timeout=30000)
            page.wait_for_function(
                """() => {
                  const value=document.getElementById('status').textContent;
                  return value.includes('驗證通過') || value.includes('驗證失敗');
                }""",
                timeout=120000)
            status=page.locator("#status").inner_text()
            details=page.locator("#output").inner_text()
            if "驗證通過" not in status:
                raise AssertionError("Real monthly WASM page failed: "+status+" / "+details[:800])
            data=json.loads(details)
            expected=({
                "accepted":True,"scenario":scenario,"status":expected_status,
                "filled":expected_fill,"shifts":shift_count,"staff":staff,
                "runtime":"this-device","iphone_safari_tested":False,
                "operationally_certified":False
            })
            if any(data.get(k)!=v for k,v in expected.items()):
                raise AssertionError("Browser misreported month result: "+details[:1200])
            report["cases"].append({
                "scenario":scenario,"status":expected_status,"filled":expected_fill,
                "elapsed_ms":data.get("elapsed_ms"),"accepted":True})
        if web_requests:
            raise AssertionError("Offline month page attempted HTTP networking")
        if js_errors:
            raise AssertionError("Unhandled browser error: "+";".join(js_errors))
        report.update({"accepted":True,
                       "total_seconds":round(time.monotonic()-start,3),
                       "external_http_requests":0,"pageerrors":0})
    except Exception as exc:
        report.update({"error":str(exc),
                       "total_seconds":round(time.monotonic()-start,3),
                       "external_http_requests":web_requests,
                       "pageerrors":js_errors})
        try:page.screenshot(path=f"month-{kind}-failure.png",full_page=True,timeout=5000)
        except Exception:pass
    finally:
        context.close()
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("html",type=Path)
    args=parser.parse_args()
    if not args.html.is_file() or args.html.stat().st_size<100000:
        raise SystemExit("Genuine complete-month WASM HTML missing or unexpectedly small")
    with sync_playwright() as driver:
        browser=driver.chromium.launch(headless=True,args=["--no-sandbox"])
        try:
            reports=[check_profile(browser,args.html,False),
                     check_profile(browser,args.html,True)]
        finally:
            browser.close()
    output={
        "accepted":all(x["accepted"] for x in reports),
        "type":"real-offline-Chromium-589-synthetic-WASM",
        "real_iphone_safari":False,
        "operational_guard_scheduler":False,
        "dense_589_optimization_proven":False,
        "reports":reports}
    Path("month_browser_proof.json").write_text(
        json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False,indent=2))
    if not output["accepted"]:
        raise SystemExit("Real offline 589-shift WASM browser acceptance FAILED")


if __name__=="__main__":
    main()
