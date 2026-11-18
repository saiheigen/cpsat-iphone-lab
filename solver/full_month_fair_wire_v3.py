"""Strict anonymous complete-month v3 fair-count WebAssembly transport.

v3 = exact seven-field guard-month-v2 frame + one comma-separated integer
soft target per anonymous staff index. Targets are computed from locally
validated v7 largest-remainder/carry/meal arithmetic and NEVER override
availability, rest, forced vacancies or previously pinned shifts.

This is an ADAPTER, not proof that C++/WASM fairness has compiled, run,
or optimized. A solver-reported OPTIMAL cannot be independently certified
from an untrusted JSON response; only independent feasibility is audited.
"""
from __future__ import annotations
import hashlib

from solver.fairness_targets_v7 import (
    FairPerson, actual_targets_v7, base_goals_v7)
from solver.full_month_wire_v2 import (
    validate_full_month_v2_export, audit_full_month_v2_response)

VERSION = "guard-month-fair-v3"


def export_full_month_fair_v3(encoded_v2: dict, people: list[FairPerson]) -> dict:
    validated = validate_full_month_v2_export(encoded_v2)
    staff = encoded_v2["people"]
    expected = [p.id for p in staff]
    if (len(people) != len(staff) or
            [p.ident for p in people] != expected):
        raise ValueError("Fairness staff order must match anonymous v2 slots exactly")
    bits = encoded_v2["payload"].splitlines()
    if len(bits) != 7 or bits[0] != "guard-month-v2":
        raise ValueError("Missing valid v2 model source")
    count = validated["tasks"]
    width = len(staff)
    mask = bits[4]
    capacities = {
        p.id: sum(mask[s * width + i] == "1" for s in range(count))
        for i, p in enumerate(staff)
    }
    base = base_goals_v7(people, capacities, count)
    adjusted = actual_targets_v7(people, capacities, count, base)
    targets = [adjusted[p.id] for p in staff]
    if any(type(t) is not int or not 0 <= t <= count for t in targets):
        raise ValueError("Unsupported soft count target outside 0..shift count")
    v3 = bits[:]
    v3[0] = VERSION
    v3.append(",".join(map(str, targets)))
    payload = "\n".join(v3) + "\n"
    if any(p.id in payload for p in staff):
        raise ValueError("Personnel identifier leaked into anonymous v3 frame")
    return {
        "contract": VERSION,
        "payload": payload,
        "targets": targets,
        "base_goals": [base[p.id] for p in staff],
        "v2_source": encoded_v2,
        "source_month": validated["month"],
        "source_pool": validated["pool"],
        "sha256": hashlib.sha256(payload.encode("ascii")).hexdigest(),
        "names_exported": False,
        "v3_wasm_real_execution_proven": False,
        "fairness_optimality_independently_proven": False,
        "operationally_certified": False,
    }


def audit_full_month_fair_v3_response(model: dict, got: dict) -> dict:
    if model.get("contract") != VERSION:
        raise ValueError("Incorrect v3 fairness frame")
    source = model["v2_source"]
    original = source["payload"].splitlines()
    lines = model["payload"].splitlines()
    if len(lines) != 8 or lines[:7] != [VERSION] + original[1:]:
        raise ValueError("Altered source availability, dates, pins or hints")
    if hashlib.sha256(model["payload"].encode("ascii")).hexdigest() != model["sha256"]:
        raise ValueError("Fairness input frame SHA changed")
    if lines[7] != ",".join(map(str, model["targets"])):
        raise ValueError("Fairness targets were modified")
    base = audit_full_month_v2_response(source, got)
    if got.get("fill_phase") not in ("OPTIMAL", "FEASIBLE"):
        raise ValueError("No valid first-stage fill status")
    if got.get("fair_phase") not in ("OPTIMAL", "FEASIBLE", "UNKNOWN"):
        raise ValueError("Invalid second-stage fairness status")
    if (got.get("status") == "OPTIMAL" and not
            (got.get("fill_optimal_proven") is True and
             got.get("fair_optimal_proven_given_fill") is True)):
        raise ValueError("Unsupported all-stage OPTIMAL claim")
    staff = source["people"]
    actual = [0] * len(staff)
    indices = got["assignments"]
    for person in indices:
        if person >= 0:
            actual[person] += 1
    if actual != got.get("actual_counts"):
        raise ValueError("WASM per-person count mismatch")
    l1 = sum(abs(a - t) for a, t in zip(actual, model["targets"]))
    if (type(got.get("final_abs_deviation")) is not int or
            l1 != got["final_abs_deviation"]):
        raise ValueError("WASM fairness deviation mismatch")
    start = got.get("phase1_abs_deviation")
    if type(start) is not int or start < l1:
        raise ValueError("Fairness stage lowered fill or worsened count deviation")
    if got.get("fairness_improved") is not (l1 < start):
        raise ValueError("Incorrect fairness-improved flag")
    return {
        "assignments": base["assignments"],
        "filled": base["filled"],
        "missing": base["missing"],
        "actual_counts": actual,
        "final_abs_count_deviation": l1,
        "phase1_abs_count_deviation": start,
        "reported_fill_phase": got["fill_phase"],
        "reported_fair_phase": got["fair_phase"],
        "independently_verified_feasible": True,
        "fairness_not_worse_than_reported_first_stage": True,
        "fairness_optimality_independently_proven": False,
        "actual_wasm_execution_proven": False,
        "operationally_certified": False,
    }
