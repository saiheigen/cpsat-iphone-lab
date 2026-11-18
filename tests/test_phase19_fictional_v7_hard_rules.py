"""Only invented fictional people/events. No real v7 backup or military data."""
from copy import deepcopy
from datetime import date
import unittest

from solver.roster_cp_sat import Event, Shift
from solver.phase19_fictional_v7_hard_rules import (
    MONTH, SOURCE, create_case, invented_month, eligible, audit_genuine_result,
)


class FakeHardRuleMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.door = create_case("door")
        cls.officer = create_case("officer")

    def test_full_month_and_anonymous_exact_v4_frame(self):
        self.assertEqual(MONTH, (2026, 12))
        for obj, expected in ((self.door,372), (self.officer,217)):
            self.assertEqual(obj["shifts"],expected)
            self.assertEqual(len(obj["frame"].splitlines()),8)
            self.assertEqual(obj["frame"].splitlines()[0],"guard-month-harsh-v4")
            self.assertEqual(obj["source"],SOURCE)
            self.assertTrue(obj["synthetic_only"])
            self.assertFalse(obj["operationally_certified"])
            self.assertFalse(obj["full_v7_rule_parity_verified"])
            self.assertFalse(obj["history_freshness_verified_for_real_data"])
            for p in obj["fixture"].people:
                self.assertNotIn(p.id,obj["frame"])
        self.assertEqual(self.door["shifts"]+self.officer["shifts"],589)

    def test_unknown_pool_disallowed(self):
        with self.assertRaises(ValueError):
            invented_month("both")

    def test_leave_night_before_and_return_day(self):
        c=self.door
        self.assertFalse(eligible(c,0,3,1))
        self.assertTrue(eligible(c,0,3,6))
        for d in (4,5,6):
            self.assertFalse(eligible(c,0,d,6))
        self.assertTrue(eligible(c,0,7,6))

    def test_nightcheck_start_of_month_including_prior_day(self):
        c=self.door
        self.assertFalse(eligible(c,1,1,6))
        self.assertFalse(eligible(c,1,2,6))
        self.assertTrue(eligible(c,1,3,6))
        self.assertFalse(eligible(self.officer,2,19,5))
        self.assertFalse(eligible(self.officer,2,20,5))
        self.assertFalse(eligible(self.officer,2,21,5))
        self.assertTrue(eligible(self.officer,2,22,5))

    def test_driver_no_night_before_and_two_day_rest(self):
        c=self.door
        self.assertFalse(eligible(c,2,9,1))
        self.assertTrue(eligible(c,2,9,6))
        self.assertFalse(eligible(c,2,10,6))
        self.assertFalse(eligible(c,2,11,6))
        self.assertTrue(eligible(c,2,12,6))
        o=self.officer
        self.assertFalse(eligible(o,3,2,1))
        self.assertTrue(eligible(o,3,2,5))
        self.assertFalse(eligible(o,3,3,5))
        self.assertFalse(eligible(o,3,4,5))
        self.assertTrue(eligible(o,3,5,6))

    def test_training_prohibits_previous_day(self):
        c=self.door
        for day in (14,15,16):
            self.assertFalse(eligible(c,3,day,6))
        self.assertTrue(eligible(c,3,17,6))
        o=self.officer
        for day in (23,24,25):
            self.assertFalse(eligible(o,5,day,5))
        self.assertTrue(eligible(o,5,26,5))

    def test_dynamic_exemption_night_and_noon(self):
        c=self.door
        self.assertFalse(eligible(c,4,8,1))
        self.assertFalse(eligible(c,4,8,2))
        self.assertTrue(eligible(c,4,8,6))
        self.assertFalse(eligible(c,5,8,8))
        self.assertTrue(eligible(c,5,8,6))
        self.assertFalse(eligible(self.officer,4,8,5))

    def test_kitchen_not_eligible_on_any_shift(self):
        c=self.door
        for day,slot in ((1,1),(5,8),(12,6),(31,12)):
            self.assertFalse(eligible(c,6,day,slot))

    def test_officer_duty_and_meal_three_day_prohibition(self):
        o=self.officer
        for day in (7,8,9):
            self.assertFalse(eligible(o,0,day,5))
        self.assertTrue(eligible(o,0,10,5))
        for day in (11,12,13):
            self.assertFalse(eligible(o,1,day,5))
        self.assertTrue(eligible(o,1,14,5))

    def test_cross_month_history_carries_rest_and_same_slot(self):
        c=self.door
        self.assertFalse(eligible(c,7,1,6))
        self.assertFalse(eligible(c,7,2,6))
        self.assertTrue(eligible(c,7,2,7))
        self.assertTrue(eligible(c,7,3,6))
        o=self.officer
        self.assertFalse(eligible(o,6,1,7))
        self.assertFalse(eligible(o,6,2,7))
        self.assertTrue(eligible(o,6,3,7))

    def test_next_sunday_standby_rejected_across_months(self):
        # November 29 and December 6, 2026 were Sundays.
        c=self.door
        self.assertEqual(date(2026,11,29).weekday(),6)
        self.assertEqual(date(2026,12,6).weekday(),6)
        self.assertFalse(eligible(c,8,6,5))
        self.assertFalse(eligible(c,8,6,10))
        self.assertTrue(eligible(c,8,6,1))

    def test_pins_legal_and_forced_vacancies_preserved(self):
        door=self.door["v2_source"]["pins"]
        officer=self.officer["v2_source"]["pins"]
        self.assertEqual(door[Shift("door",date(2026,12,2),6).key],"SIM_D_009")
        self.assertIsNone(door[Shift("door",date(2026,12,5),8).key])
        self.assertEqual(officer[Shift("officer",date(2026,12,5),5).key],"SIM_O_007")
        self.assertIsNone(officer[Shift("officer",date(2026,12,6),4).key])
        self.assertTrue(eligible(self.door,9,2,6))
        self.assertTrue(eligible(self.officer,7,5,5))

    def test_ineligible_fixed_assignment_refused_by_existing_model(self):
        c=self.door
        original=c["fixture"]
        from solver.full_month_wire_v2 import export_full_month_v2
        pins=dict(original.pins)
        pins[Shift("door",date(2026,12,4),6).key]="SIM_D_000"
        with self.assertRaisesRegex(ValueError,"violates hard rule"):
            export_full_month_v2(2026,12,"door",list(original.people),
                 events=list(original.events),history=list(original.history),
                 pins=pins)

    def test_eligibility_index_outside_bounds_refused(self):
        with self.assertRaises(ValueError):
            eligible(self.officer,999,1,1)
        with self.assertRaises(ValueError):
            eligible(self.officer,0,0,1)
        with self.assertRaises(ValueError):
            eligible(self.door,0,32,1)
        with self.assertRaises(ValueError):
            eligible(self.officer,0,1,12)

    @staticmethod
    def pin_only_result(case):
        raw=case["frame"].splitlines()
        pins=list(map(int,raw[5].split(",")))
        assignments=[p if p>=0 else -1 for p in pins]
        actual=[assignments.count(i) for i in range(case["staff"])]
        targets=list(map(int,raw[7].split(",")))
        deviation=sum(abs(a-b) for a,b in zip(actual,targets))
        n=sum(x>=0 for x in assignments)
        return {
            "status":"FEASIBLE",
            "assignments":assignments,
            "filled":n,"missing":case["shifts"]-n,
            "actual_counts":actual,
            "phase1_abs_deviation":deviation,
            "final_abs_deviation":deviation,
            "fill_phase":"FEASIBLE",
            "fill_optimal_proven":False,
            "fair_phase":"UNKNOWN",
            "fair_optimal_proven_given_fill":False,
            "hardship_phase":"UNKNOWN",
            "hardship_optimal_proven_given_locked_predecessors":False,
            "fixed_occupied_positions":True,
            "hardship_initial_score":0,
            "hardship_final_score":0,
            "hardship_improved":False,
        }

    def test_independent_reaudit_can_validate_feasible_pins_only(self):
        for case in (self.door,self.officer):
            audit=audit_genuine_result(case,self.pin_only_result(case))
            self.assertTrue(audit["independently_verified_feasible"])
            self.assertEqual(audit["filled"],1)
            self.assertFalse(audit["operationally_certified"])

    def test_reaudit_rejects_bad_forbidden_assignment(self):
        case=self.door
        fake=self.pin_only_result(case)
        n=(4-1)*12+(6-1)
        fake["assignments"][n]=0  # first fictional person is on leave
        fake["filled"]+=1
        fake["missing"]-=1
        fake["actual_counts"][0]+=1
        fake["final_abs_deviation"]=sum(abs(a-b) for a,b in zip(
            fake["actual_counts"],map(int,case["frame"].splitlines()[7].split(","))))
        fake["phase1_abs_deviation"]=fake["final_abs_deviation"]
        with self.assertRaisesRegex(ValueError,"Illegal assignment"):
            audit_genuine_result(case,fake)

    def test_reaudit_rejects_altered_frame_and_l1(self):
        case=deepcopy(self.door)
        case["frame"]=case["frame"].replace("guard-month-harsh-v4",
                                               "guard-month-fair-v3")
        with self.assertRaisesRegex(ValueError,"mutated"):
            audit_genuine_result(case,self.pin_only_result(self.door))
        case=deepcopy(self.door)
        fake=self.pin_only_result(self.door)
        fake["final_abs_deviation"]+=1
        with self.assertRaisesRegex(ValueError,"fairness L1"):
            audit_genuine_result(case,fake)

    def test_reaudit_rejects_false_optimality_flag(self):
        fake=self.pin_only_result(self.officer)
        fake["hardship_optimal_proven_given_locked_predecessors"]=True
        with self.assertRaisesRegex(ValueError,"proof indicator"):
            audit_genuine_result(self.officer,fake)

    def test_reaudit_rejects_mutated_fixed_vacancy(self):
        case=self.door
        fake=self.pin_only_result(case)
        i=(5-1)*12+(8-1)
        fake["assignments"][i]=9
        fake["filled"]+=1
        fake["missing"]-=1
        with self.assertRaises(ValueError):
            audit_genuine_result(case,fake)


if __name__=="__main__":
    unittest.main()
