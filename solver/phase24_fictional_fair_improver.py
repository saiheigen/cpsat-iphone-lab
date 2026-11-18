"""Phase 24: independently audited fictional count-fairness polishing.

This is NOT a CP-SAT solver improvement, a production importer, or a verified
v7 rule implementation. It operates only on the original Phase22 invented
source and a recomputed Phase23 legal full-calendar preview. It never edits
candidate eligibility, forced vacancies, prior history, hard pins or targets.

A deterministic, bounded one-slot reallocation improves soft integer L1
count deviation while retaining exactly the same number of staffed shifts.
The result must independently pass the original November+December event audit.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib

from solver.phase20_synthetic_rollover import RolloverError, _COUNTS
from solver.phase21_synthetic_cross_month_gate import (
    _calendar_rows, _parse_events, _blocked, _audit_duties, _conflict,
    empty_next_calendar, audit_invented_cross_month,
)
from solver.phase23_budget_safe_anytime import (
    prepare_safe_hints, _rebuild,
)

_FORMAT = 'phase24-fictional-fair-preview-v1'


def _require(ok, message):
    if not ok:
        raise RolloverError(message)


def _l1(counts, targets):
    return sum(abs(c - t) for c, t in zip(counts, targets))


def polish_fictional_fairness(handoff, *, max_checks=100000, seed_budget=150000):
    """Rebuild the trusted fabricated source, then apply only legal reassignments.

    Each accepted move strictly improves the total L1 count target deviation;
    no false global optimum claims. max_checks counts proposed reassignments
    (not CPU time). Bounded deterministic search can stop with no improvement.
    """
    _require(type(max_checks) is int and 1 <= max_checks <= 1000000,
             'Polishing check budget must be a positive bounded integer')
    _require(type(seed_budget) is int and 1 <= seed_budget <= 1000000,
             'Seed work budget must be a positive bounded integer')
    fresh = _rebuild(handoff)
    seed = prepare_safe_hints(fresh, max_checks=seed_budget)
    prev, archive, upcoming, events, original_pins, overrides = fresh['original_sources']
    names = {pool: [person['id'] for person in upcoming['pools'][pool]]
             for pool in _COUNTS}
    roster = {pool: set(people) for pool, people in names.items()}
    parsed_events = _parse_events(events, roster)
    historical = _calendar_rows(archive['schedule'], 2026, 11, roster)
    prior_by_pool_person = {(pool, person): []
                            for pool, pool_names in names.items()
                            for person in pool_names}
    for job in historical:
        prior_by_pool_person[job[0], job[1]].append(job)
    result = {}
    for pool, slots in _COUNTS.items():
        original_lines = fresh['frames'][pool]['wire'].splitlines()
        _require(len(original_lines) == 8 and original_lines[0] ==
                 'guard-month-harsh-v4', 'Wrong solver frame version')
        initial = seed['pools'][pool]['indices']
        assignments = list(initial)
        n, width = len(assignments), len(names[pool])
        mask = original_lines[4]
        pins = [int(value) for value in original_lines[5].split(',')]
        targets = [int(value) for value in original_lines[7].split(',')]
        _require(len(mask) == n*width and len(pins) == n and
                 len(targets) == width and n == slots*31,
                 'Truncated fairness input')
        jobs_by = {person: list(prior_by_pool_person[pool, person])
                   for person in names[pool]}
        counts = [0] * width
        for i, person_index in enumerate(assignments):
            if person_index < 0:
                continue
            job = (pool, names[pool][person_index],
                   date(2026, 12, i // slots + 1), i % slots + 1)
            jobs_by[names[pool][person_index]].append(job)
            counts[person_index] += 1
        before = _l1(counts, targets)
        checks = changes = 0
        # First-improvement scan is reproducible. It is not a proof of best L1.
        while checks < max_checks:
            improved = False
            for i, donor in enumerate(assignments):
                if checks >= max_checks:
                    break
                if donor < 0 or pins[i] != -2:
                    continue
                donor_cost = abs(counts[donor]-targets[donor])
                donor_after = abs(counts[donor]-1-targets[donor])
                # Transferring one slot away from this donor cannot help L1.
                if donor_after >= donor_cost:
                    continue
                old_job = (pool, names[pool][donor],
                           date(2026, 12, i // slots + 1), i % slots + 1)
                for recipient in range(width):
                    if checks >= max_checks:
                        break
                    if recipient == donor or mask[i*width+recipient] != '1':
                        continue
                    checks += 1
                    if abs(counts[recipient]+1-targets[recipient]) >= \
                            abs(counts[recipient]-targets[recipient]):
                        continue
                    job = (pool, names[pool][recipient],
                           old_job[2], old_job[3])
                    _require(not _blocked(job, parsed_events),
                             'Source event and candidate matrix disagree')
                    existing = jobs_by[names[pool][recipient]]
                    if (sum(x[2] == job[2] for x in existing) >=
                            (3 if pool == 'door' else 1)):
                        continue
                    if any(_conflict(job, x) for x in existing):
                        continue
                    # All hard facts are preserved. Change one slot, retain
                    # fill, and remember both people's complete duty history.
                    jobs_by[names[pool][donor]].remove(old_job)
                    existing.append(job)
                    assignments[i] = recipient
                    counts[donor] -= 1
                    counts[recipient] += 1
                    changes += 1
                    improved = True
                    break
                if improved:
                    break
            if not improved:
                break
        after = _l1(counts, targets)
        _require(after <= before and (changes == 0 or after < before),
                 'Polishing worsened soft count fairness')
        _require(sum(a >= 0 for a in assignments) ==
                 sum(a >= 0 for a in initial),
                 'Polishing reduced shift coverage')
        _require(all((pins[i] < 0 or assignments[i] == pins[i]) and
                     (pins[i] != -1 or assignments[i] == -1) and
                     (assignments[i] < 0 or mask[i*width+assignments[i]] == '1')
                     for i in range(n)),
                 'Polishing violated pins, forced vacancies or eligibility')
        _audit_duties([job for job in historical if job[0] == pool] +
                      [job for person in names[pool] for job in jobs_by[person]
                       if job[2].month == 12], parsed_events)
        # The only v4 wire change is the optional hint line; no extra pins.
        lines = original_lines[:]
        lines[6] = ','.join(map(str, assignments))
        wire = '\n'.join(lines) + '\n'
        _require(all(lines[k] == original_lines[k]
                     for k in (0, 1, 2, 3, 4, 5, 7)),
                 'Polishing altered original hard rules or fairness targets')
        _require(not any(who in wire for who in names[pool]),
                 'Person identifier leaked into anonymous solver wire')
        result[pool] = {
            'wire': wire,
            'sha256': hashlib.sha256(wire.encode('ascii')).hexdigest(),
            'indices': assignments,
            'filled': sum(a >= 0 for a in assignments),
            'missing': sum(a < 0 for a in assignments),
            'l1_before': before,
            'l1_after': after,
            'accepted_moves': changes,
            'checks': checks,
            'candidate_mask_unchanged': True,
            'hard_pins_unchanged': True,
            'fixed_vacancies_preserved': True,
        }
    # Independently recheck every named duty after improvements, not just
    # the changed row, including last month's fabricated history and events.
    proposed = empty_next_calendar()
    for pool, item in result.items():
        for i, p in enumerate(item['indices']):
            if p >= 0:
                proposed[pool][i][2] = names[pool][p]
    audit = audit_invented_cross_month(
        prev, archive, upcoming, proposed,
        expected_archive_sha256=fresh['anchors']['archive'],
        invented_events=events, manual_overrides=overrides)
    _require(audit['next_filled'] == sum(x['filled'] for x in result.values()),
             'Final independent month audit disagrees with count')
    return {
        'format': _FORMAT,
        'synthetic_only': True,
        'source_anchors': deepcopy(fresh['anchors']),
        'pools': result,
        'total_l1_before': sum(x['l1_before'] for x in result.values()),
        'total_l1_after': sum(x['l1_after'] for x in result.values()),
        'total_filled': sum(x['filled'] for x in result.values()),
        'total_missing': sum(x['missing'] for x in result.values()),
        'independent_original_event_audit_passed': True,
        'preview_only_not_solver_result': True,
        'l1_optimality_proven': False,
        'wasm_search_speed_improvement_proven': False,
        'genuine_wasm_executed': False,
        'real_v7_inputSig_verified': False,
        'full_v7_rule_parity_verified': False,
        'operationally_certified': False,
        'importable_as_v7_backup': False,
    }
