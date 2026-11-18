"""All fictional; no real device data, military roster or cloud-uploaded report."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import subprocess
import json
import sys
import unittest

MODULE=Path(__file__).resolve().parents[1]/"tools"/"validate_iphone_field_evidence.py"
spec=importlib.util.spec_from_file_location("iphone_field_evidence",MODULE)
validator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

EXPECTED={
    "tiny":(372,4,368),
    "door-blackouts-no-hints":(372,372,0),
    "officer-blackouts-no-hints":(217,217,0),
    "door-forced-vacancies":(372,360,12),
}


def sample(*, scenario_count=4, opener="files-quick-look",
           network="all-radios-off"):
    cases=[]
    for name,(shifts,filled,missing) in list(EXPECTED.items())[:scenario_count]:
        cases.append({
            "scenario":name,"shifts":shifts,"filled":filled,"missing":missing,
            "execution_mode":"dedicated-worker","elapsed_ms":2134,
            "fill_phase":"OPTIMAL","fair_phase":"FEASIBLE",
            "hardship_phase":"UNKNOWN","final_abs_deviation":10,
        })
    return {
        "format":"phase5-synthetic-iphone-selfcheck-v1",
        "generated_at_utc":"2026-11-18T07:00:00.000Z",
        "source":"local_synthetic_webpage_no_transmission",
        "manually_selected_open_method":opener,
        "manually_selected_network_state":network,
        "manual_physical_iphone_confirmation":True,
        "navigator_online_hint":True,
        "document_scheme":"file:",
        "document_origin":"null",
        "browser_hint_from_user_agent":"ios_like",
        "browser_identity_independently_verified":False,
        "physical_iphone_safari_verified":False,
        "operationally_certified":False,
        "full_v7_rule_parity_verified":False,
        "worker_probe":{"status":"ready","wasm_validate":True},
        "observed_main_thread_max_gap_ms":260,
        "main_thread_heartbeat_samples":810,
        "unhandled_script_errors_observed":0,
        "synthetic_cases":cases,
        "synthetic_combined_preview":(
            {"rows":589,"filled":577,"missing":12,
             "importable_as_v7_backup":False,"operationally_certified":False}
            if scenario_count==4 else None),
        "all_four_cases_observed":scenario_count==4,
        "warnings":["All fields are self-reported; not an iPhone certification."],
    }


class FieldEvidenceGateTests(unittest.TestCase):
    def assert_rejected(self, edited):
        with self.assertRaises(validator.EvidenceError):
            validator.validate_evidence(edited)

    def test_files_app_observation_is_not_safari_certification(self):
        summary=validator.validate_evidence(sample())
        self.assertTrue(summary["files_app_opening_reported"])
        self.assertTrue(summary["all_radios_disabled_self_reported"])
        self.assertFalse(summary["safari_app_independently_verified"])
        self.assertFalse(summary["physical_iphone_safari_certified"])
        self.assertFalse(summary["real_offline_independently_verified"])
        self.assertFalse(summary["operationally_certified"])
        self.assertEqual(summary["synthetic_case_count"],4)
        self.assertTrue(summary["synthetic_combined_589_preview_reported"])
        self.assertNotIn("document_origin",summary)

    def test_even_explicit_safari_selection_cannot_certify_device(self):
        summary=validator.validate_evidence(sample(opener="physical-safari"))
        self.assertTrue(summary["safari_app_opening_self_reported"])
        self.assertFalse(summary["physical_iphone_safari_certified"])

    def test_partial_report_allowed_but_not_complete(self):
        report=sample(scenario_count=1, network="unknown")
        out=validator.validate_evidence(report)
        self.assertEqual(out["synthetic_case_count"],1)
        self.assertFalse(out["synthetic_combined_589_preview_reported"])
        self.assertFalse(out["all_radios_disabled_self_reported"])

    def test_empty_diagnostic_allowed(self):
        self.assertEqual(validator.validate_evidence(sample(scenario_count=0))
                         ["synthetic_case_count"],0)

    def test_reject_false_safari_certification(self):
        report=sample()
        report["physical_iphone_safari_verified"]=True
        self.assert_rejected(report)

    def test_reject_false_v7_certification(self):
        report=sample()
        report["full_v7_rule_parity_verified"]=True
        self.assert_rejected(report)

    def test_reject_importable_preview(self):
        report=sample()
        report["synthetic_combined_preview"]["importable_as_v7_backup"]=True
        self.assert_rejected(report)

    def test_reject_extra_personnel_or_roster_fields(self):
        for key in ("assignments","people","names","availability_mask","raw_schedule"):
            report=sample()
            report[key]=["do not upload this"]
            self.assert_rejected(report)

    def test_reject_extra_case_personnel_field(self):
        report=sample()
        report["synthetic_cases"][0]["person_id"]="SIM_D_001"
        self.assert_rejected(report)

    def test_reject_wrong_month_counts(self):
        report=sample()
        report["synthetic_cases"][1]["filled"]=371
        self.assert_rejected(report)

    def test_reject_duplicate_scenarios(self):
        report=sample()
        report["synthetic_cases"][1]=deepcopy(report["synthetic_cases"][0])
        self.assert_rejected(report)

    def test_reject_false_completed_gate(self):
        report=sample(scenario_count=1)
        report["all_four_cases_observed"]=True
        self.assert_rejected(report)

    def test_reject_combined_without_both_pools(self):
        report=sample(scenario_count=1)
        report["synthetic_combined_preview"]=sample()["synthetic_combined_preview"]
        self.assert_rejected(report)

    def test_reject_boolean_as_shift_count(self):
        report=sample()
        report["synthetic_cases"][0]["shifts"]=True
        self.assert_rejected(report)

    def test_reject_unbounded_or_invalid_elapsed(self):
        report=sample()
        report["synthetic_cases"][0]["elapsed_ms"]=-1
        self.assert_rejected(report)
        report["synthetic_cases"][0]["elapsed_ms"]=4_000_000
        self.assert_rejected(report)

    def test_reject_unknown_worker_state(self):
        report=sample()
        report["worker_probe"]["status"]="magically_passed"
        self.assert_rejected(report)

    def test_reject_unrecognized_document_type(self):
        report=sample()
        report["format"]="guard-offline-v5"
        self.assert_rejected(report)

    def test_reject_unknown_opening_method(self):
        report=sample()
        report["manually_selected_open_method"]="auto-verified"
        self.assert_rejected(report)

    def test_reject_invalid_timestamp(self):
        report=sample()
        report["generated_at_utc"]="2026-99-99T77:88:00Z"
        self.assert_rejected(report)

    def test_cli_local_valid_report_only_emits_redacted_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"fictional_phone.json"
            file.write_text(json.dumps(sample(),ensure_ascii=False),
                            encoding="utf-8")
            process=subprocess.run([sys.executable,str(MODULE),str(file)],
                                   capture_output=True,text=True,check=False)
            self.assertEqual(process.returncode,0,process.stderr)
            result=json.loads(process.stdout)
            self.assertFalse(result["physical_iphone_safari_certified"])
            self.assertEqual(result["synthetic_case_count"],4)
            self.assertNotIn("document_origin",process.stdout)
            self.assertNotIn("generated_at_utc",process.stdout)

    def test_cli_does_not_echo_raw_personnel_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"unsafe.json"
            report=sample()
            report["real_name"]="SECRET_DO_NOT_PRINT"
            file.write_text(json.dumps(report),encoding="utf-8")
            proc=subprocess.run([sys.executable,str(MODULE),str(file)],
                                capture_output=True,text=True,check=False)
            self.assertNotEqual(proc.returncode,0)
            self.assertNotIn("SECRET_DO_NOT_PRINT",proc.stderr)
            self.assertNotIn("SECRET_DO_NOT_PRINT",proc.stdout)


if __name__=="__main__":
    unittest.main()
