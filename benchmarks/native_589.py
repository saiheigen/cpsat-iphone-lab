#!/usr/bin/env python3
"""Real native CP-SAT performance test on an entirely synthetic December 589-shift case.

A constructive 589/589 witness is audited and supplied as a CP-SAT hint.
The solver is *still really invoked*. Report OPTIMAL only if solver proves it.
This deliberately excludes leaves, driving, cross-month claims, and fairness;
it is not representative of actual military roster feasibility.
"""
from datetime import date
import json
from pathlib import Path
import time

from ortools.sat.python import cp_model
from solver.roster_cp_sat import Person, month_shifts, prepare, independently_check

def main():
    started = time.monotonic()
    tasks = month_shifts(2026, 12)
    people = ([Person(f"H{i:03}", "door") for i in range(1, 57)] +
              [Person(f"P{i:03}", "officer") for i in range(1, 51)])
    witness = {}
    for t in tasks:
        group_size = 28 if t.pool == "door" else 25
        pair = (t.day.day - 1) // 2
        parity = (t.day.day - 1) % 2
        serial = parity * group_size + ((t.num - 1 + pair) % group_size) + 1
        witness[t.key] = f"{'H' if t.pool == 'door' else 'P'}{serial:03}"
    independently_check(tasks, people, witness)

    model, variables = prepare(tasks, people)
    for (task_key, person_id), var in variables.items():
        model.add_hint(var, 1 if witness[task_key] == person_id else 0)
    build_end = time.monotonic()

    cp = cp_model.CpSolver()
    cp.parameters.num_search_workers = 1
    cp.parameters.max_time_in_seconds = 20.0
    status = cp.solve(model)
    status_name = cp.status_name(status)
    result = None
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        result = {t.key: None for t in tasks}
        for (key, ident), var in variables.items():
            if cp.value(var):
                if result[key] is not None:
                    raise AssertionError("Duplicate assignment")
                result[key] = ident
        independently_check(tasks, people, result)
    filled = None if result is None else sum(x is not None for x in result.values())
    report = {
        "dataset": "synthetic-2026-12-56-door-50-officer-no-absences",
        "runtime": "native-linux-python-ortools-cp-sat-single-worker",
        "tasks": len(tasks), "staff": len(people),
        "door_tasks": sum(t.pool == "door" for t in tasks),
        "officer_tasks": sum(t.pool == "officer" for t in tasks),
        "model_variables": len(model.proto.variables),
        "model_constraints": len(model.proto.constraints),
        "candidate_assignments": len(variables),
        "hint": "independently_verified_constructive_589_witness",
        "independent_full_witness_verified": True,
        "gap_to_independent_witness": None if filled is None else 589 - filled,
        "status": status_name,
        "filled": filled,
        "missing": None if filled is None else len(tasks) - filled,
        "optimal_fill_proven": status == cp_model.OPTIMAL,
        "full_589_fill_proven": status == cp_model.OPTIMAL and filled == 589,
        "build_seconds": round(build_end - started, 3),
        "solve_seconds": round(time.monotonic() - build_end, 3),
        "excludes": [
            "real personnel", "leave", "driving", "cross-month history",
            "credit/fairness optimization", "iPhone WebAssembly",
            "unmodeled unit duty rules",
        ],
    }
    Path("native_589_benchmark.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if len(tasks) != 589 or len(people) != 106:
        raise AssertionError("Bad synthetic benchmark dimensions")
    # A hint is NOT a constraint and CP-SAT is not required to return it.
    # FEASIBLE with fewer than 589 is a valid, independently audited, suboptimal
    # result; the constructive witness proves the omitted slots CAN be filled
    # in this simplified instance, but only CP-SAT OPTIMAL proves the maximum.
    # UNKNOWN likewise remains inconclusive, not a pass for optimality.

if __name__ == "__main__":
    main()
