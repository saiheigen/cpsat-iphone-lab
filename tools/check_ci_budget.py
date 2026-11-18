"""Stdlib-only policy: a single fast CI, all expensive pipelines manual.

This guards the repository trigger policy, NOT the GitHub account budget.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

_TRIGGERS = {"push", "pull_request", "pull_request_target", "schedule",
             "workflow_run", "workflow_dispatch", "repository_dispatch"}

def workflow_events(text: str) -> set[str]:
    match = re.search(r"(?m)^on:\s*\n((?:[ \t]+[^\n]*\n|\s*\n|#[^\n]*\n)*)", text)
    if match is None:
        raise ValueError("Expected top-level on: YAML event mapping")
    events = set(re.findall(r"(?m)^  ([a-z_]+):(?:\s|$)", match.group(1)))
    if not events or events - _TRIGGERS:
        raise ValueError("Unexpected or absent workflow event declaration")
    return events

def check_tree(directory: Path) -> list[str]:
    files = sorted(directory.glob("*.yml"))
    errors = []
    if not files:
        return ["No workflows to validate"]
    if not (directory / "ci-fast.yml").exists():
        errors.append("Missing designated fast CI workflow")
    for path in files:
        try:
            events = workflow_events(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        expected = ({"push", "pull_request", "workflow_dispatch"}
                    if path.name == "ci-fast.yml" else {"workflow_dispatch"})
        if events != expected:
            errors.append(f"{path.name}: {sorted(events)} != {sorted(expected)}")
    return errors

def main() -> int:
    path = Path(__file__).resolve().parents[1] / ".github" / "workflows"
    errors = check_tree(path)
    if errors:
        for error in errors:
            print("CI policy error:", error, file=sys.stderr)
        return 1
    print("Budget-safe workflow trigger policy OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
