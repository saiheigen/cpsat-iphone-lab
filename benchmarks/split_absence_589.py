"""Fictional full-December CP-SAT stress with concurrent absences and history.

Run ONLY in GitHub with made-up personnel IDs. This tests the partial
native model, not actual workforce feasibility or iPhone runtime.
"""
from datetime import date
import json
from pathlib import Path
import time

from solver.roster_cp_sat import (
    Event, History, Person, Shift, independently_check, month_shifts,
)
from solver.split_fill_cp_sat import solve_split_fill_first


def d(number, month=12):
    return date(2026, month, number)


def main():
    people = ([Person(f"H{i:03}", "door") for i in range(1, 57)] +
              [Person(f"P{i:03}", "officer") for i in range(1, 51)])
    tasks = month_shifts(2026, 12)
    events = []
    for i in range(1, 9):
        events.append(Event(f"H{i:03}", "leave", d(5), d(11)))
    for i in range(9, 13):
        events.append(Event(f"H{i:03}", "nightcheck", d(17), d(17)))
    for i in range(13, 17):
        events.append(Event(f"H{i:03}", "driver", d(23), d(23)))
    for i in range(1, 5):
        events.append(Event(f"P{i:03}", "training", d(3), d(8)))
    for i in range(5, 9):
        events.append(Event(f"P{i:03}", "officer_duty", d(12), d(15)))
    for i in range(9, 13):
        events.append(Event(f"P{i:03}", "meal", d(20), d(20)))
    for i in range(13, 17):
        events.append(Event(f"P{i:03}", "nightcheck", d(27), d(27)))
    events.append(Event("H017", "exempt_night", d(1), d(31)))
    events.append(Event("P017", "exempt_noon", d(1), d(31)))
    history = [
        History("H021", Shift("door", d(30, 11), 6)),
        History("H022", Shift("door", d(29, 11), 1)),
        History("P021", Shift("officer", d(30, 11), 5)),
        History("P022", Shift("officer", d(29, 11), 7)),
    ]
    started = time.monotonic()
    report = solve_split_fill_first(
        tasks, people, events=events, history=history,
        seconds_full=20, seconds_fallback=15)
    if report["assignments"] is not None:
        independently_check(tasks, people, report["assignments"],
                            events, history)
    output = {
        "scenario": "fictional-2026-12-589-shifts-with-absences",
        "staff": {"door": 56, "officer": 50},
        "tasks": len(tasks), "synthetic_event_records": len(events),
        "synthetic_previous_month_shifts": len(history),
        "strategy": "per-pool-full-feasibility-then-max-fill",
        "status": report["status"],
        "filled": report["filled"], "missing": report["missing"],
        "optimal_fill_proven": report["optimal_fill_proven"],
        "seconds": round(time.monotonic() - started, 3),
        "pool_statuses": {
            name: {
                "tasks": data["tasks"], "filled": data["filled"],
                "missing": data["missing"],
                "full_feasibility": data["full_feasibility"],
                "fallback": data["fallback"],
                "solution_source": data.get("solution_source", "unknown"),
                "optimal_fill_proven": data["optimal_fill_proven"],
                "seconds": data["seconds"],
            }
            for name, data in report["pools"].items()
        },
        "real_world_rules_fully_verified": False,
        "iphone_webassembly": False,
        "secrets_or_real_personnel_included": False,
        "note": ("FEASIBLE/UNKNOWN are NOT proof of infeasibility or best "
                 "possible fill. Do not use for operational rosters."),
    }
    out = Path("split_absence_589.json")
    out.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if len(tasks) != 589 or len(events) < 20:
        raise AssertionError("Stress fixture missing expected dimensions")
    # An audited FEASIBLE output or an explicit timeout is a truthful
    # benchmark result, not necessarily a successful max-fill proof.


if __name__ == "__main__":
    main()
