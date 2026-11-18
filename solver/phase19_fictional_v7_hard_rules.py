"""Phase 19: fictional-only v7-style hard-rule matrix -> genuine v4 WASM frame.

This deliberately contains NO backup loader, no CLI accepting a real roster,
no personnel names and no operational approval. It creates an immutable suite
of invented full-month duty data, converts it with the existing native v2/v3
adapters, and independently checks actual C++ WASM result assignments later.

Do not infer that an arbitrary operational v7 input is complete from the
presence of a syntactically valid mask. Past-month signatures, approvals,
actual in-island state and release authority are OUT OF SCOPE.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib

from solver.roster_cp_sat import (
    Event, History, Person, Shift, static_reason, conflicts)
from solver.full_month_wire_v2 import (
    export_full_month_v2, validate_full_month_v2_export,
    audit_full_month_v2_response)
from solver.full_month_fair_wire_v3 import (
    export_full_month_fair_v3)
from solver.fairness_targets_v7 import FairPerson

MONTH = (2026, 12)
SOURCE = "phase19-hardcoded-fictional-rules-only"
CONTRACT = "guard-month-harsh-v4"


@dataclass(frozen=True)
class InventedMonth:
    pool: str
    people: tuple[Person, ...]
    events: tuple[Event, ...]
    history: tuple[History, ...]
    pins: tuple[tuple[str, str | None], ...]


def invented_month(pool: str) -> InventedMonth:
    """Only two hard-coded imaginary cases; never read or import user data."""
    if pool == "door":
        people = tuple(Person(f"SIM_D_{n:03}", "door", kitchen=n == 6)
                       for n in range(10))
        events = (
            Event(people[0].id, "leave", date(2026, 12, 4), date(2026, 12, 5)),
            Event(people[1].id, "nightcheck", date(2026, 12, 1), date(2026, 12, 1)),
            Event(people[2].id, "driver", date(2026, 12, 10), date(2026, 12, 10)),
            Event(people[3].id, "training", date(2026, 12, 15), date(2026, 12, 16)),
            Event(people[4].id, "exempt_night", date(2026, 12, 1), date(2026, 12, 31)),
            Event(people[5].id, "exempt_noon", date(2026, 12, 1), date(2026, 12, 31)),
        )
        history = (
            History(people[7].id, Shift("door", date(2026, 11, 30), 6)),
            History(people[8].id, Shift("door", date(2026, 11, 29), 5)),
        )
        pins = ((Shift("door", date(2026, 12, 5), 8).key, None),
                (Shift("door", date(2026, 12, 2), 6).key, people[9].id))
    elif pool == "officer":
        people = tuple(Person(f"SIM_O_{n:03}", "officer") for n in range(8))
        events = (
            Event(people[0].id, "officer_duty", date(2026, 12, 8), date(2026, 12, 8)),
            Event(people[1].id, "meal", date(2026, 12, 12), date(2026, 12, 12)),
            Event(people[2].id, "nightcheck", date(2026, 12, 20), date(2026, 12, 20)),
            Event(people[3].id, "driver", date(2026, 12, 3), date(2026, 12, 3)),
            Event(people[4].id, "exempt_all", date(2026, 12, 1), date(2026, 12, 31)),
            Event(people[5].id, "training", date(2026, 12, 24), date(2026, 12, 25)),
        )
        history = (History(people[6].id,
                           Shift("officer", date(2026, 11, 30), 7)),)
        pins = ((Shift("officer", date(2026, 12, 6), 4).key, None),
                (Shift("officer", date(2026, 12, 5), 5).key, people[7].id))
    else:
        raise ValueError("Only two invented duty pools are supported")

    # Only a handful of invented calendar days are declared on-site for
    # this first source-to-WASM bridge. All remaining days are explicitly
    # exempt_all. This avoids a near-complete highly symmetric candidate
    # matrix masking whether the eligibility transport actually works.
    # It is NOT a claim about actual operational staffing or duty coverage.
    fictional_available_days = (
        ({3,7},{3},{9,12},{17},{8},{8},set(),{2,3},{6},{2,5})
        if pool == "door" else
        ({10},{14},{22},{2,5},set(),{26},{2,3,6},{5})
    )
    restrictions = []
    for person, available in zip(people, fictional_available_days):
        opened = None
        for d in range(1,33):
            prohibited = d <= 31 and d not in available
            if prohibited and opened is None:
                opened = d
            if not prohibited and opened is not None:
                restrictions.append(Event(
                    person.id,"exempt_all",date(2026,12,opened),
                    date(2026,12,d-1)))
                opened = None
    events += tuple(restrictions)
    return InventedMonth(pool, people, events, history, pins)


def create_case(pool: str) -> dict:
    fixture = invented_month(pool)
    people, events, history = list(fixture.people), list(fixture.events), list(fixture.history)
    pins = dict(fixture.pins)
    source = export_full_month_v2(
        *MONTH, pool, people, events=events, history=history, pins=pins,
        build_hint=False)
    parsed = validate_full_month_v2_export(source)
    fair = export_full_month_fair_v3(
        source, [FairPerson(p.id, weight=1.0) for p in people])
    frame = fair["payload"].replace("guard-month-fair-v3\n",
                                    CONTRACT + "\n", 1)
    fields = frame.splitlines()
    if (len(fields) != 8 or fields[0] != CONTRACT or
            fields[1] != "2026-12" or fields[2] != pool or
            fields[4] != source["payload"].splitlines()[4]):
        raise AssertionError("Rule input changed during v4 frame conversion")
    if any(p.id in frame for p in people):
        raise AssertionError("A fictional identifier entered the anonymous frame")
    return {
        "fixture": fixture, "v2_source": source, "v3_source": fair,
        "frame": frame, "sha256": hashlib.sha256(frame.encode("ascii")).hexdigest(),
        "pool": pool, "shifts": parsed["tasks"], "staff": parsed["people"],
        "source": SOURCE, "synthetic_only": True,
        "history_freshness_verified_for_real_data": False,
        "full_v7_rule_parity_verified": False,
        "operationally_certified": False,
    }


def eligible(case: dict, person_idx: int, day: int, slot: int) -> bool:
    """Inspect a literal bit in the genuine C++ wire order, no solver needed."""
    if not (0 <= person_idx < case["staff"] and 1 <= day <= 31):
        raise ValueError("Outside fictional month")
    slots = 12 if case["pool"] == "door" else 7
    if not 1 <= slot <= slots:
        raise ValueError("Outside pool shift numbering")
    i = (day - 1) * slots + slot - 1
    frame = case["frame"].splitlines()
    return frame[4][i * case["staff"] + person_idx] == "1"


def audit_genuine_result(case: dict, got: dict) -> dict:
    """Independently recheck every result against original fake events/history.

    Audit feasibility and claim consistency; this is NOT an independent
    proof of global optimality nor independent WASM execution attestation.
    """
    def require(ok, label):
        if not ok:
            raise ValueError(label)

    require(case.get("source") == SOURCE and case.get("synthetic_only") is True,
            "Only the two invented full-month cases are valid")
    require(hashlib.sha256(case["frame"].encode("ascii")).hexdigest() == case["sha256"],
            "v4 frame was mutated after independently validated export")
    old = case["v3_source"]["payload"].splitlines()
    now = case["frame"].splitlines()
    require(len(now) == 8 and now == [CONTRACT] + old[1:],
            "Hard-rule eligibility or count targets changed")
    original = case["v2_source"]
    audited = audit_full_month_v2_response(original, got)
    n = len(original["people"])
    actual = [0] * n
    for idx in got["assignments"]:
        if idx >= 0:
            actual[idx] += 1
    targets = list(map(int, now[7].split(",")))
    require(actual == got.get("actual_counts"),
            "Individual count changed or misreported")
    deviation = sum(abs(a-b) for a, b in zip(actual, targets))
    require(type(got.get("final_abs_deviation")) is int and
            deviation == got["final_abs_deviation"],
            "Count fairness L1 disagrees with independent result")
    require(type(got.get("phase1_abs_deviation")) is int and
            got["phase1_abs_deviation"] >= deviation,
            "Fair stage worsened the recorded first-stage count deviation")
    require(got.get("fill_phase") in ("OPTIMAL", "FEASIBLE") and
            got.get("fair_phase") in ("OPTIMAL", "FEASIBLE", "UNKNOWN") and
            got.get("hardship_phase") in ("OPTIMAL", "FEASIBLE", "UNKNOWN"),
            "Invalid phase status")
    for phase, flag, proved in (
        ("fill_phase", "fill_optimal_proven", "OPTIMAL"),
        ("fair_phase", "fair_optimal_proven_given_fill", "OPTIMAL"),
        ("hardship_phase", "hardship_optimal_proven_given_locked_predecessors", "OPTIMAL"),
    ):
        require(type(got.get(flag)) is bool and
                (got[phase] == proved) == got[flag],
                "Incorrect stage proof indicator")
    require(got.get("fixed_occupied_positions") is True,
            "Stage 3 might have changed occupied positions")
    require(type(got.get("hardship_initial_score")) is int and
            type(got.get("hardship_final_score")) is int and
            got["hardship_final_score"] <= got["hardship_initial_score"],
            "Hardship objective worsened or went missing")
    require(got.get("hardship_improved") is
            (got["hardship_final_score"] < got["hardship_initial_score"]),
            "Incorrect hardship-improved indicator")
    return {
        "synthetic_only": True, "source": SOURCE, "pool": case["pool"],
        "month": "2026-12", "shifts": case["shifts"],
        "filled": audited["filled"], "missing": audited["missing"],
        "frame_sha256": case["sha256"],
        "independently_verified_feasible": True,
        "full_v7_rule_parity_verified": False,
        "history_freshness_verified_for_real_data": False,
        "operationally_certified": False,
    }
