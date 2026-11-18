"""Phase 24: all imaginary data, local-only, no paid CI or real personnel."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib
import unittest

from solver.phase20_synthetic_rollover import RolloverError, _COUNTS
from solver.phase21_synthetic_cross_month_gate import (
    _calendar_rows, _parse_events, _audit_duties, audit_invented_cross_month,
    empty_next_calendar,
)
from solver.phase22_synthetic_solver_handoff import (
    fictional_source_fixture, build_fictional_handoff,
)
from solver.phase23_budget_safe_anytime import prepare_safe_hints
from solver.phase24_fictional_fair_improver import polish_fictional_fairness


class Phase24Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = fictional_source_fixture()
        p, a, n, e, pins, anchors = cls.inputs
        cls.handoff = build_fictional_handoff(
            p, a, n, e, pins, expected_anchors=anchors)
        cls.original = prepare_safe_hints(cls.handoff)
        cls.improved = polish_fictional_fairness(cls.handoff)

    def test_01_dense_full_month_coverage_unchanged(self):
        self.assertEqual(self.improved['total_filled'], 587)
        self.assertEqual(self.improved['total_missing'], 2)
        self.assertEqual(self.improved['pools']['door']['filled'], 371)
        self.assertEqual(self.improved['pools']['officer']['filled'], 216)
        self.assertEqual(self.improved['pools']['door']['missing'], 1)
        self.assertEqual(self.improved['pools']['officer']['missing'], 1)

    def test_02_count_l1_real_improvement(self):
        self.assertEqual(self.improved['total_l1_before'], 12)
        self.assertEqual(self.improved['total_l1_after'], 8)
        self.assertLess(self.improved['total_l1_after'],
                        self.improved['total_l1_before'])
        self.assertEqual(self.improved['pools']['officer']['accepted_moves'], 2)

    def test_03_improvement_does_not_make_unproven_global_claims(self):
        for key in ('l1_optimality_proven','wasm_search_speed_improvement_proven',
                    'genuine_wasm_executed','real_v7_inputSig_verified',
                    'full_v7_rule_parity_verified','operationally_certified',
                    'importable_as_v7_backup'):
            self.assertIs(self.improved[key],False)
        self.assertTrue(self.improved['preview_only_not_solver_result'])

    def test_04_original_wasm_hard_fields_and_count_targets_unchanged(self):
        for pool in _COUNTS:
            a = self.handoff['frames'][pool]['wire'].splitlines()
            b = self.improved['pools'][pool]['wire'].splitlines()
            self.assertEqual(len(a),8)
            self.assertEqual(len(b),8)
            for i in (0,1,2,3,4,5,7):
                self.assertEqual(a[i],b[i],(pool,i))

    def test_05_hard_pins_and_forced_blanks_unchanged(self):
        for pool, slots in _COUNTS.items():
            items = self.improved['pools'][pool]['indices']
            pins = list(map(int,self.handoff['frames'][pool]['wire'].splitlines()[5].split(',')))
            for i, pin in enumerate(pins):
                if pin == -1: self.assertEqual(items[i],-1)
                if pin >= 0: self.assertEqual(items[i],pin)
            self.assertEqual(len(items),31*slots)

    def test_06_eligibility_bits_respected_everywhere(self):
        for pool in _COUNTS:
            info=self.improved['pools'][pool]
            mask=self.handoff['frames'][pool]['wire'].splitlines()[4]
            width=self.handoff['frames'][pool]['staff_count']
            for i,person in enumerate(info['indices']):
                if person >= 0: self.assertEqual(mask[i*width+person],'1')

    def test_07_every_improvement_is_transfer_not_new_staffing(self):
        for pool in _COUNTS:
            before=self.original['pools'][pool]['indices']
            after=self.improved['pools'][pool]['indices']
            self.assertEqual([x >= 0 for x in before],
                             [x >= 0 for x in after])

    def test_08_aggregate_targets_and_counts_recomputed_from_literal_frame(self):
        for pool in _COUNTS:
            info=self.improved['pools'][pool]
            targets=list(map(int,info['wire'].splitlines()[7].split(',')))
            actual=[info['indices'].count(i) for i in range(len(targets))]
            self.assertEqual(sum(abs(a-b) for a,b in zip(actual,targets)),
                             info['l1_after'])

    def test_09_final_independent_cross_month_and_event_audit(self):
        prev,archive,upcoming,events,pins,overrides=self.handoff['original_sources']
        proposed=empty_next_calendar()
        for pool,info in self.improved['pools'].items():
            names=[x['id'] for x in upcoming['pools'][pool]]
            for i,p in enumerate(info['indices']):
                if p>=0: proposed[pool][i][2]=names[p]
        audited=audit_invented_cross_month(
            prev,archive,upcoming,proposed,
            expected_archive_sha256=self.handoff['anchors']['archive'],
            invented_events=events,manual_overrides=overrides)
        self.assertEqual(audited['next_filled'],587)

    def test_10_fixed_sunday_and_previous_month_restrictions_survive(self):
        # Reaudit all archived + new duty records, not only reassigned positions.
        _,archive,upcoming,events,_,_=self.handoff['original_sources']
        ids={pool:set(x['id'] for x in upcoming['pools'][pool]) for pool in _COUNTS}
        jobs=_calendar_rows(archive['schedule'],2026,11,ids)
        for pool,info in self.improved['pools'].items():
            names=[x['id'] for x in upcoming['pools'][pool]]
            slots=_COUNTS[pool]
            for i,p in enumerate(info['indices']):
                if p>=0:
                    jobs.append((pool,names[p],date(2026,12,i//slots+1),i%slots+1))
        self.assertTrue(_audit_duties(jobs,_parse_events(events,ids)))

    def test_11_anonymous_bytes_and_sha(self):
        for pool,info in self.improved['pools'].items():
            wire=info['wire']
            self.assertEqual(hashlib.sha256(wire.encode('ascii')).hexdigest(),
                             info['sha256'])
            self.assertNotIn('SIM_',wire)
            self.assertNotIn('H001',wire)

    def test_12_source_and_initial_seed_not_mutated(self):
        h=deepcopy(self.handoff)
        plan=prepare_safe_hints(h)
        original=deepcopy(h)
        unmodified=deepcopy(plan)
        polish_fictional_fairness(h)
        self.assertEqual(h,original)
        self.assertEqual(plan,unmodified)

    def test_13_runs_deterministically(self):
        newer=polish_fictional_fairness(self.handoff)
        self.assertEqual(newer,self.improved)

    def test_14_work_budget_bounded(self):
        for budget in (1,2,3,30):
            with self.subTest(budget=budget):
                r=polish_fictional_fairness(self.handoff,max_checks=budget)
                for pool in _COUNTS:
                    self.assertLessEqual(r['pools'][pool]['checks'],budget)
                self.assertLessEqual(r['total_l1_after'],r['total_l1_before'])
                self.assertEqual(r['total_filled'],587)

    def test_15_reject_invalid_budget_types(self):
        for val in (0,-3,True,False,1.5,'5',None,1000001):
            with self.subTest(val=val):
                with self.assertRaisesRegex(RolloverError,'budget'):
                    polish_fictional_fairness(self.handoff,max_checks=val)

    def test_16_reject_invalid_seed_budget(self):
        for val in (0,True,'150000',None,1000001):
            with self.subTest(val=val):
                with self.assertRaisesRegex(RolloverError,'budget'):
                    polish_fictional_fairness(self.handoff,seed_budget=val)

    def test_17_partial_legal_seed_does_not_fabricate_missing_assignments(self):
        r=polish_fictional_fairness(self.handoff,seed_budget=1,max_checks=40)
        self.assertLess(r['total_filled'],587)
        self.assertEqual(r['total_filled']+r['total_missing'],589)
        self.assertTrue(r['independent_original_event_audit_passed'])
        self.assertFalse(r['l1_optimality_proven'])

    def test_18_refuse_corrupted_candidate_mask(self):
        changed=deepcopy(self.handoff)
        frame=changed['frames']['door']
        frame['wire']=frame['wire'].replace('guard-month-harsh-v4','guard-month-fair-v3')
        with self.assertRaisesRegex(RolloverError,'changed'):
            polish_fictional_fairness(changed)

    def test_19_refuse_modified_original_event(self):
        changed=deepcopy(self.handoff)
        changed['original_sources'][3][0]['start']='2026-12-20'
        with self.assertRaisesRegex(RolloverError,'changed'):
            polish_fictional_fairness(changed)

    def test_20_refuse_modified_hard_pin(self):
        changed=deepcopy(self.handoff)
        original=changed['frames']['officer']['wire']
        lines=original.splitlines()
        fixed=lines[5].split(',')
        fixed[0]=-1
        lines[5]=','.join(map(str,fixed))
        changed['frames']['officer']['wire']='\n'.join(lines)+'\n'
        with self.assertRaisesRegex(RolloverError,'changed'):
            polish_fictional_fairness(changed)

    def test_21_refuse_modified_soft_count_targets(self):
        changed=deepcopy(self.handoff)
        changed['soft_targets']['officer']['SIM_O_000']=100
        with self.assertRaisesRegex(RolloverError,'changed'):
            polish_fictional_fairness(changed)

    def test_22_refuse_wrong_phase_source(self):
        changed=deepcopy(self.handoff)
        changed['format']='guard-offline-v5'
        with self.assertRaisesRegex(RolloverError,'fictional'):
            polish_fictional_fairness(changed)

    def test_23_worked_count_and_forced_blanks_unchanged_for_small_budget(self):
        plan=polish_fictional_fairness(self.handoff,max_checks=1)
        for pool in _COUNTS:
            self.assertEqual(sum(x>=0 for x in plan['pools'][pool]['indices']),
                             self.original['pools'][pool]['filled'])
            self.assertEqual(sum(x<0 for x in plan['pools'][pool]['indices']),1)

    def test_24_improved_pools_have_no_fairness_inflation(self):
        for pool,info in self.improved['pools'].items():
            self.assertLessEqual(info['l1_after'],info['l1_before'])
            self.assertIs(info['candidate_mask_unchanged'],True)
            self.assertIs(info['hard_pins_unchanged'],True)
            self.assertIs(info['fixed_vacancies_preserved'],True)


if __name__=='__main__':
    unittest.main()
