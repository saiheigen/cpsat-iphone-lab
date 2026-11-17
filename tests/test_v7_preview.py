"""Fictional v7 preview serialization tests: must never mutate a backup."""
from copy import deepcopy
from datetime import date
import unittest

from solver.roster_cp_sat import Person, Shift, month_shifts
from solver.v7_backup_bridge import BridgeResult
from solver.v7_preview import preview_v7_shape


def inputs():
    tasks = month_shifts(2026, 12)
    people = [Person("H001", "door"), Person("P001", "officer")]
    bridge = BridgeResult(
        month="2026-12", people=people, tasks=tasks, events=[],
        history=[], pins={}, weights={}, carry={})
    choice = {t.key: None for t in tasks}
    choice[Shift("door", date(2026, 12, 1), 6).key] = "H001"
    choice[Shift("officer", date(2026, 12, 1), 5).key] = "P001"
    out = {"status": "PARTIAL_FEASIBLE", "assignments": choice,
           "filled": 2, "missing": len(tasks)-2,
           "optimal_fill_proven": False}
    return bridge, out


class PreviewTests(unittest.TestCase):
    def test_complete_grid_and_native_iso_to_v7_serial(self):
        bridge, result = inputs()
        before = deepcopy(result["assignments"])
        preview = preview_v7_shape(bridge, result)
        self.assertEqual(result["assignments"], before)
        self.assertEqual(preview["format"], "guard-cpsat-preview-v1")
        self.assertTrue(preview["preview_only"])
        self.assertFalse(preview["importable_as_v7_backup"])
        self.assertFalse(preview["operationally_certified"])
        self.assertEqual(len(preview["schedule"]["door"]), 372)
        self.assertEqual(len(preview["schedule"]["officer"]), 217)
        self.assertEqual((preview["filled"], preview["missing"]), (2, 587))
        serial = (date(2026, 12, 1) - date(1970, 1, 1)).days
        self.assertIn([serial, 6, "H001"], preview["schedule"]["door"])
        self.assertIn([serial, 5, "P001"], preview["schedule"]["officer"])

    def test_missing_entry_rejected(self):
        bridge, result = inputs()
        result["assignments"].pop(next(iter(result["assignments"])))
        with self.assertRaisesRegex(ValueError, "Missing/extra"):
            preview_v7_shape(bridge, result)

    def test_altered_filled_count_rejected(self):
        bridge, result = inputs()
        result["filled"] = 5
        with self.assertRaisesRegex(ValueError, "metrics"):
            preview_v7_shape(bridge, result)

    def test_illegal_person_rejected(self):
        bridge, result = inputs()
        key = Shift("door", date(2026, 12, 1), 6).key
        result["assignments"][key] = "P001"
        with self.assertRaisesRegex(ValueError, "Illegal assignment"):
            preview_v7_shape(bridge, result)

    def test_cross_day_rest_conflict_rejected(self):
        bridge, result = inputs()
        result["assignments"][Shift("door", date(2026, 12, 2), 6).key] = "H001"
        result["filled"] = 3
        result["missing"] = 586
        with self.assertRaisesRegex(ValueError, "Duty conflict"):
            preview_v7_shape(bridge, result)

    def test_pinned_vacancy_must_stay_vacant(self):
        bridge, result = inputs()
        target = Shift("door", date(2026, 12, 1), 6).key
        bridge.pins[target] = None
        with self.assertRaisesRegex(ValueError, "Pin not preserved"):
            preview_v7_shape(bridge, result)

    def test_partial_grid_rejected_even_if_legal(self):
        bridge, result = inputs()
        bridge.tasks.pop()
        key = next(k for k in result["assignments"] if k not in {t.key for t in bridge.tasks})
        result["assignments"].pop(key)
        result["missing"] = 586
        with self.assertRaisesRegex(ValueError, "entire month"):
            preview_v7_shape(bridge, result)

    def test_incomplete_solver_refused(self):
        bridge, result = inputs()
        result["assignments"] = None
        with self.assertRaisesRegex(ValueError, "No complete solution"):
            preview_v7_shape(bridge, result)

    def test_false_full_claim_rejected(self):
        bridge, result = inputs()
        result["status"] = "FULL"
        with self.assertRaisesRegex(ValueError, "contradicts occupancy"):
            preview_v7_shape(bridge, result)

    def test_false_optimality_claim_rejected(self):
        bridge, result = inputs()
        result["status"] = "PARTIAL_OPTIMAL"
        with self.assertRaisesRegex(ValueError, "disagree"):
            preview_v7_shape(bridge, result)


if __name__ == "__main__":
    unittest.main()
