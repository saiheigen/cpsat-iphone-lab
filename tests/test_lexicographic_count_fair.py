"""Synthetic lexicographic CP-SAT regression tests, no real workforce."""
from datetime import date
import unittest

from solver.roster_cp_sat import Event, Person, Shift, independently_check
from solver.fairness_targets_v7 import FairPerson, base_goals_v7
from solver.lexicographic_count_fair import solve_lexicographic_count_fair


def door(day, slot):
    return Shift("door", date(2026, 12, day), slot)


class LexicographicCountFairTests(unittest.TestCase):
    def test_fill_before_fairness_and_balance_two_shift_day(self):
        tasks = [door(1, 5), door(1, 9)]
        people = [Person("H001", "door"), Person("H002", "door")]
        goals = base_goals_v7(
            [FairPerson("H001"), FairPerson("H002")],
            {"H001": 2, "H002": 2}, 2)
        self.assertEqual(goals, {"H001": 1, "H002": 1})
        result = solve_lexicographic_count_fair(
            tasks, people, goals, seconds_fill=4, seconds_fair=4)
        self.assertEqual(result["status"], "FULL")
        self.assertEqual(result["filled"], 2)
        self.assertEqual(result["missing"], 0)
        self.assertEqual(result["actual_counts"], goals)
        self.assertEqual(result["final_abs_count_deviation"], 0)
        self.assertTrue(result["fill_optimal_proven"])
        self.assertTrue(result["fair_optimal_proven_given_fill"])
        self.assertFalse(result["actual_wasm_executed"])
        self.assertTrue(independently_check(tasks, people, result["assignments"]))

    def test_unreachable_target_does_not_create_missing_duty(self):
        tasks = [door(1, 5), door(1, 9)]
        people = [Person("H001", "door"), Person("H002", "door")]
        result = solve_lexicographic_count_fair(
            tasks, people, {"H001": 0, "H002": 0},
            seconds_fill=4, seconds_fair=4)
        self.assertEqual(result["filled"], 2)
        self.assertEqual(result["final_abs_count_deviation"], 2)
        self.assertTrue(result["fill_optimal_proven"])
        self.assertTrue(independently_check(tasks, people, result["assignments"]))

    def test_fixed_person_is_not_changed_for_cosmetic_fairness(self):
        tasks = [door(1, 5), door(1, 9)]
        people = [Person("H001", "door"), Person("H002", "door")]
        pins = {tasks[0].key: "H001"}
        result = solve_lexicographic_count_fair(
            tasks, people, {"H001": 0, "H002": 2}, pins=pins,
            seconds_fill=4, seconds_fair=4)
        self.assertEqual(result["assignments"][tasks[0].key], "H001")
        self.assertEqual(result["filled"], 2)
        self.assertTrue(independently_check(tasks, people, result["assignments"],
                                            pins=pins))

    def test_absence_and_rest_rules_override_fairness_quota(self):
        tasks = [door(1, 5), door(2, 5)]
        people = [Person("H001", "door"), Person("H002", "door")]
        events = [Event("H001", "leave",
                        date(2026, 12, 1), date(2026, 12, 1))]
        result = solve_lexicographic_count_fair(
            tasks, people, {"H001": 2, "H002": 0},
            events=events, seconds_fill=4, seconds_fair=4)
        self.assertEqual(result["filled"], 1)
        self.assertEqual(result["missing"], 1)
        self.assertEqual(result["status"], "PARTIAL_FILL_PROVEN")
        self.assertEqual(result["actual_counts"]["H001"], 0)
        self.assertTrue(result["fill_optimal_proven"])
        self.assertTrue(independently_check(tasks, people, result["assignments"],
                                            events=events))

    def test_next_day_rest_outweighs_target_even_without_events(self):
        tasks = [door(1, 5), door(2, 5)]
        people = [Person("H001", "door")]
        result = solve_lexicographic_count_fair(
            tasks, people, {"H001": 2},
            seconds_fill=4, seconds_fair=4)
        self.assertEqual((result["filled"], result["missing"]), (1, 1))
        self.assertEqual(result["final_abs_count_deviation"], 1)
        self.assertTrue(result["fill_optimal_proven"])

    def test_forced_vacancy_stays_blank(self):
        tasks = [door(1, 5)]
        people = [Person("H001", "door")]
        pins = {tasks[0].key: None}
        result = solve_lexicographic_count_fair(
            tasks, people, {"H001": 1}, pins=pins,
            seconds_fill=4, seconds_fair=4)
        self.assertEqual(result["filled"], 0)
        self.assertIsNone(result["assignments"][tasks[0].key])
        self.assertTrue(result["fill_optimal_proven"])

    def test_invalid_targets_are_rejected(self):
        tasks = [door(1, 5)]
        people = [Person("H001", "door")]
        with self.assertRaisesRegex(ValueError, "Exactly one"):
            solve_lexicographic_count_fair(
                tasks, people, {"H002": 1})
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            solve_lexicographic_count_fair(
                tasks, people, {"H001": -1})


if __name__ == "__main__":
    unittest.main()
