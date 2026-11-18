# Phase 23 — budget-safe dense candidate hints and fail-closed timeout handling

Date: 2026-11-18 (Asia/Taipei). Branch: `phase20-budget-safe-rollover`.

**Scope:** Strictly invented, local-only, partial-v7 rule model. This is not a real roster importer, military schedule, official v7 `inputSig` check, or production approval. No GitHub Actions run was requested.

## Engineering result

- `solver/phase23_budget_safe_anytime.py` reconstructs anchored Phase 22 source data and independently verifies its anonymous candidate mask, real hard pins, forced vacancies and current month soft targets **before** considering a hint.
- Deterministic, bounded work builds a candidate warm-start for the existing `guard-month-harsh-v4` C++ OR-Tools WASM frame. It can propose **only** legal candidates; all original candidate bits, pins and count targets are byte-for-byte unchanged. Its work bound is a client preparation limit, not a solver-time limit.
- The invented prior 570 November assignments, original events and all proposed December assignments are independently rechecked. The returned wire contains anonymous indices, not employee identifiers, real personnel or event text.
- On the **dense invented December 2026 scenario** with 56 door and 50 officer candidates, the constructive legal preview fills 371/372 door shifts and 216/217 officer shifts (587/589 combined). One original **forced vacancy per duty pool** remains. This is not the user's previous 577/589 iPhone demo; these are unrelated fictional fixtures.
- Every non-forced position is filled in this particular artificial fixture. The trivial per-slot upper bound (at most one person per slot and forced vacancies stay vacant) **independently proves maximum possible fill for the partial fictional model**, without claiming optimal fairness, hardship equity, or source-identical v7 parity.
- `safe_timeout_verdict` does not turn `UNKNOWN`, `INFEASIBLE`, or `INVALID_INPUT` into a solver-produced solution. A true `UNKNOWN` returns **no accepted assignments**, although a separately independently audited constructive **preview-only** candidate may be used for experiments. The entire hint construction and audit are recomputed before trusting any preview flags, so forged rows, targets, hashes or proof booleans are rejected.
- Unsupported result statuses, missing pool results and forged reported schedules are refused. Reported `FEASIBLE`/ `OPTIMAL` outputs must pass the existing Phase 22 independent legality audit; this does not independently attest true WASM execution.

## What the REAL existing C++ WASM experiment showed

A previous compiled 6.7-MB genuine OR-Tools C++ WASM binary was extracted locally from the proof-gated synthetic iPhone HTML. SHA-256: `8929b0d8d98391b557a5d37f681459edf1099d2da7c7a2e6be05f6979b0b993d`.

For the same **dense invented guard matrix** of 372 shifts and 56 candidates, using the original 10-second phase-one search budget:

| Mode | Measured local duration | Real C++/WASM first-stage result |
| --- | ---: | --- |
| Without warm-start | 10,153 ms | `UNKNOWN`, no schedule |
| With the newly audited legal warm-start | 10,086 ms | `UNKNOWN`, no schedule |

The later officer comparison did not complete in that local benchmark; **no officer runtime claim is made**. **The optimization has NOT demonstrated a search-speed improvement** on this difficult dense case. A valid warm start is useful as an independently audited proposed schedule and as a candidate solver hint, not evidence that the current C++ implementation will honor it quickly.

The existing C++ source still has a first-stage `set_max_time_in_seconds(10.0)` setting. No native code was changed or recompiled in this budget-safe phase.

## Regression evidence

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_phase2*.py' -q
# Ran 97 tests, all passed locally on 2026-11-18
```

- Phase 20: 16 fictional carry/archive tests.
- Phase 21: 33 fictional November/December duty legality tests.
- Phase 22: 24 original event-to-anonymous-v4-frame/re-audit tests.
- Phase 23: **24 new** constructive warm-start, maximum-fill bound, tampering, failure-state and candidate legality tests.

No paid GitHub Actions build was dispatched. Existing unrelated workflows and account Billing/Budgets are **not** disabled.

## Next issue to solve

Real search-performance engineering requires a separate measured C++/WASM iteration: investigate symmetry, objective encoding, solver parameterization, actual use of hint values, and a clearly bounded, policy-acceptable fallback *without* relaxing any hard exclusion. Do not spend more GitHub CI minutes or advertise device readiness until budget guardrails and operational data controls have been verified.

Persistent flags remain **`real_v7_inputSig_verified=false`**, **`full_v7_rule_parity_verified=false`**, **`operationally_certified=false`** and **`importable_as_v7_backup=false`**.
