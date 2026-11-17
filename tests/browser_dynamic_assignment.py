#!/usr/bin/env python3
"""Actual offline Chromium acceptance of *dynamic* OR-Tools CP-SAT WASM page.

All scenarios are synthetic, limited to the 64/24 prototype, and independently
checked by the page against exact enumeration. No personnel or duty dates.
This is a real browser engine test, NOT iOS Safari and NOT full 589-shift solve.
"""
from pathlib import Path
import argparse
import json
import time

from playwright.sync_api import sync_playwright

SCENARIOS = {
    "four": ("OPTIMAL", 4),
    "single": ("OPTIMAL", 1),
    "elig": ("OPTIMAL", 2),
    "infeasible": ("INFEASIBLE", None),
}


def test_profile(browser, html, mobile):
    profile = "mobile-chromium" if mobile else "desktop-chromium"
    context = browser.new_context(
        viewport={"width": 390, "height": 844} if mobile else
                 {"width": 1280, "height": 800},
        device_scale_factor=3 if mobile else 1,
        is_mobile=mobile, has_touch=mobile, offline=True)
    page = context.new_page()
    network = []
    errors = []
    page.on("request", lambda request:
            network.append(request.url) if request.url.startswith(
                ("http://", "https://")) else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    start = time.monotonic()
    output = {"profile": profile, "engine": "Chromium",
              "offline": True, "real_iphone_safari": False, "scenarios": []}
    try:
        page.goto(html.resolve().as_uri(), wait_until="domcontentloaded",
                  timeout=90000)
        for scenario, (status, filled) in SCENARIOS.items():
            page.locator("#scenario").select_option(scenario)
            page.locator("#run").click(timeout=20000)
            page.wait_for_function(
                """() => document.getElementById('status').textContent.includes('通過')
                || document.getElementById('status').textContent.includes('失敗')""",
                timeout=90000,
            )
            label = page.locator("#status").inner_text()
            raw = page.locator("#output").inner_text()
            if "驗證通過" not in label:
                raise AssertionError("Dynamic CP-SAT page failed: " + label + " / " + raw[:900])
            result = json.loads(raw)
            if (result.get("accepted") is not True or
                    result.get("scenario") != scenario or
                    result.get("status") != status or
                    result.get("filled") != filled or
                    result.get("oracle_max_fill") != (-1 if filled is None else filled) or
                    result.get("runtime") != "this-device" or
                    result.get("real_iphone_verified") is not False):
                raise AssertionError("Dynamic page misreported solver result: " + raw)
            output["scenarios"].append({
                "name": scenario, "status": status,
                "filled": filled, "runtime_ms": result.get("elapsed_ms"),
                "accepted": True})
        if network:
            raise AssertionError("Unexpected network access by offline solver page")
        if errors:
            raise AssertionError("Unhandled page exception: " + "; ".join(errors))
        output.update({"accepted": True, "elapsed_s": round(time.monotonic()-start, 3),
                       "http_requests": network, "pageerrors": errors})
    except Exception as exc:
        output.update({"accepted": False, "error": str(exc),
                       "elapsed_s": round(time.monotonic()-start, 3),
                       "http_requests": network, "pageerrors": errors})
        try:
            page.screenshot(path=f"dynamic-{profile}-failure.png", full_page=True,
                            timeout=5000)
        except Exception:
            pass
    finally:
        context.close()
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    args = parser.parse_args()
    if not args.html.is_file() or args.html.stat().st_size < 100000:
        raise SystemExit("Not a large bundled genuine dynamic WASM HTML")
    with sync_playwright() as driver:
        browser = driver.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            tests = [test_profile(browser, args.html, False),
                     test_profile(browser, args.html, True)]
        finally:
            browser.close()
    report = {"accepted": all(t["accepted"] for t in tests),
              "test_type": "actual-offline-Chromium-dynamic-WASM",
              "genuine_ortools_proof_required": True,
              "iphone_safari_verified": False,
              "full_589_shift_solver_verified": False,
              "tests": tests}
    Path("dynamic_browser_proof.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["accepted"]:
        raise SystemExit("Dynamic WASM browser acceptance failed")


if __name__ == "__main__":
    main()
