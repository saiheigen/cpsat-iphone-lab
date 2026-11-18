# Physical iPhone Safari acceptance record (still pending)

**This is a blank test record, not evidence that a phone test has passed.**
The GitHub Actions runner is Linux Chromium, including its mobile-sized emulation. It does not certify physical Safari.

## Obtain a verified, synthetic-only artifact

1. On the repository's GitHub Actions page, locate **Phase 5 genuine offline UI end-to-end acceptance** and require a green successful run.
2. Under the run's artifacts, download `phase5-genuine-offline-ui-e2e-evidence`. Confirm that it contains `experimental_full_month_hardship_cp_sat.html` and `hardship_month_browser_proof.json`.
3. Confirm that the proof says `accepted: true` and `real_iphone_safari_tested: false`. Do not alter the single-page HTML.
4. Transfer **only the synthetic demo HTML** to the test iPhone. Do not import any names, real dates of military duty, eligibility masks, schedules or private files into the demo.
5. Record how the file was opened. A Files Quick Look preview, remote browser, iOS simulator or embedded webview **is not necessarily Safari**, and must not be labeled a Safari acceptance.

## Device and offline-test record (fill in, do not pre-approve)

| Field | Observed value |
|---|---|
| Date / local time | Not tested |
| Physical iPhone model | Not tested |
| iOS version | Not tested |
| Browser app and version | Not tested |
| File-loading method / URL scheme | Not tested |
| Airplane mode and Wi-Fi/cellular disabled | Not tested |
| Fresh offline page load successful | Not tested |
| Reopen offline page successful | Not tested |
| JavaScript/WASM runtime errors | Not tested |
| Memory pressure, crash, or browser reload | Not tested |

Test all four synthetic cases **in actual Safari while offline**. Never use fabricated operational data.

| Synthetic case | Expected staffed / missing | Observed | Elapsed seconds | Result |
|---|---|---|---|---|
| `tiny` | 4 / 368 | Not tested | — | Pending |
| `door-blackouts-no-hints` | 372 / 0 | Not tested | — | Pending |
| `officer-blackouts-no-hints` | 217 / 0 | Not tested | — | Pending |
| `door-forced-vacancies` | 360 / 12 | Not tested | — | Pending |

## Two-pool read-only preview gate (pending physical Safari testing)

After successfully running `officer-blackouts-no-hints` and `door-forced-vacancies` **in the same page session**, the **顯示大門＋安官 589 班預覽** control should become enabled. Before both audits pass, it must remain disabled.

- Activate the combined preview. Verify `guard-cpsat-synthetic-preview-v1`, `rows=589`, `filled=577`, `missing=12`, `door_rows=372`, `officer_rows=217`.
- Open the read-only combined detail and inspect both 31-day pools, 12 explicit vacancies and anonymous `SIM_D_...` / `SIM_O_...` identities.
- Change the selected scenario; the combined preview must disappear instead of leaving an old approved result in view.
- Verify `importable_as_v7_backup=false`, `operationally_certified=false`, `full_v7_rule_parity_verified=false` and `real_iphone_safari_verified=false`.
- Record actual elapsed time and any iPhone memory pressure, freeze or page reload. **Do not claim Safari success based on Linux Chromium or a Files preview.**

| Combined preview | Expected | Actual device observation | Result |
|---|---|---|---|
| Dual-pool WASM-audited rows | 589 total / 577 filled / 12 missing | Not tested | Pending |
| Per-day display | 62 pool/day groups / 589 rows | Not tested | Pending |
| Remains preview-only | Not importable, no operational certification | Not tested | Pending |

Verify for each result:
- The status explicitly says the independently audited genuine WASM solution succeeded.
- The displayed staffed and missing counts match the JSON, and the full vacancy list shows every missing day/slot for a partial-fill case.
- No stale vacancy list carries over when switching from a partial-fill case to a fully filled case.
- The three objective stages and their proof/optimality flags are represented faithfully; do not mistake `FEASIBLE` for `OPTIMAL`.
- There is no internet requirement for page load or solve; explicitly note any unexpected external request.

**Fail closed:** Any failed case, unexpected script error, hidden missing shift, browser crash, unresolved loading method, or uncertain browser identity leaves physical-Safari acceptance **PENDING/FAILED**. Retest after a fix. Screenshots must only show synthetic data. This test does **not** certify a military operational roster or full absence/vehicle/inspection rules.

## Release decision

- Offline Chromium CI: require a green `Phase 5 genuine offline UI end-to-end acceptance` run.
- Physical iPhone Safari: **PENDING**, until the table above contains actual observations.
- v7.0 operational schema and rule completeness: **PENDING**.
- Security review for real military data: **PENDING**.
- v2/v3 regression artifacts: preserve; do not overwrite.
