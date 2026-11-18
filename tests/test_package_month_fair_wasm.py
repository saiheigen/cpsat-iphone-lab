"""Packager PROOF-GATE unit tests with FAKE binaries, never actual WASM.

The real-fairness-workflow runs Node+genuine OR-Tools C++ WASM and
independent audits. This only verifies HTML packaging rejection controls.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"build"/"package_month_fair_wasm.py"
spec=importlib.util.spec_from_file_location("fair_packer", SCRIPT)
packer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(packer)


class FairPackagerGateTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root=Path(temp.name)
        self.js=root/"solver.js"
        self.wasm=root/"solver.wasm"
        self.proof=root/"real_proof.json"
        self.fixtures=root/"fictional_cases.json"
        self.html=root/"result.html"
        self.js.write_bytes(b"var createMonthFairModule = function () {};")
        self.wasm.write_bytes(b"\x00asm\x01\x00\x00\x00") # NOT executable solver
        labels={
            "two-shift-exact-fairness-oracle": {"status":"OPTIMAL",
                "filled":2,"optimal_fairness":0},
            "dense-full-month-door-blackouts-no-hints": {"status":"FEASIBLE",
                "tasks":372,"staff":56,"filled":372,
                "phase1_cost":100,"final_cost":70},
            "dense-full-month-officer-blackouts-no-hints": {"status":"FEASIBLE",
                "tasks":217,"staff":50,"filled":217,
                "phase1_cost":50,"final_cost":48},
            "dense-full-month-door-forced-vacancies": {"status":"FEASIBLE",
                "tasks":372,"staff":56,"filled":360,
                "phase1_cost":80,"final_cost":80},
            "pinned-adjacent-day-conflict": {"status":"INFEASIBLE",
                "fair_phase":"NOT_RUN"},
        }
        self.data={
            "accepted":True,
            "engine":"genuine-Google-OR-Tools-CP-SAT-WASM",
            "contract":"guard-month-fair-v3",
            "two_phases":True,
            "first_stage":"maximize-legal-fill",
            "second_stage":"lock-achieved-fill-and-minimize-absolute-person-count-deviations",
            "full_589_dense_model_tested":True,
            "exact_small_fairness_oracle_verified":True,
            "operationally_certified":False,
            "actual_iphone_safari_tested":False,
            "full_hard_rules_verified":False,
            "rejected_bad_input_cases":5,
            "js_sha256":hashlib.sha256(self.js.read_bytes()).hexdigest(),
            "wasm_sha256":hashlib.sha256(self.wasm.read_bytes()).hexdigest(),
            "cases":[{"name":name,"accepted":True,**props}
                     for name,props in labels.items()],
        }
        cases=[]
        for name,(shifts,staff,fill) in packer.PAGE_EXPECT.items():
            cases.append({"id":name,"name":name,"synthetic_only":True,
                "year":2026,"month":12,
                "pool":"officer" if "officer" in name else "door",
                "shifts":shifts,"staff":staff,"expectedFill":fill,
                "mask":"0"*(shifts*staff),"pins":[-2]*shifts,
                "hints":[-1]*shifts,"targets":[0]*staff})
        self.synthetic={
            "contract":"guard-month-fair-v3",
            "source":"synthetic-fixtures-no-real-workforce-data",
            "cases":cases,
        }
        self.save()

    def save(self):
        self.proof.write_text(json.dumps(self.data),encoding="utf-8")
        self.fixtures.write_text(json.dumps(self.synthetic),encoding="utf-8")

    def check_failure(self):
        with self.assertRaises(ValueError):
            packer.verify(self.js,self.wasm,self.proof,self.fixtures)

    def test_valid_shaped_fake_fixture_checks_packager_only(self):
        glue,b64,proof,fixtures=packer.verify(
            self.js,self.wasm,self.proof,self.fixtures)
        packer.make(glue,b64,proof,fixtures,self.html)
        page=self.html.read_text(encoding="utf-8")
        self.assertIn("guard-month-fair-v3",page)
        self.assertIn("createMonthFairModule",page)
        self.assertIn("兩階段",page)
        self.assertIn("真正 WASM",page)
        self.assertIn("不能核定班表",page)
        self.assertIn(self.data["wasm_sha256"],page)
        self.assertGreater(self.html.stat().st_size,10000)

    def test_reject_wrong_digest(self):
        self.wasm.write_bytes(self.wasm.read_bytes()+b"tampered")
        self.check_failure()

    def test_reject_no_actual_node_oracle(self):
        self.data["exact_small_fairness_oracle_verified"]=False
        self.save()
        self.check_failure()

    def test_reject_untrue_iphone_claim(self):
        self.data["actual_iphone_safari_tested"]=True
        self.save()
        self.check_failure()

    def test_reject_operational_certification_claim(self):
        self.data["operationally_certified"]=True
        self.save()
        self.check_failure()

    def test_reject_missing_synthetic_scenario(self):
        self.synthetic["cases"].pop()
        self.save()
        self.check_failure()

    def test_reject_fake_full_coverage(self):
        self.data["cases"][1]["filled"]=371
        self.save()
        self.check_failure()

    def test_reject_worse_fairness(self):
        self.data["cases"][2]["final_cost"]=1000
        self.save()
        self.check_failure()

    def test_reject_rewritten_wasm_version(self):
        self.data["contract"]="guard-month-v2"
        self.save()
        self.check_failure()

    def test_reject_incorrect_candidate_shape(self):
        self.synthetic["cases"][0]["mask"]="1"
        self.save()
        self.check_failure()

    def test_reject_duplicate_test_cases(self):
        self.data["cases"][2]=self.data["cases"][1]
        self.save()
        self.check_failure()

    def test_reject_false_infeasible_claim(self):
        self.data["cases"][4]["status"]="OPTIMAL"
        self.save()
        self.check_failure()


if __name__=="__main__":
    unittest.main()
