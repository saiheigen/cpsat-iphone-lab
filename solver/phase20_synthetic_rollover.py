"""Budget-safe, synthetic-only v7-style archived-count carry handoff.

No real roster import, network, disk write, v7 inputSig verification, or approval.
SHA256 checks here are integrity fingerprints with an independently supplied
expected digest; they are NOT signatures or proof of archive authenticity.
"""
from __future__ import annotations

from datetime import date, timedelta
import hashlib
import json
import math
import re

from solver.fairness_targets_v7 import (
    FairPerson, base_goals_v7, actual_targets_v7,
    archive_compensation_out_v7, import_prior_locked_carry_v7,
)

_EPOCH = date(1970, 1, 1)
_COUNTS = {"door": 12, "officer": 7}
_ALLOWED_PRIOR = "2026-11"
_ALLOWED_NEXT = "2026-12"
_ID = re.compile(r"^SIM_([DO])_[0-9]{3}$")


class RolloverError(ValueError):
    """Unsafe or inconsistent synthetic source/archive; do not import."""


def _require(cond, message):
    if not cond:
        raise RolloverError(message)


def _digest(obj):
    """Canonical *integrity* fingerprint, not an authentication signature."""
    try:
        raw = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                         allow_nan=False, ensure_ascii=True).encode("ascii")
    except (TypeError, ValueError, OverflowError) as exc:
        raise RolloverError("Invalid synthetic input for fingerprint") from exc
    return hashlib.sha256(raw).hexdigest()


def _source_people(source, *, month):
    _require(type(source) is dict and set(source) ==
             {"format", "month", "revision", "pools"}, "Malformed source")
    _require(source["format"] == "phase20-invented-source-v1" and
             source["month"] == month and
             source["revision"] == "SIMULATION-REV-001", "Wrong source version")
    groups = source["pools"]
    _require(type(groups) is dict and set(groups) == set(_COUNTS),
             "Both imaginary duty pools are required")
    result = {}
    for pool, entries in groups.items():
        _require(type(entries) is list and 1 <= len(entries) <= 100,
                 "Incomplete invented roster")
        expected_prefix = "D" if pool == "door" else "O"
        ids = set()
        output = []
        for item in entries:
            _require(type(item) is dict and set(item) ==
                     {"id", "weight", "availability", "carry_in", "meal_credit"},
                     "Invented roster contains unexpected fields")
            ident = item["id"]
            _require(type(ident) is str and (m := _ID.fullmatch(ident)) is not None
                     and m.group(1) == expected_prefix and ident not in ids,
                     "Unknown, duplicate, or non-synthetic person")
            ids.add(ident)
            weight = item["weight"]
            _require(type(weight) in (float, int) and math.isfinite(weight)
                     and 0 < weight <= 1, "Invalid fictional work weight")
            max_slots = (30 if month == _ALLOWED_PRIOR else 31) * _COUNTS[pool]
            cap = item["availability"]
            _require(type(cap) is int and 0 <= cap <= max_slots,
                     "Invalid fictional slot availability")
            for field in ("carry_in", "meal_credit"):
                val = item[field]
                _require(type(val) is int and 0 <= val <= max_slots,
                         "Invalid fictional credit")
            output.append(FairPerson(ident, float(weight), item["carry_in"],
                                     item["meal_credit"]))
        result[pool] = output
    return result


def _count_synthetic_rows(archive, people):
    schedule = archive.get("schedule")
    _require(type(schedule) is dict and set(schedule) == set(_COUNTS),
             "Missing one pool of previous-month rows")
    counts = {}
    for pool, slots in _COUNTS.items():
        rows = schedule[pool]
        _require(type(rows) is list and len(rows) == 30 * slots,
                 "Previous-month roster is truncated")
        allowed = {p.ident for p in people[pool]}
        found = {ident: 0 for ident in allowed}
        for i, row in enumerate(rows):
            day = i // slots + 1
            expected_serial = (date(2026, 11, day) - _EPOCH).days
            _require(type(row) is list and len(row) == 3 and
                     type(row[0]) is int and row[0] == expected_serial and
                     type(row[1]) is int and row[1] == (i % slots) + 1,
                     "Previous-month shift missing, duplicated, or reordered")
            person = row[2]
            _require(person is None or
                     (type(person) is str and person in allowed),
                     "Wrong-pool or unknown person in prior schedule")
            if person is not None:
                found[person] += 1
        counts[pool] = found
    return counts


def invented_fixture():
    """Generate only fixed, imaginary counts; not a legal-duty witness."""
    def source(month):
        return {
            "format": "phase20-invented-source-v1", "month": month,
            "revision": "SIMULATION-REV-001",
            "pools": {
                pool: [{"id": f"SIM_{prefix}_{i:03}",
                        "weight": 1.0 if i != 2 else 1 / 3,
                        "availability": (30 if month == _ALLOWED_PRIOR else 31)
                        * slots, "carry_in": 1 if pool == "door" and i == 1
                        and month == _ALLOWED_PRIOR else 0,
                        "meal_credit": 1 if pool == "officer" and i == 0
                        and month == _ALLOWED_PRIOR else 0}
                       for i in range(size)]
                for pool, prefix, size, slots in
                (("door", "D", 56, 12), ("officer", "O", 50, 7))
            },
        }
    previous = source(_ALLOWED_PRIOR)
    upcoming = source(_ALLOWED_NEXT)
    people = _source_people(previous, month=_ALLOWED_PRIOR)
    schedule = {}
    for pool, slots in _COUNTS.items():
        members = [p.ident for p in people[pool]]
        schedule[pool] = [
            [(date(2026, 11, i // slots + 1) - _EPOCH).days,
             i % slots + 1, members[i % len(members)]]
            for i in range(30 * slots)
        ]
    # Deliberately reallocate two fictional door positions to create
    # positive count compensation without inventing a real service record.
    for i in (24, 80):
        schedule["door"][i][2] = "SIM_D_000"
    worked = {
        pool: {p.ident: sum(row[2] == p.ident for row in schedule[pool])
               for p in people[pool]}
        for pool in _COUNTS
    }
    goals = {}
    compensated = {}
    for pool, members in people.items():
        avail = {x["id"]: x["availability"]
                 for x in previous["pools"][pool]}
        goals[pool] = base_goals_v7(members, avail, 30 * _COUNTS[pool])
        compensated[pool] = archive_compensation_out_v7(
            members, goals[pool], worked[pool])
    archive = {
        "format": "phase20-invented-locked-archive-v1",
        "month": _ALLOWED_PRIOR, "locked": True,
        "source_digest": _digest(previous),
        "schedule": schedule, "schedule_digest": _digest(schedule),
        "goals": goals, "compensation_out": compensated,
    }
    return previous, archive, upcoming, _digest(archive)


def project_invented_rollover(prior_source, prior_archive, next_source, *,
                               independently_expected_archive_sha256,
                               manual_overrides=None):
    """Refuse stale, unlocked or incomplete fabricated archive before carry.

    Caller MUST independently establish expected snapshot digest. No archive
    authenticity, real-world inputSig or operational permissions are proven.
    """
    people = _source_people(prior_source, month=_ALLOWED_PRIOR)
    next_people = _source_people(next_source, month=_ALLOWED_NEXT)
    for pool in _COUNTS:
        _require([p.ident for p in people[pool]] ==
                 [p.ident for p in next_people[pool]],
                 "Synthetic roster identity/order changed across months")
    _require(type(prior_archive) is dict and set(prior_archive) ==
             {"format", "month", "locked", "source_digest", "schedule",
              "schedule_digest", "goals", "compensation_out"},
             "Incomplete previous-month archive")
    _require(prior_archive["format"] == "phase20-invented-locked-archive-v1"
             and prior_archive["month"] == _ALLOWED_PRIOR,
             "Unrecognized prior archive")
    _require(prior_archive["locked"] is True,
             "Unapproved/unlocked prior month cannot supply carry")
    _require(type(independently_expected_archive_sha256) is str and
             len(independently_expected_archive_sha256) == 64 and
             _digest(prior_archive) == independently_expected_archive_sha256,
             "Archive changed from independently expected digest")
    _require(prior_archive["source_digest"] == _digest(prior_source),
             "Previous-month source changed; archive is stale")
    _require(prior_archive["schedule_digest"] ==
             _digest(prior_archive["schedule"]),
             "Previous-month schedule fingerprint mismatches")
    worked = _count_synthetic_rows(prior_archive, people)
    goals, compensation = prior_archive["goals"], prior_archive["compensation_out"]
    _require(type(goals) is dict and set(goals) == set(_COUNTS) and
             type(compensation) is dict and set(compensation) == set(_COUNTS),
             "Missing source-aligned archive goals/credits")
    output = {}
    manual_overrides = {} if manual_overrides is None else manual_overrides
    _require(type(manual_overrides) is dict and
             set(manual_overrides) <= set(_COUNTS),
             "Unknown manual carry pool")
    for pool, members in people.items():
        avail = {x["id"]: x["availability"]
                 for x in prior_source["pools"][pool]}
        expected_goals = base_goals_v7(members, avail, 30 * _COUNTS[pool])
        _require(goals[pool] == expected_goals,
                 "Prior archive goals disagree with original source")
        out = archive_compensation_out_v7(members, goals[pool], worked[pool])
        _require(compensation[pool] == out,
                 "Prior archive compensation disagrees with actual worked counts")
        override = manual_overrides.get(pool, {})
        _require(type(override) is dict, "Invalid manual carry overrides")
        carry = import_prior_locked_carry_v7(
            members, out, prior_locked=True, prior_stale=False,
            manual_override=override)
        current = next_people[pool]
        available = {x["id"]: x["availability"]
                     for x in next_source["pools"][pool]}
        carried = [FairPerson(p.ident, p.weight, carry[p.ident], p.meal_credit)
                   for p in current]
        base = base_goals_v7(carried, available, 31 * _COUNTS[pool])
        targets = actual_targets_v7(
            carried, available, 31 * _COUNTS[pool], base)
        output[pool] = {"carry": carry, "base_goals": base,
                        "actual_targets": targets}
    return {
        "format": "phase20-invented-rollover-preview-v1",
        "month": _ALLOWED_NEXT, "invented_only": True,
        "prior_archive_digest_verified_against_supplied_anchor": True,
        "verified_real_v7_inputSig": False,
        "archive_authenticity_verified": False,
        "cross_month_hard_rule_parity_verified": False,
        "operationally_certified": False,
        "importable_as_v7_backup": False,
        "pools": output,
    }
