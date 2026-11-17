"""Synthetic tests for split full feasibility -> legal partial fill fallback.

All examples use invented IDs, limited dates, and the *partial* rules model.
"""
from datetime import date
import unittest

from solver.roster_cp_sat import (
    Event, History, Person, Shift, independently_check, solve,
)
from solver.split_fill_cp_sat import solve_split_fill_first


def d(day, month=12):
    return date(2026, month, day)


class SplitSolverTests(unittest.TestCase):
    def test_both_pools_full_is_proven_even_without_quota_model(self):
        staff = [Person("H001", "door"), Person("P001", "officer")]
        tasks = [Shift("door", d(1), 6), Shift("officer", d(1), 5)]
        result = solve_split_fill_first(tasks, staff, seconds_full=4,
                                        seconds_fallback=4)
        self.assertEqual(result["status"], "FULL")
        self.assertEqual((result["filled"], result["missing"]), (2, 0))
        self.assertTrue(result["optimal_fill_proven"])
        for pool in ("door", "officer"):
            self.assertEqual(result["pools"][pool]["fallback"], "NOT_RUN")
        self.assertTrue(independently_check(tasks, staff, result["assignments"]))

    def test_infeasible_full_goes_to_legal_max_fill_and_keeps_empty(self):
        staff = [Person("H001", "door"), Person("P001", "officer")]
        tasks = [Shift("door", d(1), 6), Shift("door", d(2), 6),
                 Shift("officer", d(2), 6)]
        results = solve_split_fill_first(tasks, staff, seconds_full=5,
                                         seconds_fallback=5)
        self.assertEqual(results["status"], "PARTIAL_OPTIMAL")
        self.assertEqual((results["filled"], results["missing"]), (2, 1))
        self.assertEqual(results["pools"]["door"]["full_feasibility"], "INFEASIBLE")
        self.assertEqual(results["pools"]["door"]["fallback"], "OPTIMAL")
        self.assertEqual(results["pools"]["officer"]["fallback"], "NOT_RUN")
        self.assertTrue(independently_check(tasks, staff, results["assignments"]))

    def test_absence_creates_legal_gap_not_fake_staff(self):
        staff = [Person("H001", "door"), Person("P001", "officer")]
        tasks = [Shift("door", d(5), 6), Shift("officer", d(5), 6)]
        events = [Event("H001", "nightcheck", d(5), d(5))]
        result = solve_split_fill_first(tasks, staff, events=events,
                                        seconds_full=4, seconds_fallback=4)
        self.assertEqual(result["status"], "PARTIAL_OPTIMAL")
        self.assertEqual(result["assignments"][tasks[0].key], None)
        self.assertEqual(result["assignments"][tasks[1].key], "P001")
        self.assertTrue(result["optimal_fill_proven"])

    def test_forced_empty_pin_is_preserved_in_fallback(self):
        staff = [Person("H001", "door"), Person("H002", "door")]
        tasks = [Shift("door", d(1), 6), Shift("door", d(1), 10)]
        pins = {tasks[0].key: None}
        result = solve_split_fill_first(tasks, staff, pins=pins,
                                        seconds_full=4, seconds_fallback=4)
        self.assertEqual(result["status"], "PARTIAL_OPTIMAL")
        self.assertEqual(result["assignments"][tasks[0].key], None)
        self.assertEqual(result["filled"], 1)

    def test_illegal_forced_pin_rejected_not_relaxed(self):
        staff = [Person("H001", "door")]
        task = Shift("door", d(7), 6)
        events = [Event("H001", "leave", d(6), d(6))]
        with self.assertRaisesRegex(ValueError, "Pinned person violates hard rule"):
            solve_split_fill_first([task], staff, events=events,
                                   pins={task.key: "H001"})

    def test_previous_month_history_block_is_preserved(self):
        staff = [Person("H001", "door"), Person("P001", "officer")]
        tasks = [Shift("door", d(1), 6), Shift("officer", d(1), 5)]
        history = [History("H001", Shift("door", d(30, 11), 3))]
        out = solve_split_fill_first(tasks, staff, history=history,
                                     seconds_full=4, seconds_fallback=4)
        self.assertEqual((out["filled"], out["missing"]), (1, 1))
        self.assertEqual(out["assignments"][tasks[0].key], None)
        self.assertEqual(out["assignments"][tasks[1].key], "P001")

    def test_mismatched_event_or_history_rejected(self):
        staff = [Person("H001", "door"), Person("P001", "officer")]
        tasks = [Shift("door", d(1), 6)]
        with self.assertRaisesRegex(ValueError, "Unknown event"):
            solve_split_fill_first(tasks, staff,
                                   events=[Event("MISSING", "leave", d(1), d(1))])
        with self.assertRaisesRegex(ValueError, "Officer-specific"):
            solve_split_fill_first(tasks, staff,
                                   events=[Event("H001", "meal", d(1), d(1))])
        with self.assertRaisesRegex(ValueError, "wrong-pool"):
            solve_split_fill_first(tasks, staff,
                                   history=[History("H001", Shift("officer", d(30, 11), 5))])

    def test_partial_pool_not_caught_by_overall_full_status(self):
        staff = [Person("H001", "door"), Person("P001", "officer")]
        tasks = [Shift("door", d(3), 6),
                 Shift("officer", d(3), 5),
                 Shift("officer", d(3), 6)]
        result = solve_split_fill_first(tasks, staff, seconds_full=4,
                                        seconds_fallback=4)
        self.assertEqual(result["status"], "PARTIAL_OPTIMAL")
        self.assertEqual((result["filled"], result["missing"]), (2, 1))
        self.assertEqual(result["pools"]["door"]["status"], "FULL")

    def test_empty_input_has_no_fake_assignments(self):
        out = solve_split_fill_first([], [], seconds_full=4,
                                     seconds_fallback=4)
        self.assertEqual(out["status"], "FULL")
        self.assertEqual(out["filled"], 0)
        self.assertEqual(out["assignments"], {})
        self.assertFalse(out["operationally_certified"])

    def test_invalid_time_budget_rejected(self):
        for bad in (0, -1, float("nan"), float("inf"), True):
            with self.assertRaises(ValueError):
                solve_split_fill_first([], [], seconds_full=bad)

    def test_consistent_with_original_cp_sat_optimum_on_small_cases(self):
        staff = [Person("H001", "door"), Person("H002", "door"),
                 Person("P001", "officer")]
        tasks = [Shift("door", d(1), 6),
                 Shift("door", d(2), 6),
                 Shift("door", d(3), 6),
                 Shift("officer", d(1), 5),
                 Shift("officer", d(2), 5)]
        before = solve(tasks, staff, seconds=5)
        after = solve_split_fill_first(tasks, staff,
                                       seconds_full=5, seconds_fallback=5)
        self.assertEqual(before["status"], "OPTIMAL")
        self.assertEqual(after["filled"], before["filled"])
        self.assertTrue(after["optimal_fill_proven"])
        self.assertTrue(independently_check(tasks, staff, after["assignments"]))


if __name__ == "__main__":
    unittest.main()
