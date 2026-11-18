"""Invented-only end-to-end orchestration: forbid false operational approval.

Runs without binary/OR-Tools/CI; the genuine WASM integration remains a
separate, explicit local demo or manually approved release gate.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from solver.phase20_synthetic_rollover import RolloverError
from tools.fictional_offline_pipeline import (
    fictional_sparse_handoff, sanitize_and_audit, run_local, main,
)


class FictionalOfflinePipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.handoff = fictional_sparse_handoff()
        cls.valid = {}
        for pool, frame in cls.handoff["frames"].items():
            pin = list(map(int, frame["wire"].splitlines()[5].split(",")))
            result = [person if person >= 0 else -1 for person in pin]
            count = sum(person >= 0 for person in result)
            cls.valid[pool] = {
                "status": "FEASIBLE", "assignments": result,
                "filled": count, "missing": len(result)-count,
            }

    def test_01_real_full_month_rows_and_only_fictional_ids(self):
        self.assertEqual(self.handoff["frames"]["door"]["shift_count"], 372)
        self.assertEqual(self.handoff["frames"]["officer"]["shift_count"], 217)
        self.assertEqual(self.handoff["frames"]["door"]["staff_count"], 56)
        self.assertEqual(self.handoff["frames"]["officer"]["staff_count"], 50)
        for pool, bits in (("door", 12), ("officer", 7)):
            lines = self.handoff["frames"][pool]["wire"].splitlines()
            self.assertEqual(len(lines), 8)
            self.assertEqual(lines[4].count("1"), bits)
            self.assertNotIn("SIM_", self.handoff["frames"][pool]["wire"])

    def test_02_pin_only_results_pass_real_independent_cross_month_audit(self):
        value = sanitize_and_audit(self.handoff, deepcopy(self.valid))
        self.assertEqual(value["outcome"], "SYNTHETIC_FEASIBLE_NOT_OPERATIONAL")
        self.assertEqual(value["staffed"], 2)
        self.assertEqual(value["unfilled"], 587)
        self.assertTrue(value["independent_november_december_audit"])
        self.assertFalse(value["genuine_local_wasm_runtime_verified"])

    def test_03_unknown_is_blocked_without_any_schedule(self):
        answers = deepcopy(self.valid)
        answers["officer"] = {"status": "UNKNOWN"}
        result = sanitize_and_audit(self.handoff, answers)
        self.assertEqual(result["outcome"], "BLOCKED")
        self.assertFalse(result["solver_assignments_accepted"])
        self.assertIsNone(result["staffed"])
        self.assertNotIn("pool_staffed", result)
        self.assertNotIn("assignments", result)

    def test_03b_unknown_with_fabricated_assignments_rejected(self):
        answers = deepcopy(self.valid)
        answers["officer"] = {"status": "UNKNOWN", "assignments": [0]}
        with self.assertRaisesRegex(RolloverError, "Non-solution"):
            sanitize_and_audit(self.handoff, answers)

    def test_04_missing_duty_pool_is_rejected(self):
        with self.assertRaisesRegex(RolloverError, "Both solver pools"):
            sanitize_and_audit(self.handoff, {"door": self.valid["door"]})

    def test_05_fake_feasible_with_illegal_person_rejected(self):
        answers = deepcopy(self.valid)
        answers["door"]["assignments"][0] = 0
        answers["door"]["filled"] += 1
        answers["door"]["missing"] -= 1
        with self.assertRaises(RolloverError):
            sanitize_and_audit(self.handoff, answers)

    def test_06_forged_fill_count_rejected(self):
        answers = deepcopy(self.valid)
        answers["officer"]["filled"] += 1
        with self.assertRaises(RolloverError):
            sanitize_and_audit(self.handoff, answers)

    def test_07_source_digest_tampering_rejected(self):
        hacked = deepcopy(self.handoff)
        hacked["original_sources"][3][0]["start"] = "2026-12-20"
        with self.assertRaisesRegex(RolloverError, "changed"):
            sanitize_and_audit(hacked, self.valid)

    def test_08_summary_leaves_all_release_flags_false(self):
        data = sanitize_and_audit(self.handoff, self.valid)
        for flag in ("operationally_certified", "importable_as_v7_backup",
                     "real_v7_inputSig_verified", "full_v7_rule_parity_verified",
                     "real_iphone_safari_verified", "optimality_independently_proven"):
            self.assertFalse(data[flag])
        blob = json.dumps(data)
        self.assertNotIn("SIM_", blob)
        self.assertNotIn("assignments", data)

    def test_09_missing_or_untrusted_wasm_refused_without_output(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            digest = "0"*64
            with self.assertRaisesRegex(RolloverError, "absent"):
                run_local(p/"no.js", p/"no.wasm", p/"no.json", digest)
            with self.assertRaisesRegex(RolloverError, "trusted"):
                run_local(p/"no.js", p/"no.wasm", p/"no.json", "broken")

    def test_10_modified_wasm_refused_before_loading_js(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            a,b,c = p/"a.js",p/"b.wasm",p/"proof.json"
            for f in (a,b,c):
                f.write_text("tamper", encoding="utf-8")
            with self.assertRaisesRegex(RolloverError, "differs"):
                run_local(a,b,c,"0"*64)

    def test_11_cli_missing_proof_never_creates_report(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            file=p/"report.json"
            result=main(["--wasm-js",str(p/"no.js"),
                "--wasm-bin",str(p/"no.wasm"),"--proof",str(p/"no.json"),
                "--trusted-wasm-sha256","0"*64,"--output",str(file)])
            self.assertEqual(result,2)
            self.assertFalse(file.exists())

    def test_12_repeatable_fictional_source_digest(self):
        other=fictional_sparse_handoff()
        self.assertEqual(self.handoff["frames"],other["frames"])
        self.assertEqual(self.handoff["anchors"],other["anchors"])


if __name__ == "__main__":
    unittest.main()
