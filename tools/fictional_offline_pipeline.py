"""Reproducible, fictional-only local source -> genuine WASM -> reverse audit.

Never accepts operational roster files, personnel, dates or arbitrary source
payloads. The fixed synthetic fixture is intentionally SPARSE, so this is a
pipeline integration check rather than a dense-month performance benchmark.
Run from the repository root:
  python -m tools.fictional_offline_pipeline --wasm-js <module.js> \
      --wasm-bin <module.wasm> --proof <proof.json> \
      --trusted-wasm-sha256 <independently trusted digest> --output <local.json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from solver.phase20_synthetic_rollover import RolloverError, _digest, _COUNTS
from solver.phase22_synthetic_solver_handoff import (
    fictional_source_fixture, build_fictional_handoff,
    audit_fictional_solver_response,
)

_ROOT = Path(__file__).resolve().parents[1]
_RUNNER = _ROOT / "integration" / "fictional_genuine_wasm_runner.cjs"
_FORMAT = "fictional-v4-local-e2e-evidence-v1"
_VALID = {"FEASIBLE", "OPTIMAL"}


def fictional_sparse_handoff():
    """Anchor a tiny but complete 589-row case, not an operational input API.

    Only fictional fixed staff retain one in-month workday; all other
    candidates are blocked by additional *fictional* full exemptions. This
    exercises leave, carry, event encoding and legal pinned duties without a
    20-second dense optimization, and is intentionally NOT full coverage.
    """
    prior, archived, upcoming, events, pins, anchors = fictional_source_fixture()
    for pool, people in upcoming["pools"].items():
        for item in people:
            ident = item["id"]
            only = 7 if ident == "SIM_D_048" else 5 if ident == "SIM_O_048" else None
            blocks = ((1, 31),) if only is None else ((1, only - 1), (only + 1, 31))
            for first, last in blocks:
                if first <= last:
                    events.append({
                        "pool": pool, "person": ident, "kind": "exempt_all",
                        "start": f"2026-12-{first:02d}",
                        "end": f"2026-12-{last:02d}",
                    })
    anchors["events"] = _digest(events)
    handoff = build_fictional_handoff(
        prior, archived, upcoming, events, pins, expected_anchors=anchors)
    for pool, width in (("door", 56), ("officer", 50)):
        frame = handoff["frames"][pool]
        lines = frame["wire"].splitlines()
        if (frame["staff_count"] != width or
                frame["shift_count"] != 31 * _COUNTS[pool] or
                (lines[4].count("1") != (12 if pool == "door" else 7))):
            raise RolloverError("Unexpected invented fixture geometry")
    return handoff


def sanitize_and_audit(handoff, solver_results, *, genuine_runtime_verified=False):
    """Never display raw staff indices; refuse UNKNOWN and forged assignments.

    genuine_runtime_verified is supplied only by the local runner after
    verifying the WASM runtime and hash. No JSON status alone proves that.
    """
    if type(solver_results) is not dict or set(solver_results) != set(_COUNTS):
        raise RolloverError("Both solver pools must be present")
    statuses = {}
    for pool in _COUNTS:
        item = solver_results[pool]
        if type(item) is not dict or type(item.get("status")) is not str:
            raise RolloverError("Malformed solver response")
        statuses[pool] = item["status"]
        if statuses[pool] not in _VALID and "assignments" in item:
            raise RolloverError("Non-solution status must not include assignments")
    if any(status not in _VALID for status in statuses.values()):
        return {
            "format": _FORMAT, "synthetic_only": True, "outcome": "BLOCKED",
            "statuses": statuses, "solver_assignments_accepted": False,
            "genuine_local_wasm_runtime_verified": genuine_runtime_verified is True,
            "independent_november_december_audit": False,
            "staffed": None, "unfilled": None, "operationally_certified": False,
            "importable_as_v7_backup": False,
            "real_v7_inputSig_verified": False,
            "full_v7_rule_parity_verified": False,
        }
    cleaned = {}
    for pool in _COUNTS:
        item = solver_results[pool]
        if not all(key in item for key in ("status", "assignments", "filled", "missing")):
            raise RolloverError("Solver claims a solution without an entire calendar")
        cleaned[pool] = {key: item[key] for key in
                         ("status", "assignments", "filled", "missing")}
    validated = audit_fictional_solver_response(handoff, cleaned)
    return {
        "format": _FORMAT, "synthetic_only": True,
        "outcome": "SYNTHETIC_FEASIBLE_NOT_OPERATIONAL",
        "statuses": statuses,
        "solver_assignments_accepted": True,
        "genuine_local_wasm_runtime_verified": genuine_runtime_verified is True,
        "independent_november_december_audit": validated["independent_full_month_legality_audit"],
        "staffed": validated["filled"], "unfilled": validated["missing"],
        "pool_staffed": validated["by_pool"],
        "month_rows": validated["total_shifts"],
        "optimality_independently_proven": False,
        "operationally_certified": False,
        "importable_as_v7_backup": False,
        "real_v7_inputSig_verified": False,
        "full_v7_rule_parity_verified": False,
        "real_iphone_safari_verified": False,
    }


def run_local(wasm_js: Path, wasm_bin: Path, proof: Path, expected_sha: str):
    if not re.fullmatch(r"[a-f0-9]{64}", expected_sha):
        raise RolloverError("Expected a separately trusted 64-character WASM SHA256")
    for path in (wasm_js, wasm_bin, proof):
        if not path.is_file():
            raise RolloverError("Required local WASM/proof file is absent")
    if hashlib.sha256(wasm_bin.read_bytes()).hexdigest() != expected_sha:
        raise RolloverError("Locally supplied WASM differs from independent trusted SHA256")
    handoff = fictional_sparse_handoff()
    frames = {pool: {
        "wire": info["wire"], "sha256": info["sha256"],
    } for pool, info in handoff["frames"].items()}
    request = {
        "synthetic_only": True, "contract": "guard-month-harsh-v4",
        "frames": frames, "trusted_wasm_sha256": expected_sha,
    }
    try:
        proc = subprocess.run([
            "node", str(_RUNNER), str(wasm_js.resolve()), str(wasm_bin.resolve()),
            str(proof.resolve()),
        ], input=json.dumps(request, ensure_ascii=True), capture_output=True,
            text=True, timeout=90, cwd=_ROOT, check=False)
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise RolloverError("Local genuine WASM invocation failed or exceeded runtime limit") from exc
    if proc.returncode:
        # The Node runner intentionally prints no raw frames on failure.
        raise RolloverError("Local WASM/provenance verification failed")
    try:
        output = json.loads(proc.stdout)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise RolloverError("Invalid local WASM process output") from exc
    if type(output) is not dict or output.get("verified_runtime") is not True or \
            output.get("wasm_sha256") != expected_sha:
        raise RolloverError("WASM output provenance unavailable")
    result = sanitize_and_audit(handoff, output.get("results"),
                                genuine_runtime_verified=True)
    result["wasm_sha256"] = expected_sha
    result["anonymous_input_sha256"] = {
        pool: entry["sha256"] for pool, entry in frames.items()}
    result["provenance_kind"] = "MATCHES_USER_SUPPLIED_TRUSTED_DIGEST_NOT_AUTHENTICATED_SIGNATURE"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wasm-js", type=Path, required=True)
    parser.add_argument("--wasm-bin", type=Path, required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--trusted-wasm-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = run_local(args.wasm_js, args.wasm_bin, args.proof,
                           args.trusted_wasm_sha256)
    except RolloverError as exc:
        print("Synthetic pipeline blocked: " + str(exc), file=sys.stderr)
        return 2
    # Only harmless aggregated invented results go to output; no real names,
    # raw mask, staff indices, events or previous-month roster.
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print("Synthetic local WASM pipeline:", report["outcome"],
          "staffed:", report["staffed"], "unfilled:", report["unfilled"])
    return 0 if report["solver_assignments_accepted"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
