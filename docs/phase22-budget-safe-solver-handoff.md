# Phase 22 — Budget-safe synthetic v7-like archive → full-month WASM handoff

Date: 2026-11-18, Taiwan time. Branch: `phase20-budget-safe-rollover`.
**All people/events are invented.** This work does not use or certify real military rosters, personnel names, duty events, approved archives, or v7 backups.

## Actual implementation

- `solver/phase22_synthetic_solver_handoff.py`: read only `SIM_D_###` and `SIM_O_###` person IDs and the previous phase's anchored, locked *invented* November archive. It first calls the Phase 21 full-calendar cross-month legality gate, checking all 570 prior rows.
- Independently compare SHA-256 of the previous archive, prior/current sources, event ledger, and pinned slots against **caller-supplied** expected digests. These fingerprints only detect changes relative to an anchor; they do not authenticate source ownership or a v7 `inputSig`.
- Recompute candidate eligibility from archived prior shift history and fabricated leave, driver, training, meal, night inspection and exemptions. Hard exclusions are encoded in the `mask` before scheduling; fixed vacancies and legal person pins are checked separately. The current month's full **372 guard + 217 officer slots** are encoded as strict eight-line `guard-month-harsh-v4` frames with anonymous per-pool indexes, with **56 guard + 50 officer** fictional staff.
- Compute fairness soft targets from the **actual reconstructed eligible-bit counts**, rather than assuming previously entered full-month capacity is the real candidate pool. Carry-over is derived from Phase 20's independently recomputed previous-month worked counts, not an unverified summary.
- Reconstruct the original frames and anchors when inspecting a possible WASM result; reject tampered wire, invalid staff index, prohibited assignment, overwritten vacancy, altered pin, false count, missing month slot, and within/cross-month pairwise duty conflict. The independent post-solve check proves *feasibility only*, never mathematical optimality or runtime identity from self-reported response fields.
- Source files and tests were copied **byte-for-byte** from the locally executed Python environment to this branch. The pure-Python code does **not** itself invoke the C++ WASM binary or connect to the browser.

## Local tests: 73/73

Run on a machine with Python 3 and no OR-Tools or network requirement:

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_phase20_synthetic_rollover.py' -q
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_phase21_synthetic_cross_month_gate.py' -q
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_phase22_synthetic_solver_handoff.py' -q
```

Totals: Phase 20 = **16**, Phase 21 = **33**, Phase 22 = **24**. All passed locally.

## Separate actual offline C++/WASM local replay

The known prior verified, **synthetic iPhone HTML** embedded a real WebAssembly binary. We extracted that existing binary and Emscripten glue locally, confirmed `WebAssembly.validate(...)`, and verified its SHA-256:

`8929b0d8d98391b557a5d37f681459edf1099d2da7c7a2e6be05f6979b0b993d`

The original broadly eligible 106-person two-pool handoff proved computationally challenging. At least the **door first stage returned `UNKNOWN` within its 10-second solver limit**; this is not a legal or optimal solve. We did **not** erase the original event prohibitions to make that pass.

For independent end-to-end transport verification, a *separate sparse invented case* explicitly marked all non-participating December dates as `exempt_all`, while retaining both source-derived month boundaries and forced pins. This created just **12 allowed guard/person/shift bits** and **7 allowed officer bits** over the full 589-row grid.

The same real CP-SAT C++/WASM binary produced:

| Fictional pool | Calendar rows | Filled | Vacancies | C++ status | Three stages | Local measured time |
| --- | ---: | ---: | ---: | --- | --- | ---: |
| Guard | 372 | 3 | 369 | `OPTIMAL` | All reported `OPTIMAL` | 158 ms |
| Officer | 217 | 1 | 216 | `OPTIMAL` | All reported `OPTIMAL` | 32 ms |

The output assignments were then **reconstructed and independently re-audited with Python** against the original fake November archive, cross-month rest and fake December exclusion events. Audit passed: **589 rows, 4 filled, 585 deliberately vacant**. This is a **sparse functional integration check**, not a dense staffing benchmark. The independently verified property is assignment feasibility; all solver optimality fields remain external solver reports.

A safe summary is included in the user's local artifact under `phase22_local_synthetic_wasm_proof.json`. Full fake masks, assignments and private Emscripten binaries are **not** committed or put in Actions artifacts.

## Zero new Actions usage on Phase 22 branch

No `workflow_dispatch`, recompile, `pull_request` or workflow changes were made. The existing historical 31 workflow files have no matching automatic trigger for these new Phase 22 file paths on this non-main branch. The branch had **0 runs** when checked. This says nothing about the user's account-wide spending, Budgets and alerts configuration or concurrent activity on other branches.

## Release blockers

1. The actual original editable v7 HTML and its `inputSig` signing/freshness process have **not** been authenticated or incorporated; digests here are only source consistency checks.
2. Real staff/leave/transport/inspection/meal data completeness, privacy, approval and local-only persistence remain unverified. No official roster import/export.
3. The local replay is not proof of physical iPhone Safari, airplane mode or sustained mobile performance; that separate previous device report was Files-app embedded preview and manually selected network status.
4. The **dense realistic-capacity full-month** performance still requires solver hints, time-budget design and evidence-backed tuning before any operational interface. A returned `UNKNOWN` cannot be silently interpreted as a blank legal schedule.
5. v7 equivalence of the complete set of rules, credits, signed archives, approvals and equitable hardship metrics has not been proven.

**Release decision: fictional engineering test PASS; operational usage BLOCKED.**
