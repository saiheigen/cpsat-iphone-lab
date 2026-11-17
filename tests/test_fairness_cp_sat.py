"""Synthetic regression tests for strict fill -> quota -> hardship hierarchy.

No personal or operational data. These tests require actual OR-Tools CP-SAT.
"""
from datetime import date
import unittest

from solver.roster_cp_sat import Event, Person, Shift, independently_check
from solver.fairness_cp_sat import solve_layered, _apportion


def d(day):
    return date(2026, 12, day)


class QuotaFairnessTests(unittest.TestCase):
    def test_stable_integer_quota_distribution(self):
        self.assertEqual(_apportion(7, ["H002", "H001"], {"H001": 1, "H002": 1}),
                         {"H001": 4, "H002": 3})
        self.assertEqual(_apportion(0, ["H002"], {"H002": 10}), {"H002": 0})

    def test_fill_priority_over_perfect_fairness(self):
        tasks = [Shift("door", d(1), x) for x in (2, 6, 10, 12)]
        people = [Person("H001", "door"), Person("H002", "door")]
        result = solve_layered(tasks, people, carry={"H001": 1}, seconds_per_stage=5)
        self.assertEqual(result["filled"], 4)
        self.assertEqual(result["missing"], 0)
        self.assertEqual(result["quota_targets"], {"H001": 1, "H002": 3})
        self.assertEqual(result["quota_score"], 0)
        self.assertTrue(result["proved"]["fill"])
        self.assertTrue(result["proved"]["quota"])
        self.assertTrue(independently_check(tasks, people, result["assignments"]))

    def test_business_weight_changes_base_reference(self):
        people = [Person("H001", "door"), Person("H002", "door")]
        tasks = [Shift("door", d(1), x) for x in (2, 6, 10)]
        result = solve_layered(tasks, people,
                               weights={"H001": 1, "H002": "0.333333"},
                               seconds_per_stage=5)
        self.assertEqual(result["filled"], 3)
        self.assertEqual(result["base_targets"], {"H001": 2, "H002": 1})
        self.assertEqual(result["quota_score"], 0)

    def test_meal_duty_is_credit_not_extra_scheduled_shift(self):
        people = [Person("P001", "officer"), Person("P002", "officer")]
        tasks = [Shift("officer", d(7), 5), Shift("officer", d(9), 6)]
        events = [Event("P001", "meal", d(5), d(5))]
        result = solve_layered(tasks, people, events=events,
                               seconds_per_stage=5)
        self.assertEqual(result["meal_credits"]["P001"], 1)
        self.assertEqual(result["quota_targets"], {"P001": 0, "P002": 2})
        self.assertEqual(result["filled"], 2)
        self.assertTrue(result["proved"]["quota"])

    def test_same_day_officer_cap_never_relaxed(self):
        people = [Person("P001", "officer")]
        tasks = [Shift("officer", d(3), 5), Shift("officer", d(3), 7)]
        result = solve_layered(tasks, people, seconds_per_stage=5)
        self.assertEqual(result["filled"], 1)
        self.assertEqual(result["missing"], 1)

    def test_synthetic_hardship_stage_present(self):
        people = [Person("H001", "door"), Person("H002", "door")]
        tasks = [Shift("door", d(1), 1), Shift("door", d(1), 8)]
        result = solve_layered(tasks, people, seconds_per_stage=5)
        self.assertEqual(result["filled"], 2)
        self.assertIn(result["stages"]["hardship"], ("OPTIMAL", "FEASIBLE"))
        self.assertIsNotNone(result["hardship_score"])

    def test_no_hardship_shifts_are_not_applicable(self):
        tasks = [Shift("door", d(1), 6)]
        people = [Person("H001", "door")]
        result = solve_layered(tasks, people, seconds_per_stage=5)
        self.assertEqual(result["stages"]["hardship"], "NOT_APPLICABLE")
        self.assertTrue(result["proved"]["hardship"])

    def test_illegal_pinned_cannot_be_optimized_away(self):
        tasks = [Shift("door", d(6), 6)]
        people = [Person("H001", "door")]
        events = [Event("H001", "leave", d(5), d(5))]
        with self.assertRaisesRegex(ValueError, "violates hard rule"):
            solve_layered(tasks, people, events=events,
                          pins={tasks[0].key: "H001"})

    def test_invalid_adjustments_fail_closed(self):
        people = [Person("H001", "door")]
        tasks = [Shift("door", d(1), 6)]
        for bad in (-1, 2, "NaN", "not-a-number"):
            with self.assertRaises(ValueError):
                solve_layered(tasks, people, weights={"H001": bad})
        with self.assertRaises(ValueError):
            solve_layered(tasks, people, carry={"H001": -1})
        with self.assertRaises(ValueError):
            solve_layered(tasks, people, carry={"UNKNOWN": 1})
        with self.assertRaises(ValueError):
            solve_layered(tasks, people, seconds_per_stage=0)

    def test_second_phase_is_skipped_if_first_infeasible(self):
        people = [Person("H001", "door")]
        tasks = [Shift("door", d(1), 6), Shift("door", d(2), 6)]
        result = solve_layered(tasks, people, pins={t.key: "H001" for t in tasks})
        self.assertEqual(result["stages"]["fill"], "INFEASIBLE")
        self.assertEqual(result["stages"]["quota"], "NOT_RUN")
        self.assertIsNone(result["assignments"])


if __name__ == "__main__":
    unittest.main()
