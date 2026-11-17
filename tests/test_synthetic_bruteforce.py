"""Differential synthetic audit: exact brute-force fill oracle vs genuine CP-SAT.

Run with AUDIT_SEED=0..5 in six separate CI jobs. No real rosters. Brute-force
enumeration is separate from CP-SAT encoding, but shares the declared hard
rule functions (static_reason and conflicts) with the independent auditor:
NOT independent verification of *all* real-world regulations.
"""
from datetime import date, timedelta
from itertools import product
import os
import random
import unittest

from solver.roster_cp_sat import (
    Event, History, Person, Shift, independently_check, month_shifts, solve,
    static_reason,
)
from solver.split_fill_cp_sat import solve_split_fill_first


class DifferentialFillTests(unittest.TestCase):
    def test_30_randomized_synthetic_cases_against_exact_enumeration(self):
        group = int(os.environ.get("AUDIT_SEED", "0"))
        rng = random.Random(20261118 + group * 1000003)
        possible_days = [date(2026, 12, d) for d in range(1, 7)]
        people = [Person("H001", "door"), Person("H002", "door"),
                  Person("P001", "officer"), Person("P002", "officer")]
        tested = 0
        for case in range(30):
            # Mix 2-hour guards and 2/4/6-hour officer shifts.
            all_tasks = [
                Shift(pool, day, number)
                for pool, n in (("door", 12), ("officer", 7))
                for day in possible_days for number in range(1, n + 1)
            ]
            rng.shuffle(all_tasks)
            tasks = sorted(all_tasks[:6], key=lambda t: t.key)
            events = []
            if rng.randrange(3):
                who = rng.choice(people)
                event_type = rng.choice([
                    "leave", "nightcheck", "driver", "training",
                    "exempt_night", "exempt_noon", "exempt_all",
                ])
                start = rng.choice(possible_days)
                events = [Event(who.id, event_type, start, start)]
            history = []
            if rng.randrange(3) == 0:
                who = rng.choice(people)
                past_num = rng.randint(1, 12 if who.pool == "door" else 7)
                history = [History(who.id, Shift(who.pool, date(2026, 11, 30), past_num))]
            pins = {}
            if rng.randrange(3) == 0:
                forced_empty = rng.choice(tasks)
                pins[forced_empty.key] = None

            allowed = []
            for task in tasks:
                choices = [None] + [
                    p.id for p in people
                    if p.pool == task.pool and static_reason(p, task, events) is None
                ]
                if task.key in pins:
                    choices = [pins[task.key]]
                allowed.append(choices)
            exact_max = -1
            for options in product(*allowed):
                proposal = {t.key: who for t, who in zip(tasks, options)}
                try:
                    independently_check(tasks, people, proposal,
                                        events=events, history=history, pins=pins)
                except ValueError:
                    continue
                exact_max = max(exact_max, sum(v is not None for v in proposal.values()))
            if exact_max < 0:
                self.fail(f"Oracle produced no legal blank solution (group {group}, case {case})")

            cp = solve(tasks, people, events, history, pins, seconds=3)
            self.assertEqual(cp["status"], "OPTIMAL",
                             f"group {group}, case {case}, tasks {len(tasks)}")
            self.assertTrue(cp["proven_optimal_for_subset_model"])
            self.assertEqual(cp["filled"], exact_max,
                             f"group {group}, case {case}")
            self.assertTrue(independently_check(tasks, people, cp["assignments"],
                                               events, history, pins))
            # Exact search oracle must also agree with the new split-pool
            # full-first strategy, including forced blanks and absences.
            split = solve_split_fill_first(
                tasks, people, events, history, pins,
                seconds_full=2, seconds_fallback=3)
            self.assertEqual(split["filled"], exact_max,
                             f"split group {group}, case {case}")
            self.assertTrue(split["optimal_fill_proven"])
            self.assertTrue(independently_check(
                tasks, people, split["assignments"],
                events, history, pins))
            tested += 1
        print(f"PASS: exact reference vs real CP-SAT, seed_group={group}, cases={tested}")

    def test_calendar_shapes_leap_year_and_year_boundary(self):
        self.assertEqual(len(month_shifts(2028, 2)), 29 * 19)
        self.assertEqual(len(month_shifts(2027, 2)), 28 * 19)
        self.assertEqual(len(month_shifts(2026, 12)), 31 * 19)


if __name__ == "__main__":
    unittest.main()
