"""Experimental standalone native CP-SAT roster model; SYNTHETIC inputs only.

This is a *subset* of the v7.0 scheduling rules, intentionally not integrated
with the mobile website. It must not be used for operational duty schedules.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from itertools import combinations
import calendar

from ortools.sat.python import cp_model

SLOTS = {
    "door": [(22, 24), (0, 2), (2, 4), (4, 6), (6, 8), (8, 10),
             (10, 12), (12, 14), (14, 16), (16, 18), (18, 20), (20, 22)],
    "officer": [(22, 24), (0, 2), (2, 4), (4, 6), (6, 12), (12, 18), (18, 22)],
}
EVENT_TYPES = {
    "leave", "training", "officer_duty", "meal", "nightcheck", "driver",
    "exempt_all", "exempt_night", "exempt_noon",
}
DAY = timedelta(days=1)


@dataclass(frozen=True)
class Person:
    id: str
    pool: str
    kitchen: bool = False


@dataclass(frozen=True)
class Shift:
    pool: str
    day: date
    num: int

    def __post_init__(self):
        if self.pool not in SLOTS or not (1 <= self.num <= len(SLOTS[self.pool])):
            raise ValueError("Unknown pool or shift number")

    @property
    def start(self) -> int:
        return SLOTS[self.pool][self.num - 1][0]

    @property
    def end(self) -> int:
        return SLOTS[self.pool][self.num - 1][1]

    @property
    def hours(self) -> int:
        return self.end - self.start

    @property
    def key(self) -> str:
        return f"{self.pool}:{self.day.isoformat()}:{self.num}"

    @property
    def night(self) -> bool:
        return self.start < 6 or self.start >= 22

    @property
    def noon(self) -> bool:
        return self.start == 12

    @property
    def sunday_standby(self) -> bool:
        return self.day.weekday() == 6 and (
            (self.pool == "door" and 6 <= self.start < 20) or
            (self.pool == "officer" and self.num == 7)
        )


@dataclass(frozen=True)
class Event:
    person: str
    type: str
    start: date
    end: date

    def __post_init__(self):
        if self.type not in EVENT_TYPES or self.start > self.end:
            raise ValueError("Invalid event type or reversed date range")


@dataclass(frozen=True)
class History:
    person: str
    shift: Shift


def month_shifts(year: int, month: int) -> list[Shift]:
    last_day = calendar.monthrange(year, month)[1]
    return [Shift(pool, date(year, month, d), n)
            for pool in ("door", "officer")
            for d in range(1, last_day + 1)
            for n in range(1, len(SLOTS[pool]) + 1)]


def static_reason(person: Person, shift: Shift, events: list[Event]) -> str | None:
    if person.pool != shift.pool:
        return "wrong-pool"
    if person.kitchen:
        return "kitchen"
    d = shift.day
    for e in events:
        if e.person != person.id:
            continue
        if e.type == "leave":
            if e.start <= d <= e.end + DAY:
                return "leave-or-return"
            if d == e.start - DAY and shift.night:
                return "night-before-leave"
        elif e.type == "training":
            if e.start - DAY <= d <= e.end:
                return "training"
        elif e.type == "officer_duty":
            if e.start - DAY <= d <= e.end + DAY:
                return "officer-duty"
        elif e.type == "meal":
            if e.start - DAY <= d <= e.end + DAY:
                return "meal-and-rest"
        elif e.type == "nightcheck":
            if e.start - DAY <= d <= e.end + DAY:
                return "nightcheck"
        elif e.type == "driver":
            if e.start <= d <= e.end + DAY:
                return "driving-or-rest"
            if d == e.start - DAY and shift.night:
                return "night-before-driving"
        elif e.type == "exempt_all":
            if e.start <= d <= e.end:
                return "full-exemption"
        elif e.type == "exempt_night":
            if e.start <= d <= e.end and shift.night:
                return "night-exemption"
        elif e.type == "exempt_noon":
            if e.start <= d <= e.end and shift.noon:
                return "noon-exemption"
    return None


def conflicts(a: Shift, b: Shift) -> bool:
    if a.pool != b.pool:
        return False
    days = abs((a.day - b.day).days)
    if days == 1:  # stand one day, next day rest
        return True
    if days <= 2 and a.num == b.num:  # same slot separated by >2 days
        return True
    if days == 7 and a.sunday_standby and b.sunday_standby:
        return True
    if days != 0:
        return False
    if a.pool == "officer":  # one officer shift per day
        return True
    earlier, later = sorted([a, b], key=lambda shift: shift.start)
    return later.start - earlier.end < 6  # full 6h rest between 2h shifts


def prepare(tasks: list[Shift], persons: list[Person],
            events: list[Event] | None = None,
            history: list[History] | None = None,
            pins: dict[str, str | None] | None = None):
    """Build fill-first model. Never silently relax unavailable or pinned duty."""
    events = events or []
    history = history or []
    pins = pins or {}
    ids = [p.id for p in persons]
    if len(set(ids)) != len(ids) or any(not i for i in ids):
        raise ValueError("Person IDs must be distinct and nonempty")
    if any(p.pool not in SLOTS for p in persons):
        raise ValueError("Unknown person's duty pool")
    if len({t.key for t in tasks}) != len(tasks):
        raise ValueError("Duplicate shift key")
    by_id = {p.id: p for p in persons}
    by_shift = {t.key: t for t in tasks}
    for e in events:
        if e.person not in by_id:
            raise ValueError(f"Unknown event person: {e.person}")
        if e.type in ("officer_duty", "meal") and by_id[e.person].pool != "officer":
            raise ValueError("Officer-specific event assigned to non-officer")
    for h in history:
        if h.person not in by_id or h.shift.pool != by_id[h.person].pool:
            raise ValueError("Unknown / mismatched history")
        if h.shift.key in by_shift:
            raise ValueError("History overlaps the target roster")
    hist_by_person = defaultdict(list)
    for h in history:
        hist_by_person[h.person].append(h.shift)
    for ident, entries in hist_by_person.items():
        for a, b in combinations(entries, 2):
            if conflicts(a, b):
                raise ValueError(f"Conflicting prior history: {ident}")
    for k, person_id in pins.items():
        if k not in by_shift:
            raise ValueError(f"Pin references unknown task: {k}")
        if person_id is not None and person_id not in by_id:
            raise ValueError(f"Pin references unknown person: {person_id}")

    model = cp_model.CpModel()
    assignments = {}
    by_task = defaultdict(list)
    by_person = defaultdict(list)
    for t in tasks:
        for p in persons:
            if p.pool != t.pool or static_reason(p, t, events):
                continue
            if any(conflicts(t, past) for past in hist_by_person[p.id]):
                continue
            v = model.new_bool_var(f"x_{p.id}_{t.key}")
            assignments[(t.key, p.id)] = v
            by_task[t.key].append(v)
            by_person[p.id].append((t, v))
        model.add(sum(by_task[t.key]) <= 1)
        if t.key in pins:
            who = pins[t.key]
            if who is None:
                model.add(sum(by_task[t.key]) == 0)
            elif (t.key, who) not in assignments:
                raise ValueError(f"Pinned person violates hard rule: {t.key} / {who}")
            else:
                model.add(assignments[(t.key, who)] == 1)

    for person_id, xs in by_person.items():
        by_day = defaultdict(list)
        for t, v in xs:
            by_day[t.day].append((t, v))
        # Stated rest rule: nobody works on two consecutive calendar days.
        active = {}
        for d, entries in by_day.items():
            limit = 3 if by_id[person_id].pool == "door" else 1
            model.add(sum(v for _, v in entries) <= limit)
            active[d] = model.new_bool_var(f"on_{person_id}_{d.isoformat()}")
            model.add(sum(v for _, v in entries) >= active[d])
            model.add(sum(v for _, v in entries) <= limit * active[d])
        for d, v in active.items():
            if d + DAY in active:
                model.add(v + active[d + DAY] <= 1)
        # Scale as O(days * slots^2), not O(month_shifts^2) per person.
        # Next-day rest was already enforced through the daily active booleans.
        by_day_num = {(t.day, t.num): v for t, v in xs}
        for d, entries in by_day.items():
            if by_id[person_id].pool == "door":
                for (a, va), (b, vb) in combinations(entries, 2):
                    if conflicts(a, b):
                        model.add(va + vb <= 1)
            # Same shift number may not recur on day +1 or day +2.
            for t, v in entries:
                for offset in (1, 2):
                    other = by_day_num.get((d + offset * DAY, t.num))
                    if other is not None:
                        model.add(v + other <= 1)
            # Consecutive Sundays' standby; the exact eligible time windows
            # are defined by Shift.sunday_standby (based on existing v7 slots).
            standby = [v for t, v in entries if t.sunday_standby]
            next_sunday = [v for t, v in by_day.get(d + 7 * DAY, [])
                           if t.sunday_standby]
            if standby and next_sunday:
                model.add(sum(standby + next_sunday) <= 1)

    model.maximize(sum(assignments.values()))
    return model, assignments


def independently_check(tasks: list[Shift], persons: list[Person],
                        chosen: dict[str, str | None],
                        events: list[Event] | None = None,
                        history: list[History] | None = None,
                        pins: dict[str, str | None] | None = None):
    """Pure-Python audit, intentionally does not read CP-SAT's constraints."""
    if set(chosen) != {t.key for t in tasks}:
        raise ValueError("Missing/extra tasks in result")
    by_id = {p.id: p for p in persons}
    task_by_key = {t.key: t for t in tasks}
    chosen_by_person = defaultdict(list)
    for k, who in chosen.items():
        if who is None:
            continue
        t = task_by_key[k]
        if who not in by_id or static_reason(by_id[who], t, events or []):
            raise ValueError(f"Illegal assignment: {k}={who}")
        chosen_by_person[who].append(t)
    for h in history or []:
        chosen_by_person[h.person].append(h.shift)
    for ident, values in chosen_by_person.items():
        for a, b in combinations(values, 2):
            if conflicts(a, b):
                raise ValueError(f"Duty conflict for {ident}: {a.key} vs {b.key}")
        per_day = defaultdict(int)
        for t in values:
            per_day[t.day] += 1
        max_per_day = 3 if by_id[ident].pool == "door" else 1
        if any(n > max_per_day for n in per_day.values()):
            raise ValueError(f"Daily cap exceeded: {ident}")
    for key, value in (pins or {}).items():
        if chosen.get(key) != value:
            raise ValueError("Pin not preserved")
    return True


def solve(tasks: list[Shift], persons: list[Person],
          events: list[Event] | None = None,
          history: list[History] | None = None,
          pins: dict[str, str | None] | None = None,
          seconds: float = 5.0) -> dict:
    model, x = prepare(tasks, persons, events, history, pins)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = seconds
    status = solver.solve(model)
    name = solver.status_name(status)
    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        return {"status": name, "filled": None, "missing": None,
                "proven_optimal_for_subset_model": False, "assignments": None}
    chosen = {t.key: None for t in tasks}
    for (key, person_id), variable in x.items():
        if solver.value(variable) == 1:
            if chosen[key] is not None:
                raise AssertionError("Multiple people assigned to one shift")
            chosen[key] = person_id
    independently_check(tasks, persons, chosen, events, history, pins)
    filled = sum(v is not None for v in chosen.values())
    return {
        "status": name, "filled": filled, "missing": len(tasks) - filled,
        "proven_optimal_for_subset_model": status == cp_model.OPTIMAL,
        "assignments": chosen,
    }
