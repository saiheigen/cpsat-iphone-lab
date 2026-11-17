"""Local-only bounded adapter for experimental assignment-v1 CP-SAT WASM.

Exports anonymous indices and eligibility bits, NOT names or duty dates.
The C++ contract is intentionally capped at 64 shifts and 24 staff.
Never silently split a month into chunks because cross-chunk rest and
history constraints would be lost. This is NOT operational certification.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any

from solver.roster_cp_sat import (
    Event, History, Person, Shift, conflicts, independently_check, prepare,
)

MAX_SHIFTS = 64
MAX_PEOPLE = 24
MAX_CONFLICTS = 1024
MAX_PAYLOAD_BYTES = 16000


def encode_assignment_v1(
    shifts: list[Shift],
    people: list[Person],
    events: list[Event] | None = None,
    history: list[History] | None = None,
    pins: dict[str, str | None] | None = None,
) -> dict:
    """Encode a bounded subset of currently modeled Python hard rules.

    The existing native model is built first as a validation and candidate
    oracle. Only constraints expressible as eligible candidate bits, fixed
    slots and pairwise person conflicts are exported. This is deliberately
    restricted to the current door/officer model and not a generic
    production-grade constraint compiler.
    """
    events, history, pins = events or [], history or [], pins or {}
    if not 1 <= len(shifts) <= MAX_SHIFTS:
        raise ValueError("WASM prototype accepts 1–64 shifts; refuse truncation")
    if not 1 <= len(people) <= MAX_PEOPLE:
        raise ValueError("WASM prototype accepts 1–24 people; refuse truncation")
    if len({t.key for t in shifts}) != len(shifts):
        raise ValueError("Duplicate shifts")
    if len({p.id for p in people}) != len(people):
        raise ValueError("Duplicate people")
    # prepare verifies typed events, history, pin IDs and overlaps.
    _model, available = prepare(shifts, people, events, history, pins)
    ids = {p.id: index for index, p in enumerate(people)}
    allowed = "".join(
        "1" if (t.key, p.id) in available else "0"
        for t in shifts for p in people
    )
    edges = [
        (i, j) for (i, a), (j, b) in combinations(enumerate(shifts), 2)
        if conflicts(a, b)
    ]
    if len(edges) > MAX_CONFLICTS:
        raise ValueError("Too many conflicts for bounded WASM prototype")
    fixed = []
    for t in shifts:
        if t.key not in pins:
            fixed.append(-2)  # Unconstrained
        elif pins[t.key] is None:
            fixed.append(-1)  # Deliberately vacant
        else:
            if (t.key, pins[t.key]) not in available:
                raise ValueError("Pinned person violates hard rules")
            fixed.append(ids[pins[t.key]])
    payload = "\n".join((
        "assignment-v1",
        f"{len(shifts)} {len(people)}",
        allowed,
        ";".join(f"{a}:{b}" for a, b in edges),
        ",".join(map(str, fixed)),
    )) + "\n"
    if len(payload.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ValueError("Prototype payload too large")
    return {
        "contract": "assignment-v1",
        "payload": payload,
        "shifts": shifts,
        "people": people,
        "events": events,
        "history": history,
        "pins": pins,
        "conflicts": edges,
        "anonymous": True,
        "operationally_certified": False,
        "supports_full_month": False,
    }


def audit_assignment_v1_response(encoded: dict, result: dict) -> dict:
    """Reconstruct and audit C++ WASM output before treating as a solution."""
    if encoded.get("contract") != "assignment-v1":
        raise ValueError("Wrong WASM bridge contract")
    if not isinstance(result, dict):
        raise ValueError("Missing solver result object")
    status = result.get("status")
    if status not in ("OPTIMAL", "FEASIBLE"):
        # UNKNOWN, INFEASIBLE and INVALID_INPUT are diagnostic only and must
        # NEVER be turned into an all-empty or approved schedule.
        raise ValueError(f"No verified feasible WASM roster: {status}")
    shifts = encoded["shifts"]
    people = encoded["people"]
    values = result.get("assignments")
    if not isinstance(values, list) or len(values) != len(shifts):
        raise ValueError("Missing or truncated assignment array")
    chosen = {}
    for task, value in zip(shifts, values):
        if (type(value) is not int or
                value < -1 or value >= len(people)):
            raise ValueError("Invalid person index returned by WASM")
        chosen[task.key] = None if value == -1 else people[value].id
    independently_check(
        shifts, people, chosen,
        encoded["events"], encoded["history"], encoded["pins"])
    filled = sum(v is not None for v in chosen.values())
    if result.get("filled") != filled or result.get("missing") != len(shifts) - filled:
        raise ValueError("WASM count mismatch")
    return {
        "assignments": chosen,
        "filled": filled,
        "missing": len(shifts) - filled,
        "solver_status": status,
        "fill_optimal_proven_for_current_subset": status == "OPTIMAL",
        "operationally_certified": False,
        "full_month_verified": False,
    }
