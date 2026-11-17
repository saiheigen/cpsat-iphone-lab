#!/usr/bin/env python3
"""Real CP-SAT smoke test on native Linux. Does not validate browser or WASM."""
import json
import sys
from ortools.sat.python import cp_model

model = cp_model.CpModel()
x = model.new_int_var(0, 3, "x")
y = model.new_int_var(0, 3, "y")
model.add(x + y <= 3)
model.maximize(2*x + 3*y)

solver = cp_model.CpSolver()
solver.parameters.num_search_workers = 1
solver.parameters.max_time_in_seconds = 15.0
status = solver.solve(model)

result = {
    "runtime": "linux-native-ortools-python",
    "status": solver.status_name(status),
    "objective": solver.objective_value if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
    "x": solver.value(x) if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
    "y": solver.value(y) if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
    "is_real_cpsat": True,
    "proves_wasm": False,
    "proves_iphone": False,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
assert status == cp_model.OPTIMAL, f"Expected OPTIMAL, got {result['status']}"
assert (solver.value(x), solver.value(y), round(solver.objective_value)) == (0, 3, 9)
