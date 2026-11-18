# Phase 5 — Dedicated Worker genuine offline CP-SAT acceptance

**Scope:** synthetic-only offline page; not the physical iPhone Safari, not the v7 operational scheduler, and not approval of all military constraints. No actual military personnel, availability masks, schedules or duty events were used.

## Changes

- `src/phase5_hardship_worker.js`: contains the dedicated Worker bootstrap. The attested Emscripten glue is prepended within a Blob URL created at runtime from the same self-contained HTML; the actual WASM binary is transferred to the Worker once (no external script import, CDN, network request or new compilation).
- `build/package_month_hardship_wasm.py`: packages the Worker into the same single-page HTML, prioritizes it for `solve_guard_month_harsh_v4`, keeps an explicitly labeled main-thread fallback if a Worker cannot start, locks the scenario selector while solving, and preserves the independent audit and explicit vacancy counters.
- `tests/test_package_month_hardship_wasm.py`: validates the full generated browser JavaScript and source Worker syntax, while continuing to treat its artificial WASM data as **not proof**.
- `tests/browser_month_hardship_wasm.py`: records execution mode and maximum observed main-thread heartbeat gap; requires the real Worker in offline Chromium. The WebKit execution mode is observed rather than falsely assumed.
- `.github/workflows/phase5-offline-webkit.yml`: **rebuilds current branch Worker-enabled HTML** from previously attested genuine C++/WASM binaries, reruns the actual independent CP-SAT audit and browser tests. It does not re-test a stale pinned HTML file.

## Actual GitHub evidence — 2026-11-18

- [Offline desktop/mobile Chromium Worker acceptance #44237911822](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44237911822): **completed/success**. All four scenarios passed under each profile; `execution_mode=dedicated-worker`. Desktop max observed heartbeat interval was about **166.6 ms** throughout multiple 12–22 second CP-SAT solves (not an iPhone performance measurement). All vacancy and combined 589-row assertions passed. No external HTTP requests or uncaught JavaScript exceptions.
- [Offline Linux WebKit acceptance #44237912018](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44237912018): **completed/success for solver and UI**, all four scenarios per profile; however `execution_mode=main-thread-fallback` in WebKit 26.0. Its fallback was visibly blocking: desktop `main_thread_max_heartbeat_gap_ms≈20273`. **WebKit has NOT passed nonblocking Worker acceptance**. It also still rejects `file://` in this Linux test setup and loads the same local HTML bytes into about:blank instead; neither result certifies iOS Safari.
- [Real WASM integration #44237911809](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44237911809): **completed/success**.
- [Synthetic adapter/v7 preview regression #44237911863](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44237911863): **completed/success**.

The observed WebKit fallback is deliberately retained to keep the synthetic test usable. **Do not claim that the iPhone UI cannot freeze**, or that WebKit file opening works, based on these results. The browser report separates runtime, loading method, optimality status and physical-device identity.

## Next acceptance gates

1. Identify why Linux WebKit cannot start the Blob Worker in its `about:blank` test context; test a supported origin/load method separately from the actual WASM runtime. Do not silently mark fallback as background-safe.
2. Test actual Safari on a real iPhone with only the fictional HTML. Measure initial load, multi-case memory and the maximum UI nonresponsive interval. A Files Quick Look or a different webview is not equivalent to Safari.
3. Audit full v7 hard rules, cross-month archive freshness, imported data isolation and approval flow before enabling operational records.
