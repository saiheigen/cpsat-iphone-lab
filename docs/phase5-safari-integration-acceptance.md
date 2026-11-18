# Phase 5 — iPhone Safari and production integration gates

Status: **NOT ACCEPTED**. This document is an executable review checklist, not evidence of a completed Safari test or production integration.

## Proven baseline (synthetic-only)
- Three-stage genuine C++/WASM Node solve and independent audit: https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44223914115
- Proof-gated offline HTML package: https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44229016057
- Offline Chromium desktop/mobile-sized tests: https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44229165784
- **Mobile-sized Chromium is not iPhone Safari.**

## Required acceptance gates
1. **Artifact integrity**: download the proof-gated HTML and proof JSON from the successful runs; verify the expected SHA-256 evidence and accepted audit before use. Never replace the validated v2/v3 artifacts.
2. **Real Safari on physical iPhone**: open the offline HTML in Safari on an iPhone, with airplane mode enabled after the file is local. Record iOS version, device, loading mechanism, runtime errors, elapsed time, memory failures, and outcome. A simulator or Chromium emulation does not pass this gate.
3. **Offline behavior**: ensure no network dependency or external script request; reload after connectivity is disabled. Verify Worker/WASM startup and all synthetic cases actually solve rather than merely rendering fixture output.
4. **Independent audit**: compare each produced synthetic solution against a separately implemented constraint auditor; reject any invalid or missing assignment. Preserve failing seeds and sanitized traces.
5. **Integration contract**: map synthetic inputs to the existing v7.0 scheduler schema on a separate integration branch. Do not silently relax mandatory constraints when infeasible. Missing shifts must remain explicit.
6. **Regression**: rerun Node genuine solver, independent audit, offline Chromium desktop/mobile-sized tests, and earlier v2/v3 regression checks after any integration change.
7. **Security**: never commit actual military schedules, personnel data, or sensitive eligibility matrices to this public repository. Use only fabricated fixtures. Review artifact contents before upload.
8. **Release decision**: mark production-ready only after physical Safari evidence, integration tests, security review, and full rule-level acceptance all pass.

## Next implementation tasks
- Add a deterministic synthetic-only integration adapter and tests, with explicit input/output schema and error states.
- Add CI regression that fails if the adapter changes a mandatory rule or suppresses an unfilled shift.
- Add a manual Safari evidence template; keep the physical-device gate pending until actually tested.

No production v7.0 merge or Safari success is claimed by this document.
