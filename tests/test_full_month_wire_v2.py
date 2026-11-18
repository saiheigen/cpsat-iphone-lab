"""Full-calendar synthetic month wire tests. No real rosters.

These verify only Python's serialized candidates and v7 partial-rule
parity; a genuine dynamic C++/WASM month solver DOES NOT EXIST YET.
"""
from datetime import date
import hashlib
import unittest

from solver.roster_cp_sat import Event, History, Person, Shift
from solver.full_month_wire_v2 import (
    export_full_month_v2, validate_full_month_v2_export,
    audit_full_month_v2_response,
)


def fictional_people():
    return ([Person(f"H{i:03}", "door") for i in range(1, 57)] +
            [Person(f"P{i:03}", "officer") for i in range(1, 51)])


def d(n, m=12):
    return date(2026, m, n)


class CompleteMonthWireTests(unittest.TestCase):
    def test_both_complete_pools_total_589_shifts_106_staff(self):
        people = fictional_people()
        passed = []
        for pool, expected_tasks, expected_staff in (
            ("door", 372, 56), ("officer", 217, 50)
        ):
            encoded = export_full_month_v2(2026, 12, pool, people)
            info = validate_full_month_v2_export(encoded)
            self.assertEqual((info["tasks"], info["people"]),
                             (expected_tasks, expected_staff))
            self.assertGreater(info["eligible_bits"], 0)
            self.assertTrue(info["validated"])
            self.assertFalse(info["actual_wasm_solved"])
            self.assertFalse(encoded["actual_wasm_compiler_implemented"])
            self.assertFalse(info["operationally_certified"])
            self.assertNotIn("H001", encoded["payload"])
            self.assertNotIn("P001", encoded["payload"])
            passed.append(info["tasks"])
        self.assertEqual(sum(passed), 589)

    def test_leave_nightcheck_driver_and_previous_month_rest_not_lost(self):
        people = fictional_people()
        events = [
            Event("H001", "leave", d(4), d(5)),
            Event("H002", "nightcheck", d(12), d(12)),
            Event("H003", "driver", d(17), d(17)),
        ]
        hist = [History("H004", Shift("door", d(30, 11), 6))]
        tasks = export_full_month_v2(
            2026, 12, "door", people, events, hist)
        info = validate_full_month_v2_export(tasks)
        self.assertTrue(info["validated"])
        mask = tasks["payload"].splitlines()[4]
        who = {p.id: i for i, p in enumerate(tasks["people"])}
        shifts = {t.key: i for i, t in enumerate(tasks["tasks"])}
        width = len(tasks["people"])
        def allowed(ident, day, num):
            row = shifts[Shift("door", d(day), num).key]
            return mask[row * width + who[ident]]
        self.assertEqual(allowed("H001", 6, 6), "0")  # Return day
        self.assertEqual(allowed("H001", 7, 6), "1")
        self.assertEqual(allowed("H002", 11, 6), "0") # Nightcheck previous
        self.assertEqual(allowed("H003", 16, 1), "0") # Driver previous night
        self.assertEqual(allowed("H004", 1, 6), "0")  # Prior month rest

    def test_pins_and_audited_warm_start_preserved(self):
        people = fictional_people()
        task = Shift("door", d(5), 6)
        blank = Shift("door", d(6), 6)
        fixed = {task.key: "H021", blank.key: None}
        encoded = export_full_month_v2(
            2026, 12, "door", people, pins=fixed, build_hint=True)
        info = validate_full_month_v2_export(encoded)
        self.assertTrue(info["validated"])
        lines = encoded["payload"].splitlines()
        pins = list(map(int, lines[5].split(",")))
        hints = list(map(int, lines[6].split(",")))
        ids = {t.key: i for i, t in enumerate(encoded["tasks"])}
        self.assertEqual(pins[ids[task.key]], 20)
        self.assertEqual(hints[ids[task.key]], 20)
        self.assertEqual(pins[ids[blank.key]], -1)
        self.assertEqual(hints[ids[blank.key]], -1)

    def test_modify_eligibility_then_recompute_digest_still_fails(self):
        encoded = export_full_month_v2(2026, 12, "door", fictional_people())
        lines = encoded["payload"].splitlines()
        lines[4] = ("0" if lines[4][0] == "1" else "1") + lines[4][1:]
        encoded["payload"] = "\n".join(lines) + "\n"
        encoded["sha256"] = hashlib.sha256(encoded["payload"].encode("ascii")).hexdigest()
        with self.assertRaisesRegex(ValueError, "Availability"):
            validate_full_month_v2_export(encoded)

    def test_truncate_a_day_even_with_adjusted_count_is_forbidden(self):
        encoded = export_full_month_v2(2026, 12, "door", fictional_people())
        encoded["tasks"] = encoded["tasks"][:-12]
        with self.assertRaisesRegex(ValueError, "complete, ordered"):
            validate_full_month_v2_export(encoded)

    def test_mutated_pin_even_with_recalculated_sha_is_rejected(self):
        task = Shift("door", d(3), 6)
        encoded = export_full_month_v2(
            2026, 12, "door", fictional_people(), pins={task.key: None})
        lines = encoded["payload"].splitlines()
        pins = lines[5].split(",")
        pins[encoded["tasks"].index(task)] = "-2"
        lines[5] = ",".join(pins)
        encoded["payload"] = "\n".join(lines) + "\n"
        encoded["sha256"] = hashlib.sha256(encoded["payload"].encode("ascii")).hexdigest()
        with self.assertRaisesRegex(ValueError, "fixed shift"):
            validate_full_month_v2_export(encoded)

    def test_wrong_pool_pin_and_duplicate_people_rejected(self):
        people = fictional_people()
        with self.assertRaisesRegex(ValueError, "Pins outside"):
            export_full_month_v2(
                2026, 12, "door", people,
                pins={Shift("officer", d(1), 5).key: "P001"})
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            export_full_month_v2(2026, 12, "door", people + [people[0]])

    def test_february_leap_month_uses_29_days(self):
        people = [Person("H001", "door"), Person("P001", "officer")]
        pool = export_full_month_v2(2028, 2, "door", people)
        out = validate_full_month_v2_export(pool)
        self.assertEqual(out["tasks"], 29 * 12)
        self.assertTrue(out["validated"])

    def test_audited_candidate_can_be_rechecked_as_hypothetical_wasm_response(self):
        # Deliberately synthetic/mock result. The real WASM CI has a
        # separate Node oracle; this test validates the zero-trust adapter.
        encoded = export_full_month_v2(
            2026, 12, "door", fictional_people(), build_hint=True)
        raw = encoded["payload"].splitlines()
        indices = list(map(int, raw[6].split(",")))
        filled = sum(index >= 0 for index in indices)
        self.assertGreater(filled, 0)
        audited = audit_full_month_v2_response(
            encoded, {"status": "FEASIBLE", "assignments": indices,
                      "filled": filled, "missing": 372 - filled})
        self.assertEqual(audited["filled"], filled)
        self.assertTrue(audited["validated_against_original_rules"])
        self.assertFalse(audited["operationally_certified"])
        self.assertFalse(audited["real_iphone_safari_verified"])
        self.assertEqual(audited["source"], "WASM_RESPONSE_INDEPENDENTLY_AUDITED")

    def test_corrupted_same_day_hints_fail_even_with_rehashed_payload(self):
        encoded = export_full_month_v2(
            2026, 12, "door", fictional_people())
        lines = encoded["payload"].splitlines()
        hints = lines[6].split(",")
        # Dec 1, 06-08 and 08-10; same person cannot serve both.
        hints[4] = "0"
        hints[5] = "0"
        lines[6] = ",".join(hints)
        encoded["payload"] = "\n".join(lines) + "\n"
        encoded["sha256"] = hashlib.sha256(encoded["payload"].encode("ascii")).hexdigest()
        with self.assertRaisesRegex(ValueError, "Illegal full-month hint"):
            validate_full_month_v2_export(encoded)

    def test_bad_wasm_response_is_never_turned_into_roster(self):
        encoded = export_full_month_v2(
            2026, 12, "door", fictional_people())
        empty = [-1] * 372
        for status in ("UNKNOWN", "INFEASIBLE", "MODEL_INVALID", None):
            with self.assertRaisesRegex(ValueError, "No verified feasible"):
                audit_full_month_v2_response(
                    encoded, {"status": status, "assignments": empty,
                              "filled": 0, "missing": 372})
        with self.assertRaisesRegex(ValueError, "truncated"):
            audit_full_month_v2_response(
                encoded, {"status": "FEASIBLE", "assignments": empty[:-1],
                          "filled": 0, "missing": 372})
        with self.assertRaisesRegex(ValueError, "staff index"):
            audit_full_month_v2_response(
                encoded, {"status": "FEASIBLE",
                          "assignments": [True] + empty[1:],
                          "filled": 1, "missing": 371})
        with self.assertRaisesRegex(ValueError, "filled count"):
            audit_full_month_v2_response(
                encoded, {"status": "FEASIBLE", "assignments": empty,
                          "filled": True, "missing": 372})

    def test_wasm_response_cannot_assign_ineligible_history_or_pinned_vacancy(self):
        people = fictional_people()
        history = [History("H001", Shift("door", d(30, 11), 6))]
        forced_blank = Shift("door", d(2), 6)
        encoded = export_full_month_v2(
            2026, 12, "door", people, history=history,
            pins={forced_blank.key: None})
        shifts = {t.key: k for k, t in enumerate(encoded["tasks"])}
        wrong = [-1] * 372
        wrong[shifts[Shift("door", d(1), 6).key]] = 0
        with self.assertRaisesRegex(ValueError, "eligibility"):
            audit_full_month_v2_response(
                encoded, {"status": "FEASIBLE", "assignments": wrong,
                          "filled": 1, "missing": 371})
        wrong = [-1] * 372
        wrong[shifts[forced_blank.key]] = 1
        with self.assertRaisesRegex(ValueError, "Pin not preserved"):
            audit_full_month_v2_response(
                encoded, {"status": "FEASIBLE", "assignments": wrong,
                          "filled": 1, "missing": 371})

    def test_wasm_response_rejects_consecutive_days_even_when_both_eligible(self):
        encoded = export_full_month_v2(
            2026, 12, "door", fictional_people())
        tasks = {t.key: i for i, t in enumerate(encoded["tasks"])}
        indices = [-1] * len(encoded["tasks"])
        indices[tasks[Shift("door", d(1), 6).key]] = 0
        indices[tasks[Shift("door", d(2), 6).key]] = 0
        with self.assertRaisesRegex(ValueError, "Duty conflict"):
            audit_full_month_v2_response(
                encoded, {"status": "FEASIBLE", "assignments": indices,
                          "filled": 2, "missing": 370})

    def test_cannot_mislabel_v2_as_a_verified_wasm_solve(self):
        encoded = export_full_month_v2(2026, 12, "officer", fictional_people())
        self.assertFalse(encoded["actual_wasm_solved"])
        self.assertFalse(encoded["operationally_certified"])
        self.assertEqual(encoded["contract"], "guard-month-v2")


if __name__ == "__main__":
    unittest.main()
