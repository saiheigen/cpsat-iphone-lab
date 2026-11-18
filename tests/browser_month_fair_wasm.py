#!/usr/bin/env python3
"""Actual offline Chromium two-stage fair-count OR-Tools WebAssembly acceptance.

This tests a REAL solver inside desktop and mobile-sized Linux Chromium.
It DOES NOT prove iPhone Safari, production duty rules or hardship fairness.
Any fake HTML containing only JavaScript results cannot satisfy the expected
page and runtime provenance without also passing Node proof + checksums.
"""
from pathlib import Path
import argparse
import json
import time

from playwright.sync_api import sync_playwright

CASES = {
    "tiny": (372,2,2),
    "door-blackouts-no-hints": (372,56,372),
    "officer-blackouts-no-hints": (217,50,217),
    "door-forced-vacancies": (372,56,360),
}


def run(browser, html: Path, mobile: bool):
    name="mobile-chromium-emulation" if mobile else "desktop-chromium"
    ctx=browser.new_context(
        viewport={"width":390,"height":844} if mobile else
                 {"width":1280,"height":800},
        device_scale_factor=3 if mobile else 1,
        is_mobile=mobile,has_touch=mobile,offline=True)
    page=ctx.new_page()
    network=[]
    errors=[]
    page.on("request",lambda request:
            network.append(request.url) if request.url.startswith(
                ("http://","https://")) else None)
    page.on("pageerror",lambda err:errors.append(str(err)))
    started=time.monotonic()
    record={"profile":name,"real_iphone_safari":False,
            "offline":True,"cases":[]}
    try:
        page.goto(html.resolve().as_uri(),wait_until="domcontentloaded",
                  timeout=90000)
        for case,(shift_count,staff,filled) in CASES.items():
            page.locator("#scenario").select_option(case)
            page.locator("#run").click(timeout=30000)
            page.wait_for_function(
                """() => {
                    const text=document.getElementById('status').textContent;
                    return text.includes('檢查通過') || text.includes('驗證失敗');
                }""",timeout=120000)
            status=page.locator("#status").inner_text()
            text=page.locator("#output").inner_text()
            if "檢查通過" not in status:
                raise AssertionError("Genuine fair WASM browser failed: "+
                                     status+" / "+text[:900])
            result=json.loads(text)
            for key,expected in {
                "accepted":True,"scenario":case,
                "shifts":shift_count,"staff":staff,"filled":filled,
                "runtime":"this-device",
                "real_iphone_safari_verified":False,
                "operationally_certified":False,
            }.items():
                if result.get(key)!=expected:
                    raise AssertionError("Incorrect fair-count browser field "+
                                         key+": "+text[:500])
            if result.get("status") not in ("OPTIMAL","FEASIBLE"):
                raise AssertionError("No legal WASM result")
            if result["final_abs_deviation"]>result["phase1_abs_deviation"]:
                raise AssertionError("Fairness worsened baseline")
            if case=="tiny" and result["final_abs_deviation"]!=0:
                raise AssertionError("Exact tiny fairness optimum not achieved")
            if result.get("fairness_optimal_proven") and result.get("fair_phase")!="OPTIMAL":
                raise AssertionError("Forged fair optimality")
            record["cases"].append({
                "name":case,"filled":result["filled"],
                "phase1_abs_deviation":result["phase1_abs_deviation"],
                "final_abs_deviation":result["final_abs_deviation"],
                "fill_phase":result["fill_phase"],"fair_phase":result["fair_phase"],
                "elapsed_ms":result["elapsed_ms"],"accepted":True})
        if network:
            raise AssertionError("Page sent external HTTP request: "+str(network))
        if errors:
            raise AssertionError("Unhandled browser JS exceptions: "+str(errors))
        record.update({"accepted":True,"external_http_requests":0,
                       "js_exceptions":0})
    except Exception as e:
        record.update({"accepted":False,"error":str(e),
                       "external_http_requests":network,
                       "js_exceptions":errors})
        try:
            page.screenshot(path="fair-"+name+"-failure.png",
                            full_page=True,timeout=5000)
        except Exception:
            pass
    finally:
        record["elapsed_seconds"]=round(time.monotonic()-started,3)
        ctx.close()
    return record


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("html",type=Path)
    args=parser.parse_args()
    if not args.html.is_file() or args.html.stat().st_size<100000:
        raise SystemExit("Genuine full-month fair-count WASM HTML missing or too small")
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
        try:
            runs=[run(browser,args.html,False),run(browser,args.html,True)]
        finally:
            browser.close()
    report={
        "accepted":all(x["accepted"] for x in runs),
        "real_offline_chromium_executed":True,
        "real_iphone_safari_verified":False,
        "complete_operational_roster_verified":False,
        "objective":"legal_fill_fixed_then_L1_soft_count_deviation",
        "runs":runs
    }
    Path("fair_month_browser_proof.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report["accepted"]:
        raise SystemExit("Real offline Chromium fairness WASM acceptance FAILED")


if __name__=="__main__":
    main()
