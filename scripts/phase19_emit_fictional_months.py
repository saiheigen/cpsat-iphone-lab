#!/usr/bin/env python3
"""Generate ONLY two hard-coded imaginary complete-month v4 WASM inputs.

No arguments, no real-world backup import, no network, no PII.
"""
import json
from pathlib import Path

from solver.phase19_fictional_v7_hard_rules import (
    CONTRACT, MONTH, SOURCE, create_case)

cases=[]
for pool in ("door","officer"):
    obj=create_case(pool)
    cases.append({
        "pool":pool,
        "synthetic_only":True,
        "frame":obj["frame"],
        "frame_sha256":obj["sha256"],
        "shifts":obj["shifts"],
        "staff":obj["staff"],
    })
result={
    "contract":CONTRACT,
    "source":SOURCE,
    "month":"%04d-%02d"%MONTH,
    "synthetic_only":True,
    "operationally_certified":False,
    "full_v7_rule_parity_verified":False,
    "cases":cases,
}
Path("phase19_fictional_wasm_input.json").write_text(
    json.dumps(result,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
print(json.dumps({
    "synthetic_only":True,
    "month":result["month"],
    "pools":[{"pool":x["pool"],"shifts":x["shifts"],"staff":x["staff"]}
             for x in cases],
    "no_real_data":True,
},ensure_ascii=True))
