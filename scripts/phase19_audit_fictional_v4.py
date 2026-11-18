#!/usr/bin/env python3
"""Reconstruct invented event rules and independently re-audit real WASM output."""
import json
from pathlib import Path

from solver.phase19_fictional_v7_hard_rules import (
    SOURCE, CONTRACT, create_case, audit_genuine_result)

path=Path("phase19_fictional_wasm_output.json")
raw=json.loads(path.read_text(encoding="utf-8"))
assert raw["source"]==SOURCE and raw["contract"]==CONTRACT
assert raw["synthetic_only"] is True
assert raw["genuine_cpp_wasm_executed"] is True
assert raw["operationally_certified"] is False
assert raw["full_v7_rule_parity_verified"] is False
assert len(raw["cases"])==2
assert {item["pool"] for item in raw["cases"]}=={"door","officer"}
summary=[]
for item in raw["cases"]:
    case=create_case(item["pool"])
    assert item["frame_sha256"]==case["sha256"]
    assert item["shifts"]==case["shifts"]
    assert item["staff"]==case["staff"]
    inspected=audit_genuine_result(case,item["result"])
    assert inspected["independently_verified_feasible"] is True
    assert inspected["operationally_certified"] is False
    assert inspected["history_freshness_verified_for_real_data"] is False
    summary.append({
        "pool":item["pool"],"shifts":item["shifts"],
        "filled":inspected["filled"],"missing":inspected["missing"],
        "frame_sha256":case["sha256"],
        "independently_audited_against_original_fictional_events":True,
        "operationally_certified":False,
    })
assert sum(x["shifts"] for x in summary)==589
output={
    "accepted":True,
    "source":SOURCE,
    "genuine_cpp_wasm_run":True,
    "independent_python_hard_rule_reaudit":True,
    "fictional_full_month_shifts":589,
    "real_iphone_safari_tested":False,
    "full_v7_rule_parity_verified":False,
    "operationally_certified":False,
    "cases":summary,
}
Path("phase19_fictional_rules_proof.json").write_text(
    json.dumps(output,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
print(json.dumps(output,indent=2,ensure_ascii=True))
