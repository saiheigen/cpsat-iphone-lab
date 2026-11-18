"""Experimental third-stage harsh-duty fairness, native CP-SAT.

No C++ WASM claim. Phase 1 maximizes legal fill; phase 2 locks fill and
minimizes integer L1 count difference. Phase 3 locks EACH FILLED POSITION
as well as achieved total count fairness, then minimizes normalized hardship.

v7 categories: four 22-06 door slots; night total; door noon 12-14;
officer noon 12-18; officer 6h shifts and actual officer duty hours.
The new weighted integer L1 objective is NOT v7 deepQuality's squared terms.
Only synthetic data are used in GitHub tests, never actual duty information.
"""
from __future__ import annotations

from collections import Counter
import math
from ortools.sat.python import cp_model

from solver.lexicographic_count_fair import (
    solve_lexicographic_count_fair, _run, _chosen, _deviation)
from solver.roster_cp_sat import prepare, independently_check

WEIGHTS = {
    "night_total": 2,
    "night_22_24": 1, "night_00_02": 1,
    "night_02_04": 1, "night_04_06": 1,
    "noon": 2,
    "officer_hours": 1,
    "officer_six_hour": 2,
}


def shift_burdens(shift) -> dict[str, int]:
    if shift.pool == "door":
        burdens = {}
        if 1 <= shift.num <= 4:
            burdens["night_total"] = 1
            burdens[("night_22_24", "night_00_02", "night_02_04",
                     "night_04_06")[shift.num - 1]] = 1
        if shift.num == 8:
            burdens["noon"] = 1
        return burdens
    if shift.pool == "officer":
        burdens = {"officer_hours": shift.hours}
        if 1 <= shift.num <= 4:
            burdens["night_total"] = 1
        if shift.num == 6:
            burdens["noon"] = 1
        if shift.hours == 6:
            burdens["officer_six_hour"] = 1
        return burdens
    raise ValueError("Unsupported duty pool")


def hardship_score(tasks, chosen, people=None):
    """Recalculate independently of the CP-SAT objective.

    F * observed_per_person - category_total * person_shift_count
    gives normalized L1 burden without favoring staff who work fewer shifts.
    """
    if set(chosen) != {t.key for t in tasks}:
        raise ValueError("Missing or extra assignments")
    ids = [p.id for p in people] if people is not None else sorted(
        {v for v in chosen.values() if v is not None})
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate personnel")
    count = Counter({p: 0 for p in ids})
    burden = {p: Counter() for p in ids}
    totals = Counter()
    filled = 0
    for task in tasks:
        who = chosen[task.key]
        if who is None:
            continue
        if who not in count:
            raise ValueError("Unknown assignment personnel")
        filled += 1
        count[who] += 1
        for category, units in shift_burdens(task).items():
            totals[category] += units
            burden[who][category] += units
    components = {category: sum(
        abs(filled * burden[p][category] - total * count[p])
        for p in ids) for category, total in totals.items()}
    return {
        "score": sum(v * WEIGHTS[cat] for cat, v in components.items()),
        "components": components, "filled": filled, "totals": dict(totals),
        "actual_counts": dict(count),
        "burdens": {p: dict(burden[p]) for p in ids}
    }


def solve_three_stage_hardship(
    tasks, persons, targets, *, events=None, history=None, pins=None,
    seconds_fill=5.0, seconds_fair=5.0, seconds_hardship=5.0,
):
    """Protect fill positions, all pins/rest, and exact achieved count L1.

    On phase-3 timeout or inferior result, retain the independently checked
    phase-2 incumbent. Phase-3 OPTIMAL means optimal ONLY for locked filled
    shift positions and current achieved L1 count cost, not global v7 quality.
    """
    if (type(seconds_hardship) not in (int, float) or
            not math.isfinite(seconds_hardship) or seconds_hardship <= 0):
        raise ValueError("Hardship time limit must be positive and finite")
    events, history, pins = events or [], history or [], pins or {}
    if len({t.pool for t in tasks}) > 1:
        raise ValueError("Solve hardship in one duty pool at a time")
    by_id = {p.id: p for p in persons}
    if len(by_id) != len(persons) or set(targets) != set(by_id):
        raise ValueError("Targets must cover unique personnel exactly")

    prior = solve_lexicographic_count_fair(
        tasks, persons, targets, events, history, pins,
        seconds_fill=seconds_fill, seconds_fair=seconds_fair)
    if prior["assignments"] is None:
        return {**prior, "hardship_phase": "NOT_RUN",
                "hardship_optimal_proven_given_locked_predecessors": False,
                "stage3_wasm_executed": False}
    previous = prior["assignments"]
    before = hardship_score(tasks, previous, persons)
    filled = prior["filled"]
    count_cost = prior["final_abs_count_deviation"]

    model, variables = prepare(tasks, persons, events, history, pins)
    staff = [p.id for p in persons]
    by_shift = {t.key: [v for (k, _), v in variables.items() if k == t.key]
                for t in tasks}
    for t in tasks:
        model.add(sum(by_shift[t.key]) == int(previous[t.key] is not None))

    per_person = {ident: sum(v for (key, who), v in variables.items()
                             if who == ident) for ident in staff}
    count_gaps = []
    for ident in staff:
        gap = model.new_int_var(0, len(tasks) + targets[ident],
                                f"fixed_count_L1_{ident}")
        model.add_abs_equality(gap, per_person[ident] - targets[ident])
        count_gaps.append(gap)
    model.add(sum(count_gaps) == count_cost)

    terms = []
    # The exact set of filled shift positions is fixed, so category totals
    # from the legally audited prior solution are constants.
    for ident in staff:
        for category, total in before["totals"].items():
            burden = sum(
                shift_burdens(t).get(category, 0) * variables[(t.key, ident)]
                for t in tasks if (t.key, ident) in variables and
                shift_burdens(t).get(category, 0)
            )
            bound = max(1, 12 * max(1, filled) ** 2)
            deviation = model.new_int_var(0, bound,
                                          f"burden_{category}_{ident}")
            model.add_abs_equality(
                deviation, filled * burden - total * per_person[ident])
            terms.append(WEIGHTS[category] * deviation)
    model.minimize(sum(terms))
    solver, status, phase = _run(model, seconds_hardship)
    final, after, used_third = previous, before, False
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        candidate = _chosen(tasks, persons, variables, solver, events, history, pins)
        if any((candidate[t.key] is None) != (previous[t.key] is None)
               for t in tasks):
            raise AssertionError("Stage three changed occupied shift positions")
        deviation, _ = _deviation(candidate, targets)
        if deviation != count_cost:
            raise AssertionError("Stage three sacrificed count fairness")
        audited = hardship_score(tasks, candidate, persons)
        if audited["score"] <= before["score"]:
            final, after, used_third = candidate, audited, True
        elif status == cp_model.OPTIMAL:
            raise AssertionError("Proven hardship optimum worse than prior feasible")
    independently_check(tasks, persons, final, events, history, pins)
    final_count_cost, actual = _deviation(final, targets)
    if final_count_cost != count_cost or after["filled"] != filled:
        raise AssertionError("Final hardship result changed protected objectives")
    return {
        **prior, "assignments": final, "actual_counts": actual,
        "hardship_phase": phase,
        "hardship_optimal_proven_given_locked_predecessors":
            bool(status == cp_model.OPTIMAL and used_third),
        "hardship_initial_score": before["score"],
        "hardship_final_score": after["score"],
        "hardship_improved": after["score"] < before["score"],
        "hardship_components_before": before["components"],
        "hardship_components_after": after["components"],
        "fixed_occupied_positions": True,
        "final_abs_count_deviation": final_count_cost,
        "stage3_wasm_executed": False,
        "hardship_objective_scope": "normalized-integer-L1-not-v7-squared-loss",
        "operationally_certified": False,
    }
