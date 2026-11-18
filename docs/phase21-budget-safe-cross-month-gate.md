# Phase 21 — Cross-month duty legality and archive carry guard

Date: 2026-11-18 (Asia/Taipei). **Synthetic local proof only.**
Branch: \`phase20-budget-safe-rollover\` (no pull request; changes do not activate existing workflow path filters). All identifiers begin \`SIM_\`; do not upload genuine personnel rosters, events, dates, eligibility matrices or archive backups.

## What was implemented

- \`solver/phase21_synthetic_cross_month_gate.py\` — independent pure-Python, *fictional-only* inspection of every November 2026 archived duty position and every December 2026 proposed position, after the existing Phase 20 archive fingerprint / carry validation has passed.
- \`tests/test_phase21_synthetic_cross_month_gate.py\` — **33 local tests** designed to detect copied or invented incompatible duty history, next-day assignments, same-slot two-day conflicts, following-Sunday standby, incorrect rest between two door shifts on one day, duplicate officer duty, a full December grid truncated or reordered, unknown and wrong-pool fictional staff, malformed event dates and false archive fingerprints.
- Prior November archive: **570 complete rows** (360 door, 210 officer), created with four rotating imaginary staff cohorts to respect the model's partial within-month rest rules. December proposed input: **589 complete positions** (372 door, 217 officer), with explicit \`None\` vacancies and a small lawful example. The two months are joined *without* ignoring the previous month's final two days or preceding Sunday.
- The new prior archive is intentionally **different from the Phase 20 count-arithmetic-only fixture**; Phase 20's synthetic row assignments were not a legal roster witness. We rebuild the Phase 20 carry snapshot using the legally spaced invented month, recompute observed counts and carry, and then independently verify the archive again before assessing any new duty.

## Important synthetic fail-closed tests

| Case | Expected behavior |
| --- | --- |
| Nov 30 duty → Dec 1 duty for same fictional person | Refused (next-day rest) |
| Nov 29 same time slot → Dec 1 same time slot | Refused (two-day repeated slot) |
| Nov 29 Sunday standby → Dec 6 Sunday standby | Refused (consecutive-Sunday standby) |
| Nov 30 leave last day → Dec 1 return day | Refused |
| Nov 30 night inspection or driver duty → Dec 1 guard/officer | Refused |
| Training next day → previous day duty | Refused |
| Two incompatible door shifts in one day | Refused |
| Two officer shifts same day | Refused |
| Changed November duties, with **new** SHA-256 fingerprints and unchanged headcounts | Still refused if prior month's historical assignments violate rest rules |
| Unknown ID, mixed duty pool, missing row, corrupt serial order, unlocked or stale archive | Refused |
| Two lawful duties across month boundary | Accepted in synthetic-only preview |

Hard constraints and reference semantics are aligned to the *partial experimental* native model, **not** an authenticated original v7.0 application. In particular, no inference is made that all real-life duty event records, permits, cancellations and signatures were complete.

## Local verification, no GitHub Actions charges

Run with Python 3; only Python standard library and the repository's existing \`solver/fairness_targets_v7.py\` are necessary:

\`\`\`bash
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_phase20_synthetic_rollover.py' -q
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_phase21_synthetic_cross_month_gate.py' -q
\`\`\`

**Local result:** 16/16 Phase 20 tests and 33/33 Phase 21 tests passed, **49/49 total**. Tested source file content was copied byte-for-byte to the GitHub branch. There was **no fresh GitHub Actions compilation or run** for this stage; this is not a CI acceptance result and not proof of execution on a physical iPhone.

The user-facing local bundle \`phase21_cross_month_bundle.zip\` includes the tested modules, tests and a synthetic-only proof summary. Original iPhone browser results from earlier phases remain separate.

## Persistent safety flags returned

- \`archive_digest_matches_supplied_anchor=true\` — consistency check only; **not** an authentic signature.
- \`cross_month_duty_eligibility_audited=true\` — only over supplied fabricated events and the partial native-model rule set.
- \`verified_real_v7_inputSig=false\`.
- \`archive_authenticity_verified=false\`.
- \`source_aligned_full_v7_rules_verified=false\`.
- \`genuine_wasm_executed=false\` for this phase.
- \`operationally_certified=false\`.
- \`importable_as_v7_backup=false\`.

**Operational release remains BLOCKED.** Next gates: original v7 \`inputSig\` + approved archive provenance (from authorized local source); completeness of real leave/training/night-inspection/driver/meal data; and an end-to-end local device pipeline from actual sources to true WASM (not another synthetic-only shortcut). Do not send any actual military data through GitHub Actions.