"""Synthetic-only tests of complete-month v3 fairness transport.

No tests here execute WebAssembly. Genuine Node+WASM acceptance is separately
required and must not be inferred from these Python adapter tests.
"""
from datetime import date
import hashlib
import unittest

from solver.roster_cp_sat import Person, Shift
from solver.full_month_wire_v2 import export_full_month_v2
from solver.full_month_fair_wire_v3 import (
    export_full_month_fair_v3, audit_full_month_fair_v3_response)
from solver.fairness_targets_v7 import FairPerson


class FairMonthWireTests(unittest.TestCase):
    def source(self):
        people = [Person("H001","door"),Person("H002","door")]
        base = export_full_month_v2(2026,12,"door",people)
        fair = [FairPerson("H001",carry=2,meal_credit=1),
                FairPerson("H002",weight=1/3)]
        return export_full_month_fair_v3(base,fair)

    def test_complete_anonymous_8_line_frame_and_soft_credits(self):
        payload=self.source()
        lines=payload["payload"].splitlines()
        self.assertEqual(len(lines),8)
        self.assertEqual(lines[0],"guard-month-fair-v3")
        self.assertEqual(lines[1],"2026-12")
        self.assertEqual(lines[3],"372 2")
        self.assertEqual(len(lines[4]),744)
        self.assertEqual(payload["base_goals"],[279,93])
        self.assertEqual(payload["targets"],[276,96])
        self.assertNotIn("H001",payload["payload"])
        self.assertNotIn("H002",payload["payload"])
        self.assertFalse(payload["v3_wasm_real_execution_proven"])

    def test_all_589_canonical_duty_slots_across_pools_without_truncation(self):
        members=([Person(f"H{i:03}","door") for i in range(1,57)] +
                 [Person(f"P{i:03}","officer") for i in range(1,51)])
        for pool,total,staff in [("door",372,56),("officer",217,50)]:
            v2=export_full_month_v2(2026,12,pool,members)
            v3=export_full_month_fair_v3(
                v2,[FairPerson(p.id) for p in v2["people"]])
            lines=v3["payload"].splitlines()
            self.assertEqual(len(lines[4]),total*staff)
            self.assertEqual(len(lines[7].split(",")),staff)
            self.assertEqual(sum(v3["targets"]),total)
            self.assertFalse(v3["fairness_optimality_independently_proven"])

    def test_order_mismatch_refuses_misapplied_credits(self):
        base=self.source()["v2_source"]
        with self.assertRaisesRegex(ValueError,"staff order"):
            export_full_month_fair_v3(
                base,[FairPerson("H002"),FairPerson("H001")])
        with self.assertRaisesRegex(ValueError,"staff order"):
            export_full_month_fair_v3(
                base,[FairPerson("H001")])

    def test_fake_json_is_eligible_for_audit_but_never_proves_execution(self):
        v3=self.source()
        blank=[-1]*372
        full_cost=sum(v3["targets"])
        result={
            "status":"FEASIBLE","fill_phase":"FEASIBLE",
            "fair_phase":"UNKNOWN","fill_optimal_proven":False,
            "fair_optimal_proven_given_fill":False,
            "assignments":blank,"filled":0,"missing":372,
            "actual_counts":[0,0],
            "phase1_abs_deviation":full_cost,
            "final_abs_deviation":full_cost,
            "fairness_improved":False,
        }
        audit=audit_full_month_fair_v3_response(v3,result)
        self.assertTrue(audit["independently_verified_feasible"])
        self.assertFalse(audit["actual_wasm_execution_proven"])
        self.assertFalse(audit["fairness_optimality_independently_proven"])
        self.assertFalse(audit["operationally_certified"])

    def test_forged_optimal_json_and_fake_deviation_rejected(self):
        v3=self.source()
        blank=[-1]*372
        cost=sum(v3["targets"])
        result={
            "status":"OPTIMAL","fill_phase":"FEASIBLE",
            "fair_phase":"UNKNOWN",
            "fill_optimal_proven":False,
            "fair_optimal_proven_given_fill":False,
            "assignments":blank,"filled":0,"missing":372,
            "actual_counts":[0,0],
            "phase1_abs_deviation":cost,
            "final_abs_deviation":cost,
            "fairness_improved":False,
        }
        with self.assertRaisesRegex(ValueError,"OPTIMAL"):
            audit_full_month_fair_v3_response(v3,result)
        result["status"]="FEASIBLE"
        result["final_abs_deviation"]=1
        with self.assertRaisesRegex(ValueError,"deviation"):
            audit_full_month_fair_v3_response(v3,result)
        result["final_abs_deviation"]=cost
        result["actual_counts"]=[1,0]
        with self.assertRaisesRegex(ValueError,"count mismatch"):
            audit_full_month_fair_v3_response(v3,result)

    def test_solver_status_flags_cannot_contradict_each_other(self):
        v3 = self.source()
        count = 372
        cost = sum(v3["targets"])
        original = {
            "status": "FEASIBLE", "fill_phase": "FEASIBLE",
            "fair_phase": "UNKNOWN", "fill_optimal_proven": False,
            "fair_optimal_proven_given_fill": False,
            "assignments": [-1] * count, "filled": 0, "missing": count,
            "actual_counts": [0, 0],
            "phase1_abs_deviation": cost,
            "final_abs_deviation": cost,
            "fairness_improved": False,
        }
        def reject(updates, pattern):
            claim = {**original, **updates}
            with self.assertRaisesRegex(ValueError, pattern):
                audit_full_month_fair_v3_response(v3, claim)
        reject({"fair_optimal_proven_given_fill": True}, "Fairness proof flag")
        reject({"fair_phase": "OPTIMAL"}, "Fairness proof flag")
        reject({"fill_phase": "OPTIMAL"}, "OPTIMAL fill phase")
        reject({"fill_optimal_proven": True}, "Unproven fill-optimal")
        reject({"fair_phase": "OPTIMAL",
                "fair_optimal_proven_given_fill": True,
                "fill_phase": "OPTIMAL",
                "fill_optimal_proven": True}, "overall status")
        reject({"phase1_abs_deviation": cost + 1,
                "fairness_improved": True}, "UNKNOWN fairness phase")
        reject({"fair_optimal_proven_given_fill": 1}, "boolean solver proof")

    def test_rehashed_modified_target_still_rejected(self):
        v3=self.source()
        lines=v3["payload"].splitlines()
        lines[7]="0,372"
        v3["payload"]="\n".join(lines)+"\n"
        v3["sha256"]=hashlib.sha256(v3["payload"].encode("ascii")).hexdigest()
        with self.assertRaisesRegex(ValueError,"targets were modified"):
            audit_full_month_fair_v3_response(v3,{})

    def test_v3_cannot_override_v2_fixed_vacancy(self):
        task=Shift("door",date(2026,12,1),5)
        people=[Person("H001","door")]
        v2=export_full_month_v2(
            2026,12,"door",people,pins={task.key:None})
        v3=export_full_month_fair_v3(v2,[FairPerson("H001")])
        self.assertEqual(v3["payload"].splitlines()[5].split(",")[4],"-1")
        lines=v3["payload"].splitlines()
        pins=lines[5].split(",")
        pins[4]="-2"
        lines[5]=",".join(pins)
        v3["payload"]="\n".join(lines)+"\n"
        v3["sha256"]=hashlib.sha256(v3["payload"].encode("ascii")).hexdigest()
        with self.assertRaisesRegex(ValueError,"Altered source"):
            audit_full_month_fair_v3_response(v3,{})


if __name__=="__main__":
    unittest.main()
