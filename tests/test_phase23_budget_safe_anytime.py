"""Pure local, fictional-only test; no real people, WASM or paid cloud CI."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import unittest

from solver.phase20_synthetic_rollover import RolloverError
from solver.phase21_synthetic_cross_month_gate import (
    _calendar_rows, _parse_events, _audit_duties, _EPOCH,
)
from solver.phase22_synthetic_solver_handoff import (
    fictional_source_fixture, build_fictional_handoff,
)
from solver.phase23_budget_safe_anytime import (
    prepare_safe_hints, safe_timeout_verdict,
)


class Phase23Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = fictional_source_fixture()
        p,a,n,e,pins,anchors = cls.sources
        cls.handoff = build_fictional_handoff(
            p,a,n,e,pins,expected_anchors=anchors)
        cls.plan = prepare_safe_hints(cls.handoff)

    def test_01_dense_full_month_and_anonymous_inputs(self):
        plan = self.plan
        self.assertEqual(set(plan['pools']), {'door','officer'})
        self.assertEqual({p:x['filled'] for p,x in plan['pools'].items()},
                         {'door':371,'officer':216})
        self.assertEqual(sum(x['missing'] for x in plan['pools'].values()),2)
        for pool,rows in (('door',372),('officer',217)):
            item = plan['pools'][pool]
            self.assertEqual(len(item['indices']),rows)
            self.assertEqual(len(item['wire'].splitlines()),8)
            self.assertNotIn('SIM_',item['wire'])
            self.assertNotIn('H001',item['wire'])
            self.assertTrue(item['verified_against_original_fictional_events'])
        self.assertTrue(plan['independently_verified_hard_constraints'])
        self.assertFalse(plan['operationally_certified'])

    def test_02_full_fill_relative_to_forced_vacancies_is_mathematically_proven(self):
        self.assertTrue(self.plan['max_fill_proven_for_partial_fictional_model'])
        self.assertEqual(self.plan['coverage_upper_bound'],
                         {'door':371,'officer':216})
        self.assertFalse(self.plan['all_fairness_optimality_proven'])
        self.assertFalse(self.plan['genuine_wasm_executed'])

    def test_03_preserves_all_hard_input_fields_byte_for_byte(self):
        for pool in ('door','officer'):
            old=self.handoff['frames'][pool]['wire'].splitlines()
            new=self.plan['pools'][pool]['wire'].splitlines()
            self.assertEqual(len(old),8)
            self.assertEqual(len(new),8)
            for i in (0,1,2,3,4,5,7):
                self.assertEqual(old[i],new[i],(pool,i))
            self.assertNotEqual(old[6],new[6])

    def test_04_forced_blank_and_fixed_staff_preserved(self):
        for pool,day,slot,expect in (
            ('door',5,8,-1),('door',7,6,48),
            ('officer',6,4,-1),('officer',5,5,48)):
            i=(day-1)*(12 if pool=='door' else 7)+slot-1
            self.assertEqual(self.plan['pools'][pool]['indices'][i],expect)

    def test_05_no_added_pins_no_eligibility_changes(self):
        for pool,item in self.plan['pools'].items():
            rows=item['wire'].splitlines()
            staff=self.handoff['frames'][pool]['staff_count']
            for i,p in enumerate(item['indices']):
                if p>=0:
                    self.assertEqual(rows[4][i*staff+p],'1')

    def test_06_independent_historical_and_event_legality(self):
        p,a,n,e,pins,anchors=self.handoff['original_sources']
        people={pool:set(x['id'] for x in n['pools'][pool])
                for pool in ('door','officer')}
        prior=_calendar_rows(a['schedule'],2026,11,people)
        ev=_parse_events(e,people)
        jobs=list(prior)
        for pool,item in self.plan['pools'].items():
            slots=12 if pool=='door' else 7
            names=[x['id'] for x in n['pools'][pool]]
            jobs += [(pool,names[j],date(2026,12,i//slots+1),i%slots+1)
                     for i,j in enumerate(item['indices']) if j>=0]
        self.assertTrue(_audit_duties(jobs,ev))

    def test_07_work_budget_can_end_early_but_not_break_pins(self):
        result=prepare_safe_hints(self.handoff,max_checks=1)
        self.assertLess(result['pools']['door']['filled'],371)
        self.assertFalse(result['max_fill_proven_for_partial_fictional_model'])
        self.assertGreaterEqual(result['pools']['door']['filled'],1)
        self.assertGreaterEqual(result['pools']['officer']['filled'],1)
        self.assertTrue(result['independently_verified_hard_constraints'])

    def test_08_invalid_greedy_work_budget_refused(self):
        for val in (0,-1,True,1000001,1.1,None):
            with self.subTest(val=val):
                with self.assertRaises(RolloverError):
                    prepare_safe_hints(self.handoff,max_checks=val)

    def test_09_original_handoff_frame_tamper_refused(self):
        bad=deepcopy(self.handoff)
        bad['frames']['door']['wire']=bad['frames']['door']['wire'].replace(
            'guard-month-harsh-v4','guard-month-fair-v3')
        with self.assertRaisesRegex(RolloverError,'changed'):
            prepare_safe_hints(bad)

    def test_10_original_handoff_source_mutation_refused(self):
        bad=deepcopy(self.handoff)
        bad['original_sources'][3][0]['start']='2026-12-03'
        with self.assertRaisesRegex(RolloverError,'changed'):
            prepare_safe_hints(bad)

    def test_11_wrong_source_format_refused(self):
        bad=deepcopy(self.handoff)
        bad['format']='guard-offline-v5'
        with self.assertRaisesRegex(RolloverError,'fictional'):
            prepare_safe_hints(bad)

    def test_12_timeout_unknown_never_becomes_solver_solution(self):
        verdict=safe_timeout_verdict(self.handoff,self.plan,
            {'door':{'status':'UNKNOWN'},'officer':{'status':'UNKNOWN'}})
        self.assertEqual(verdict['reason'],'UNKNOWN')
        self.assertFalse(verdict['solver_result_accepted'])
        self.assertTrue(verdict['heuristic_preview_usable_for_further_testing_only'])
        self.assertIsNone(verdict['accepted_assignments'])
        self.assertTrue(verdict['fallback_fill_maximum_proven_for_partial_fictional_model'])
        self.assertEqual(verdict['fallback_filled'],{'door':371,'officer':216})
        self.assertFalse(verdict['operationally_certified'])

    def test_13_solver_unknown_cannot_hide_forged_assignments(self):
        with self.assertRaisesRegex(RolloverError,'must not contain'):
            safe_timeout_verdict(self.handoff,self.plan,
                {'door':{'status':'UNKNOWN','assignments':[-1]*372},
                 'officer':{'status':'UNKNOWN'}})

    def test_14_infeasible_is_not_a_safe_timeout_preview(self):
        verdict=safe_timeout_verdict(self.handoff,self.plan,
            {'door':{'status':'INFEASIBLE'},'officer':{'status':'UNKNOWN'}})
        self.assertFalse(verdict['solver_result_accepted'])
        self.assertFalse(verdict['heuristic_preview_usable_for_further_testing_only'])

    def test_15_invalid_input_blocks_preview(self):
        verdict=safe_timeout_verdict(self.handoff,self.plan,
            {'door':{'status':'INVALID_INPUT'},'officer':{'status':'OPTIMAL'}})
        self.assertFalse(verdict['solver_result_accepted'])
        self.assertFalse(verdict['heuristic_preview_usable_for_further_testing_only'])

    def test_16_unrecognized_status_refused(self):
        with self.assertRaisesRegex(RolloverError,'unsupported'):
            safe_timeout_verdict(self.handoff,self.plan,
                {'door':{'status':'SUPER_OPTIMAL'},'officer':{'status':'UNKNOWN'}})

    def test_17_missing_pool_reply_refused(self):
        with self.assertRaisesRegex(RolloverError,'Both duty'):
            safe_timeout_verdict(self.handoff,self.plan,
                {'door':{'status':'UNKNOWN'}})

    def test_18_modified_hint_indices_cannot_be_claimed_audited(self):
        bad=deepcopy(self.plan)
        bad['pools']['door']['indices'][0]=0
        with self.assertRaisesRegex(RolloverError,'modified'):
            safe_timeout_verdict(self.handoff,bad,
                {'door':{'status':'UNKNOWN'},'officer':{'status':'UNKNOWN'}})

    def test_19_modified_hint_sha_cannot_be_claimed_audited(self):
        bad=deepcopy(self.plan)
        bad['pools']['door']['sha256']='0'*64
        with self.assertRaisesRegex(RolloverError,'modified'):
            safe_timeout_verdict(self.handoff,bad,
                {'door':{'status':'UNKNOWN'},'officer':{'status':'UNKNOWN'}})

    def test_20_modified_upper_bound_claim_cannot_be_claimed_proven(self):
        bad=deepcopy(self.plan)
        bad['coverage_upper_bound']['door']+=1
        with self.assertRaisesRegex(RolloverError,'modified'):
            safe_timeout_verdict(self.handoff,bad,
                {'door':{'status':'UNKNOWN'},'officer':{'status':'UNKNOWN'}})

    def test_21_pin_only_reported_feasible_is_independently_checked(self):
        answers={}
        for pool,info in self.handoff['frames'].items():
            pin=[int(x) for x in info['wire'].splitlines()[5].split(',')]
            assignments=[p if p>=0 else -1 for p in pin]
            filled=sum(p>=0 for p in assignments)
            answers[pool]={'status':'FEASIBLE','assignments':assignments,
                           'filled':filled,'missing':info['shift_count']-filled}
        verdict=safe_timeout_verdict(self.handoff,self.plan,answers)
        self.assertEqual(verdict['filled'],2)
        self.assertTrue(verdict['solver_result_accepted'])
        self.assertFalse(verdict['independently_certified_optimal'])
        self.assertFalse(verdict['operationally_certified'])

    def test_22_fake_feasible_result_count_is_refused(self):
        answers={}
        for pool,info in self.handoff['frames'].items():
            n=info['shift_count']; answers[pool]={
                'status':'FEASIBLE','assignments':[-1]*n,
                'filled':0,'missing':n}
        with self.assertRaises(RolloverError):
            safe_timeout_verdict(self.handoff,self.plan,answers)

    def test_23_same_results_deterministic(self):
        other=prepare_safe_hints(self.handoff)
        self.assertEqual(other,self.plan)

    def test_24_all_preview_security_flags_false(self):
        for k in ('operationally_certified','real_v7_inputSig_verified',
                  'full_v7_rule_parity_verified','genuine_wasm_executed',
                  'importable_as_v7_backup'):
            self.assertFalse(self.plan[k])


if __name__=='__main__':
    unittest.main()