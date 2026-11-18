# Phase 5 — Linux WebKit compatibility gate (NOT physical iPhone Safari)

This stage adds a real **Linux WebKit engine** test that loads the same immutable, proof-gated synthetic standalone CP-SAT/WASM HTML as the successful Chromium run.

- Pinned source artifact: https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44235028475
- Engine-specific CI: `.github/workflows/phase5-offline-webkit.yml`
- Shared acceptance runner: `tests/browser_month_hardship_wasm.py --browser webkit`
- Same four fictional scenarios, the same independently audited solver response, 589-shift combined preview, explicit 12 vacant duties and zero external HTTP requests.
- Two Linux profiles: desktop WebKit and touch-enabled mobile-sized WebKit; **neither** is a real iPhone nor an iOS Safari process.

## Known first-run observation — not yet a WebKit success

Linux WebKit 26.0 initially reported `Page.goto: WebKit encountered an internal error` when directly navigating to a `file://` HTML artifact (both desktop and mobile-sized contexts). This failure happened **before** any CP-SAT solve. It does not establish that iPhone Safari cannot run the solver. The original Chromium runner with the same file passed.

To isolate that problem, the runner now records the exact `file_url_navigation` result and—*only if the WebKit file navigation fails*—loads the same local HTML bytes in the browser via Playwright `page.set_content` at `about:blank`. This still runs the genuine embedded C++/WASM with the network disabled, but **does not prove file:// loading**. The report contains `page_load_method` and `file_url_error` (if any), and keeps `real_iphone_safari_verified=false`.

**Acceptance must be scoped to observed evidence:**
1. If the WebKit engine test succeeds with `page_load_method=in_memory_local_html_bytes`, record **WebKit offline runtime passed; WebKit file:// not proven**.
2. If it fails, record **WebKit compatibility failed** and preserve logs/screenshots; do not change solver correctness claims.
3. Independently test real-device Safari opening mechanism and actual offline behavior per `docs/phase5-real-iphone-safari-manual-check.md`.
4. Never promote a synthetic demo to an operational military scheduler or import the preview into v7.

No original v2/v3 release artifact is overwritten; nothing from real military rosters or eligibility is committed.
