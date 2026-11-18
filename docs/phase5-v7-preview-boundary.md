# Synthetic CP-SAT → v7-shaped preview boundary

Status: **synthetic preview only**. No physical iPhone Safari acceptance and **no live v7 integration** are claimed.

## Verified source alignment

The repository's earlier `solver/v7_backup_bridge.py` and `solver/v7_preview.py` document the v7 schedule row shape `[unix_day_number, slot_number, personID]` and the separate **non-importable preview** contract. The original v7.0 HTML is not in this repository; the current phase-5 code **cannot modify it or prove complete source-level parity**.

## What is implemented

- `integration/phase5_synthetic_adapter.cjs`: synthetic-only `guard-month-harsh-v4` input and independently audited assignment projection.
- `integration/phase5_v7_preview_adapter.cjs`: requires BOTH pools, one month, a full 12-shift/day door calendar and a full 7-shift/day officer calendar; projects to the v7-style row triples; includes explicit `null` for all vacancies. IDs are generated solely as `SIM_D_###` and `SIM_O_###`. No names or military records are ingested.
- Preview marker: `guard-cpsat-synthetic-preview-v1` (intentionally **not** `guard-offline-v5`). Flags `preview_only=true`, `importable_as_v7_backup=false`, `operationally_certified=false`, `full_v7_rule_parity_verified=false` and `real_iphone_safari_verified=false` prevent mistaken certification.
- `tests/phase5_v7_preview.test.cjs`: full 589-row validation, missing-shift preservation, cross-month/pool contamination rejection and invalid-output rejection.
- `tests/phase5_real_wasm_integration.cjs`: reconstructs a **single combined 589-row preview** from two genuine fictional OR-Tools WASM executions (360/372 door, 217/217 officer, 577 filled and 12 missing). It separately retains genuine-solver proof and independent rules auditing.
- Standalone HTML demo adds a **single-pool** expandable 31-day fictional roster by day and shift; it is not the combined two-pool preview and cannot export or restore a v7 backup. `tests/browser_month_hardship_wasm.py` tests complete row counts, explicit blanks and changing scenarios.

## Remaining engineering gates

1. Fetch or connect the actual v7.0 HTML from an authorized, non-public source; review its import/export/locking APIs before writing to any saved state.
2. Validate ALL v7 eligibility constraints and cross-month archive freshness against official behavior, using fictional data only.
3. Verify the exact v7 read-only preview API and its failure paths. Never modify an existing approved or locked month until independently certified.
4. Run the physical-device iPhone Safari offline test using `docs/phase5-real-iphone-safari-manual-check.md`.
5. Keep real military personnel, schedules, inspections and eligibility matrices out of public GitHub commits and all cloud CI artifacts.

This is not a deployable operational military scheduling application.
