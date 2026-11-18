#!/usr/bin/env python3
"""Run actual dense 589-shift C++ CP-SAT WASM in offline Chromium.

Only synthetic data from the deterministic Node preflight. This exercises
the existing proof-gated single-file HTML but invokes its genuine exported
WASM entrypoint with more realistic candidate masks. No JS solver mock.
Browser 'mobile' mode is NOT a real iPhone Safari device.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

from playwright.sync_api import sync_playwright

EVALUATE = r"""async ({payload})=>{
    if(typeof createMonthModule!=='function')
        throw Error('Missing real OR-Tools Emscripten factory');
    if(typeof wasmBytes!=='function' || typeof RAW==='undefined')
        throw Error('Missing real embedded WASM bytes from proof-gated page');
    if(!window.__denseMonthModule){
        const data=wasmBytes(RAW);
        if(!WebAssembly.validate(data))
            throw Error('Invalid embedded WebAssembly');
        window.__denseMonthModule=await createMonthModule({
            wasmBinary:data,print:()=>{},
            printErr:x=>console.error(String(x))
        });
    }
    const t0=performance.now();
    const response=JSON.parse(window.__denseMonthModule.ccall(
        'solve_guard_month_v2','string',['string'],[payload]
    ));
    return {response,elapsed_ms:Math.round(performance.now()-t0)};
}"""


def run(browser, html_path: Path, cases: list[dict], mobile: bool):
    profile = "mobile-chromium-emulation" if mobile else "desktop-chromium"
    context = browser.new_context(
        viewport={"width": 390, "height": 844} if mobile else
                 {"width": 1280, "height": 800},
        is_mobile=mobile, has_touch=mobile,
        device_scale_factor=3 if mobile else 1,
        offline=True)
    page = context.new_page()
    page.set_default_timeout(120000)
    requests = []
    errors = []
    page.on("request", lambda r:
            requests.append(r.url) if r.url.startswith(
                ("https://", "http://")) else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    result = {"profile": profile, "real_iphone_safari": False,
              "offline": True, "cases": []}
    started = time.monotonic()
    try:
        page.goto(html_path.resolve().as_uri(),
                  wait_until="domcontentloaded", timeout=90000)
        for case in cases:
            measured = page.evaluate(EVALUATE, {"payload": case["payload"]})
            response = measured["response"]
            if response.get("status") not in (
                "OPTIMAL", "FEASIBLE", "UNKNOWN"):
                raise AssertionError(
                    "Genuine WASM returned abnormal status in synthetic case: "+
                    json.dumps({
                        "case": [case["pool"], case["variant"]],
                        "response": response}, ensure_ascii=False)[:1400])
            # The full returned assignments are passed to a SEPARATE Node
            # reference auditor, not trusted here solely due to status.
            result["cases"].append({
                "pool": case["pool"], "variant": case["variant"],
                "shifts": case["shifts"], "staff": case["staff"],
                "reference_filled": case["referenceFilled"],
                "status": response["status"],
                "elapsed_ms": measured["elapsed_ms"],
                "solver_response": response,
            })
        if requests:
            raise AssertionError("Unexpected external HTTP request in offline browser")
        if errors:
            raise AssertionError("Unhandled browser JavaScript errors: " +
                                 "; ".join(errors[:4]))
        result["completed"] = True
        result["requests"] = []
        result["js_errors"] = []
    except Exception as e:
        result["completed"] = False
        result["error"] = str(e)
        result["requests"] = requests
        result["js_errors"] = errors
        try:
            page.screenshot(path=f"dense-month-{profile}-error.png",
                            full_page=True, timeout=5000)
        except Exception:
            pass
    finally:
        result["elapsed_s"] = round(time.monotonic()-started, 3)
        context.close()
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("html", type=Path)
    p.add_argument("fixtures", type=Path)
    p.add_argument("output", type=Path)
    args=p.parse_args()
    if not args.html.is_file() or args.html.stat().st_size < 100000:
        raise SystemExit("Genuine proof-gated WASM HTML missing/too small")
    data=json.loads(args.fixtures.read_text(encoding="utf-8"))
    if data.get("source")!="local-fabricated-static-fixture-not-real-workforce":
        raise SystemExit("Refusing real-world or unknown benchmark inputs")
    cases=data.get("cases")
    expected={(pool,mode) for pool in ("door","officer")
              for mode in ("blackouts-hints","blackouts-no-hints","forced-vacancies")}
    if (not isinstance(cases,list) or len(cases)!=6 or
        {(c["pool"],c["variant"]) for c in cases}!=expected):
        raise SystemExit("Missing or malformed six-case synthetic batch")
    with sync_playwright() as driver:
        browser=driver.chromium.launch(headless=True,args=["--no-sandbox"])
        try:
            runs=[run(browser,args.html,cases,mobile=False),
                  run(browser,args.html,cases,mobile=True)]
        finally:
            browser.close()
    result={"browser_engine":"actual-offline-Chromium",
            "real_iphone_safari":False,
            "synthetic_only":True,
            "actual_cpsat_execution":True,
            "independent_assignment_audit":"RUN_SEPARATELY_AFTER_THIS_STEP",
            "html_sha256":hashlib.sha256(args.html.read_bytes()).hexdigest(),
            "runs":runs}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "browser_engine":result["browser_engine"],
        "runs":[{
            "profile":r["profile"],"completed":r.get("completed"),
            "elapsed_s":r["elapsed_s"],"error":r.get("error"),
            "results":[{"pool":c["pool"],"variant":c["variant"],
                        "status":c["status"],
                        "elapsed_ms":c["elapsed_ms"],
                        "filled":c["solver_response"].get("filled")}
                       for c in r["cases"]]}
            for r in runs]},ensure_ascii=False,indent=2))
    if not all(r.get("completed") for r in runs):
        raise SystemExit("One or more real offline dense browser runs failed")


if __name__=="__main__":
    main()
