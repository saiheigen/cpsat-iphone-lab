"""Local-only, deliberately NON-IMPORTABLE v7 preview export.

It preserves the v7 schedule row shape [unix_day_number, slot_number, personID]
but NEVER emits a guard-offline-v5 backup or modifies a saved/locked month.
No transfer, network, browser state, or real personnel data.

Unsafe to treat as an approved operational roster. Current native solver is
a partial rules model; definitive duty audit and approval remain external.
"""
from __future__ import annotations

from datetime import date
from typing import Mapping

from solver.roster_cp_sat import independently_check, month_shifts

_EPOCH = date(1970, 1, 1)


def preview_v7_shape(bridge, solver_output):
    """Validate and convert an independently audited schedule to preview only.

    Input bridge is BridgeResult from convert_v7_backup, solver_output is the
    native split-fill result. The result must be a complete *mapping* of all
    shift keys including explicit None for vacancies; never fabricate gaps.
    """
    if getattr(bridge, "operationally_certified", False):
        raise ValueError("Bridge should never claim operational certification")
    if not isinstance(solver_output, dict):
        raise ValueError("Expected solver result mapping")
    chosen = solver_output.get("assignments")
    if not isinstance(chosen, dict):
        raise ValueError("No complete solution from native solver")
    if not isinstance(bridge.tasks, list) or len({t.key for t in bridge.tasks}) != len(bridge.tasks):
        raise ValueError("Duplicate or malformed roster shifts")
    if len({p.id for p in bridge.people}) != len(bridge.people):
        raise ValueError("Duplicate person IDs")
    independently_check(
        bridge.tasks, bridge.people, chosen,
        bridge.events, bridge.history, bridge.pins)
    filled = sum(v is not None for v in chosen.values())
    missing = len(bridge.tasks) - filled
    if solver_output.get("filled") != filled or solver_output.get("missing") != missing:
        raise ValueError("Solver metrics do not match independently audited schedule")
    expected_month = bridge.month
    try:
        year, month = map(int, expected_month.split("-"))
        reference = month_shifts(year, month)
    except (AttributeError, TypeError, ValueError):
        raise ValueError("Invalid preview month") from None
    if {t.key for t in bridge.tasks} != {t.key for t in reference}:
        raise ValueError("Preview must contain the entire month; partial grids rejected")
    status = solver_output.get("status")
    proof = bool(solver_output.get("optimal_fill_proven", False))
    if status not in ("FULL", "PARTIAL_OPTIMAL", "PARTIAL_FEASIBLE"):
        raise ValueError("Unsupported or incomplete solver result status")
    if (status == "FULL") != (missing == 0):
        raise ValueError("FULL status contradicts occupancy")
    if (status == "PARTIAL_OPTIMAL") != (proof and missing > 0):
        if status == "PARTIAL_OPTIMAL" or (proof and missing > 0):
            raise ValueError("Partial optimality flag and status disagree")
    schedule = {"door": [], "officer": []}
    for t in bridge.tasks:
        day_serial = (t.day - _EPOCH).days
        schedule[t.pool].append([day_serial, t.num, chosen[t.key]])
    for pool in ("door", "officer"):
        expected = sum(t.pool == pool for t in bridge.tasks)
        if len(schedule[pool]) != expected:
            raise AssertionError("Missing v7 schedule rows for pool")
    return {
        # Different tag from guard-offline-v5 on purpose: never restore this
        # preview as an application backup and overwrite an approved roster.
        "format": "guard-cpsat-preview-v1",
        "preview_only": True,
        "month": expected_month,
        "source": "native-partial-cp-sat-model",
        "importable_as_v7_backup": False,
        "operationally_certified": False,
        "cross_month_confirmed": bridge.cross_month_confirmed,
        "compensation_confirmed": bridge.compensation_confirmed,
        "status": solver_output["status"],
        "fill_optimal_proven_for_subset": bool(
            solver_output.get("optimal_fill_proven", False)),
        "filled": filled,
        "missing": missing,
        "schedule": schedule,
        "warnings": list(bridge.warnings) + [
            "預覽用資料：尚未與 v7.0 正式網站逐條驗證，不可直接當成已核定班表。",
            "未完成完整跨月規格、業參、公平補償與 iPhone WASM 實機驗收。",
        ],
    }
