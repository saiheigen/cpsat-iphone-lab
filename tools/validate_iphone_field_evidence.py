#!/usr/bin/env python3
"""Validate a *self-reported* local synthetic iPhone WASM test JSON.

This tool never accepts live rosters, eligibility matrices, military records,
a v7 backup, or a declaration that physical Safari has been independently
certified. It does not connect to a network or save the submitted report.
Run locally; do NOT upload a user's report into public/cloud GitHub CI.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

CASES = {
    "tiny": (372, 4, 368),
    "door-blackouts-no-hints": (372, 372, 0),
    "officer-blackouts-no-hints": (217, 217, 0),
    "door-forced-vacancies": (372, 360, 12),
}
TOP_FIELDS = frozenset({
    "format", "generated_at_utc", "source",
    "manually_selected_open_method", "manually_selected_network_state",
    "manual_physical_iphone_confirmation", "navigator_online_hint",
    "document_scheme", "document_origin", "browser_hint_from_user_agent",
    "browser_identity_independently_verified", "physical_iphone_safari_verified",
    "operationally_certified", "full_v7_rule_parity_verified",
    "worker_probe", "observed_main_thread_max_gap_ms",
    "main_thread_heartbeat_samples", "unhandled_script_errors_observed",
    "synthetic_cases", "synthetic_combined_preview",
    "all_four_cases_observed", "warnings",
})
CASE_FIELDS = frozenset({
    "scenario", "shifts", "filled", "missing", "execution_mode",
    "elapsed_ms", "fill_phase", "fair_phase", "hardship_phase",
    "final_abs_deviation",
})
COMBINED_FIELDS = frozenset({
    "rows", "filled", "missing", "importable_as_v7_backup",
    "operationally_certified",
})
PROBE_FIELDS = frozenset({"status", "wasm_validate"})

class EvidenceError(ValueError):
    """A report fails the schema or contradicts its own synthetic results."""


def require(condition: bool, message: str):
    if not condition:
        raise EvidenceError(message)


def shape(obj, fields: frozenset[str], name: str):
    require(type(obj) is dict, name + " must be an object")
    unknown = set(obj) - fields
    require(not unknown, name + " contains unknown or unsafe fields: " +
            ", ".join(sorted(unknown)[:5]))


def integer(value, name: str, *, minimum: int = 0, maximum: int = 2_000_000):
    require(type(value) is int and minimum <= value <= maximum,
            name + " must be a bounded integer")


def validate_evidence(report: dict) -> dict:
    """Return a *redacted summary* without ever certifying Safari or v7."""
    shape(report, TOP_FIELDS, "report")
    require(report.get("format") == "phase5-synthetic-iphone-selfcheck-v1",
            "unsupported self-check report version")
    require(report.get("source") == "local_synthetic_webpage_no_transmission",
            "report is not the local synthetic self-check")
    for field in ("browser_identity_independently_verified",
                  "physical_iphone_safari_verified",
                  "operationally_certified", "full_v7_rule_parity_verified"):
        require(report.get(field) is False, field + " must remain false")
    for field in ("manual_physical_iphone_confirmation", "navigator_online_hint",
                  "all_four_cases_observed"):
        require(type(report.get(field)) is bool, field + " must be boolean")
    require(report.get("manually_selected_open_method") in {
        "unknown", "physical-safari", "files-quick-look",
        "embedded-webview", "other-browser",
    }, "invalid manually selected opener")
    require(report.get("manually_selected_network_state") in {
        "unknown", "all-radios-off", "connected",
    }, "invalid manually selected network state")
    require(report.get("document_scheme") in {
        "file:", "about:", "data:", "blob:", "http:", "https:",
    }, "invalid document scheme")
    origin = report.get("document_origin")
    require(type(origin) is str and 0 < len(origin) <= 255,
            "missing or oversized document origin")
    require(report.get("browser_hint_from_user_agent") in {
        "ios_like", "other_or_unknown",
    }, "unknown browser hint")
    timestamp = report.get("generated_at_utc")
    require(type(timestamp) is str and len(timestamp) <= 60, "invalid timestamp")
    try:
        utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        require(utc.tzinfo is not None, "timestamp timezone missing")
    except (ValueError, OverflowError) as error:
        raise EvidenceError("invalid timestamp") from error
    require(utc.astimezone(timezone.utc).year >= 2026,
            "timestamp is outside this test series")
    for field in ("observed_main_thread_max_gap_ms",
                  "main_thread_heartbeat_samples",
                  "unhandled_script_errors_observed"):
        integer(report.get(field), field)
    probe = report.get("worker_probe")
    shape(probe, PROBE_FIELDS, "worker probe")
    require(probe.get("status") in {
        "not_run", "ready", "unavailable", "invalid_response",
        "error", "timeout", "exception",
    }, "unrecognized Worker probe status")
    require(type(probe.get("wasm_validate")) is bool,
            "Worker probe WASM validation must be boolean")

    cases = report.get("synthetic_cases")
    require(type(cases) is list and len(cases) <= len(CASES),
            "only four synthetic scenarios are allowed")
    accepted = set()
    modes = {}
    for i, item in enumerate(cases):
        shape(item, CASE_FIELDS, "scenario " + str(i))
        name = item.get("scenario")
        require(type(name) is str and name in CASES,
                "unknown or non-synthetic scenario")
        require(name not in accepted, "duplicate scenario " + name)
        accepted.add(name)
        for field, expected in zip(("shifts", "filled", "missing"), CASES[name]):
            require(type(item.get(field)) is int and item[field] == expected,
                    name + ": incorrect " + field)
        mode = item.get("execution_mode")
        require(mode in ("dedicated-worker", "main-thread-fallback"),
                name + ": invalid execution mode")
        modes[name] = mode
        integer(item.get("elapsed_ms"), name + ": elapsed_ms",
                minimum=0, maximum=3_600_000)
        integer(item.get("final_abs_deviation"),
                name + ": final_abs_deviation", maximum=1_000_000_000)
        for key in ("fill_phase", "fair_phase", "hardship_phase"):
            phase = item.get(key)
            require(type(phase) is str and 0 < len(phase) <= 40,
                    name + ": missing " + key)
    complete = len(accepted) == 4
    require(report.get("all_four_cases_observed") is complete,
            "all_four_cases_observed contradicts captured scenario count")

    combined = report.get("synthetic_combined_preview")
    if combined is not None:
        shape(combined, COMBINED_FIELDS, "combined preview")
        for field, expected in (("rows", 589), ("filled", 577), ("missing", 12)):
            require(type(combined.get(field)) is int and combined[field] == expected,
                    "combined preview has incorrect " + field)
        require(combined.get("importable_as_v7_backup") is False,
                "combined preview must not be importable")
        require(combined.get("operationally_certified") is False,
                "combined preview must remain uncertified")
        require({"door-forced-vacancies", "officer-blackouts-no-hints"} <= accepted,
                "combined preview lacks both constituent solver cases")
    warnings = report.get("warnings")
    require(type(warnings) is list and len(warnings) <= 10 and
            all(type(w) is str and len(w) <= 250 for w in warnings),
            "missing or unsafe safety warnings")
    opener = report["manually_selected_open_method"]
    network = report["manually_selected_network_state"]
    return {
        "evidence_type": "self_reported_synthetic_device_observation",
        "source_report_schema_valid": True,
        "synthetic_case_count": len(accepted),
        "synthetic_case_ids": sorted(accepted),
        "expected_synthetic_counts_match": True,
        "synthetic_combined_589_preview_reported": combined is not None,
        "worker_probe_reported_ready": probe["status"] == "ready",
        "worker_modes": modes,
        "files_app_opening_reported": opener == "files-quick-look",
        "safari_app_opening_self_reported": opener == "physical-safari",
        "physical_iphone_self_reported":
            report["manual_physical_iphone_confirmation"],
        "all_radios_disabled_self_reported": network == "all-radios-off",
        "real_offline_independently_verified": False,
        "safari_app_independently_verified": False,
        "physical_iphone_safari_certified": False,
        "operationally_certified": False,
        "full_v7_rule_parity_verified": False,
        "requires_manual_device_review": True,
        "note": ("This validates self-reported fictional counts and schema. "
                 "It does NOT independently verify the iPhone, network state, "
                 "browser identity, on-device WASM provenance or a real roster."),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="local self-check JSON; not a v7 backup")
    args = parser.parse_args()
    try:
        require(args.report.stat().st_size <= 30_000,
                "report exceeds the safe size limit")
        document = json.loads(args.report.read_text(encoding="utf-8"))
        summary = validate_evidence(document)
    except (EvidenceError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print("REJECTED: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
