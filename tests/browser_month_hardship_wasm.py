#!/usr/bin/env python3
"""Actual offline Chromium/WebKit three-stage hardship OR-Tools WASM acceptance.

This tests a REAL solver in Linux desktop and mobile-sized browser engines.
Linux WebKit and Chromium are NOT a physical iPhone Safari or operational approval.
Any fake HTML containing only JavaScript results cannot satisfy the expected
page and runtime provenance without also passing Node proof + checksums.
"""
from pathlib import Path
import argparse
import json
import time

from playwright.sync_api import sync_playwright

CASES = {
    "tiny": (372,2,4),
    "door-blackouts-no-hints": (372,56,372),
    "officer-blackouts-no-hints": (217,50,217),
    "door-forced-vacancies": (372,56,360),
}


def run(browser, html: Path, mobile: bool, engine: str = "chromium"):
    name=("mobile-"+engine+"-emulation" if mobile else "desktop-"+engine)
    ctx=browser.new_context(
        viewport={"width":390,"height":844} if mobile else
                 {"width":1280,"height":800},
        device_scale_factor=3 if mobile else 1,
        is_mobile=mobile,has_touch=mobile,offline=True)
    network=[]
    errors=[]
    def capture_events(p):
        p.on("request",lambda request:
             network.append(request.url) if request.url.startswith(
                 ("http://","https://")) else None)
        p.on("pageerror",lambda err:errors.append(str(err)))
    page=ctx.new_page()
    capture_events(page)
    started=time.monotonic()
    record={"profile":name,"engine":engine,"browser_version":browser.version,
            "physical_iphone":False,"real_iphone_safari":False,
            "offline":True,"cases":[]}
    try:
        if engine=="webkit":
            # Linux WebKit may reject file:// in its sandbox. Probe separately
            # and never report a successful in-memory run as a file:// pass.
            try:
                page.goto(html.resolve().as_uri(),wait_until="domcontentloaded",
                          timeout=90000)
                record["file_url_navigation"]="success"
                record["page_load_method"]="file_url"
            except Exception as file_error:
                record["file_url_navigation"]="failed"
                record["file_url_error"]=str(file_error).split("\\n",1)[0][:220]
                page.close()
                page=ctx.new_page()
                capture_events(page)
                page.goto("about:blank",wait_until="domcontentloaded")
                page.set_content(html.read_text(encoding="utf-8"),
                                 wait_until="domcontentloaded",timeout=90000)
                record["page_load_method"]="in_memory_local_html_bytes"
        else:
            page.goto(html.resolve().as_uri(),wait_until="domcontentloaded",
                      timeout=90000)
            record["file_url_navigation"]="success"
            record["page_load_method"]="file_url"
        page.evaluate("""() => {
            let last=performance.now();
            window.__phase5HeartbeatMaxGap=0;
            window.__phase5HeartbeatCount=0;
            window.__phase5HeartbeatTimer=setInterval(()=>{
                const now=performance.now();
                window.__phase5HeartbeatMaxGap=Math.max(
                    window.__phase5HeartbeatMaxGap,now-last);
                window.__phase5HeartbeatCount++;
                last=now;
            },100);
        }""")
        if page.locator("#combined-run").is_enabled() or page.locator("#combined-preview").is_visible():
            raise AssertionError("Unproven two-pool preview already enabled")
        for index,(case,(shift_count,staff,filled)) in enumerate(CASES.items()):
            page.locator("#scenario").select_option(case)
            if index:
                if "請重新執行求解" not in page.locator("#status").inner_text():
                    raise AssertionError("Old case falsely remains approved after selection")
                if (page.locator("#vacancy-details").is_visible() or
                        page.locator("#vacancy-details").get_attribute("open") is not None or
                        page.locator("#vacancy-list li").count() or
                        page.locator("#roster-preview").is_visible() or
                        page.locator("#roster-days li").count()):
                    raise AssertionError("Old case preview or vacancy state remained active")
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
                    raise AssertionError("Incorrect night/noon/long-shift hardship browser field "+
                                         key+": "+text[:500])
            mode=result.get("execution_mode")
            if mode not in ("dedicated-worker","main-thread-fallback"):
                raise AssertionError("Missing true execution mode provenance")
            if engine=="chromium" and mode!="dedicated-worker":
                raise AssertionError("Chromium failed to use Web Worker for offline WASM")
            if (result["elapsed_ms"]>=5000 and mode=="dedicated-worker" and
                    page.evaluate("window.__phase5HeartbeatMaxGap")>2500):
                raise AssertionError("Worker solver stalled browser main thread")
            vacancies=result.get("vacancies")
            if (not isinstance(vacancies,list) or
                    len(vacancies)!=shift_count-filled or
                    len({(v.get("day"),v.get("slot")) for v in vacancies})!=len(vacancies)):
                raise AssertionError("Missing or duplicated unfilled-shift list")
            summary=page.locator("#summary").inner_text()
            if ("已排 "+str(filled)+" 班" not in summary or
                    "缺班 "+str(shift_count-filled)+" 班" not in summary):
                raise AssertionError("Incorrect visible vacancy summary")
            details=page.locator("#vacancy-details")
            expected_days=len({v["day"] for v in vacancies})
            if vacancies:
                if not details.is_visible():
                    raise AssertionError("Full vacancy list is hidden")
                if page.locator("#vacancy-list li").count()!=expected_days:
                    raise AssertionError("Grouped vacancy days do not match solver")
                if details.get_attribute("open") is not None:
                    raise AssertionError("New vacancy list must start collapsed")
                page.locator("#vacancy-title").click()
                if not page.locator("#vacancy-list").is_visible():
                    raise AssertionError("Vacancy details cannot be expanded")
                lines=page.locator("#vacancy-list li").all_inner_texts()
                for v in vacancies:
                    line=next((line for line in lines if line.startswith(
                        str(v["day"])+"日：")),None)
                    if line is None:
                        raise AssertionError("Vacancy day not displayed")
                    if "第"+str(v["slot"])+"班" not in line:
                        raise AssertionError("Vacancy slot not displayed on correct day")
            elif details.is_visible() or page.locator("#vacancy-list li").count():
                raise AssertionError("Stale vacancy list remains after complete fill")
            roster=page.locator("#roster-preview")
            if not roster.is_visible():
                raise AssertionError("Full synthetic-month roster preview is hidden")
            if roster.get_attribute("open") is not None:
                raise AssertionError("New roster preview should start collapsed")
            if page.locator("#roster-days .roster-day").count()!=shift_count//(12 if case.startswith("door") or case=="tiny" else 7):
                raise AssertionError("Missing one or more preview days")
            if page.locator("#roster-days li").count()!=shift_count:
                raise AssertionError("Truncated synthetic-month roster preview")
            roster.locator("summary").click()
            if not page.locator("#roster-days").is_visible():
                raise AssertionError("Synthetic-month roster cannot be expanded")
            preview_lines=page.locator("#roster-days li").all_inner_texts()
            if sum("｜缺班" in line for line in preview_lines)!=shift_count-filled:
                raise AssertionError("Preview hides or changes unfilled shifts")
            if any("虛構人員" not in line and "缺班" not in line for line in preview_lines):
                raise AssertionError("Preview has an unrecognized person or blank shift")
            if result.get("status") not in ("OPTIMAL","FEASIBLE"):
                raise AssertionError("No legal WASM result")
            if result["final_abs_deviation"]>result["phase1_abs_deviation"]:
                raise AssertionError("Count fairness worsened baseline")
            if case=="tiny" and result["final_abs_deviation"]!=0:
                raise AssertionError("Exact toy count fairness not achieved")
            if result.get("fairness_optimal_proven") and result.get("fair_phase")!="OPTIMAL":
                raise AssertionError("Forged count fairness optimality")
            if result.get("hardship_phase") not in ("OPTIMAL","FEASIBLE","UNKNOWN"):
                raise AssertionError("Invalid 3rd-stage hardship phase")
            before=result.get("hardship_initial_score")
            after=result.get("hardship_final_score")
            if (type(before) is not int or type(after) is not int or
                    before < 0 or after < 0 or after > before):
                raise AssertionError("Third-stage hardship score worsened or missing")
            if result.get("hardship_optimal_proven") and result["hardship_phase"]!="OPTIMAL":
                raise AssertionError("False hardship optimality report")
            if page.locator("#combined-run").is_enabled()!=(case=="door-forced-vacancies"):
                raise AssertionError("Two-pool preview activation not proof-gated")
            record["cases"].append({
                "name":case,"filled":result["filled"],
                "execution_mode":mode,
                "main_thread_max_heartbeat_gap_ms":round(page.evaluate(
                    "window.__phase5HeartbeatMaxGap"),2),
                "phase1_abs_deviation":result["phase1_abs_deviation"],
                "final_abs_deviation":result["final_abs_deviation"],
                "fill_phase":result["fill_phase"],"fair_phase":result["fair_phase"],
                "hardship_phase":result["hardship_phase"],
                "hardship_initial_score":before,
                "hardship_final_score":after,
                "elapsed_ms":result["elapsed_ms"],"accepted":True})
        page.locator("#combined-run").click()
        combined_status=page.locator("#combined-status").inner_text()
        if "✅" not in combined_status or "缺班 12 班" not in combined_status:
            raise AssertionError("Two-pool combined approval did not pass")
        combined=json.loads(page.locator("#combined-output").inner_text())
        for key,expected in {
            "accepted":True,"format":"guard-cpsat-synthetic-preview-v1",
            "schema_shape":"v7-month-schedule-rows-v1",
            "month":"2026-12","rows":589,"filled":577,"missing":12,
            "door_rows":372,"officer_rows":217,
            "synthetic_only":True,"preview_only":True,
            "importable_as_v7_backup":False,"operationally_certified":False,
            "full_v7_rule_parity_verified":False,
            "real_iphone_safari_verified":False,
        }.items():
            if combined.get(key)!=expected:
                raise AssertionError("False combined v7 preview field "+key)
        if not page.locator("#combined-preview").is_visible():
            raise AssertionError("Combined roster details hidden")
        if page.locator("#combined-days h3").count()!=2:
            raise AssertionError("Both duty pools were not identified")
        if page.locator("#combined-days .roster-day").count()!=62:
            raise AssertionError("Combined roster lost a day")
        if page.locator("#combined-days li").count()!=589:
            raise AssertionError("Combined 589-shift preview was truncated")
        page.locator("#combined-preview summary").click()
        lines=page.locator("#combined-days li").all_inner_texts()
        if sum("｜缺班" in line for line in lines)!=12:
            raise AssertionError("Combined preview concealed missing shifts")
        if not any("SIM_D_" in line for line in lines):
            raise AssertionError("Missing anonymous door personnel")
        if not any("SIM_O_" in line for line in lines):
            raise AssertionError("Missing anonymous officer personnel")
        page.locator("#scenario").select_option("tiny")
        if (page.locator("#combined-preview").is_visible() or
                page.locator("#combined-days li").count() or
                '"accepted": true' in page.locator("#combined-output").inner_text()):
            raise AssertionError("Stale combined preview survived scenario change")
        record["combined_preview"]={
            "accepted":True,"rows":combined["rows"],"filled":combined["filled"],
            "missing":combined["missing"],"importable_as_v7_backup":False
        }
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
            page.screenshot(path="hardship-"+name+"-failure.png",
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
    parser.add_argument("--browser",choices=("chromium","webkit"),default="chromium",
                        help="WebKit is a Linux engine check, not physical iPhone Safari")
    args=parser.parse_args()
    if not args.html.is_file() or args.html.stat().st_size<100000:
        raise SystemExit("Genuine full-month night/noon/long-shift hardship WASM HTML missing or too small")
    with sync_playwright() as p:
        browser=(p.chromium.launch(headless=True,args=["--no-sandbox"])
                 if args.browser=="chromium" else
                 p.webkit.launch(headless=True))
        try:
            runs=[run(browser,args.html,False,args.browser),
                  run(browser,args.html,True,args.browser)]
        finally:
            browser.close()
    report={
        "accepted":all(x["accepted"] for x in runs),
        "browser_engine":args.browser,
        "linux_engine_only":True,
        "real_offline_chromium_executed":args.browser=="chromium",
        "real_offline_webkit_executed":args.browser=="webkit",
        "real_iphone_safari_verified":False,
        "complete_operational_roster_verified":False,
        "objective":"legal_fill_then_count_L1_then_locked_hardship_weighted_L1",
        "runs":runs
    }
    report_path=("hardship_month_browser_proof.json" if args.browser=="chromium"
                 else "hardship_month_webkit_proof.json")
    Path(report_path).write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report["accepted"]:
        raise SystemExit("Real offline "+args.browser+" hardship WASM acceptance FAILED")


if __name__=="__main__":
    main()
