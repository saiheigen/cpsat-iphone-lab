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
