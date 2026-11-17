"""Regression tests for legal constructive CP-SAT warm starts, synthetic only."""
from datetime import date
import unittest

from solver.roster_cp_sat import (
    Event, History, Person, Shift, independently_check, month_shifts,
)
from solver.constructive_witness import construct_legal_seed


def d(n, month=12):
    return date(2026, month, n)


class ConstructiveSeedTests(unittest.TestCase):
    def test_monthly_no_absences_seed_audited(self):
        persons = ([Person(f"H{i:03}", "door") for i in range(1, 57)] +
                   [Person(f"P{i:03}", "officer") for i in range(1, 51)])
        tasks = month_shifts(2026, 12)
        result = construct_legal_seed(tasks, persons, attempts=4)
        self.assertEqual(len(result["assignments"]), 589)
        self.assertTrue(result["independent_hard_rule_audit_passed"])
        self.assertTrue(independently_check(tasks, persons, result["assignments"]))
        self.assertFalse(result["operationally_certified"])
        self.assertGreater(result["filled"], 0)

    def test_absence_and_cross_month_history_preserved(self):
        persons = [Person("H001", "door"), Person("H002", "door")]
        tasks = [Shift("door", d(n), 6) for n in (1, 2, 3, 4)]
        ev = [Event("H001", "nightcheck", d(2), d(2))]
        hist = [History("H002", Shift("door", d(30, 11), 3))]
        result = construct_legal_seed(tasks, persons, ev, hist)
        self.assertIsNone(result["assignments"][tasks[0].key])
        self.assertTrue(independently_check(
            tasks, persons, result["assignments"], ev, hist))

    def test_pinned_future_first_not_reassigned(self):
        persons = [Person("H001", "door"), Person("H002", "door")]
        tasks = [Shift("door", d(1), 6), Shift("door", d(2), 6),
                 Shift("door", d(3), 6)]
        pins = {tasks[2].key: "H001", tasks[0].key: None}
        result = construct_legal_seed(tasks, persons, pins=pins)
        self.assertIsNone(result["assignments"][tasks[0].key])
        self.assertEqual(result["assignments"][tasks[2].key], "H001")
        self.assertTrue(independently_check(
            tasks, persons, result["assignments"], pins=pins))

    def test_no_false_proof_when_staff_insufficient(self):
        persons = [Person("H001", "door")]
        tasks = [Shift("door", d(1), 6), Shift("door", d(2), 6)]
        result = construct_legal_seed(tasks, persons)
        self.assertEqual(result["filled"], 1)
        self.assertEqual(result["missing"], 1)
        self.assertFalse(result["full_upper_bound_reached"])
        self.assertIsNone(result["optimality_proof"])

    def test_empty_people_does_not_divide_by_zero(self):
        tasks = [Shift("door", d(1), 6)]
        result = construct_legal_seed(tasks, [])
        self.assertEqual((result["filled"], result["missing"]), (0, 1))
        self.assertEqual(result["assignments"], {tasks[0].key: None})

    def test_invalid_pin_and_bad_attempts_rejected(self):
        people = [Person("H001", "door")]
        tasks = [Shift("door", d(1), 6)]
        with self.assertRaisesRegex(ValueError, "Unknown pinned person"):
            construct_legal_seed(tasks, people, pins={tasks[0].key: "H002"})
        with self.assertRaisesRegex(ValueError, "attempts"):
            construct_legal_seed(tasks, people, attempts=0)


if __name__ == "__main__":
    unittest.main()
