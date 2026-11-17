"""Packaging gate unit tests only; no fabricated result is treated as real CP-SAT."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "build" / "package_iphone_cp_sat.py"
spec = importlib.util.spec_from_file_location("iphone_packager", SCRIPT)
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)

class PackageGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.js = root / "solver.js"
        self.wasm = root / "solver.wasm"
        self.report = root / "node.json"
        # Deliberately synthetic fixture. No CP-SAT executable is used here.
        self.js.write_bytes(b"var createCPSatModule=function(){};")
        self.wasm.write_bytes(b"\x00asm\x01\x00\x00\x00")
        self.obj = {
            "accepted": True,
            "solver": {"engine":"Google OR-Tools CP-SAT","status":"OPTIMAL",
                       "desks":0,"tables":3,"profit":90},
            "oracle": {"profit":90,"winners":[{"d":0,"t":3}]},
            "js_sha256": hashlib.sha256(self.js.read_bytes()).hexdigest(),
            "wasm_sha256": hashlib.sha256(self.wasm.read_bytes()).hexdigest()
        }
        self.save()

    def save(self):
        self.report.write_text(json.dumps(self.obj),encoding="utf-8")

    def check_rejected(self):
        with self.assertRaises(ValueError):
            pack.verify(self.js,self.wasm,self.report)

    def test_missing_accepted(self):
        self.obj["accepted"]=False;self.save();self.check_rejected()

    def test_wasm_hash_mismatch(self):
        self.wasm.write_bytes(self.wasm.read_bytes()+b"changed")
        self.check_rejected()

    def test_js_hash_mismatch(self):
        self.js.write_bytes(self.js.read_bytes()+b"changed")
        self.check_rejected()

    def test_wrong_objective(self):
        self.obj["solver"]["profit"]=89;self.save();self.check_rejected()

    def test_wrong_oracle(self):
        self.obj["oracle"]["winners"]=[{"d":3,"t":0}]
        self.save();self.check_rejected()

    def test_invalid_wasm_header(self):
        self.wasm.write_bytes(b"not a real wasm")
        self.check_rejected()

    def test_missing_factory(self):
        self.js.write_bytes(b"var somethingElse=function(){};")
        self.check_rejected()

    def test_structure_of_packaged_page_only(self):
        # Tests HTML rendering mechanics using a fake input fixture.
        # It proves neither the CP-SAT native solver nor iPhone execution.
        out=Path(self.tmp.name)/"phone.html"
        pack.main([str(self.js),str(self.wasm),str(self.report),str(out)])
        data=out.read_text("utf-8")
        self.assertIn("iphone",data.lower())
        self.assertIn("createCPSatModule",data)
        self.assertIn(self.obj["wasm_sha256"],data)
        self.assertIn("本機",data)

if __name__=="__main__":
    unittest.main()
