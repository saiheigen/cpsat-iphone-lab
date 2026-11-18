"""Phase 22 invented-only transport and response audit, no GitHub Actions."""
from copy import deepcopy
from datetime import date
import unittest

from solver.phase20_synthetic_rollover import RolloverError, _digest
from solver.phase22_synthetic_solver_handoff import (
    fictional_source_fixture, build_fictional_handoff, audit_fictional_solver_response)


class Phase22Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = fictional_source_fixture()

    def build(self, parts=None, **kwargs):
        prev, archive, upcoming, events, pins, anchors = deepcopy(parts or self.source)
        return build_fictional_handoff(prev, archive, upcoming, events, pins,
                                      expected_anchors=anchors, **kwargs)

    @staticmethod
    def bits(bundle, pool, person, day, slot):
        frame = bundle['frames'][pool]['wire'].splitlines()
        staff = bundle['frames'][pool]['staff_count']
        slots = 12 if pool=='door' else 7
        return frame[4][((day-1)*slots+slot-1)*staff+person]

    @staticmethod
    def pin_only_response(bundle):
        response={}
        for pool, frame in bundle['frames'].items():
            pins=[int(x) for x in frame['wire'].splitlines()[5].split(',')]
            indexed=[p if p >= 0 else -1 for p in pins]
            num=sum(x>=0 for x in indexed)
            response[pool]={"status":"FEASIBLE", "assignments":indexed,
                            "filled":num, "missing":frame['shift_count']-num}
        return response

    def test_01_two_full_month_frames_with_canonical_eight_lines(self):
        b=self.build()
        self.assertEqual({k:v['shift_count'] for k,v in b['frames'].items()},
                         {'door':372,'officer':217})
        self.assertEqual({k:v['staff_count'] for k,v in b['frames'].items()},
                         {'door':56,'officer':50})
        for pool, frame in b['frames'].items():
            lines=frame['wire'].splitlines()
            self.assertEqual(len(lines),8)
            self.assertEqual(lines[:3],['guard-month-harsh-v4','2026-12',pool])
            self.assertEqual(len(lines[4]),frame['shift_count']*frame['staff_count'])
            self.assertEqual(len(lines[5].split(',')),frame['shift_count'])
            self.assertEqual(len(lines[6].split(',')),frame['shift_count'])
            self.assertEqual(len(lines[7].split(',')),frame['staff_count'])
            self.assertNotIn('SIM_',frame['wire'])
        self.assertFalse(b['genuine_wasm_executed'])
        self.assertFalse(b['real_v7_inputSig_verified'])
        self.assertFalse(b['operationally_certified'])

    def test_02_historical_nov30_rest_block_dec1(self):
        b=self.build()
        self.assertEqual(self.bits(b,'door',12,1,6),'0')
        self.assertEqual(self.bits(b,'officer',7,1,5),'0')
        self.assertEqual(self.bits(b,'door',48,1,6),'1')

    def test_03_nov29_same_slot_block_dec1_even_with_two_day_gap(self):
        b=self.build()
        self.assertEqual(self.bits(b,'door',0,1,1),'0')
        self.assertEqual(self.bits(b,'door',0,1,2),'1')

    def test_04_consecutive_sunday_standby_across_month(self):
        b=self.build()
        self.assertEqual(date(2026,11,29).weekday(),6)
        self.assertEqual(date(2026,12,6).weekday(),6)
        self.assertEqual(self.bits(b,'door',4,6,5),'0')
        self.assertEqual(self.bits(b,'door',4,6,1),'1')

    def test_05_leave_and_return_day(self):
        b=self.build()
        self.assertEqual(self.bits(b,'door',48,3,1),'0')
        self.assertEqual(self.bits(b,'door',48,3,6),'1')
        for d in (4,5,6):
            self.assertEqual(self.bits(b,'door',48,d,6),'0')
        self.assertEqual(self.bits(b,'door',48,7,6),'1')

    def test_06_driver(self):
        b=self.build()
        self.assertEqual(self.bits(b,'door',49,9,1),'0')
        self.assertEqual(self.bits(b,'door',49,9,6),'1')
        for d in (10,11):
            self.assertEqual(self.bits(b,'door',49,d,6),'0')
        self.assertEqual(self.bits(b,'door',49,12,6),'1')

    def test_07_exemptions(self):
        b=self.build()
        self.assertEqual(self.bits(b,'door',50,8,1),'0')
        self.assertEqual(self.bits(b,'door',50,8,6),'1')
        self.assertEqual(self.bits(b,'door',51,8,8),'0')
        self.assertEqual(self.bits(b,'door',51,8,6),'1')
        self.assertEqual(self.bits(b,'officer',49,8,6),'0')

    def test_08_officer_nightcheck_meal_training(self):
        b=self.build()
        for day in (11,12,13):
            self.assertEqual(self.bits(b,'officer',40,day,5),'0')
        for day in (16,17,18):
            self.assertEqual(self.bits(b,'officer',41,day,5),'0')
        for day in (23,24,25):
            self.assertEqual(self.bits(b,'officer',42,day,5),'0')
        self.assertEqual(self.bits(b,'officer',42,26,5),'1')

    def test_09_pin_and_forced_blank_positions(self):
        b=self.build()
        for pool,day,slot,expect in [('door',7,6,48),('door',5,8,-1),
                                     ('officer',5,5,48),('officer',6,4,-1)]:
            lines=b['frames'][pool]['wire'].splitlines()
            n=12 if pool=='door' else 7
            self.assertEqual(int(lines[5].split(',')[(day-1)*n+slot-1]),expect)

    def test_10_effective_mask_capacities_are_computed_not_assumed(self):
        b=self.build()
        self.assertLess(b['mask_capacities']['door']['SIM_D_000'],372)
        self.assertLess(b['mask_capacities']['door']['SIM_D_048'],372)
        self.assertEqual(b['mask_capacities']['officer']['SIM_O_049'],0)
        self.assertEqual(len(b['soft_targets']['door']),56)
        self.assertEqual(len(b['soft_targets']['officer']),50)

    def test_11_anchored_original_sources_and_pins_immutable(self):
        for idx in (0,1,2,3,4):
            with self.subTest(source_index=idx):
                parts=deepcopy(self.source)
                if idx==0: parts[0]['pools']['door'][0]['weight']=0.8
                if idx==1: parts[1]['locked']=False
                if idx==2: parts[2]['pools']['officer'][0]['weight']=0.8
                if idx==3: parts[3].pop()
                if idx==4: parts[4].pop('door:2026-12-05:8')
                with self.assertRaisesRegex(RolloverError,'Stale or changed source'):
                    self.build(parts)

    def test_12_missing_independent_anchor_refused(self):
        parts=deepcopy(self.source)
        del parts[5]['events']
        with self.assertRaisesRegex(RolloverError,'anchors'):
            self.build(parts)

    def test_13_pinned_ineligible_person_rejected_even_if_reanchored(self):
        parts=deepcopy(self.source)
        parts[4]['door:2026-12-04:6']='SIM_D_048'
        parts[5]['pins']=_digest(parts[4])
        with self.assertRaisesRegex(RolloverError,'Pinned person is disallowed'):
            self.build(parts)

    def test_14_pin_wrong_duty_pool_rejected(self):
        parts=deepcopy(self.source)
        parts[4]['door:2026-12-07:6']='SIM_O_048'
        parts[5]['pins']=_digest(parts[4])
        with self.assertRaisesRegex(RolloverError,'Wrong-pool'):
            self.build(parts)

    def test_15_illegal_pin_slot_rejected(self):
        parts=deepcopy(self.source)
        parts[4]['officer:2026-12-07:8']=None
        parts[5]['pins']=_digest(parts[4])
        with self.assertRaisesRegex(RolloverError,'Wrong-pool'):
            self.build(parts)

    def test_16_anonymous_returned_pin_only_roster_independently_audits(self):
        b=self.build()
        proof=audit_fictional_solver_response(b,self.pin_only_response(b))
        self.assertEqual((proof['total_shifts'],proof['filled'],proof['missing']),
                         (589,2,587))
        self.assertTrue(proof['independent_full_month_legality_audit'])
        self.assertFalse(proof['genuine_wasm_executed'])
        self.assertFalse(proof['operationally_certified'])

    def test_17_reject_modified_eligibility_result_even_with_adjusted_counts(self):
        b=self.build(); result=self.pin_only_response(b)
        i=(4-1)*12+6-1
        result['door']['assignments'][i]=48
        result['door']['filled']+=1; result['door']['missing']-=1
        with self.assertRaisesRegex(RolloverError,'eligibility mask'):
            audit_fictional_solver_response(b,result)

    def test_18_reject_forced_vacancy_overwrite(self):
        b=self.build(); result=self.pin_only_response(b)
        result['door']['assignments'][(5-1)*12+8-1]=49
        with self.assertRaisesRegex(RolloverError,'Forced blank'):
            audit_fictional_solver_response(b,result)

    def test_19_reject_pinned_person_replacement(self):
        b=self.build(); result=self.pin_only_response(b)
        result['officer']['assignments'][(5-1)*7+5-1]=47
        with self.assertRaisesRegex(RolloverError,'Fixed assignment'):
            audit_fictional_solver_response(b,result)

    def test_20_reject_cross_month_pairwise_conflict(self):
        b=self.build(); result=self.pin_only_response(b)
        # Both eligible statically but same person works on 1 and 2 Dec.
        idx=48
        for d,slot in ((1,6),(2,6)):
            i=(d-1)*12+slot-1
            self.assertEqual(self.bits(b,'door',idx,d,slot),'1')
            result['door']['assignments'][i]=idx
        result['door']['filled']+=2;result['door']['missing']-=2
        with self.assertRaisesRegex(RolloverError,'Conflicting'):
            audit_fictional_solver_response(b,result)

    def test_21_reject_missing_or_corrupted_results(self):
        b=self.build(); result=self.pin_only_response(b)
        del result['officer']
        with self.assertRaisesRegex(RolloverError,'Both pool'):
            audit_fictional_solver_response(b,result)
        result=self.pin_only_response(b)
        result['officer']['assignments'].pop()
        with self.assertRaisesRegex(RolloverError,'Missing assignment rows'):
            audit_fictional_solver_response(b,result)
        result=self.pin_only_response(b)
        result['door']['assignments'][0]=True
        with self.assertRaisesRegex(RolloverError,'Invalid assigned staff'):
            audit_fictional_solver_response(b,result)

    def test_22_status_cannot_certify_optimality(self):
        b=self.build(); result=self.pin_only_response(b)
        result['door']['status']='OPTIMAL'
        proof=audit_fictional_solver_response(b,result)
        self.assertFalse(proof['optimality_independently_proven'])
        result['door']['status']='UNKNOWN'
        with self.assertRaisesRegex(RolloverError,'feasible assignment'):
            audit_fictional_solver_response(b,result)

    def test_23_payload_mutation_rejected(self):
        b=self.build(); result=self.pin_only_response(b)
        b['frames']['door']['wire']=b['frames']['door']['wire'].replace('guard-month-harsh-v4','bad-contract')
        with self.assertRaisesRegex(RolloverError,'altered'):
            audit_fictional_solver_response(b,result)

    def test_24_modified_source_after_export_rejected(self):
        b=self.build(); result=self.pin_only_response(b)
        b['original_sources'][3].append({'kind':'leave'})
        with self.assertRaisesRegex(RolloverError,'Stale or changed source'):
            audit_fictional_solver_response(b,result)


if __name__=='__main__':
    unittest.main()
