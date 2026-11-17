"""Test offline dynamic HTML packaging MECHANICS only.

The source binaries here are intentionally fake. These tests cannot prove
CP-SAT runs. The actual dynamic WASM workflow must rerun the genuine engine
with its own independent enumeration before packaging.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "build" / "package_dynamic_assignment.py"
spec = importlib.util.spec_from_file_location("dynamic_package", SCRIPT)
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)


class DynamicPackageGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.js = base / "bridge.js"
        self.wasm = base / "bridge.wasm"
        self.proof = base / "proof.json"
        self.html = base / "page.html"
        self.js.write_bytes(b"var createAssignmentModule=function(){};")
        self.wasm.write_bytes(b"\x00asm\x01\x00\x00\x00")
        self.data = {
            "accepted": True,
            "engine": "genuine-ORTools-CP-SAT-in-WASM",
            "contract": "bounded-dynamic-assignment-v1",
            "invalid_input_cases": 4,
            "operationally_certified": False,
            "full_589_shift_model": False,
            "js_sha256": hashlib.sha256(self.js.read_bytes()).hexdigest(),
            "wasm_sha256": hashlib.sha256(self.wasm.read_bytes()).hexdigest(),
            "tests": [
                {"name": name, "status": status,
                 "got_filled": filled,
                 "oracle_max_fill": -1 if filled is None else filled,
                 "accepted": True}
                for name, (status, filled) in pack.SCENARIOS.items()
            ],
        }
        self.save()

    def save(self):
        self.proof.write_text(json.dumps(self.data), encoding="utf-8")

    def reject(self):
        with self.assertRaises(ValueError):
            pack.verify(self.js, self.wasm, self.proof)

    def test_all_fields_and_demo_structure_only(self):
        pack.package(self.js, self.wasm, self.proof, self.html)
        page = self.html.read_text(encoding="utf-8")
        self.assertIn("createAssignmentModule", page)
        self.assertIn("assignment-v1", page)
        self.assertIn("WebAssembly.validate", page)
        self.assertIn("虛構", page)
        self.assertNotIn("guard-offline-v5", page)
        self.assertIn(self.data["wasm_sha256"], page)
        self.assertGreater(self.html.stat().st_size, 3000)

    def test_missing_genuine_runtime_proof(self):
        self.data["accepted"] = False
        self.save()
        self.reject()

    def test_untrue_589_claim_rejected(self):
        self.data["full_589_shift_model"] = True
        self.save()
        self.reject()

    def test_untrue_operational_claim_rejected(self):
        self.data["operationally_certified"] = True
        self.save()
        self.reject()

    def test_wrong_or_missing_scenario_rejected(self):
        self.data["tests"].pop()
        self.save()
        self.reject()

    def test_duplicate_scenarios_rejected(self):
        self.data["tests"][1] = self.data["tests"][0]
        self.save()
        self.reject()

    def test_wrong_wasm_sha_rejected(self):
        self.wasm.write_bytes(self.wasm.read_bytes() + b"altered")
        self.reject()

    def test_wrong_glue_sha_rejected(self):
        self.js.write_bytes(self.js.read_bytes() + b"altered")
        self.reject()

    def test_wrong_max_fill_rejected(self):
        self.data["tests"][0]["got_filled"] = 3
        self.save()
        self.reject()

    def test_wrong_oracle_rejected(self):
        self.data["tests"][0]["oracle_max_fill"] = 2
        self.save()
        self.reject()


if __name__ == "__main__":
    unittest.main()
