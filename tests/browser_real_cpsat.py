#!/usr/bin/env python3
"""Real browser acceptance for offline, verified CP-SAT WebAssembly HTML.

Runs ACTUAL Emscripten + Google OR-Tools CP-SAT in headless Chromium. Chrome
mobile emulation is NOT iPhone/Safari testing. No roster data is involved.
Any HTTP(S) resource request, JS pageerror, or incorrect optimum fails.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

from playwright.sync_api import sync_playwright

EXPECTED = {"engine": "Google OR-Tools CP-SAT", "status": "OPTIMAL",
            "desks": 0, "tables": 3, "profit": 90}


def run(browser, path, profile):
    mobile = profile.startswith("mobile-")
    opts = {
        "viewport": {"width": 390, "height": 844} if mobile else
                    {"width": 1280, "height": 800},
        "device_scale_factor": 3 if mobile else 1,
        "is_mobile": mobile,
        "has_touch": mobile,
        "offline": True,
    }
    context = browser.new_context(**opts)
    page = context.new_page()
    network_requests = []
    errors = []
    page.on("request", lambda request:
            network_requests.append(request.url)
            if request.url.startswith(("http://", "https://")) else None)
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    started = time.monotonic()
    result = {"profile": profile, "browser": browser.browser_type.name,
              "real_iphone_safari": False, "offline": True}
    try:
        page.goto(path.resolve().as_uri(), wait_until="domcontentloaded", timeout=90000)
        page.locator("#run").click(timeout=20000)
        page.wait_for_function(
            """() => {
                const t=document.getElementById('status').textContent;
                return t.includes('通過') || t.includes('失敗') || t.includes('未通過');
            }""",
            timeout=120000,
        )
        status_text = page.locator("#status").inner_text()
        output_text = page.locator("#output").inner_text()
        if "實測通過" not in status_text:
            raise AssertionError("Browser CP-SAT result not accepted: " +
                                 status_text + " / " + output_text[:1200])
        data = json.loads(output_text)
        if data.get("passed") is not True:
            raise AssertionError("Browser did not report accepted CP-SAT run")
        if any(data.get("got", {}).get(k) != v for k, v in EXPECTED.items()):
            raise AssertionError("Browser solver values differ from independent oracle")
        if data.get("runtime") != "this-device":
            raise AssertionError("Remote runtime unexpectedly used")
        if network_requests:
            raise AssertionError("Offline file attempted network requests")
        if errors:
            raise AssertionError("Unhandled browser errors: " + ";".join(errors))
        result.update({
            "accepted": True, "status_text": status_text,
            "solver_result": data["got"],
            "reported_runtime_ms": data.get("ms"),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "user_agent": data.get("userAgent"),
            "http_requests": network_requests,
            "unhandled_browser_errors": errors,
        })
    except Exception as exc:
        result.update({
            "accepted": False, "error": str(exc),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "http_requests": network_requests,
            "unhandled_browser_errors": errors,
        })
        try:
            page.screenshot(path=f"browser-cpsat-{profile}-failure.png",
                            full_page=True, timeout=5000)
        except Exception:
            pass
    finally:
        context.close()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    args = parser.parse_args()
    if not args.html.is_file() or args.html.stat().st_size < 100000:
        raise SystemExit("Genuine, bundled HTML file missing or too small")

    with sync_playwright() as p:
        chromium = p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            tests = [
                run(chromium, args.html, "desktop-chromium"),
                run(chromium, args.html, "mobile-chromium"),
            ]
        finally:
            chromium.close()
        webkit = p.webkit.launch(headless=True)
        try:
            tests.append(run(webkit, args.html, "mobile-webkit"))
        finally:
            webkit.close()
    report = {
        "accepted": all(t["accepted"] for t in tests),
        "test_type": "actual-offline-Chromium-and-Linux-WebKit-not-iOS-Safari",
        "source": "previously-Node-verified-genuine-OR-Tools-WASM-artifact",
        "does_not_prove": [
            "iPhone real Safari", "589-shift WASM solver",
            "native roster integration", "operational schedule rules",
        ],
        "tests": tests,
    }
    Path("browser_cpsat_acceptance.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["accepted"]:
        raise SystemExit("At least one offline Chromium CP-SAT check FAILED")


if __name__ == "__main__":
    main()
