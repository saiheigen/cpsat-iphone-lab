# Phase 19 — fictional v7-style hard rules → genuine three-stage CP-SAT WASM

**Status:** This milestone is a synthetic-only eligibility transport + independent audit experiment. It is NOT a production v7.0 scheduler, never reads a real backup, and MUST NOT be represented as verified operational duty readiness.

## What is actually in the repository

- `solver/phase19_fictional_v7_hard_rules.py` constructs exactly two **hard-coded invented** complete-month scenarios for December 2026: **372 door** and **217 officer** shifts. Invented IDs are `SIM_D_...` and `SIM_O_...`; there is **no arbitrary roster importer**.
- The existing native rule/bridge code (`solver/roster_cp_sat.py`, `solver/full_month_wire_v2.py`, `solver/full_month_fair_wire_v3.py`) builds the full 31-day per-shift/person availability matrix, validates canonical order and pinned shifts, and computes local fictional soft count targets. The generated eight-line `guard-month-harsh-v4` payload intentionally omits names and event text.
- `tests/test_phase19_fictional_v7_hard_rules.py` independently asserts literal prohibition bits and rejects forged schedules or falsified stage/score flags before any real WASM claims.
- `scripts/phase19_emit_fictional_months.py` emits only these invented matrices and their SHA-256.
- `tests/phase19_genuine_v4_rule_gate.cjs` calls the **real C++ OR-Tools WASM binary**, not a JavaScript solver mimic, and checks full-month assignment legality, occupancy, fair-count and hardship statistics.
- `scripts/phase19_audit_fictional_v4.py` reconstructs both invented sources, checks source hashes, and independently audits every returned assignment against original imaginary leave, training, meal, duty, nightcheck, vehicle, exemption, kitchen, pinned and prior-month history records.
- `.github/workflows/phase19-fictional-v7-hard-rule-gate.yml` gates the above steps: native tests first, then download **previously attested** genuine WASM, rerun its proof with original JS/binary hashes, process the invented two-pool input, run independent Python audit and publish only synthetic metadata/proof.

## Rule coverage represented by the invented fixtures

| Topic | Concrete fabricated edge case | Expected hard rule |
| --- | --- | --- |
| Leave | 4–5 December and day immediately before; return 6 December | No duty during leave/return day; pre-leave night prohibited |
| Night inspection | 1 December guard, 20 December officer | Previous day, inspection day and following day fully prohibited |
| Driver | 10 December guard, 3 December officer | Prior night prohibited; driving day and following day prohibited |
| Training | 15–16 December guard, 24–25 December officer | Previous day through graduation day prohibited |
| Officer duty | 8 December | Prior day, current day and next day prohibited in this partial native event semantics |
| Meal duty | 12 December | Same three-day exclusion under current native test model; meal-count credit is separately represented in other modules |
| Fixed kitchen | Invented guard SIM_D_006 | No guard duty |
| Exemptions | All-month guard nights and midday; all-month officer general exemption | Affected shift categories remain ineligible |
| Previous-month activity | 30 November guard/officer and Sunday 29 November guard | Next-day rest, two-day same-slot and consecutive-Sunday standby stay prohibited across month boundary |
| Pins and forced vacancies | Fictional pinned 2 December guard, 5 December officer; explicit blanks | Must be preserved even when fairness or fill would prefer a different value |

These checks rely on the existing **partial** native v7-inspired semantics; they do not prove exact parity to every original v7.0 rule or post-approval state. In particular, the original v7.0 HTML is **not present in this repository**.

## Release blockers that remain

1. **Real data input completeness and freshness:** the fixed fictional events have known provenance by construction. There is no validated pipeline from actual names, leave records, in-island status, night inspection, vehicle duty, locked prior-month rosters or `inputSig` freshness. Never infer any of these from a precomputed bit matrix.
2. **Exact v7 parity:** prior records suggest detailed rules for duty officers, meal credits, business-unit work days, same-day multi-shift fairness, carry, archives and administrative release. The partial native model and v4 count/hardship objective are not source-identical to all of them.
3. **Independent optimizer proof:** auditing output proves **feasibility within the transported partial model**, not independently certifying a solver's `OPTIMAL` flag or an authorized real schedule.
4. **Field data protection:** no real personnel names, exact inspection patterns, duty calendars, eligibility matrices or backup files may be uploaded to GitHub or its Actions artifacts. Introduce a privileged local-only backend and data-source authorization review before operational integration.
5. **Physical Safari vs Files viewer:** the user's structured iPhone report validated four genuine fictional solves and a 589-row combined preview in a Files embedded viewer. This is not independent Safari App acceptance or an independently verified radios-off run.

**Operational release gate: BLOCKED.** A synthetic full-month success is evidence of the proposed engineering bridge, not permission to print an actual duty roster.

## Evidence status

- Native hard-rule and forged-response unit gate: **19/19 tests passed**, workflow #44264855615 native job.
- Genuine C++/WASM fictional leave/nightcheck/driver/history end-to-end: **requires success conclusion of workflow #44264855615**; do not mark complete solely on upload/compilation.
