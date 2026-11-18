"""Tests for inexpensive, fail-closed workflow trigger policy."""
import tempfile
import unittest
from pathlib import Path
from tools.check_ci_budget import workflow_events, check_tree

class CiTriggerPolicyTests(unittest.TestCase):
    def test_fast_mapping(self):
        data = "name: CI\non:\n  push:\n    branches: [main]\n  pull_request:\n  workflow_dispatch:\npermissions:\n  contents: read\n"
        self.assertEqual(workflow_events(data), {"push", "pull_request", "workflow_dispatch"})

    def test_nested_input_is_not_event(self):
        data = "on:\n  workflow_dispatch:\n    inputs:\n      source_run_id:\n        required: true\npermissions:\n  contents: read\n"
        self.assertEqual(workflow_events(data), {"workflow_dispatch"})

    def test_implicit_or_unknown_structure_rejected(self):
        for data in ("name: CI\non: workflow_dispatch\n", "on:\n  boom:\n"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                workflow_events(data)

    def test_prohibited_legacy_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "ci-fast.yml").write_text("on:\n  push:\n  pull_request:\n  workflow_dispatch:\n")
            (work / "legacy.yml").write_text("on:\n  workflow_dispatch:\n  workflow_run:\n")
            self.assertTrue(any("legacy.yml" in e for e in check_tree(work)))
            (work / "legacy.yml").write_text("on:\n  workflow_dispatch:\n")
            self.assertEqual(check_tree(work), [])

if __name__ == "__main__":
    unittest.main()
