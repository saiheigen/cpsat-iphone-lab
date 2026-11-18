"""Two-phase lexicographic fairness prototype, native CP-SAT only.

Stage 1: maximize the number of legally assigned shifts. Stage 2: lock
exactly that number and minimize the L1 deviations from SOFT per-person
targets. All hard constraints are rebuilt via the same prepare() function,
and the entire assignment is independently rechecked before return.

This prototype is NOT yet connected to the full-month C++/WASM solver.
It only optimizes *counts*, not harsh shifts, officer long hours,
business duties, or real-world workforce policies.
"""
from __future__ import annotations

import math
from ortools.sat.python import cp_model
from solver.roster_cp_sat import prepare, independently_check


def _run(model, limit):
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = limit
    status = solver.solve(model)
    return solver, status, solver.status_name(status)


def _chosen(tasks, persons, variables, solver, events, history, pins):
    chosen = {t.key: None for t in tasks}
    for (shift, ident), var in variables.items():
        if solver.value(var):
            if chosen[shift] is not None:
                raise AssertionError("Duplicate assignment in CP-SAT solution")
            chosen[shift] = ident
    independently_check(tasks, persons, chosen, events, history, pins)
    return chosen


def _deviation(chosen, targets):
    actual = {ident: 0 for ident in targets}
    for ident in chosen.values():
        if ident is not None:
            actual[ident] += 1
    return sum(abs(actual[k] - v) for k, v in targets.items()), actual


def solve_lexicographic_count_fair(
    tasks, persons, targets, events=None, history=None, pins=None,
    seconds_fill=5.0, seconds_fair=5.0,
):
    """Never sacrifice an already-found legal shift to improve fairness.

    Unproven fill status remains unproven. A full, independently checked
    schedule proves maximal number of filled slots by trivial upper bound.
    Fairness 'OPTIMAL' means optimal ONLY for locked achieved fill count
    and the simple L1 count objective, not for all duty-quality measures.
    """
    events, history, pins = events or [], history or [], pins or {}
    ids = {p.id for p in persons}
    if len(ids) != len(persons) or set(targets) != ids:
        raise ValueError("Exactly one fairness target required per staff ID")
    if any(type(n) is not int or n < 0 for n in targets.values()):
        raise ValueError("Fairness targets must be nonnegative integers")
    for seconds in (seconds_fill, seconds_fair):
        if (isinstance(seconds, bool) or
                not isinstance(seconds, (int, float)) or
                not math.isfinite(seconds) or seconds <= 0):
            raise ValueError("Solver time limits must be positive and finite")

    fill_model, fill_vars = prepare(tasks, persons, events, history, pins)
    first, st1, phase1 = _run(fill_model, seconds_fill)
    if st1 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {
            "status": "NO_FEASIBLE_SOLVER_RESULT",
            "assignments": None, "filled": None, "missing": None,
            "fill_phase": phase1, "fair_phase": "NOT_RUN",
            "fill_optimal_proven": False, "fair_optimal_proven": False,
            "operationally_certified": False,
        }
    candidate = _chosen(tasks, persons, fill_vars, first, events, history, pins)
    fill = sum(ident is not None for ident in candidate.values())
    fill_proven = st1 == cp_model.OPTIMAL or fill == len(tasks)
    first_cost, _ = _deviation(candidate, targets)

    # Important: start with identical hard rules; only the objective and
    # an equality fixing the already-achieved coverage change.
    fair_model, fair_vars = prepare(tasks, persons, events, history, pins)
    fair_model.add(sum(fair_vars.values()) == fill)
    gaps = []
    for ident in sorted(targets):
        assigned = sum(v for (key, who), v in fair_vars.items() if who == ident)
        upper = len(tasks) + targets[ident]
        gap = fair_model.new_int_var(0, upper, f"fair_count_gap_{ident}")
        fair_model.add_abs_equality(gap, assigned - targets[ident])
        gaps.append(gap)
    fair_model.minimize(sum(gaps))
    second, st2, phase2 = _run(fair_model, seconds_fair)
    best = candidate
    cost = first_cost
    better = False
    if st2 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        improved = _chosen(tasks, persons, fair_vars, second,
                           events, history, pins)
        n = sum(ident is not None for ident in improved.values())
        if n != fill:
            raise AssertionError("Fairness stage changed the number of staffed shifts")
        new_cost, _ = _deviation(improved, targets)
        if new_cost > first_cost:
            # A model-solver discrepancy must not be silently accepted as
            # a fake improvement. Retain the legally audited first roster.
            if st2 == cp_model.OPTIMAL:
                raise AssertionError("Proven fairness optimum worse than first feasible")
        else:
            best = improved
            cost = new_cost
            better = new_cost < first_cost

    independently_check(tasks, persons, best, events, history, pins)
    _, actual = _deviation(best, targets)
    return {
        "status": "FULL" if fill == len(tasks) else
                  "PARTIAL_FILL_PROVEN" if fill_proven else
                  "PARTIAL_FILL_NOT_PROVEN",
        "assignments": best, "filled": fill,
        "missing": len(tasks) - fill,
        "fill_phase": phase1, "fair_phase": phase2,
        "fill_optimal_proven": fill_proven,
        "fair_optimal_proven_given_fill": st2 == cp_model.OPTIMAL,
        "fairness_improved": better,
        "first_abs_count_deviation": first_cost,
        "final_abs_count_deviation": cost,
        "actual_counts": actual, "soft_targets": dict(targets),
        "objective_scope": "L1-count-deviation-only",
        "actual_wasm_executed": False,
        "operationally_certified": False,
    }
