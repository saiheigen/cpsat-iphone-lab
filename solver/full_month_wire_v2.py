"""Synthetic-only full-month wire protocol design for future CP-SAT WASM.

guard-month-v2 is NOT supported by the existing 64x24 C++ WASM bridge.
This module validates and serializes a complete month per disjoint duty pool
without truncation. Every candidate must honor static availability, current
roster pool, historical conflicts and fixed slots. The C++ V2 solver must
independently reconstruct and enforce intra-month rest/Sunday constraints.

No real personnel information is exported; staff IDs, names, events,
and dates beyond YYYY-MM are never serialized. This is NOT a production
roster converter or iPhone solver.
"""
from __future__ import annotations

from datetime import date
import hashlib
from typing import Any

from solver.roster_cp_sat import (
    Event, History, Person, Shift, conflicts, independently_check,
    month_shifts, prepare, static_reason,
)
from solver.constructive_witness import construct_legal_seed


VERSION = "guard-month-v2"
SLOTS_PER_DAY = {"door": 12, "officer": 7}
MAX_STAFF = 106
MAX_SHIFTS = 589
MAX_MASK_BITS = 589 * 106


def _month_pool(tasks: list[Shift], year: int, month: int, pool: str):
    expected = [t for t in month_shifts(year, month) if t.pool == pool]
    if [t.key for t in tasks] != [t.key for t in expected]:
        raise ValueError("Only a complete, ordered, canonical month is accepted")
    return expected


def export_full_month_v2(
    year: int, month: int, pool: str,
    persons: list[Person],
    events: list[Event] | None = None,
    history: list[History] | None = None,
    pins: dict[str, str | None] | None = None,
    build_hint: bool = False,
) -> dict:
    if pool not in SLOTS_PER_DAY:
        raise ValueError("Unknown pool")
    tasks = [t for t in month_shifts(year, month) if t.pool == pool]
    people = [p for p in persons if p.pool == pool]
    if not (1 <= len(people) <= MAX_STAFF):
        raise ValueError("Full-month protocol needs 1 to 106 staff per pool")
    if len({p.id for p in persons}) != len(persons):
        raise ValueError("Duplicate staff IDs")
    events, history, pins = events or [], history or [], pins or {}
    ids = {p.id: p for p in persons}
    if any(e.person not in ids for e in events):
        raise ValueError("Unknown event personnel")
    if any(h.person not in ids for h in history):
        raise ValueError("Unknown history personnel")
    if any(k not in {t.key for t in tasks} for k in pins):
        raise ValueError("Pins outside requested duty pool")
    if any(v is not None and (v not in ids or ids[v].pool != pool)
           for v in pins.values()):
        raise ValueError("Pinned person not in requested duty pool")
    pool_events = [e for e in events if ids[e.person].pool == pool]
    pool_history = [h for h in history if ids[h.person].pool == pool]
    if any(h.shift.pool != pool for h in pool_history):
        raise ValueError("Historical task pool does not match person pool")
    # The real native solver validates cross-month history and hard pins.
    _model, available = prepare(tasks, people, pool_events, pool_history, pins)
    mask = "".join("1" if (t.key, p.id) in available else "0"
                   for t in tasks for p in people)
    assert len(mask) == len(tasks) * len(people)
    if len(mask) > MAX_MASK_BITS or len(tasks) > MAX_SHIFTS:
        raise ValueError("Month exceeds negotiated wire format limits")
    positions = {p.id: i for i, p in enumerate(people)}
    fixed = [
        (-2 if t.key not in pins else
         -1 if pins[t.key] is None else positions[pins[t.key]])
        for t in tasks
    ]
    if build_hint:
        seed = construct_legal_seed(
            tasks, people, pool_events, pool_history, pins, attempts=6)
        hint = [(-1 if seed["assignments"][t.key] is None
                 else positions[seed["assignments"][t.key]])
                for t in tasks]
    else:
        hint = [-1] * len(tasks)
    # No identifiers, events or daily duty dates appear in the wire payload.
    payload = "\n".join((
        VERSION, f"{year:04}-{month:02}", pool,
        f"{len(tasks)} {len(people)}",
        mask, ",".join(map(str, fixed)), ",".join(map(str, hint)),
    )) + "\n"
    return {
        "contract": VERSION,
        "payload": payload,
        "pool": pool,
        "month": f"{year:04}-{month:02}",
        "tasks": tasks,
        "people": people,
        "events": pool_events,
        "history": pool_history,
        "pins": pins,
        "sha256": hashlib.sha256(payload.encode("ascii")).hexdigest(),
        "complete_canonical_month": True,
        "names_exported": False,
        "actual_wasm_compiler_implemented": False,
        "actual_wasm_solved": False,
        "operationally_certified": False,
    }


def validate_full_month_v2_export(encoded: dict) -> dict:
    """Independently inspect literal wire bytes and recompute candidate matrix.

    This ensures serialization does not lose shifts, pin intent, availability
    or historic exclusions. It does not prove an unimplemented C++ V2 solver.
    """
    payload = encoded.get("payload")
    if not isinstance(payload, str):
        raise ValueError("No full-month wire payload")
    raw = payload.splitlines()
    if len(raw) != 7 or raw[0] != VERSION:
        raise ValueError("Malformed guard-month-v2 frame")
    month, pool = raw[1], raw[2]
    if pool not in SLOTS_PER_DAY:
        raise ValueError("Invalid pool in wire format")
    if len(month) != 7 or month[4] != "-":
        raise ValueError("Invalid month")
    try:
        year, number = map(int, month.split("-"))
        n_tasks, n_people = map(int, raw[3].split())
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid frame counts") from exc
    tasks = _month_pool(encoded["tasks"], year, number, pool)
    people = encoded["people"]
    if n_tasks != len(tasks) or n_people != len(people):
        raise ValueError("Truncated or padded people/tasks in month frame")
    if len(raw[4]) != n_tasks * n_people or any(c not in "01" for c in raw[4]):
        raise ValueError("Truncated or corrupted eligibility matrix")
    try:
        fixed = list(map(int, raw[5].split(",")))
        hints = list(map(int, raw[6].split(",")))
    except ValueError as exc:
        raise ValueError("Bad fixed or hinted assignments") from exc
    if len(fixed) != n_tasks or len(hints) != n_tasks:
        raise ValueError("Wrong fixed/hint column lengths")
    if hashlib.sha256(payload.encode("ascii")).hexdigest() != encoded.get("sha256"):
        raise ValueError("Payload was changed after export")
    history_by = {}
    for h in encoded["history"]:
        history_by.setdefault(h.person, []).append(h.shift)
    for i, t in enumerate(tasks):
        expected_pin = (-2 if t.key not in encoded["pins"] else
                        -1 if encoded["pins"][t.key] is None else
                        next(k for k, p in enumerate(people)
                             if p.id == encoded["pins"][t.key]))
        if fixed[i] != expected_pin:
            raise ValueError("A fixed shift or forced vacancy was altered")
        if not -1 <= hints[i] < len(people):
            raise ValueError("Invalid warm-start index")
        if hints[i] >= 0 and raw[4][i * n_people + hints[i]] != "1":
            raise ValueError("Warm-start references an unavailable person")
        if fixed[i] >= 0 and hints[i] != -1 and hints[i] != fixed[i]:
            raise ValueError("Warm-start disagrees with a fixed person")
        if fixed[i] == -1 and hints[i] != -1:
            raise ValueError("Warm-start violates a forced vacancy")
        for j, p in enumerate(people):
            should = (p.pool == pool and not static_reason(
                p, t, encoded["events"]) and
                not any(conflicts(t, h) for h in history_by.get(p.id, ())))
            actual = raw[4][i * n_people + j] == "1"
            if actual != should:
                raise ValueError("Availability or cross-month exclusion was lost")
    if any(p.id in payload for p in people):
        raise ValueError("PII identity appeared in anonymous wire frame")
    return {"tasks": n_tasks, "people": n_people, "eligible_bits": raw[4].count("1"),
            "pool": pool, "month": month, "sha256": encoded["sha256"],
            "validated": True, "actual_wasm_solved": False,
            "operationally_certified": False}
