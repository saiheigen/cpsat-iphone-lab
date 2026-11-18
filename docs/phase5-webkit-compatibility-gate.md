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

## Verified results — 2026-11-18 (Taiwan)

- [WebKit compatibility run #44236138486](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44236138486): **completed/success** for offline genuine WASM execution in Linux WebKit **26.0** desktop and touch-sized emulation.
- Four scenarios per profile (**8/8**): the genuine CP-SAT completed, independent audit passed, combined fictional **589 rows = 577 staffed + 12 vacancies** was checked; no external HTTP requests or unhandled page errors.
- Crucial caveat: **both WebKit profiles rejected direct `file://` navigation**. Both successful runs used `page_load_method=in_memory_local_html_bytes`, with the local HTML rendered into `about:blank`. The original `file://` opening path remains **failed in Linux WebKit**, not accepted. Safari on a real iPhone still needs separate real-device testing.
- [Chromium regression run #44236138326](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44236138326): **completed/success** on unchanged offline Chromium file-path acceptance.
- [Genuine WASM adapter regression #44236138522](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44236138522): **completed/success**.
- Solver phase limits are visible: WebKit door 372/372 had `fair_phase=UNKNOWN` with L1=444 (not improved); door forced-vacancy 360/372 had `fair_phase=FEASIBLE` and L1 150→86; officer 217/217 had `fair_phase=OPTIMAL`, L1 166→10. **No unproven global fairness-optimality claim.** Browser engines and runtime budgets can produce different valid (and differently optimized) solutions.

Current acceptance summary: **WebKit offline engine/WASM success; direct WebKit file navigation failed; physical iPhone Safari still PENDING; operational v7 rule parity PENDING**.
