"""Native validation of anonymous bounded WASM assignment-v1 transport.

Invented names and IDs only. Does not invoke WASM; its separate C++/
WebAssembly job verifies the actual CP-SAT contract and brute-force oracle.
"""
from datetime import date
import unittest

from solver.roster_cp_sat import Event, History, Person, Shift, month_shifts
from solver.wasm_assignment_adapter import (
    audit_assignment_v1_response, encode_assignment_v1,
)


class WasmModelAdapterTests(unittest.TestCase):
    @staticmethod
    def small():
        people = [Person("H001", "door"), Person("H002", "door"),
                  Person("P001", "officer")]
        tasks = [Shift("door", date(2026, 12, 1), 6),
                 Shift("door", date(2026, 12, 2), 6),
                 Shift("officer", date(2026, 12, 1), 5)]
        events = [Event("H001", "leave", date(2026, 12, 1),
                        date(2026, 12, 1))]
        pins = {tasks[0].key: "H002", tasks[2].key: None}
        return tasks, people, events, pins

    def test_exact_binary_contract_preserves_eligibility_and_conflict(self):
        tasks, people, events, pins = self.small()
        encoded = encode_assignment_v1(tasks, people, events=events, pins=pins)
        self.assertEqual(encoded["contract"], "assignment-v1")
        self.assertEqual(encoded["payload"],
                         "assignment-v1\n3 3\n010010001\n0:1\n1,-2,-1\n")
        for person in people:
            self.assertNotIn(person.id, encoded["payload"])
        self.assertFalse(encoded["supports_full_month"])
        self.assertFalse(encoded["operationally_certified"])

    def test_independent_result_validation_and_conversion(self):
        tasks, people, events, pins = self.small()
        model = encode_assignment_v1(tasks, people, events=events, pins=pins)
        result = {"status": "OPTIMAL",
                  "assignments": [1, -1, -1], "filled": 1, "missing": 2}
        checked = audit_assignment_v1_response(model, result)
        self.assertEqual(checked["assignments"][tasks[0].key], "H002")
        self.assertIsNone(checked["assignments"][tasks[1].key])
        self.assertTrue(checked["fill_optimal_proven_for_current_subset"])
        self.assertFalse(checked["full_month_verified"])

    def test_timeouts_and_unsolved_results_are_not_schedules(self):
        tasks, people, events, pins = self.small()
        model = encode_assignment_v1(tasks, people, events=events, pins=pins)
        for status in ("UNKNOWN", "INFEASIBLE", "INVALID_INPUT", None):
            with self.assertRaisesRegex(ValueError, "No verified feasible"):
                audit_assignment_v1_response(
                    model, {"status": status, "assignments": [-1, -1, -1]})

    def test_tampering_cannot_override_pin_or_eligibility(self):
        tasks, people, events, pins = self.small()
        model = encode_assignment_v1(tasks, people, events=events, pins=pins)
        with self.assertRaisesRegex(ValueError, "Pin not preserved"):
            audit_assignment_v1_response(
                model, {"status": "OPTIMAL",
                        "assignments": [-1, -1, -1], "filled": 0, "missing": 3})
        with self.assertRaisesRegex(ValueError, "Illegal assignment"):
            audit_assignment_v1_response(
                model, {"status": "OPTIMAL",
                        "assignments": [1, 0, -1], "filled": 2, "missing": 1})
        with self.assertRaisesRegex(ValueError, "count mismatch"):
            audit_assignment_v1_response(
                model, {"status": "OPTIMAL",
                        "assignments": [1, -1, -1], "filled": 2, "missing": 1})

    def test_next_day_rest_conflict_pair_encoded(self):
        t = [Shift("door", date(2026, 12, d), 6) for d in (1, 2, 3)]
        people = [Person("H001", "door")]
        encoded = encode_assignment_v1(t, people)
        self.assertIn("0:1", encoded["payload"])
        self.assertIn("1:2", encoded["payload"])
        self.assertIn("0:2", encoded["payload"])  # same slot within two days

    def test_previous_month_history_disqualifies_person(self):
        t = [Shift("door", date(2026, 12, 1), 6)]
        staff = [Person("H001", "door"), Person("H002", "door")]
        past = [History("H001", Shift("door", date(2026, 11, 30), 6))]
        model = encode_assignment_v1(t, staff, history=past)
        self.assertEqual(model["payload"].splitlines()[2], "01")

    def test_bad_bounds_fail_without_truncating_records(self):
        shifts = month_shifts(2026, 12)
        people = [Person("H001", "door")]
        with self.assertRaisesRegex(ValueError, "1–64"):
            encode_assignment_v1(shifts[:65], people)
        with self.assertRaisesRegex(ValueError, "1–24"):
            encode_assignment_v1(shifts[:1],
                                 [Person(f"H{i:03}", "door") for i in range(25)])

    def test_wrong_pool_pin_is_rejected(self):
        task = Shift("door", date(2026, 12, 1), 6)
        staff = [Person("H001", "door"), Person("P001", "officer")]
        with self.assertRaisesRegex(ValueError, "Pinned person violates hard rule"):
            encode_assignment_v1([task], staff, pins={task.key: "P001"})


if __name__ == "__main__":
    unittest.main()
