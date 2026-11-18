"""Proof-gate regression for full-month WASM HTML packaging.

Fictional proof data and deliberately fake 8-byte WASM header are used here
ONLY to test rejection behavior. A real Node+WASM solver verification in
GitHub is a separate mandatory gate for any deliverable.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

FILE=Path(__file__).resolve().parents[1]/"build"/"package_full_month_wasm.py"
spec=importlib.util.spec_from_file_location("full_month_packager",FILE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class FullMonthPackagerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.js=root/"module.js"
        self.wasm=root/"module.wasm"
        self.proof=root/"proof.json"
        self.html=root/"offline.html"
        self.js.write_bytes(b"var createMonthModule=function(){};")
        self.wasm.write_bytes(b"\x00asm\x01\x00\x00\x00")
        self.info={
            "accepted":True,
            "engine":"genuine-ORTools-CP-SAT-WASM",
            "contract":"guard-month-v2",
            "synthetic_full_month_shifts_tested":589,
            "synthetic_staff_tested":106,
            "all_operational_rules_tested":False,
            "dense_full_month_performance_verified":False,
            "real_iphone_safari_verified":False,
            "js_sha256":hashlib.sha256(self.js.read_bytes()).hexdigest(),
            "wasm_sha256":hashlib.sha256(self.wasm.read_bytes()).hexdigest(),
            "cases":[
                {"name":name,"status":
                 "INFEASIBLE" if filled is None else "OPTIMAL",
                 "shifts":tasks,"staff":staff,
                 "filled":filled,"accepted":True}
                for name,(tasks,staff,filled) in mod.CASES.items()
            ]
        }
        self.save()

    def save(self):
        self.proof.write_text(json.dumps(self.info),encoding="utf-8")

    def fail(self):
        with self.assertRaises(ValueError):
            mod.verify(self.js,self.wasm,self.proof)

    def test_rendering_synthetic_only_html(self):
        glue,b64,proof=mod.verify(self.js,self.wasm,self.proof)
        mod.make(glue,b64,proof,self.html)
        page=self.html.read_text("utf-8")
        self.assertIn("guard-month-v2",page)
        self.assertIn("createMonthModule",page)
        self.assertIn("589 班",page)
        self.assertIn("不能匯入",page)
        self.assertIn(self.info["wasm_sha256"],page)
        self.assertNotIn("guard-offline-v5",page)
        self.assertGreater(self.html.stat().st_size,2500)

    def test_digest_tampering_rejected(self):
        self.wasm.write_bytes(self.wasm.read_bytes()+b"tampered")
        self.fail()

    def test_uncertified_node_wasm_rejected(self):
        self.info["accepted"]=False
        self.save()
        self.fail()

    def test_full_month_geometry_cannot_be_faked(self):
        self.info["synthetic_full_month_shifts_tested"]=588
        self.save()
        self.fail()

    def test_missing_negative_scenario_rejected(self):
        self.info["cases"].pop()
        self.save()
        self.fail()

    def test_wrong_sunday_constraint_result_rejected(self):
        item=next(x for x in self.info["cases"]
                  if x["name"]=="consecutive-Sunday-standby-infeasible")
        item["status"]="OPTIMAL"
        self.save()
        self.fail()

    def test_false_iphone_claim_rejected(self):
        self.info["real_iphone_safari_verified"]=True
        self.save()
        self.fail()

    def test_false_real_world_rule_claim_rejected(self):
        self.info["all_operational_rules_tested"]=True
        self.save()
        self.fail()

if __name__=="__main__":
    unittest.main()
