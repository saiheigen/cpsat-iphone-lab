# Phase 5 — field-evidence gate and v7 parity checklist

Date: 2026-11-18 (Taiwan). **This document does not contain personnel names, duty schedules, eligibility masks, or genuine military data.** Every GitHub CI input is synthetic. The original v7.0 HTML is NOT present in this repository; earlier bridge documentation records that it was inspected in a separate project context. Do not claim direct current source-level parity without that authoritative original.

## What the phone session actually establishes

- User reported directly opening `experimental_full_month_hardship_cp_sat.html` from the **iPhone Files app**; the screenshot displays successful background Worker and genuine WASM three-stage verification for the **fictional tiny case**: 372 shifts, four staffed and 368 deliberately vacant.
- After a request to test with airplane mode and Wi-Fi disabled, the user replied that it worked. This is a **self-reported offline test**, not device instrumentation. The user then said the next stage was done, but has not supplied an exported JSON with complete observations, actual elapsed times or final numbers for every case.
- The screenshot's UI is a Files/Quick Look document preview, **not independently identified Safari.app**.
- Thus record: **physical iPhone Files-app local small-case runtime: user-observed success**; **offline and other full-month scenarios: user-reported, awaiting structured report**; **physical Safari.app acceptance: PENDING**; **operational v7 parity: PENDING**.

These are intentionally distinct from the CI Chromium and Linux WebKit synthetic proofs.

## Newly added privacy-safe report validator

`tools/validate_iphone_field_evidence.py` accepts only the exact `phase5-synthetic-iphone-selfcheck-v1` schema emitted by `src/phase5_iphone_selfcheck.js`.

Run on a trusted local machine or approved non-public environment:

```bash
python3 tools/validate_iphone_field_evidence.py /path/to/fictional_phone_report.json
```

The CLI prints only a **redacted summary** of synthetic scenario IDs, expected staffing counts, source-reported device opening mode and Worker state; it never prints raw `document_origin` or full device text. It **never** declares Safari or offline independently verified; even manually checking those controls cannot promote the status. The script rejects a v7 backup, unexpected fields, extra person/roster fields, duplicate or altered shift counts, forged certifications, or an importable "preview."

Partial reports of 0–3 synthetic cases are accepted as **incomplete diagnostics** (not an all-cases pass). A purported 589-row combined preview requires both constituent case results and exact `577 filled / 12 vacant` counts. No raw assignments or eligibility masks are permitted.

`tests/test_iphone_field_evidence.py` uses **invented** sample reports only; `.github/workflows/phase18-iphone-field-evidence.yml` tests the validator without any actual user's report as a CI artifact.

## v7 rule/status audit — keep hard constraints hard

| Topic | Current confirmed implementation | Still missing or not verifiable |
| --- | --- | --- |
| Duty grid and month | Genuine v4 C++ WASM handles 12 door and 7 officer shifts per day, full month; browser verifies four fictional cases | No actual v7 source HTML merged into the proof-gated standalone site; no authorized real-data interface |
| Staffing legality | C++ model applies submitted per-shift/person eligibility bits, pins, hints and within-pool rest/conflict constraints, then independent fictional audit | The page has four **fixed synthetic** matrices; it does not itself compute/verify real leave, training, duty officer, meal, night-check, driving, exemption and kitchen records |
| Filling and hard exclusions | First objective maximizes assignment coverage without relaxing the supplied eligible bits; missing shifts are explicit | Completeness and freshness of a real input eligibility matrix cannot be inferred from a legal CP-SAT output |
| Count and hardship fairness | Second objective locks fill and minimizes integer L1 count deviation; third locks fill positions and achieved count deviation, seeks normalized night/noon/officer long-shift fairness | Not identical to full v7 `deepQuality`, weekly admin-duty distribution, historic hardship equity or all source priority levels; `FEASIBLE`/`UNKNOWN` are not full global optimum proofs |
| Carry and meal credit | Separate `solver/fairness_targets_v7.py` and `solver/v7_backup_bridge.py` include tested synthetic carry/meal-credit parsing | Standalone v4 browser accepts already-reduced targets, not independently authorized previous-month carry; archive `inputSig` freshness and approval still need v7-origin evidence |
| Month and archive boundaries | `solver/v7_backup_bridge.py` enforces partial prior-month history shape and explicitly exposes unconfirmed history flags | Original locked/approved schedule state, cross-month history freshness, revision rollback and signature verification have not been accepted in the real integrated browser |
| v7 persistence/approval | Synthetic preview rows use `[daySerial, slot, SIM_personID]`, explicit `null` vacancies | `importable_as_v7_backup=false`, no official write-back, signature or authorized roster approval path |
| iPhone compatibility | User-observed Files App tiny solve plus Chromium and Linux WebKit genuine offline test results | Independent Safari.app identity, actual flight-mode metadata, memory/thermal pressure, background suspension and full-month performance report pending |
| Data protection | Synthetic-only fixed browser page; no real personnel data in committed code or public CI | Security review and approved on-device storage/data handling before any production deployment |

**Release gate: BLOCKED for operational use.** Never hide vacant shifts or relax prohibitions to satisfy count fairness. Do not submit actual military records, dates, inspection patterns, eligibility masks or backups into GitHub Actions.

## Engineering order after this milestone

1. Review a **sanitized local JSON self-check** from the iPhone Files-app test, if the user chooses to share it. Record the counts and actual on-device runtime without guessing. No automated hardware certification.
2. Obtain the actual original v7.0 source or supported private local module to compare rules and data-boundaries. Do NOT rewrite a historic v7 backup or approved schedule.
3. Using invented month boundaries and people only, implement a source-aligned local-only eligibility/history adapter with independent audit and explicit failure on missing, stale or contradictory information.
4. Preserve the already green genuine WASM, offline Worker, restart, cancel and fault-recovery CI while expanding rule completeness.
5. Separately test real iPhone Safari and real network-off mode, not Files Quick Look, before any claim of Safari.app acceptance.

Current milestone: **engineering evidence schema and discrepancy checklist**, not a production launch.
