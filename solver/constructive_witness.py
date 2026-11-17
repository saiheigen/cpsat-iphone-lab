"""Deterministic, legally checked construction for *synthetic* CP-SAT warm starts.

An incomplete greedy result is only a feasible incumbent, never an optimality
proof. A full, independently audited result does prove maximal *fill count*
under the CURRENT PARTIAL model, because one person per shift is an upper bound.
It does NOT prove fairness or complete real-world scheduling rules.
"""
from collections import defaultdict
from datetime import date
from solver.roster_cp_sat import conflicts, static_reason, independently_check


def construct_legal_seed(tasks, people, events=None, history=None, pins=None,
                         attempts=12):
    events, history, pins = events or [], history or [], pins or {}
    if not isinstance(attempts, int) or isinstance(attempts, bool) or not 1 <= attempts <= 64:
        raise ValueError("attempts must be an integer between 1 and 64")
    ids = {p.id: p for p in people}
    if len(ids) != len(people) or any(not p.id for p in people):
        raise ValueError("Duplicate or empty personnel IDs")
    keys = {t.key for t in tasks}
    if len(keys) != len(tasks):
        raise ValueError("Duplicate task IDs")
    if any(k not in keys for k in pins):
        raise ValueError("Unknown pinned shift")
    if any(v is not None and v not in ids for v in pins.values()):
        raise ValueError("Unknown pinned person")
    if any(e.person not in ids for e in events):
        raise ValueError("Unknown event person")
    if any(h.person not in ids or h.shift.pool != ids[h.person].pool for h in history):
        raise ValueError("Unknown or wrong-pool historical personnel")

    prior = defaultdict(list)
    for h in history:
        prior[h.person].append(h.shift)
    pinned = defaultdict(list)
    for t in tasks:
        who = pins.get(t.key)
        if who is None:
            continue
        p = ids[who]
        if static_reason(p, t, events):
            raise ValueError(f"Pinned person is unavailable: {t.key}, {who}")
        if any(conflicts(t, past) for past in prior[who] + pinned[who]):
            raise ValueError(f"Pinned person conflicts with past or another pin: {t.key}")
        pinned[who].append(t)
    # Preserve pinned dates and counts for all attempts, including shifts
    # later in the month, before filling any other slots.
    best, best_filled = None, -1
    eligible = {}
    for t in tasks:
        eligible[t.key] = [p for p in people if p.pool == t.pool
                           and static_reason(p, t, events) is None]
    # Place restrictive slots earlier *within each calendar day*. Never
    # reorder calendar days: stand/rest conflicts are future dependencies.
    ordered = sorted(tasks, key=lambda t:
                     (t.day, len(eligible[t.key]), t.pool, t.start))
    id_order = {p.id: i for i, p in enumerate(sorted(people, key=lambda p: p.id))}
    for attempt in range(attempts):
        shifts = defaultdict(list)
        for who, items in prior.items():
            shifts[who].extend(items)
        for who, items in pinned.items():
            shifts[who].extend(items)
        assigned_count = defaultdict(int)
        today_count = defaultdict(int)
        for who, items in pinned.items():
            assigned_count[who] += len(items)
        choice = {t.key: pins.get(t.key) for t in tasks}
        for task in ordered:
            if task.key in pins:
                continue
            eligible_people = []
            for p in eligible[task.key]:
                current = shifts[p.id]
                if any(conflicts(task, old) for old in current):
                    continue
                daily = sum(old.day == task.day for old in current)
                if daily >= (3 if p.pool == "door" else 1):
                    continue
                # No raw equality constraints are skipped; conflicts handles
                # Sunday standby, same-number repeats and 6-hour rests.
                score = (daily, assigned_count[p.id],
                         (id_order[p.id] + 13 * attempt + task.day.day) % len(people))
                eligible_people.append((score, p.id))
            if eligible_people:
                _, who = min(eligible_people)
                choice[task.key] = who
                shifts[who].append(task)
                assigned_count[who] += 1
        independently_check(tasks, people, choice, events, history, pins)
        filled = sum(who is not None for who in choice.values())
        if filled > best_filled:
            best, best_filled = choice, filled
        if filled == len(tasks):
            break
    return {
        "assignments": best,
        "filled": best_filled,
        "missing": len(tasks) - best_filled,
        "full_upper_bound_reached": best_filled == len(tasks),
        "independent_hard_rule_audit_passed": True,
        "optimality_proof": "full_task_upper_bound" if best_filled == len(tasks) else None,
        "operationally_certified": False,
    }
