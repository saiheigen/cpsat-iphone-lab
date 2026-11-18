"""Source-aligned synthetic tests for v7.0 fairness and carry arithmetic.

These tests verify target math only, not fair CP-SAT optimization or
full real-world operational roster rules.
"""
import unittest

from solver.fairness_targets_v7 import (
    FairPerson, base_goals_v7, actual_targets_v7,
    archive_compensation_out_v7, import_prior_locked_carry_v7,
)


class V7FairnessParityTests(unittest.TestCase):
    def test_largest_remainder_same_weight_uses_list_order(self):
        people = [FairPerson("A"), FairPerson("B"), FairPerson("C")]
        avail = {p.ident: 10 for p in people}
        self.assertEqual(base_goals_v7(people, avail, 10),
                         {"A": 4, "B": 3, "C": 3})
        self.assertEqual(base_goals_v7(people, avail, 5),
                         {"A": 2, "B": 2, "C": 1})

    def test_business_weight_one_third_is_a_soft_share(self):
        people = [FairPerson("ORD"), FairPerson("BUS", weight=1/3)]
        avail = {"ORD": 10, "BUS": 10}
        self.assertEqual(base_goals_v7(people, avail, 8),
                         {"ORD": 6, "BUS": 2})

    def test_carried_credits_reduce_target_and_reallocate_elsewhere(self):
        staff = [FairPerson("A", carry=2), FairPerson("B")]
        avail = {"A": 10, "B": 10}
        goals = base_goals_v7(staff, avail, 8)
        self.assertEqual(goals, {"A": 4, "B": 4})
        self.assertEqual(actual_targets_v7(staff, avail, 8, goals),
                         {"A": 2, "B": 6})

    def test_meal_credit_and_carry_are_additive(self):
        staff = [FairPerson("A", carry=1, meal_credit=2),
                 FairPerson("B")]
        avail = {"A": 10, "B": 10}
        self.assertEqual(actual_targets_v7(
            staff, avail, 8, {"A": 4, "B": 4}),
            {"A": 1, "B": 7})

    def test_no_eligible_people_no_fake_targets(self):
        people = [FairPerson("A"), FairPerson("B")]
        avail = {"A": 0, "B": 0}
        self.assertEqual(base_goals_v7(people, avail, 8),
                         {"A": 0, "B": 0})
        self.assertEqual(actual_targets_v7(
            people, avail, 8, {"A": 0, "B": 0}),
            {"A": 0, "B": 0})

    def test_static_capacity_does_not_create_hard_quota(self):
        people = [FairPerson("A"), FairPerson("B")]
        avail = {"A": 1, "B": 1}
        goals = base_goals_v7(people, avail, 8)
        self.assertEqual(goals, {"A": 4, "B": 4})
        # v7 target is *advice*, not proof that 4 duties are schedulable.
        self.assertEqual(actual_targets_v7(people, avail, 8, goals), goals)

    def test_redistribution_stops_at_static_capacity(self):
        people = [FairPerson("A", carry=8), FairPerson("B")]
        avail = {"A": 3, "B": 3}
        targets = actual_targets_v7(
            people, avail, 8, {"A": 4, "B": 4})
        # v7 prioritizes no-credit staff, but a compensated person can
        # receive duties when everyone else is already at their static cap.
        # B's *base* target 4 exceeds static capacity 3, so it stays 4.
        # Remaining duties are assigned back to A until A reaches cap 3.
        self.assertEqual(targets, {"A": 3, "B": 4})
        self.assertLess(sum(targets.values()), 8)

    def test_debts_are_never_automatically_pursued(self):
        people = [FairPerson("A", carry=1, meal_credit=1),
                  FairPerson("B", carry=0, meal_credit=0)]
        goals = {"A": 6, "B": 6}
        worked = {"A": 6, "B": 2}
        out = archive_compensation_out_v7(people, goals, worked)
        self.assertEqual(out, {"A": 2})
        self.assertNotIn("B", out)

    def test_locked_prior_auto_carry_requires_fresh_snapshot(self):
        people = [FairPerson("A"), FairPerson("B")]
        output = {"A": 2, "B": 1}
        self.assertEqual(
            import_prior_locked_carry_v7(
                people, output, prior_locked=True, prior_stale=False),
            {"A": 2, "B": 1})
        self.assertEqual(
            import_prior_locked_carry_v7(
                people, output, prior_locked=False, prior_stale=False),
            {"A": 0, "B": 0})
        self.assertEqual(
            import_prior_locked_carry_v7(
                people, output, prior_locked=True, prior_stale=True),
            {"A": 0, "B": 0})

    def test_manual_override_wins_over_auto_carry_even_if_zero(self):
        people = [FairPerson("A"), FairPerson("B")]
        received = import_prior_locked_carry_v7(
            people, {"A": 5, "B": 3},
            prior_locked=True, prior_stale=False,
            manual_override={"A": 0})
        self.assertEqual(received, {"A": 0, "B": 3})

    def test_archive_carry_calculation_includes_previous_credit(self):
        people = [FairPerson("A", carry=2, meal_credit=1),
                  FairPerson("B")]
        self.assertEqual(
            archive_compensation_out_v7(
                people, {"A": 6, "B": 6},
                {"A": 7, "B": 6}),
            {"A": 4})

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            base_goals_v7([FairPerson("A"), FairPerson("A")],
                          {"A": 8}, 8)
        with self.assertRaisesRegex(ValueError, "weight"):
            base_goals_v7([FairPerson("A", weight=-1)],
                          {"A": 8}, 8)
        with self.assertRaisesRegex(ValueError, "Static availability"):
            base_goals_v7([FairPerson("A")], {"A": -1}, 8)
        with self.assertRaisesRegex(ValueError, "nonnegative integer"):
            archive_compensation_out_v7(
                [FairPerson("A")], {"A": 1}, {"A": -1})
        with self.assertRaisesRegex(ValueError, "Carry"):
            import_prior_locked_carry_v7(
                [FairPerson("A")], {"A": -1},
                prior_locked=True, prior_stale=False)


if __name__ == "__main__":
    unittest.main()
