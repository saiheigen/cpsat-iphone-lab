"""Phase 22: fictional-only full-month rule/credit handoff to v4 WASM wire.

This is NOT a real v7 input adapter or a claim of iPhone execution. It does
not depend on OR-Tools, run network calls, authenticate archived records or
approve duty. It *must* never be fed actual personnel or inspection patterns.
The source SHA256 anchors here prove equality only to caller-supplied digests.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib
import re

from solver.fairness_targets_v7 import (
    FairPerson, base_goals_v7, actual_targets_v7)
from solver.phase20_synthetic_rollover import RolloverError, _digest, _COUNTS, _EPOCH
from solver.phase21_synthetic_cross_month_gate import (
    imaginary_legal_boundary_fixture, empty_next_calendar,
    audit_invented_cross_month, _calendar_rows, _conflict, _blocked, _parse_events)

_FORMAT = "phase22-fictional-full-month-harsh-v4-handoff"
_VERSION = "guard-month-harsh-v4"
_MONTH = "2026-12"
_PINS = re.compile(r"^(door|officer):2026-12-(0[1-9]|[12][0-9]|3[01]):([1-9]|1[0-2])$")


def fictional_source_fixture():
    """Only deterministic made-up people, events, archived history and pins."""
    prev, archive, upcoming, archive_anchor = imaginary_legal_boundary_fixture()
    events = [
        {"pool":"door", "person":"SIM_D_048", "kind":"leave",
         "start":"2026-12-04", "end":"2026-12-05"},
        {"pool":"door", "person":"SIM_D_049", "kind":"driver",
         "start":"2026-12-10", "end":"2026-12-10"},
        {"pool":"door", "person":"SIM_D_050", "kind":"exempt_night",
         "start":"2026-12-01", "end":"2026-12-31"},
        {"pool":"door", "person":"SIM_D_051", "kind":"exempt_noon",
         "start":"2026-12-01", "end":"2026-12-31"},
        {"pool":"officer", "person":"SIM_O_040", "kind":"nightcheck",
         "start":"2026-12-12", "end":"2026-12-12"},
        {"pool":"officer", "person":"SIM_O_041", "kind":"meal",
         "start":"2026-12-17", "end":"2026-12-17"},
        {"pool":"officer", "person":"SIM_O_042", "kind":"training",
         "start":"2026-12-24", "end":"2026-12-25"},
        {"pool":"officer", "person":"SIM_O_049", "kind":"exempt_all",
         "start":"2026-12-01", "end":"2026-12-31"},
    ]
    pins = {
        "door:2026-12-07:6": "SIM_D_048",
        "door:2026-12-05:8": None,
        "officer:2026-12-05:5": "SIM_O_048",
        "officer:2026-12-06:4": None,
    }
    anchors = {
        "archive": archive_anchor,
        "prior_source": _digest(prev),
        "next_source": _digest(upcoming),
        "events": _digest(events),
        "pins": _digest(pins),
    }
    return prev, archive, upcoming, events, pins, anchors


def _fingerprints(prior_source, archive, next_source, events, pins, anchors):
    if type(anchors) is not dict or set(anchors) != {
            "archive", "prior_source", "next_source", "events", "pins"}:
        raise RolloverError("Independent synthetic source anchors are required")
    for key, raw in (("archive", archive), ("prior_source", prior_source),
                     ("next_source", next_source), ("events", events),
                     ("pins", pins)):
        if type(anchors[key]) is not str or not re.fullmatch(r"[0-9a-f]{64}", anchors[key]):
            raise RolloverError("Malformed expected synthetic digest")
        if _digest(raw) != anchors[key]:
            raise RolloverError("Stale or changed source: " + key)


def _validated_pins(pins, next_source):
    if type(pins) is not dict:
        raise RolloverError("Pinned shift mapping must be explicit")
    ids = {pool: {x["id"] for x in next_source["pools"][pool]}
           for pool in _COUNTS}
    parsed = {}
    for key, who in pins.items():
        match = _PINS.fullmatch(key) if type(key) is str else None
        if match is None:
            raise RolloverError("Invalid fictional pinned shift key")
        pool, day, slot = match.group(1), int(match.group(2)), int(match.group(3))
        if slot > _COUNTS[pool] or (who is not None and
                                   (type(who) is not str or who not in ids[pool])):
            raise RolloverError("Wrong-pool or unknown pinned person")
        parsed[(pool, day, slot)] = who
    return parsed


def build_fictional_handoff(prior_source, archive, next_source, events, pins, *,
                             expected_anchors, manual_overrides=None):
    """Produce exactly two anonymous v4 candidate/target frames, fail closed.

    The Phase20 declared availability is not trusted as actual eligible
    capacity: we recompute that from each post-history/event mask instead.
    The v4 solver still owns within-December pairwise conflict enforcement.
    """
    _fingerprints(prior_source, archive, next_source, events, pins, expected_anchors)
    parsed_pins = _validated_pins(pins, next_source)
    baseline = audit_invented_cross_month(
        prior_source, archive, next_source, empty_next_calendar(),
        expected_archive_sha256=expected_anchors["archive"],
        invented_events=events, manual_overrides=manual_overrides)
    people = {pool: [entry["id"] for entry in next_source["pools"][pool]]
              for pool in _COUNTS}
    event_index = _parse_events(events, {pool: set(ids) for pool, ids in people.items()})
    history = _calendar_rows(archive["schedule"], 2026, 11,
                             {pool: set(ids) for pool, ids in people.items()})
    hist_by_id = {(pool, ident): [] for pool, ids in people.items() for ident in ids}
    for job in history:
        hist_by_id[(job[0], job[1])].append(job)
    frames, masks, targets = {}, {}, {}
    for pool, slots in _COUNTS.items():
        ids = people[pool]
        eligible_bits, fixed, rows = [], [], []
        for day in range(1, 32):
            when = date(2026, 12, day)
            for slot in range(1, slots+1):
                key = (pool, day, slot)
                one_slot = []
                for ident in ids:
                    job = (pool, ident, when, slot)
                    allowed = not _blocked(job, event_index) and not any(
                        _conflict(job, past) for past in hist_by_id[(pool, ident)])
                    one_slot.append("1" if allowed else "0")
                if key in parsed_pins:
                    who = parsed_pins[key]
                    if who is None:
                        fixed.append(-1)
                    else:
                        idx = ids.index(who)
                        if one_slot[idx] != "1":
                            raise RolloverError("Pinned person is disallowed by original events/history")
                        fixed.append(idx)
                else:
                    fixed.append(-2)
                eligible_bits.extend(one_slot)
                rows.append((when, slot))
        mask = "".join(eligible_bits)
        capacities = {ident: sum(mask[i*len(ids)+j] == "1"
                                 for i in range(len(rows)))
                      for j, ident in enumerate(ids)}
        credited = []
        for raw in next_source["pools"][pool]:
            ident = raw["id"]
            credited.append(FairPerson(
                ident, raw["weight"], baseline["carry"][pool][ident],
                raw["meal_credit"]))
        goals = base_goals_v7(credited, capacities, len(rows))
        target = actual_targets_v7(credited, capacities, len(rows), goals)
        indexed_targets = [target[ident] for ident in ids]
        fields = [
            _VERSION, _MONTH, pool, f"{len(rows)} {len(ids)}",
            mask, ",".join(map(str, fixed)),
            ",".join(["-1"]*len(rows)),
            ",".join(map(str, indexed_targets)),
        ]
        wire = "\n".join(fields) + "\n"
        if any(ident in wire for ident in ids):
            raise RolloverError("Identifiers leaked into anonymous solver wire")
        frames[pool] = {"wire": wire, "sha256": hashlib.sha256(wire.encode("ascii")).hexdigest(),
                        "shift_count": len(rows), "staff_count": len(ids)}
        masks[pool] = capacities
        targets[pool] = target
    return {
        "format": _FORMAT, "month": _MONTH, "invented_only": True,
        "frames": frames,
        "mask_capacities": masks,
        "soft_targets": targets,
        "anchors": deepcopy(expected_anchors),
        "original_sources": (deepcopy(prior_source), deepcopy(archive), deepcopy(next_source),
                             deepcopy(events), deepcopy(pins), deepcopy(manual_overrides)),
        "genuine_wasm_executed": False,
        "real_v7_inputSig_verified": False,
        "archive_authenticity_verified": False,
        "full_v7_parity_verified": False,
        "operationally_certified": False,
        "importable_as_v7_backup": False,
    }


def audit_fictional_solver_response(handoff, results):
    """Rebuild original bytes and cross-month-audit a claimed solver result.

    This proves only synthetic *feasibility* and data consistency. No external
    CP-SAT optimality proof or real WebAssembly execution is inferred.
    """
    if type(handoff) is not dict or handoff.get("format") != _FORMAT or \
            handoff.get("invented_only") is not True:
        raise RolloverError("Unknown or non-fictional transport")
    if type(results) is not dict or set(results) != set(_COUNTS):
        raise RolloverError("Both pool responses are required")
    src = handoff.get("original_sources")
    if type(src) is not tuple or len(src) != 6:
        raise RolloverError("Original synthetic source not retained for independent audit")
    prev, archive, upcoming, events, pins, overrides = src
    rebuilt = build_fictional_handoff(
        prev, archive, upcoming, events, pins,
        expected_anchors=handoff["anchors"], manual_overrides=overrides)
    for key in ("frames", "mask_capacities", "soft_targets"):
        if handoff.get(key) != rebuilt[key]:
            raise RolloverError("WASM frame, targets or eligibility matrix altered")
    schedule = empty_next_calendar()
    filled = {}
    for pool, slots in _COUNTS.items():
        answer = results[pool]
        if type(answer) is not dict or set(answer) != {
                "status", "assignments", "filled", "missing"}:
            raise RolloverError("Solver result shape invalid")
        if answer["status"] not in ("OPTIMAL", "FEASIBLE"):
            raise RolloverError("No solver-reported feasible assignment")
        indices = answer["assignments"]
        frame = rebuilt["frames"][pool]
        n, staff = frame["shift_count"], frame["staff_count"]
        if type(indices) is not list or len(indices) != n:
            raise RolloverError("Missing assignment rows")
        lines = frame["wire"].splitlines()
        mask = lines[4]
        fixed = [int(x) for x in lines[5].split(",")]
        names = [entry["id"] for entry in upcoming["pools"][pool]]
        count = 0
        for i, index in enumerate(indices):
            if type(index) is not int or index < -1 or index >= staff:
                raise RolloverError("Invalid assigned staff index")
            if fixed[i] == -1 and index != -1:
                raise RolloverError("Forced blank changed")
            if fixed[i] >= 0 and index != fixed[i]:
                raise RolloverError("Fixed assignment changed")
            if index >= 0:
                if mask[i*staff+index] != "1":
                    raise RolloverError("WASM assignment violates eligibility mask")
                schedule[pool][i][2] = names[index]
                count += 1
        if type(answer["filled"]) is not int or answer["filled"] != count or \
                type(answer["missing"]) is not int or answer["missing"] != n-count:
            raise RolloverError("Solver counts disagree with explicit assignments")
        filled[pool] = count
    audited = audit_invented_cross_month(
        prev, archive, upcoming, schedule,
        expected_archive_sha256=handoff["anchors"]["archive"],
        invented_events=events, manual_overrides=overrides)
    if audited["next_filled"] != sum(filled.values()):
        raise RolloverError("Independent cross-month legality audit disagrees")
    return {
        "format": "phase22-fictional-verified-feasibility-v1",
        "month": _MONTH, "invented_only": True,
        "source_anchored_to_supplied_digests": True,
        "independent_full_month_legality_audit": True,
        "total_shifts": 589, "filled": sum(filled.values()),
        "missing": 589-sum(filled.values()), "by_pool": filled,
        "genuine_wasm_executed": False,
        "optimality_independently_proven": False,
        "real_v7_inputSig_verified": False,
        "operationally_certified": False,
        "importable_as_v7_backup": False,
    }
