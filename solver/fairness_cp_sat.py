"""Native CP-SAT *experimental* lexicographic fairness, synthetic inputs only.

Priority 1: maximal legally filled shifts.
Priority 2: minimal deviations from availability-weighted and credit-adjusted
            person quotas, separately in door and officer pools.
Priority 3: minimal per-slot night/noon hardship deviations.
An unfinished/FEASIBLE stage never becomes an OPTIMAL claim. All output is
independently checked against the existing hard-rule auditor.

Not yet integrated with the website or browser WebAssembly.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math

from ortools.sat.python import cp_model

from solver.roster_cp_sat import (
    Person, Shift, Event, History, prepare, independently_check,
)

MILLION = Decimal("1000000")


def _scaled_weight(value):
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("Invalid business weight") from None
    if not n.is_finite() or not (Decimal("0") <= n <= Decimal("1")):
        raise ValueError("Business weight must be between 0 and 1")
    return int((n * MILLION).to_integral_value(rounding=ROUND_HALF_UP))


def _validate_adjustments(persons, weights, carry):
    by_id = {p.id: p for p in persons}
    if any(p not in by_id for p in weights):
        raise ValueError("Unknown person in weights")
    if any(p not in by_id for p in carry):
        raise ValueError("Unknown person in carry")
    values = {p.id: _scaled_weight(weights.get(p.id, 1)) for p in persons}
    amounts = {}
    for p in persons:
        raw = carry.get(p.id, 0)
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
            raise ValueError("Carry credit must be a nonnegative integer")
        amounts[p.id] = raw
    return values, amounts


def _apportion(total, keys, scores):
    """Stable largest remainder integer apportionment; total may be 0."""
    keys = sorted(keys)
    if total < 0:
        raise ValueError("Negative task count")
    positive = sum(max(0, scores.get(k, 0)) for k in keys)
    if not positive:
        return {k: 0 for k in keys}
    numerators = {k: total * max(0, scores.get(k, 0)) for k in keys}
    base = {k: numerators[k] // positive for k in keys}
    leftovers = total - sum(base.values())
    ranking = sorted(keys, key=lambda k: (-(numerators[k] % positive), k))
    for k in ranking[:leftovers]:
        base[k] += 1
    return base


def _meal_days(persons, tasks, events):
    valid_months = {(t.day.year, t.day.month) for t in tasks if t.pool == "officer"}
    ids = {p.id for p in persons if p.pool == "officer"}
    credits = defaultdict(set)
    for e in events:
        if e.type != "meal" or e.person not in ids:
            continue
        d = e.start
        while d <= e.end:
            if (d.year, d.month) in valid_months:
                credits[e.person].add(d)
            d += timedelta(days=1)
    return {p.id: len(credits[p.id]) for p in persons}


def _targets(persons, tasks, allowed, chosen, weights, carry, events):
    """Pool-specific reference targets using existing v7 base/credit/redistribute shape.

    Static availability is an *opportunity count*, not proof that a person
    can legally take that many actual shifts after rest constraints.
    """
    pool_people = defaultdict(list)
    for p in persons:
        pool_people[p.pool].append(p.id)
    task_by_key = {t.key: t for t in tasks}
    avail = defaultdict(int)
    for key, person_id in allowed:
        avail[person_id] += 1
    meal = _meal_days(persons, tasks, events)
    result = {}
    baseline = {}
    for pool, keys in pool_people.items():
        active_tasks = sum(1 for t in tasks if t.pool == pool and chosen[t.key] is not None)
        scores = {i: avail[i] * weights[i] for i in keys}
        base = _apportion(active_tasks, keys, scores)
        baseline.update(base)
        adjusted = {i: max(0, base[i] - meal[i] - carry[i]) for i in keys}
        left = active_tasks - sum(adjusted.values())
        while left > 0:
            eligible = [i for i in keys if scores[i] > 0 and adjusted[i] < avail[i]]
            if not eligible:
                break
            preferred = [i for i in eligible if meal[i] == 0 and carry[i] == 0]
            if preferred:
                eligible = preferred
            def rank(i):
                # Comparator surrogate for v7 target vs baseline / availability*weight.
                denominator = max(1, scores[i])
                return ((adjusted[i] - base[i]) / denominator, i)
            best = min(eligible, key=rank)
            adjusted[best] += 1
            left -= 1
        result.update(adjusted)
    return result, baseline, meal


def _extracted(tasks, variables, solver, persons, events, history, pins):
    result = {t.key: None for t in tasks}
    for (key, ident), variable in variables.items():
        if solver.value(variable):
            if result[key] is not None:
                raise AssertionError("Duplicate person assigned to shift")
            result[key] = ident
    independently_check(tasks, persons, result, events, history, pins)
    return result


def _score_deviations(assignments, people, targets):
    done = defaultdict(int)
    for who in assignments.values():
        if who is not None:
            done[who] += 1
    return sum(abs(done[p.id] - targets.get(p.id, 0)) for p in people)


def _hardship_categories(tasks):
    groups = defaultdict(list)
    for t in tasks:
        if t.start in (22, 0, 2, 4):
            groups[(t.pool, f"night{t.start}")].append(t)
        if t.start == 12:
            groups[(t.pool, "noon")].append(t)
    return groups


def solve_layered(tasks: list[Shift], persons: list[Person],
                  events: list[Event] | None = None,
                  history: list[History] | None = None,
                  pins: dict[str, str | None] | None = None,
                  weights: dict[str, float] | None = None,
                  carry: dict[str, int] | None = None,
                  seconds_per_stage: float = 5.0) -> dict:
    """Return 3 independently audited stages and scoped proof flags.

    No later stage is attempted unless every preceding priority is OPTIMAL.
    """
    events, history, pins = events or [], history or [], pins or {}
    if not isinstance(seconds_per_stage, (int, float)) or not math.isfinite(seconds_per_stage) or seconds_per_stage <= 0:
        raise ValueError("Time budget must be finite and positive")
    weight, carry_credit = _validate_adjustments(persons, weights or {}, carry or {})
    model, variables = prepare(tasks, persons, events, history, pins)
    stages = {"fill": "NOT_RUN", "quota": "NOT_RUN", "hardship": "NOT_RUN"}

    def run():
        s = cp_model.CpSolver()
        s.parameters.num_search_workers = 1
        s.parameters.max_time_in_seconds = seconds_per_stage
        status = s.solve(model)
        return s, s.status_name(status), status

    solver, name, status = run()
    stages["fill"] = name
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"stages": stages, "filled": None, "missing": None,
                "assignments": None, "quota_targets": None,
                "proved": {"fill": False, "quota": False, "hardship": False}}
    chosen = _extracted(tasks, variables, solver, persons, events, history, pins)
    best_filled = sum(p is not None for p in chosen.values())
    report = {"stages": stages, "filled": best_filled,
              "missing": len(tasks) - best_filled, "assignments": chosen,
              "quota_targets": None, "base_targets": None,
              "meal_credits": None, "quota_score": None,
              "hardship_score": None,
              "proved": {"fill": status == cp_model.OPTIMAL, "quota": False, "hardship": False}}

    if status != cp_model.OPTIMAL:
        return report  # do not claim fill maximal on a time-limited FEASIBLE result

    model.add(sum(variables.values()) == best_filled)
    targets, baselines, meal = _targets(
        persons, tasks, variables, chosen, weight, carry_credit, events)
    report["quota_targets"] = targets
    report["base_targets"] = baselines
    report["meal_credits"] = meal
    report["quota_score"] = _score_deviations(chosen, persons, targets)
    by_person = defaultdict(list)
    for (_, ident), v in variables.items():
        by_person[ident].append(v)
    deviations = []
    for p in persons:
        dev = model.new_int_var(0, len(tasks) + max(targets.get(p.id, 0), 0),
                                f"quota_dev_{p.id}")
        model.add_abs_equality(dev, sum(by_person[p.id]) - targets[p.id])
        deviations.append(dev)
    model.minimize(sum(deviations))
    fair_solver, fair_name, fair_status = run()
    stages["quota"] = fair_name
    if fair_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return report

    fair_choice = _extracted(tasks, variables, fair_solver, persons, events, history, pins)
    if sum(v is not None for v in fair_choice.values()) != best_filled:
        raise AssertionError("Fairness reduced the number of filled shifts")
    fair_score = _score_deviations(fair_choice, persons, targets)
    if fair_score <= report["quota_score"]:
        chosen = fair_choice
        report["assignments"] = chosen
        report["quota_score"] = fair_score
    if fair_status != cp_model.OPTIMAL:
        return report
    report["proved"]["quota"] = True

    model.add(sum(deviations) == int(round(fair_solver.objective_value)))
    hardness = []
    goals = {}
    for (pool, category), group in _hardship_categories(tasks).items():
        ids = [p.id for p in persons if p.pool == pool]
        current = sum(chosen[t.key] is not None for t in group)
        group_keys = {t.key for t in group}
        candidates = defaultdict(list)
        for (key, ident), variable in variables.items():
            if key in group_keys:
                candidates[ident].append(variable)
        scores = {i: len(candidates[i]) * weight[i] for i in ids}
        target = _apportion(current, ids, scores)
        goals[(pool, category)] = target
        for ident in ids:
            dev = model.new_int_var(0, len(group) + target[ident],
                                    f"hardship_{pool}_{category}_{ident}")
            model.add_abs_equality(dev, sum(candidates[ident]) - target[ident])
            hardness.append(dev)
    if not hardness:
        stages["hardship"] = "NOT_APPLICABLE"
        report["proved"]["hardship"] = True
        report["hardship_score"] = 0
        return report

    def hardship_deviation(result):
        categories = _hardship_categories(tasks)
        return sum(
            abs(sum(result[t.key] == ident for t in categories[key]) - target[ident])
            for key, target in goals.items() for ident in target
        )

    # Keep the already-proven quota incumbent if a later search times out or
    # produces a worse FEASIBLE hardship solution.
    incumbent_hardship = hardship_deviation(chosen)
    report["hardship_score"] = incumbent_hardship
    model.minimize(sum(hardness))
    hard_solver, hard_name, hard_status = run()
    stages["hardship"] = hard_name
    if hard_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        hard_choice = _extracted(tasks, variables, hard_solver, persons, events, history, pins)
        if sum(p is not None for p in hard_choice.values()) != best_filled:
            raise AssertionError("Hardship stage reduced legally filled shifts")
        if _score_deviations(hard_choice, persons, targets) != fair_score:
            raise AssertionError("Hardship stage changed proven quota score")
        found_score = hardship_deviation(hard_choice)
        if hard_status == cp_model.OPTIMAL and found_score > incumbent_hardship:
            raise AssertionError("Proven hardship optimum is worse than feasible incumbent")
        if found_score <= incumbent_hardship:
            report["assignments"] = hard_choice
            report["hardship_score"] = found_score
    report["proved"]["hardship"] = hard_status == cp_model.OPTIMAL
    return report
