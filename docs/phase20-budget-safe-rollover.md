# Phase 20 — Budget-safe synthetic cross-month carry integrity gate

Status: **local Python regression passed; not GitHub Actions verified.**
Date: 2026-11-18 (Asia/Taipei).

## Why this phase does not consume CI

This work is isolated in the new branch `phase20-budget-safe-rollover`, created from the successfully developed `phase5-safari-integration-gates` branch. **No pull request is opened.** This phase adds only:

- `solver/phase20_synthetic_rollover.py`
- `tests/test_phase20_synthetic_rollover.py`
- this documentation file.

The repository has 31 historical workflow YAML files, but their current automatic source-path filters do **not** cover these specific new files on this non-main branch. The commit messages also contain `[skip ci]`. **No GitHub workflow is manually dispatched for this phase.** This does not disable unrelated Actions in the account or change GitHub billing settings. Check `Settings → Billing and licensing → Budgets and alerts` before permitting any future expensive run.

### Local-only verification

In a checkout of this branch, using the repository's existing
`solver/fairness_targets_v7.py` (pure Python):

```bash
python3 -m unittest discover -s tests -p 'test_phase20_synthetic_rollover.py' -v
```

The phase 20 module and the 16 fictional tests were first checked in a local Python environment with a local mirror of the existing pure-Python fairness arithmetic. All **16/16 passed**. The new GitHub branch has **not** run paid GitHub Actions; do not label it CI-accepted.

## What this implementation actually checks

- An invented November 2026 archive contains the **complete 570-slot calendar**: 360 door and 210 officer rows. December target counts are for **372 door and 217 officer** slots.
- All fabricated identifiers must be `SIM_D_###` or `SIM_O_###`. No actual names, military event patterns, approved rosters or private backups are read or uploaded.
- A caller supplies an **independently expected archive fingerprint**. An unlocked archive, a mismatched snapshot/source fingerprint, changed revision, incomplete month, swapped/duplicate position, unknown identity, false saved base goals or incorrect compensation totals all **fail closed**.
- Worked counts are **derived from the actual archived row triples**, not trusted from a claimed summary.
- The existing `fairness_targets_v7.py` arithmetic is reused to calculate prior base goals, positive integer compensation, imported fresh locked carry, and the next month's soft target redistribution. A zero manual override takes precedence **only after** archive integrity checks pass.
- Representative fictional computed carry: `SIM_D_000 = 2`, `SIM_O_000 = 1`. These are math demonstration numbers, not real staff or actual allocations.
- Output explicitly sets `verified_real_v7_inputSig=false`, `archive_authenticity_verified=false`, `cross_month_hard_rule_parity_verified=false`, `operationally_certified=false`, and `importable_as_v7_backup=false`.

## Important limitations

1. A SHA-256 fingerprint is **not a digital signature**. It proves comparison against the caller's supplied anchor only; it **does not independently establish** source authenticity, authorization, archive lock provenance, v7 `inputSig` equivalence, or freshness of an actual approved roster.
2. Prior full-month schedule positions here are invented to test count arithmetic, **not audited for actual hard duty rest eligibility**. Therefore full source-aligned v7 cross-month legal duty constraints remain an open gate.
3. The original editable v7 HTML is **not in this repository**. This module is not connected to an import/export UI, persistence, operational approvals or the genuine iPhone WASM webpage. It makes **no claim to production readiness**.
4. Never put real military names, availability, night inspections, driver dates, snapshots or personnel backup files into a public repository or cloud Actions run.

## Next engineering gates

- Independently establish actual original v7 archive revision and inputSig algorithm from its authorized source (not by inventing one).
- Add a separate fictional cross-month duty-history eligibility audit, not just count compensation.
- Validate archive locking, rollback and operator approval on an authorized private environment before any live roster integration.
- Continue lightweight local test runs. Explicitly authorize any expensive C++/WASM GitHub Actions run only after billing guardrails have been confirmed.

**Release decision: preview-only / blocked for operational roster use.**
