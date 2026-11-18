"""Phase 23: budget-safe, fictional-only legal CP-SAT hinting and timeout gate.

No network, no real roster input, no Emscripten recompilation, no GitHub Actions.
Creates an optional *warm start*, never pins, removes or relaxes a hard rule.
A heuristic preview is never a solver-produced FEASIBLE/OPTIMAL schedule.
The source and its fingerprints are supplied by Phase 22 and are NOT official
v7 inputSig/authentication/approval evidence.  No operational certification.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib

from solver.phase20_synthetic_rollover import RolloverError, _COUNTS
from solver.phase21_synthetic_cross_month_gate import (
    _conflict, _calendar_rows, _parse_events, _blocked, _audit_duties,
    empty_next_calendar, audit_invented_cross_month,
)
from solver.phase22_synthetic_solver_handoff import (
    _VERSION, _FORMAT, _fingerprints, build_fictional_handoff,
    audit_fictional_solver_response,
)

_PHASE = "phase23-fictional-hinted-v4-v1"
_PROVEN = {"OPTIMAL", "FEASIBLE"}
_NON_SOLUTION = {"UNKNOWN", "INFEASIBLE", "INVALID_INPUT", "MODEL_INVALID"}


def _require(ok, why):
    if not ok:
        raise RolloverError(why)


def _rebuild(handoff):
    _require(type(handoff) is dict and handoff.get("format") == _FORMAT and
             handoff.get("invented_only") is True and
             handoff.get("operationally_certified") is False,
             "Only the anchored fictional Phase22 source is supported")
    sources = handoff.get("original_sources")
    _require(type(sources) is tuple and len(sources) == 6,
             "Original imaginary inputs missing")
    prev, archive, upcoming, events, pins, overrides = sources
    _fingerprints(prev, archive, upcoming, events, pins, handoff.get("anchors"))
    fresh = build_fictional_handoff(
        prev, archive, upcoming, events, pins,
        expected_anchors=handoff["anchors"], manual_overrides=overrides)
    for key in ("frames", "mask_capacities", "soft_targets"):
        _require(handoff.get(key) == fresh[key],
                 "Previous anonymous candidate matrix or targets were changed")
    return fresh


def _validate_seed(pool, ids, rows, pins, mask, history, events):
    slots = _COUNTS[pool]
    _require(len(rows) == 31 * slots and len(pins) == len(rows) and
             len(mask) == len(rows) * len(ids), "Truncated fictional month")
    found = {i: [] for i in range(len(ids))}
    assigned = [-1] * len(rows)
    for i, (p, bits) in enumerate(zip(pins,
                                      (mask[s*len(ids):(s+1)*len(ids)]
                                       for s in range(len(rows))))):
        _require(type(p) is int and -2 <= p < len(ids),
                 "Invalid pinned/fixed vacancy index")
        _require(all(c in "01" for c in bits), "Corrupt eligibility bit")
        if p >= 0:
            _require(bits[p] == "1", "Pinned unavailable person")
            assigned[i] = p
            found[p].append((pool, ids[p], date(2026, 12, i//slots+1),
                             i%slots+1))
    for p, jobs in found.items():
        all_jobs = history.get((pool, ids[p]), []) + jobs
        _audit_duties(all_jobs, events)
    return assigned, found


def prepare_safe_hints(handoff, *, max_checks=150000):
    """Build optional full-calendar greedy hints; independent original-data audit.

    A strict deterministic guard is enforced for the *computation* budget,
    not a promise about solver runtime. Pinned positions are set first.
    Candidates are chosen by fewest-eligible-slot first, then balanced toward
    already validated *soft* count goals. No optimization proof is claimed.
    """
    _require(type(max_checks) is int and 1 <= max_checks <= 1000000,
             "Hint work budget must be a bounded positive integer")
    source = _rebuild(handoff)
    prev, archive, upcoming, events, pins, overrides = source["original_sources"]
    ids = {pool: [p["id"] for p in upcoming["pools"][pool]] for pool in _COUNTS}
    index = _parse_events(events, {pool: set(values) for pool, values in ids.items()})
    prior_jobs = _calendar_rows(archive["schedule"], 2026, 11,
                                {pool: set(values) for pool, values in ids.items()})
    past = {(pool, who): [] for pool, names in ids.items() for who in names}
    for job in prior_jobs:
        past[job[0], job[1]].append(job)
    outputs, candidate_counts, check_counts = {}, {}, {}
    fill_upper_bounds = {}
    for pool, slots in _COUNTS.items():
        frame = source["frames"][pool]
        lines = frame["wire"].splitlines()
        _require(len(lines) == 8 and lines[0] == _VERSION and
                 lines[1] == "2026-12" and lines[2] == pool,
                 "Invalid fictional v4 solver frame")
        n = frame["shift_count"]
        width = frame["staff_count"]
        names = ids[pool]
        _require(len(names) == width and n == 31*slots,
                 "Wrong fictional solver dimensions")
        mask = lines[4]
        try:
            pins = [int(x) for x in lines[5].split(",")]
            targets = [int(x) for x in lines[7].split(",")]
        except ValueError as exc:
            raise RolloverError("Invalid fictional frame integers") from exc
        _require(len(targets) == width and all(t >= 0 for t in targets),
                 "Malformed soft targets")
        assignments, current = _validate_seed(
            pool, names, list(range(n)), pins, mask, past, index)
        for i, person in enumerate(assignments):
            if person >= 0:
                job = (pool, names[person], date(2026,12,i//slots+1), i%slots+1)
                _require(not _blocked(job, index), "Pinned original event prohibited")
        by_row = [tuple(j for j, bit in enumerate(mask[i*width:(i+1)*width])
                        if bit == "1") for i in range(n)]
        ordering = sorted((i for i in range(n) if pins[i] == -2),
                          key=lambda i: (len(by_row[i]), i // slots, i % slots))
        counts = [len(current[j]) for j in range(width)]
        checks = 0
        for i in ordering:
            if checks >= max_checks:
                break
            day = date(2026,12,i//slots+1)
            slot = i % slots + 1
            candidates = sorted(by_row[i], key=lambda p: (
                # Minimize relative soft-target deviation, not hard-assign quotas.
                counts[p] / max(1, targets[p]),
                counts[p], p))
            for p in candidates:
                checks += 1
                if checks > max_checks:
                    break
                job = (pool, names[p], day, slot)
                if _blocked(job, index):
                    raise RolloverError("Anonymous mask disagrees with source event")
                if any(_conflict(job, existing) for existing in current[p]):
                    continue
                per_day = sum(existing[2] == day for existing in current[p])
                if per_day >= (3 if pool == "door" else 1):
                    continue
                assignments[i] = p
                current[p].append(job)
                counts[p] += 1
                break
        # Recheck every provisional assignment against ALL original fictional
        # November history, date events, pinned and rest constraints.
        month_jobs = [
            (pool, names[p], date(2026,12,i//slots+1), i%slots+1)
            for i,p in enumerate(assignments) if p >= 0
        ]
        _audit_duties([x for x in prior_jobs if x[0] == pool] + month_jobs, index)
        for i, pin in enumerate(pins):
            _require(pin < 0 or assignments[i] == pin,
                     "A real hard pin was moved by heuristic")
            _require(pin != -1 or assignments[i] == -1,
                     "A forced vacancy was filled by heuristic")
            _require(assignments[i] < 0 or mask[i*width+assignments[i]] == "1",
                     "Heuristic assignment not eligible")
        hinted = lines[:]
        hinted[6] = ",".join(map(str, assignments))
        wire = "\n".join(hinted) + "\n"
        _require(all(hinted[k] == lines[k] for k in (0,1,2,3,4,5,7)),
                 "Hint changed solver hard input or fairness targets")
        _require(not any(who in wire for who in names),
                 "Heuristic wire leaked fictional identity")
        outputs[pool] = {
            "wire": wire,
            "sha256": hashlib.sha256(wire.encode("ascii")).hexdigest(),
            "indices": assignments,
            "filled": sum(p >= 0 for p in assignments),
            "missing": n - sum(p >= 0 for p in assignments),
            "candidate_bits": mask.count("1"),
            "hinted_only_not_pinned": True,
            "verified_against_original_fictional_events": True,
        }
        candidate_counts[pool] = len(ordering)
        check_counts[pool] = checks
        # Trivial strict upper bound: a non-forced row can hold at most one
        # assignment if it has at least one eligible person.
        fill_upper_bounds[pool] = sum(
            pin != -1 and bool(by_row[i]) for i, pin in enumerate(pins))
    proposed = empty_next_calendar()
    for pool, s in outputs.items():
        names = ids[pool]
        for i,p in enumerate(s["indices"]):
            if p >= 0:
                proposed[pool][i][2] = names[p]
    audit = audit_invented_cross_month(
        prev, archive, upcoming, proposed,
        expected_archive_sha256=source["anchors"]["archive"],
        invented_events=events, manual_overrides=overrides)
    _require(audit["next_filled"] == sum(s["filled"] for s in outputs.values()),
             "Independent complete-month heuristic audit disagrees")
    return {
        "format": _PHASE, "synthetic_only": True,
        "source_anchors": deepcopy(source["anchors"]),
        "pools": outputs,
        "candidate_rows_examined": candidate_counts,
        "candidate_checks": check_counts,
        "max_checks": max_checks,
        "coverage_upper_bound": fill_upper_bounds,
        "max_fill_proven_for_partial_fictional_model": all(
            outputs[pool]["filled"] == fill_upper_bounds[pool]
            for pool in _COUNTS),
        "constructive_preview_not_solver_result": True,
        "independently_verified_hard_constraints": True,
        "global_fill_optimality_proven": False,
        "all_fairness_optimality_proven": False,
        "genuine_wasm_executed": False,
        "full_v7_rule_parity_verified": False,
        "real_v7_inputSig_verified": False,
        "operationally_certified": False,
        "importable_as_v7_backup": False,
    }


def safe_timeout_verdict(handoff, hint_plan, replies):
    """Never transform UNKNOWN into a fabricated solver FEASIBLE status.

    If either pool has no certified CP-SAT solution, return a blocked verdict
    with NO assigned schedule or detailed personnel data. The separately
    independently audited heuristic hints remain a NON-SOLVER preview.
    """
    _rebuild(handoff)
    _require(type(hint_plan) is dict and hint_plan.get("format") == _PHASE and
             hint_plan.get("constructive_preview_not_solver_result") is True and
             hint_plan.get("independently_verified_hard_constraints") is True,
             "Missing independently audited fictional warm-start preview")
    _require(hint_plan.get("source_anchors") == handoff["anchors"],
             "Heuristic preview source snapshot changed")
    # Reconstruct deterministic hints and independent historical/event audit.
    # Never trust supplied flags/indices when deciding a timeout fallback.
    expected = prepare_safe_hints(handoff, max_checks=hint_plan.get("max_checks"))
    _require(hint_plan == expected,
             "Heuristic hints or claimed proof were modified after audit")
    _require(type(hint_plan.get("pools")) is dict and
             set(hint_plan["pools"]) == set(_COUNTS),
             "Missing fictional pool hints")
    for pool in _COUNTS:
        item = hint_plan["pools"][pool]
        _require(type(item) is dict and item.get("hinted_only_not_pinned") is True,
                 "Invalid heuristic hint output")
        original = handoff["frames"][pool]["wire"].splitlines()
        updated = item["wire"].splitlines()
        _require(len(updated) == 8 and len(original) == 8 and
                 all(original[i] == updated[i] for i in (0,1,2,3,4,5,7)) and
                 hashlib.sha256(item["wire"].encode("ascii")).hexdigest() ==
                 item["sha256"] and updated[6] == ",".join(map(str,item["indices"])),
                 "Hint proof malformed or input changed")
    _require(type(replies) is dict and set(replies) == set(_COUNTS),
             "Both duty pool responses are required")
    failures = []
    for pool in _COUNTS:
        response = replies[pool]
        _require(type(response) is dict and type(response.get("status")) is str,
                 "Malformed result status")
        status = response["status"]
        if status in _NON_SOLUTION:
            _require("assignments" not in response,
                     "Failure must not contain a claimed certified schedule")
            failures.append((pool, status))
        else:
            _require(status in _PROVEN,
                     "Unknown/unsupported purported solver status")
    if failures:
        return {
            "format": "phase23-blocked-solver-result-v1",
            "reason": failures[0][1],
            "pool": failures[0][0],
            "synthetic_only": True,
            "solver_result_accepted": False,
            "heuristic_preview_usable_for_further_testing_only":
                all(status == "UNKNOWN" for _, status in failures),
            "fallback_fill_maximum_proven_for_partial_fictional_model":
                hint_plan["max_fill_proven_for_partial_fictional_model"],
            "fallback_filled": {pool: hint_plan["pools"][pool]["filled"]
                                for pool in _COUNTS},
            "accepted_assignments": None,
            "full_v7_rule_parity_verified": False,
            "operationally_certified": False,
            "importable_as_v7_backup": False,
        }
    cleaned = {}
    for pool in _COUNTS:
        result = replies[pool]
        cleaned[pool] = {key: result.get(key) for key in
                         ("status", "assignments", "filled", "missing")}
    audit = audit_fictional_solver_response(handoff, cleaned)
    _require(audit["independent_full_month_legality_audit"] is True,
             "Solver output not independently verified")
    return {
        "format": "phase23-verified-fictional-solver-result-v1",
        "synthetic_only": True,
        "solver_result_accepted": True,
        "source_anchored_to_supplied_digests": True,
        "filled": audit["filled"], "missing": audit["missing"],
        "full_v7_rule_parity_verified": False,
        "independently_certified_optimal": False,
        "real_v7_inputSig_verified": False,
        "operationally_certified": False,
        "importable_as_v7_backup": False,
    }