#!/usr/bin/env python3
"""Single-pool full-occupancy feasibility experiment, fictional data only.

Compare with the original joint-pool maximize-fill benchmark (20 s: FEASIBLE,
554/589). Do not treat a timeout as infeasibility or full hard-rule coverage.
No real names, military records, leaves, cross-month history or fairness.
"""
import json
import os
from pathlib import Path
import time

from ortools.sat.python import cp_model

from solver.roster_cp_sat import Person, month_shifts, prepare, independently_check


def witness_for(task):
    group = 28 if task.pool == "door" else 25
    cycle = (task.day.day - 1) // 2
    parity = (task.day.day - 1) % 2
    number = parity * group + ((task.num - 1 + cycle) % group) + 1
    return f"{'H' if task.pool == 'door' else 'P'}{number:03}"


def main():
    pool = os.environ.get("BENCH_POOL", "")
    if pool not in ("door", "officer"):
        raise SystemExit("BENCH_POOL must be door or officer")
    t0 = time.monotonic()
    tasks = [t for t in month_shifts(2026, 12) if t.pool == pool]
    people = ([Person(f"H{i:03}", "door") for i in range(1, 57)] if pool == "door"
              else [Person(f"P{i:03}", "officer") for i in range(1, 51)])
    witness = {t.key: witness_for(t) for t in tasks}
    independently_check(tasks, people, witness)
    model, candidates = prepare(tasks, people)
    # All tasks must be occupied. This turns the first objective into a
    # feasibility decision. It is safe ONLY if the known witness is genuine.
    model.add(sum(candidates.values()) == len(tasks))
    for (task_id, person_id), var in candidates.items():
        model.add_hint(var, 1 if witness[task_id] == person_id else 0)
    build_time = time.monotonic() - t0

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = 25.0
    status = solver.solve(model)
    actual = None
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        actual = {t.key: None for t in tasks}
        for (task, ident), var in candidates.items():
            if solver.value(var):
                if actual[task] is not None:
                    raise AssertionError("Multiple personnel in one task")
                actual[task] = ident
        independently_check(tasks, people, actual)
    filled = None if actual is None else sum(v is not None for v in actual.values())
    if filled is not None and filled != len(tasks):
        raise AssertionError("Feasible assignment failed full-coverage gate")
    if status == cp_model.INFEASIBLE:
        raise AssertionError("The independently audited full witness contradicts infeasibility")
    result = {
        "experiment": "split-native-full-occupancy",
        "scenario": "synthetic-no-absences-only",
        "pool": pool,
        "tasks": len(tasks),
        "people": len(people),
        "candidate_assignments": len(candidates),
        "variables": len(model.proto.variables),
        "constraints": len(model.proto.constraints),
        "build_seconds": round(build_time, 3),
        "solve_seconds": round(time.monotonic() - t0 - build_time, 3),
        "status": solver.status_name(status),
        "found_full_roster": filled == len(tasks),
        "proved_optimal_for_this_subset": status == cp_model.OPTIMAL and filled == len(tasks),
        "independent_complete_witness": True,
        "full_real_world_rules_verified": False,
        "iphone_wasm_verified": False,
        "unverified_features": [
            "real leave and duty restrictions",
            "cross-month approval and compensation",
            "monthly fair and hardship optimization",
            "phone browser native WASM",
        ],
    }
    Path(f"native_split_{pool}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # UNKNOWN/FEASIBLE remains recorded as such; no false assertion of success.


if __name__ == "__main__":
    main()
