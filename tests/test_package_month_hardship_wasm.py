"""Only proof-gated packaging checks, deliberately FAKE tiny wasm/header.

Passing these tests DOES NOT prove actual C++ WASM execution, solver validity,
iPhone Safari support, operational rules or hardship optimum for 589 shifts.
"""
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"build"/"package_month_hardship_wasm.py"
spec=importlib.util.spec_from_file_location("hardship_packer",SCRIPT)
packer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(packer)


class HardshipPackagerGateTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        p=Path(temp.name)
        self.js=p/"solver.js"
        self.wasm=p/"solver.wasm"
        self.proof=p/"proof.json"
        self.fixtures=p/"fictional.json"
        self.html=p/"experimental.html"
        self.js.write_bytes(b"var createMonthHardshipModule = function(){};")
        self.wasm.write_bytes(b"\x00asm\x01\x00\x00\x00")  # header ONLY, NOT real solver
        cases=[
            {"name":"exact-four-shift-hardship-oracle",
             "status":"OPTIMAL","filled":4,"hardship":6,"oracle":6},
            {"name":"door-blackouts-no-hints","status":"FEASIBLE",
             "shifts":372,"staff":56,"filled":372,
             "phase1_abs_deviation":50,"final_abs_deviation":12,
             "hardship_before":200,"hardship_after":190,
             "fill_phase":"OPTIMAL","fair_phase":"OPTIMAL",
             "hardship_phase":"FEASIBLE","hardship_optimal_proven":False},
            {"name":"officer-blackouts-no-hints","status":"OPTIMAL",
             "shifts":217,"staff":50,"filled":217,
             "phase1_abs_deviation":40,"final_abs_deviation":10,
             "hardship_before":120,"hardship_after":110,
             "fill_phase":"OPTIMAL","fair_phase":"OPTIMAL",
             "hardship_phase":"OPTIMAL","hardship_optimal_proven":True},
            {"name":"door-forced-vacancies","status":"FEASIBLE",
             "shifts":372,"staff":56,"filled":360,
             "phase1_abs_deviation":40,"final_abs_deviation":4,
             "hardship_before":180,"hardship_after":180,
             "fill_phase":"OPTIMAL","fair_phase":"OPTIMAL",
             "hardship_phase":"UNKNOWN","hardship_optimal_proven":False},
        ]
        self.data={
            "accepted":True,"engine":"genuine-Google-OR-Tools-CP-SAT-WASM",
            "contract":"guard-month-harsh-v4","three_phases":True,
            "filled_positions_protected":True,
            "count_fairness_protected":True,"synthetic_only":True,
            "real_iphone_safari_tested":False,
            "operationally_certified":False,
            "full_hard_rules_verified":False,
            "exact_independent_hardship_oracle_verified":True,
            "tested_full_589_dense_shifts":True,
            "invalid_frames_rejected":3,
            "js_sha256":hashlib.sha256(self.js.read_bytes()).hexdigest(),
            "wasm_sha256":hashlib.sha256(self.wasm.read_bytes()).hexdigest(),
            "cases":[{"accepted":True,**x} for x in cases]
        }
        fixture_cases=[]
        for name,(shifts,staff,fill) in packer.PAGE_EXPECT.items():
            fixture_cases.append({
                "id":name,"name":name,"year":2026,"month":12,
                "pool":"officer" if name.startswith("officer") else "door",
                "shifts":shifts,"staff":staff,"expectedFill":fill,
                "mask":"0"*(shifts*staff),"pins":[-2]*shifts,
                "hints":[-1]*shifts,"targets":[0]*staff,
                "synthetic_only":True,
                "oracleBest":6 if name=="tiny" else None,
            })
        self.synthetic={
            "contract":"guard-month-harsh-v4",
            "source":"synthetic-fixtures-no-real-workforce-data",
            "cases":fixture_cases}
        self.save()
        self.data["fixture_sha256"]=hashlib.sha256(
            self.fixtures.read_bytes()).hexdigest()
        self.save()

    def save(self):
        self.proof.write_text(json.dumps(self.data),encoding="utf-8")
        self.fixtures.write_text(json.dumps(self.synthetic),encoding="utf-8")

    def fail(self,pattern=None):
        with self.assertRaisesRegex(ValueError,pattern or ".*"):
            packer.verify(self.js,self.wasm,self.proof,self.fixtures)

    def test_valid_shaped_FAKE_proof_gate_and_page_markup_ONLY(self):
        js,wasm,proof,fixtures=packer.verify(
            self.js,self.wasm,self.proof,self.fixtures)
        packer.make(js,wasm,proof,fixtures,self.html)
        page=self.html.read_text("utf-8")
        self.assertIn("guard-month-harsh-v4",page)
        self.assertIn("createMonthHardshipModule",page)
        self.assertIn("hardshipScore",page)
        self.assertIn("不能核定班表",page)
        self.assertGreater(self.html.stat().st_size,10000)

    def test_generated_standalone_browser_javascript_is_syntactically_valid(self):
        # This is only JS syntax checking with a FAKE WASM fixture.
        # It neither invokes WebAssembly nor verifies real browsers.
        js,wasm,proof,fixtures=packer.verify(
            self.js,self.wasm,self.proof,self.fixtures)
        packer.make(js,wasm,proof,fixtures,self.html)
        text=self.html.read_text("utf-8")
        self.assertEqual(text.count("<script"),2)
        audit_script=text.split('<script id="phase5-wasm-glue">',1)[1].split("</script>",1)[1].split("<script>",1)[1].split("</script>",1)[0]
        self.assertNotIn("__CASES__",audit_script)
        result=subprocess.run(["node","--check","-"],input=audit_script,
                              capture_output=True,text=True,check=False)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("hardshipScore",audit_script)
        self.assertIn("solve_guard_month_harsh_v4",audit_script)
        self.assertIn("dedicated-worker",audit_script)
        self.assertIn("WORKER_BOOTSTRAP=",audit_script)
        self.assertNotIn("__WORKER_BOOTSTRAP__",audit_script)
        worker=SCRIPT.parents[1]/"src"/"phase5_hardship_worker.js"
        worker_check=subprocess.run(["node","--check",str(worker)],
                                    capture_output=True,text=True,check=False)
        self.assertEqual(worker_check.returncode,0,worker_check.stderr)
        self.assertIn("self.postMessage({type:",worker.read_text("utf-8"))
        self.assertNotIn("importScripts(",worker.read_text("utf-8"))

    def test_changed_binary_rejected(self):
        self.wasm.write_bytes(self.wasm.read_bytes()+b"t")
        self.fail("binary hash mismatch")

    def test_changed_fictional_fixture_rejected_even_if_valid_shape(self):
        self.synthetic["cases"][0]["name"]="malicious changed scenario"
        self.save()
        self.fail("Unattested browser fixtures")

    def test_missing_fixture_hash_rejected(self):
        self.data.pop("fixture_sha256")
        self.save()
        self.fail("Unattested browser fixtures")

    def test_forged_hardship_improvement_rejected(self):
        self.data["cases"][1]["hardship_after"]=300
        self.save()
        self.fail("protected objective")

    def test_forged_fill_rejected(self):
        self.data["cases"][1]["filled"]=371
        self.save()
        self.fail("preserved fill")

    def test_false_optimality_flag_rejected(self):
        self.data["cases"][1]["hardship_optimal_proven"]=True
        self.save()
        self.fail("optimality")

    def test_invented_tiny_oracle_rejected(self):
        self.data["cases"][0]["hardship"]=0
        self.save()
        self.fail("independent exact hardship oracle")

    def test_fake_iphone_or_operational_certification_rejected(self):
        self.data["real_iphone_safari_tested"]=True
        self.save()
        self.fail("proof")
        self.data["real_iphone_safari_tested"]=False
        self.data["operationally_certified"]=True
        self.save()
        self.fail("proof")

    def test_duplicate_real_cases_rejected(self):
        self.data["cases"][2]=self.data["cases"][1]
        self.save()
        self.fail("repeated")

    def test_missing_count_protection_rejected(self):
        self.data["count_fairness_protected"]=False
        self.save()
        self.fail("proof")

    def test_wrong_category_fixture_shape_rejected_after_attesting(self):
        self.synthetic["cases"][2]["mask"]="0"
        self.save()
        self.data["fixture_sha256"]=hashlib.sha256(
            self.fixtures.read_bytes()).hexdigest()
        self.save()
        self.fail("eligibility")

    def test_json_script_breakout_escaped_when_attested(self):
        malicious="</script><script>window.leak=1</script>"
        self.synthetic["cases"][0]["name"]=malicious
        self.save()
        self.data["fixture_sha256"]=hashlib.sha256(
            self.fixtures.read_bytes()).hexdigest()
        self.save()
        js,wasm,proof,fixtures=packer.verify(
            self.js,self.wasm,self.proof,self.fixtures)
        packer.make(js,wasm,proof,fixtures,self.html)
        text=self.html.read_text("utf-8")
        self.assertNotIn(malicious,text)
        self.assertIn(r"\u003c/script\u003e",text)


if __name__=="__main__":
    unittest.main()
