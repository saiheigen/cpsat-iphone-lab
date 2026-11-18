# Phase 5 — synthetic browser Worker fault recovery and cancellation

Scope: the single-file **fictional** genuine CP-SAT WebAssembly experiment. This is NOT a production military roster, an iPhone Safari real-device certification, or a complete v7 rule-parity test.

## Recovery rules

1. A new genuine C++/WASM solve should prefer a dedicated Web Worker when available.
2. If Worker startup times out or fails, clear the cached startup Promise so a later attempt can retry; retain a **labeled** main-thread fallback on browsers where Workers cannot start.
3. If Worker sends an error, cannot decode a message, or stops responding, reject pending solves. **Never** turn a missing/failed reply into an accepted schedule.
4. Track the one-time transferable `.wasm` binary **per Worker instance**. On Worker termination or reset, clear the transferred-binary flag so the next Worker receives a fresh copy.
5. An in-flight solve has a 90-second **browser-side watchdog**, after which its results must not be adopted. This is a synthetic experiment bound, not a guarantee that every phone completes in 90 seconds.
6. The user-facing **取消目前的背景求解** cancels an in-flight Worker, increments the generation and terminates that worker. No later response from the previous generation is eligible to publish a roster.
7. The user-facing **重啟本機運算引擎並清空預覽** explicitly drops local solver state, combined previews, vacancy rows, approved fictional pool results, captured phone self-check metrics and any previously generated copyable report.
8. Cancellation cannot preempt **synchronous main-thread fallback** while JavaScript is blocked. The UI must not claim to provide background cancellation in that mode. Do not treat synthetic browser emulation as actual iOS memory/CPU evidence.

## CI regression

`tests/browser_month_hardship_wasm.py` now tests four genuinely solved anonymous scenarios and then, for each browser profile:

- Explicit restart clears accepted single-pool/589-row previews and the old iPhone self-check.
- A simulated Worker `error` event after `ready` must cause failure without accepting any schedule; a new genuine tiny WebAssembly CP-SAT solve must recover afterward.
- On Worker-capable Chromium and WebKit zero-external-egress profiles, start a real long-month case, cancel it, ensure no stale approved result, and successfully solve again.
- On WebKit's Playwright forced-offline **main-thread fallback**, test restart but **skip preemptive cancel** and report the limitation explicitly rather than claiming success.
- No real military names, duty information or eligibility masks are introduced. No external HTTP/HTTPS connections are permitted.

Keep evidence links scoped to the exact committed CI run. **A GitHub Actions run only counts as passed when completed with conclusion success.** Do not claim physical iPhone Safari or real-device memory behavior without separately observed real-device test results.

## Completed evidence — 2026-11-18

- [Chromium real-WASM browser CI #44257072735](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44257072735): **completed / success**. Desktop and mobile-sized emulation both passed the real solver, combined fictional schedule, explicit engine restart, simulated Worker error, fresh-worker recovery, cancellation of a long synthetic run, and another genuine tiny CP-SAT solve. Both records had `fault_injected=true`, `cancelled_real_long_job=true`, `stale_result_rejected=true`, `subsequent_genuine_worker_solve_passed=true`.
- [Linux WebKit dual-policy CI #44257072838](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44257072838): **completed / success**. Four profile/policy combinations exercised Worker restart. The **two zero-external-egress profiles** verified genuine dedicated-worker error injection and cancellation/recovery (2/2). The **two Playwright forced-offline main-thread fallback profiles** verified restart but **did not claim preemptive cancellation**. Every result remains synthetic, and actual iPhone Safari has not been tested.
- [Genuine C++ WASM adapter integration #44256772292](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44256772292) and [synthetic boundary regression #44256772223](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44256772223): **completed / success**.
- The Chromium UI artifact ZIP and directly extracted `experimental_full_month_hardship_cp_sat.html` are available from the successful Chromium workflow's artifact. No operational duty data was used.

**Limits:** The 90-second timeout is a policy of this test UI, not a maximum on every phone. Repeated Worker resets and synthetic runs do not establish long-term iPhone memory stability. Full v7 cross-month/leave/inspection/vehicle/roster approval remains unimplemented or unverified; no official duty schedule is certified.
