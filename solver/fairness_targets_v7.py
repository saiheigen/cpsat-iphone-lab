"""Source-aligned v7.0 soft fairness targets and integer carry-over.

This independently implements and tests the arithmetic behaviors of
v7.0 JS calcGoals, calcActualTargets, and archive compensationOut.
It does NOT change CP-SAT search, override hard restrictions, or approve
operational duty rosters. v7 targets are guidance, NOT legal eligibility.
"""
from __future__ import annotations
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class FairPerson:
    ident: str
    weight: float = 1.0
    carry: int = 0
    meal_credit: int = 0


def _number(value, label):
    if not isinstance(value, (float, int)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    return float(value)


def _validate(people, availability, count):
    if type(count) is not int or count < 0:
        raise ValueError("Shift count must be nonnegative integer")
    if len({p.ident for p in people}) != len(people) or any(
        not p.ident for p in people
    ):
        raise ValueError("Duplicate or empty staff IDs")
    if set(availability) != {p.ident for p in people}:
        raise ValueError("Availability must include exactly all people")
    for p in people:
        weight = _number(p.weight, "weight")
        if weight < 0:
            raise ValueError("Negative personnel weight unsupported")
        for name, value in (("carry", p.carry), ("meal credit", p.meal_credit)):
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be nonnegative integer")
        cap = availability[p.ident]
        if type(cap) is not int or cap < 0:
            raise ValueError("Static availability must be nonnegative integer")


def base_goals_v7(people: list[FairPerson], availability: dict[str, int],
                  shift_count: int) -> dict[str, int]:
    """v7 calcGoals: largest remainder, stable input-order tie break.

    Static candidate-slot counts times weight do not establish actual
    achievable monthly duty capacity once rest conflicts are considered.
    """
    _validate(people, availability, shift_count)
    weights = [availability[p.ident] * p.weight for p in people]
    total = sum(weights)
    if total <= 0:
        return {p.ident: 0 for p in people}
    exact = [shift_count * w / total for w in weights]
    base = [math.floor(x) for x in exact]
    left = shift_count - sum(base)
    ranking = sorted(range(len(people)),
                     key=lambda i: (-(exact[i] - base[i]), i))
    for i in ranking[:left]:
        base[i] += 1
    return {p.ident: value for p, value in zip(people, base)}


def actual_targets_v7(
    people: list[FairPerson], availability: dict[str, int],
    shift_count: int, goals: dict[str, int],
) -> dict[str, int]:
    """v7 calcActualTargets: discount carry+meal, then redistribute.

    If all available people hit their static capacity, remaining slots
    stay unallocated as targets instead of fabricating eligible staff.
    """
    _validate(people, availability, shift_count)
    if set(goals) != {p.ident for p in people} or any(
        type(v) is not int or v < 0 for v in goals.values()
    ):
        raise ValueError("Base goals must include nonnegative integer values")
    credits = [p.carry + p.meal_credit for p in people]
    base = [goals[p.ident] for p in people]
    target = [max(0, b - credits[i]) for i, b in enumerate(base)]
    capacity = [availability[p.ident] for p in people]
    eligible = [i for i, cap in enumerate(capacity) if cap > 0]
    free = shift_count - sum(target)
    if free < 0:
        raise ValueError("Unreasonable target sum")
    while free > 0:
        choices = [i for i in eligible
                   if target[i] < capacity[i] and credits[i] == 0]
        if not choices:
            choices = [i for i in eligible if target[i] < capacity[i]]
        if not choices:
            break
        choices.sort(key=lambda i: (
            (target[i] - base[i]) /
            max(.01, capacity[i] * people[i].weight), i))
        target[choices[0]] += 1
        free -= 1
    return {p.ident: v for p, v in zip(people, target)}


def archive_compensation_out_v7(
    people: list[FairPerson], goals: dict[str, int],
    worked: dict[str, int],
) -> dict[str, int]:
    """v7 locked snapshot: max(0,trunc(worked+meal+carry-base))."""
    ids = {p.ident for p in people}
    if len(ids) != len(people) or ids != set(goals) or ids != set(worked):
        raise ValueError("Missing or duplicate compensation staff IDs")
    output = {}
    for p in people:
        n, g = worked[p.ident], goals[p.ident]
        if type(n) is not int or n < 0 or type(g) is not int or g < 0:
            raise ValueError("Worked and base goal counts must be nonnegative integers")
        excess = max(0, math.trunc(n + p.meal_credit + p.carry - g))
        if excess > 0:
            output[p.ident] = excess
    return output


def import_prior_locked_carry_v7(
    people: list[FairPerson], prior_output: dict[str, int],
    *, prior_locked: bool, prior_stale: bool,
    manual_override: dict[str, int] | None = None,
) -> dict[str, int]:
    """Manual input prevails; previous auto carry requires fresh locked month.

    The caller must supply validated prior archive state; we do not
    infer it or accept untrusted operational data for this module.
    """
    ids = {p.ident for p in people}
    if len(ids) != len(people):
        raise ValueError("Duplicate staff IDs")
    manual_override = manual_override or {}
    if any(k not in ids for k in (*manual_override, *prior_output)):
        raise ValueError("Carry references unknown staff")
    for value in (*manual_override.values(), *prior_output.values()):
        if type(value) is not int or value < 0:
            raise ValueError("Carry must be a nonnegative integer")
    return {
        p.ident: (manual_override[p.ident] if p.ident in manual_override
                  else prior_output.get(p.ident, 0)
                  if prior_locked and not prior_stale else 0)
        for p in people
    }
