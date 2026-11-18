"""Synthetic-only November→December staffing legality and archive boundary audit.

This is deliberately NOT a v7 backup importer or a military roster certifier.
The previous archive's invented row coverage and integrity are verified through
Phase 20; here we *add* independent temporal legality checks against every
invented archived shift and proposed complete December calendar.

No external services; no OR-Tools dependency; no actual roster names/dates.
Archive SHA256 compares to a supplied reference, not a digital signature.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import date, timedelta
from itertools import combinations

from solver.phase20_synthetic_rollover import (
    RolloverError, _digest, _EPOCH, _COUNTS, invented_fixture,
    project_invented_rollover,
)

_PRIOR_YEAR, _PRIOR_MONTH, _NEXT_YEAR, _NEXT_MONTH = 2026, 11, 2026, 12
_TIME = {
    "door": [(22, 24), (0, 2), (2, 4), (4, 6), (6, 8), (8, 10),
             (10, 12), (12, 14), (14, 16), (16, 18), (18, 20), (20, 22)],
    "officer": [(22, 24), (0, 2), (2, 4), (4, 6), (6, 12), (12, 18), (18, 22)],
}
_EVENTS = {"leave", "nightcheck", "driver", "training", "officer_duty",
           "meal", "exempt_all", "exempt_night", "exempt_noon"}
_ONE = timedelta(days=1)


def _ensure(condition, reason):
    if not condition:
        raise RolloverError(reason)


def _calendar_rows(schedule, year, month, expected_ids):
    """Parse a complete, ordered 2-pool schedule without trusting summaries."""
    _ensure(type(schedule) is dict and set(schedule) == set(_COUNTS),
            "Missing one duty pool")
    days = 30 if month == 11 else 31
    duties = []
    for pool, slots in _COUNTS.items():
        rows = schedule[pool]
        _ensure(type(rows) is list and len(rows) == days * slots,
                "Incomplete duty calendar")
        for i, row in enumerate(rows):
            duty_date = date(year, month, i // slots + 1)
            serial = (duty_date - _EPOCH).days
            slot = i % slots + 1
            _ensure(type(row) is list and len(row) == 3 and
                    type(row[0]) is int and row[0] == serial and
                    type(row[1]) is int and row[1] == slot,
                    "Duplicated, shifted or reordered duty row")
            who = row[2]
            _ensure(who is None or (type(who) is str and who in expected_ids[pool]),
                    "Unknown or wrong-pool fictional person")
            if who is not None:
                duties.append((pool, who, duty_date, slot))
    return duties


def _standby(pool, d, slot):
    start = _TIME[pool][slot-1][0]
    return d.weekday() == 6 and (
        6 <= start < 20 if pool == "door" else slot == 7)


def _conflict(a, b):
    """Independent pure-Python implementation of the partial native model.

    a,b = (pool, id, date, slot). Same person's same-pool jobs only.
    """
    pool = a[0]
    gap = abs((a[2] - b[2]).days)
    if gap == 1:
        return True
    if gap <= 2 and a[3] == b[3]:
        return True
    if gap == 7 and _standby(pool, a[2], a[3]) and _standby(pool, b[2], b[3]):
        return True
    if gap != 0:
        return False
    if pool == "officer":
        return True
    ordered = sorted((a, b), key=lambda x: _TIME[pool][x[3] - 1][0])
    earlier_end = _TIME[pool][ordered[0][3] - 1][1]
    later_start = _TIME[pool][ordered[1][3] - 1][0]
    return later_start - earlier_end < 6


def _parse_events(events, people):
    _ensure(type(events) is list, "Fictional events must be a list")
    parsed = defaultdict(list)
    for event in events:
        _ensure(type(event) is dict and set(event) ==
                {"pool", "person", "kind", "start", "end"},
                "Invalid fictional event shape")
        pool = event["pool"]
        _ensure(pool in _COUNTS and type(event["person"]) is str and
                event["person"] in people[pool],
                "Fictional event person is not in duty pool")
        kind = event["kind"]
        _ensure(type(kind) is str and kind in _EVENTS,
                "Unknown fictional event type")
        _ensure(pool == "officer" or kind not in ("meal", "officer_duty"),
                "Officer-only event assigned to guard")
        try:
            _ensure(type(event["start"]) is str and
                    type(event["end"]) is str,
                    "Invalid event date type")
            start = date.fromisoformat(event["start"])
            end = date.fromisoformat(event["end"])
        except (ValueError, TypeError) as exc:
            raise RolloverError("Invalid event calendar date") from exc
        _ensure(start <= end and date(2026, 11, 1) <= start and
                end <= date(2027, 1, 2),
                "Invalid fictional event date range")
        parsed[(pool, event["person"])].append((kind, start, end))
    return parsed


def _blocked(job, events):
    pool, person, day, slot = job
    start_h = _TIME[pool][slot - 1][0]
    night = start_h < 6 or start_h >= 22
    noon = start_h == 12
    for kind, a, b in events.get((pool, person), ()):
        if kind == "leave" and (a <= day <= b + _ONE or
                                day == a - _ONE and night):
            return True
        if kind == "training" and a - _ONE <= day <= b:
            return True
        if kind in ("officer_duty", "meal", "nightcheck") and a - _ONE <= day <= b + _ONE:
            return True
        if kind == "driver" and (a <= day <= b + _ONE or
                                 day == a - _ONE and night):
            return True
        if kind == "exempt_all" and a <= day <= b:
            return True
        if kind == "exempt_night" and a <= day <= b and night:
            return True
        if kind == "exempt_noon" and a <= day <= b and noon:
            return True
    return False


def _audit_duties(duties, events):
    by_person = defaultdict(list)
    for job in duties:
        _ensure(not _blocked(job, events),
                "Duty violates an original imaginary event prohibition")
        by_person[(job[0], job[1])].append(job)
    for key, jobs in by_person.items():
        per_day = defaultdict(int)
        for job in jobs:
            per_day[job[2]] += 1
        _ensure(all(n <= (3 if key[0] == "door" else 1)
                    for n in per_day.values()),
                "Per-day maximum duty exceeded")
        for a, b in combinations(jobs, 2):
            _ensure(not _conflict(a, b),
                    "Conflicting same-day, next-day, same-slot or Sunday duty")
    return True


def imaginary_legal_boundary_fixture():
    """Create a complete fictional *legally spaced* prior 570-row archive.

    Phase20's count-only invented archive was intentionally NOT a legal duty
    witness. For this phase we construct a new legal November witness and
    recompute the synthetic archive's archived worked-count credits.
    """
    from solver.fairness_targets_v7 import (
        archive_compensation_out_v7,
    )
    from solver.phase20_synthetic_rollover import _source_people
    previous, archive, upcoming, _ = invented_fixture()
    previous = deepcopy(previous)
    archive = deepcopy(archive)
    prior_people = _source_people(previous, month="2026-11")
    new_schedule = {}
    for pool, slots in _COUNTS.items():
        rows = []
        for d in range(1, 31):
            serial = (date(2026, 11, d) - _EPOCH).days
            # Four nonadjacent fictional cohorts; each individual works at
            # most once per day, never on consecutive days, and different
            # people staff consecutive Sundays.
            cohort = (d - 1) % 4
            for slot in range(1, slots + 1):
                who = f"SIM_{'D' if pool == 'door' else 'O'}_{cohort * slots + slot - 1:03}"
                rows.append([serial, slot, who])
        new_schedule[pool] = rows
    archive["schedule"] = new_schedule
    archive["schedule_digest"] = _digest(new_schedule)
    for pool, members in prior_people.items():
        actual = {p.ident: 0 for p in members}
        for serial, slot, who in new_schedule[pool]:
            actual[who] += 1
        archive["compensation_out"][pool] = archive_compensation_out_v7(
            members, archive["goals"][pool], actual)
    return previous, archive, upcoming, _digest(archive)


def empty_next_calendar():
    """Full 589-row blank fictional December proposal, no incomplete month."""
    return {
        pool: [[(date(2026, 12, d) - _EPOCH).days, slot, None]
               for d in range(1, 32) for slot in range(1, slots + 1)]
        for pool, slots in _COUNTS.items()
    }


def place(schedule, pool, day, slot, person):
    """Test utility; actual auditor never silently edits a proposed roster."""
    schedule[pool][(day-1) * _COUNTS[pool] + slot - 1][2] = person


def audit_invented_cross_month(prior_source, archive, next_source,
                               next_schedule, *, expected_archive_sha256,
                               invented_events=None, manual_overrides=None):
    """Cross-month feasibility gate AFTER full Phase20 integrity/carry proof.

    All previous month assignments must be internally legal, not just
    complete and correctly hashed. Any proposed December duty must also
    honor archived history and invented date-crossing events.
    """
    carried = project_invented_rollover(
        prior_source, archive, next_source,
        independently_expected_archive_sha256=expected_archive_sha256,
        manual_overrides=manual_overrides)
    ids = {pool: {x["id"] for x in next_source["pools"][pool]}
           for pool in _COUNTS}
    event_index = _parse_events([] if invented_events is None else invented_events,
                                ids)
    prev = _calendar_rows(archive["schedule"], 2026, 11, ids)
    proposed = _calendar_rows(next_schedule, 2026, 12, ids)
    _audit_duties(prev, event_index)
    _audit_duties(prev + proposed, event_index)
    _ensure(sum(len(x) for x in next_schedule.values()) == 589,
            "Full invented December duty calendar required")
    return {
        "format": "phase21-imaginary-cross-month-gate-v1",
        "synthetic_only": True,
        "previous_month": "2026-11",
        "next_month": "2026-12",
        "prior_rows": 570,
        "upcoming_rows": 589,
        "prior_filled": len(prev),
        "next_filled": len(proposed),
        "next_missing": 589 - len(proposed),
        "cross_month_duty_eligibility_audited": True,
        "archive_digest_matches_supplied_anchor": True,
        "carry_forward_calculated": True,
        "carry": {pool: carried["pools"][pool]["carry"] for pool in _COUNTS},
        "verified_real_v7_inputSig": False,
        "archive_authenticity_verified": False,
        "source_aligned_full_v7_rules_verified": False,
        "genuine_wasm_executed": False,
        "operationally_certified": False,
        "importable_as_v7_backup": False,
    }
