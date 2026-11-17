"""Synthetic-only native CP-SAT scheduling experiment.

Separate nonoverlapping guard/NCO pools. First test if each pool can fill
every shift with no hard-rule relaxation. If that fails or times out,
rebuild the original model and maximize legal filled shifts. No missing
solution is silently turned into an all-blank or fake staff roster.

This is a *partial* rule model, not a certified real duty scheduler.
"""
from __future__ import annotations

import math
import time
from ortools.sat.python import cp_model
from solver.roster_cp_sat import prepare, independently_check
from solver.constructive_witness import construct_legal_seed

POOLS = ("door", "officer")


def _solve_model(model, seconds):
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = seconds
    status = solver.solve(model)
    return solver, status, solver.status_name(status)


def _result(tasks, persons, variables, solver, events, history, pins):
    chosen = {t.key: None for t in tasks}
    for (key, person), var in variables.items():
        if solver.value(var):
            if chosen[key] is not None:
                raise AssertionError("Double booking detected")
            chosen[key] = person
    independently_check(tasks, persons, chosen, events, history, pins)
    return chosen


def solve_split_fill_first(tasks, persons, events=None, history=None,
                           pins=None, seconds_full=5.0,
                           seconds_fallback=10.0):
    """Return a combined schedule only if both pool solves are audited.

    A fully filled pool has a proof of maximum fill from the trivial upper
    bound: at most one person per shift. For partially filled pools, only
    CP-SAT OPTIMAL on the max-fill stage gives optimality proof.
    """
    for budget in (seconds_full, seconds_fallback):
        if (not isinstance(budget, (float, int)) or isinstance(budget, bool)
                or not math.isfinite(budget) or budget <= 0):
            raise ValueError("Search time budgets must be positive and finite")
    events, history, pins = events or [], history or [], pins or {}
    ids = {p.id: p for p in persons}
    if len(ids) != len(persons) or any(not p.id or p.pool not in POOLS for p in persons):
        raise ValueError("Invalid or duplicate person identities")
    if len({t.key for t in tasks}) != len(tasks) or any(t.pool not in POOLS for t in tasks):
        raise ValueError("Invalid or duplicate shift keys")
    if any(e.person not in ids for e in events):
        raise ValueError("Unknown event person")
    if any(e.type in ("meal", "officer_duty") and ids[e.person].pool != "officer" for e in events):
        raise ValueError("Officer-specific duty event belongs to guard")
    if any(h.person not in ids or h.shift.pool != ids[h.person].pool for h in history):
        raise ValueError("Unknown or wrong-pool history person")
    keys = {t.key for t in tasks}
    if any(k not in keys for k in pins):
        raise ValueError("Pin references unknown shift")
    if any(v is not None and v not in ids for v in pins.values()):
        raise ValueError("Pin references unknown person")

    diagnostics, combined = {}, {}
    for pool in POOLS:
        started = time.monotonic()
        tt = [t for t in tasks if t.pool == pool]
        pp = [p for p in persons if p.pool == pool]
        ee = [e for e in events if ids[e.person].pool == pool]
        hh = [h for h in history if ids[h.person].pool == pool]
        pi = {k: v for k, v in pins.items() if k.startswith(pool + ":")}
        # Even for empty task pools, validate any relevant historical data.
        if not tt:
            prepare([], pp, ee, hh, pi)
            diagnostics[pool] = {
                "status": "EMPTY", "full_feasibility": "NOT_APPLICABLE",
                "fallback": "NOT_RUN", "tasks": 0, "filled": 0, "missing": 0,
                "assignments": {}, "optimal_fill_proven": True,
                "seconds": round(time.monotonic() - started, 3)}
            continue

        full_model, full_vars = prepare(tt, pp, ee, hh, pi)
        seed = construct_legal_seed(tt, pp, ee, hh, pi, attempts=12)
        for (task, ident), var in full_vars.items():
            full_model.add_hint(var, 1 if seed["assignments"][task] == ident else 0)
        full_model.add(sum(full_vars.values()) == len(tt))
        first, st, first_name = _solve_model(full_model, seconds_full)
        if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            answer = _result(tt, pp, full_vars, first, ee, hh, pi)
            if sum(x is not None for x in answer.values()) != len(tt):
                raise AssertionError("Full-fill equality was violated")
            diagnostics[pool] = {
                "status": "FULL", "full_feasibility": first_name,
                "fallback": "NOT_RUN", "tasks": len(tt), "filled": len(tt),
                "missing": 0, "assignments": answer,
                "solution_source": "cp_sat",
                "optimal_fill_proven": True,
                "seconds": round(time.monotonic() - started, 3)}
            combined.update(answer)
            continue

        if seed["full_upper_bound_reached"]:
            if st != cp_model.UNKNOWN:
                raise AssertionError("CP-SAT rejected independently audited full witness")
            # Explicitly show the solver timed out. Full legal witness, however,
            # independently proves maximal fill under the current partial rules.
            answer = seed["assignments"]
            diagnostics[pool] = {
                "status": "FULL", "full_feasibility": first_name,
                "fallback": "NOT_RUN",
                "solution_source": "independent_constructive_witness",
                "tasks": len(tt), "filled": len(tt), "missing": 0,
                "assignments": answer, "optimal_fill_proven": True,
                "seconds": round(time.monotonic() - started, 3)}
            combined.update(answer)
            continue

        # Full feasibility was INFEASIBLE/UNKNOWN. Drop the full-fill equality
        # entirely and optimize maximal legal coverage without weakening any
        # eligibility, history, rest, or pin constraints.
        fallback_model, fallback_vars = prepare(tt, pp, ee, hh, pi)
        for (task, ident), var in fallback_vars.items():
            fallback_model.add_hint(
                var, 1 if seed["assignments"][task] == ident else 0)
        second, st2, second_name = _solve_model(fallback_model, seconds_fallback)
        answer, filled, source = None, None, None
        if st2 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            answer = _result(tt, pp, fallback_vars, second, ee, hh, pi)
            filled = sum(x is not None for x in answer.values())
            source = "cp_sat"
            if st == cp_model.INFEASIBLE and filled == len(tt):
                raise AssertionError("Proven full infeasibility contradicts full solution")
        if st2 in (cp_model.INFEASIBLE, cp_model.MODEL_INVALID):
            raise AssertionError("Max-fill solver rejected a verified legal seed")
        if filled is None or seed["filled"] > filled:
            if st2 == cp_model.OPTIMAL:
                raise AssertionError("Proven optimum worse than independently verified seed")
            answer, filled, source = (seed["assignments"], seed["filled"],
                                      "independent_constructive_witness")
        if answer is not None:
            combined.update(answer)
        diagnostics[pool] = {
            "status": "PARTIAL" if answer is not None else "NO_FEASIBLE_RESULT",
            "full_feasibility": first_name, "fallback": second_name,
            "tasks": len(tt), "filled": filled,
            "missing": len(tt) - filled if filled is not None else None,
            "assignments": answer, "solution_source": source,
            "optimal_fill_proven": st2 == cp_model.OPTIMAL,
            "seconds": round(time.monotonic() - started, 3)}

    all_found = all(d["assignments"] is not None for d in diagnostics.values())
    proven = all_found and all(d["optimal_fill_proven"] for d in diagnostics.values())
    if not all_found:
        return {"status": "INCOMPLETE_NO_COMBINED_SCHEDULE",
                "assignments": None, "filled": None, "missing": None,
                "optimal_fill_proven": False, "pools": diagnostics,
                "operationally_certified": False}
    independently_check(tasks, persons, combined, events, history, pins)
    filled = sum(v is not None for v in combined.values())
    status = ("FULL" if filled == len(tasks) else
              "PARTIAL_OPTIMAL" if proven else "PARTIAL_FEASIBLE")
    return {"status": status, "assignments": combined, "filled": filled,
            "missing": len(tasks) - filled, "optimal_fill_proven": proven,
            "pools": diagnostics, "operationally_certified": False}
