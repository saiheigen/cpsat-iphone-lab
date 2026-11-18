"""No real duty roster and no external services; invented December only."""
from copy import deepcopy
from datetime import date
import unittest

from solver.phase20_synthetic_rollover import RolloverError, _digest
from solver.phase21_synthetic_cross_month_gate import (
    audit_invented_cross_month, imaginary_legal_boundary_fixture,
    empty_next_calendar, place,
)


class ImaginaryCrossMonthTests(unittest.TestCase):
    def setUp(self):
        self.source, self.archive, self.next_source, self.anchor = (
            imaginary_legal_boundary_fixture())
        self.proposed = empty_next_calendar()

    def audit(self, **kw):
        return audit_invented_cross_month(
            self.source, self.archive, self.next_source, self.proposed,
            expected_archive_sha256=self.anchor, **kw)

    def _archive_rehash(self):
        self.archive['schedule_digest'] = _digest(self.archive['schedule'])
        self.anchor = _digest(self.archive)

    def test_01_legally_spaced_prior_month_complete_both_pools(self):
        x=self.audit()
        self.assertEqual((x['prior_rows'],x['upcoming_rows']), (570,589))
        self.assertEqual((x['prior_filled'],x['next_missing']), (570,589))
        self.assertTrue(x['cross_month_duty_eligibility_audited'])
        self.assertFalse(x['operationally_certified'])
        self.assertFalse(x['verified_real_v7_inputSig'])
        self.assertFalse(x['archive_authenticity_verified'])
        self.assertFalse(x['genuine_wasm_executed'])
        self.assertFalse(x['source_aligned_full_v7_rules_verified'])
        self.assertFalse(x['importable_as_v7_backup'])

    def test_02_actual_fictional_carry_is_derived_from_legal_prior_history(self):
        x=self.audit()
        self.assertTrue(any(n>0 for n in x['carry']['door'].values()))
        self.assertTrue(any(n>0 for n in x['carry']['officer'].values()))
        self.assertTrue(x['carry_forward_calculated'])

    def test_03_legal_first_day_and_next_sunday_in_both_pools(self):
        place(self.proposed,'door',1,6,'SIM_D_048')
        place(self.proposed,'officer',1,7,'SIM_O_040')
        place(self.proposed,'door',6,5,'SIM_D_027')
        place(self.proposed,'officer',6,7,'SIM_O_036')
        x=self.audit()
        self.assertEqual((x['next_filled'],x['next_missing']), (4,585))

    def test_04_november_30_blocks_december_1_stand_one_rest_one_guard(self):
        # SIM_D_017 stood one guard duty on 30 November.
        place(self.proposed,'door',1,4,'SIM_D_017')
        with self.assertRaisesRegex(RolloverError,'Conflicting'):
            self.audit()

    def test_05_november_30_blocks_december_1_officer(self):
        place(self.proposed,'officer',1,4,'SIM_O_009')
        with self.assertRaisesRegex(RolloverError,'Conflicting'):
            self.audit()

    def test_06_november_29_same_slot_blocks_december_1_guard(self):
        place(self.proposed,'door',1,6,'SIM_D_005')
        with self.assertRaisesRegex(RolloverError,'same-slot'):
            self.audit()

    def test_07_november_29_same_slot_blocks_december_1_officer(self):
        place(self.proposed,'officer',1,7,'SIM_O_006')
        with self.assertRaisesRegex(RolloverError,'same-slot'):
            self.audit()

    def test_08_two_consecutive_sundays_guard_standby_blocked(self):
        self.assertEqual(date(2026,11,29).weekday(),6)
        self.assertEqual(date(2026,12,6).weekday(),6)
        place(self.proposed,'door',6,5,'SIM_D_004')
        with self.assertRaisesRegex(RolloverError,'Sunday'):
            self.audit()

    def test_09_two_consecutive_sundays_officer_standby_blocked(self):
        place(self.proposed,'officer',6,7,'SIM_O_006')
        with self.assertRaisesRegex(RolloverError,'Sunday'):
            self.audit()

    def test_10_sunday_night_guard_not_standby_by_partial_native_rules(self):
        place(self.proposed,'door',6,1,'SIM_D_000')
        result=self.audit()
        self.assertEqual(result['next_filled'],1)

    def test_11_return_from_leave_on_december_1_blocks_fictional_guard(self):
        place(self.proposed,'door',1,6,'SIM_D_048')
        with self.assertRaisesRegex(RolloverError,'event prohibition'):
            self.audit(invented_events=[{'pool':'door','person':'SIM_D_048',
                'kind':'leave','start':'2026-11-30','end':'2026-11-30'}])

    def test_12_night_inspection_november_30_blocks_december_1(self):
        place(self.proposed,'officer',1,5,'SIM_O_040')
        with self.assertRaisesRegex(RolloverError,'event prohibition'):
            self.audit(invented_events=[{'pool':'officer','person':'SIM_O_040',
                'kind':'nightcheck','start':'2026-11-30','end':'2026-11-30'}])

    def test_13_driver_november_30_blocks_december_1(self):
        place(self.proposed,'door',1,6,'SIM_D_048')
        with self.assertRaisesRegex(RolloverError,'event prohibition'):
            self.audit(invented_events=[{'pool':'door','person':'SIM_D_048',
                'kind':'driver','start':'2026-11-30','end':'2026-11-30'}])

    def test_14_driving_next_day_pre_night_prohibition(self):
        place(self.proposed,'door',1,1,'SIM_D_048')
        with self.assertRaisesRegex(RolloverError,'event prohibition'):
            self.audit(invented_events=[{'pool':'door','person':'SIM_D_048',
                'kind':'driver','start':'2026-12-02','end':'2026-12-02'}])

    def test_15_leave_before_night_blocked_but_day_allowed(self):
        ev=[{'pool':'door','person':'SIM_D_048','kind':'leave',
             'start':'2026-12-02','end':'2026-12-02'}]
        place(self.proposed,'door',1,1,'SIM_D_048')
        with self.assertRaisesRegex(RolloverError,'event prohibition'):
            self.audit(invented_events=ev)
        place(self.proposed,'door',1,1,None)
        place(self.proposed,'door',1,6,'SIM_D_048')
        self.assertEqual(self.audit(invented_events=ev)['next_filled'],1)

    def test_16_training_previous_day_prohibited(self):
        place(self.proposed,'officer',1,5,'SIM_O_040')
        with self.assertRaisesRegex(RolloverError,'event prohibition'):
            self.audit(invented_events=[{'pool':'officer','person':'SIM_O_040',
                'kind':'training','start':'2026-12-02','end':'2026-12-03'}])

    def test_17_officer_duty_and_meal_early_month_blocked(self):
        for kind in ('officer_duty','meal'):
            with self.subTest(kind=kind):
                place(self.proposed,'officer',1,7,'SIM_O_040')
                with self.assertRaisesRegex(RolloverError,'event prohibition'):
                    self.audit(invented_events=[{'pool':'officer','person':'SIM_O_040',
                        'kind':kind,'start':'2026-12-02','end':'2026-12-02'}])

    def test_18_exemptions_night_noon_and_full(self):
        for kind,slot in [('exempt_night',1),('exempt_noon',8),('exempt_all',6)]:
            with self.subTest(kind=kind):
                place(self.proposed,'door',1,slot,'SIM_D_048')
                with self.assertRaisesRegex(RolloverError,'event prohibition'):
                    self.audit(invented_events=[{'pool':'door','person':'SIM_D_048',
                        'kind':kind,'start':'2026-12-01','end':'2026-12-01'}])
                self.proposed=empty_next_calendar()

    def test_19_duplicate_duty_same_day_officer_rejected(self):
        place(self.proposed,'officer',1,4,'SIM_O_040')
        place(self.proposed,'officer',1,5,'SIM_O_040')
        with self.assertRaisesRegex(RolloverError,'Per-day maximum'):
            self.audit()

    def test_20_guard_same_day_minimum_six_hour_interval(self):
        place(self.proposed,'door',1,4,'SIM_D_048')
        place(self.proposed,'door',1,5,'SIM_D_048')
        with self.assertRaisesRegex(RolloverError,'Conflicting'):
            self.audit()
        place(self.proposed,'door',1,5,None)
        place(self.proposed,'door',1,9,'SIM_D_048')
        self.assertEqual(self.audit()['next_filled'],2)

    def test_21_second_day_next_month_stand_one_rest_one(self):
        place(self.proposed,'door',1,6,'SIM_D_048')
        place(self.proposed,'door',2,7,'SIM_D_048')
        with self.assertRaisesRegex(RolloverError,'Conflicting'):
            self.audit()

    def test_22_prior_archive_internal_conflict_rejected_even_if_fingerprints_recomputed(self):
        # Swap two fictional persons between day 1 and day 5, so day 1
        # and day 5 each carry an illegal same-person pair, but per-person
        # total worked-counts and compensation numbers do not change.
        schedule=self.archive['schedule']['door']
        schedule[5][2],schedule[4*12+6][2] = schedule[4*12+6][2],schedule[5][2]
        self._archive_rehash()
        with self.assertRaisesRegex(RolloverError,'Conflicting'):
            self.audit()

    def test_23_prior_consecutive_sunday_standby_rejected(self):
        # Move Nov30's cohort-1 guard 06-08 assignment to Nov29 06-08,
        # while the same fictional person already staffed Nov22 06-08.
        schedule=self.archive['schedule']['door']
        nov29=(29-1)*12+4
        nov30=(30-1)*12+4
        schedule[nov29][2],schedule[nov30][2] = (
            schedule[nov30][2],schedule[nov29][2])
        self._archive_rehash()
        with self.assertRaisesRegex(RolloverError,'Sunday'):
            self.audit()

    def test_24_edited_archive_fingerprint_rejected_before_legality(self):
        self.archive['locked']=False
        with self.assertRaisesRegex(RolloverError,'unlocked'):
            self.audit()

    def test_25_stale_previous_source_rejected(self):
        self.source['pools']['door'][0]['weight'] = 0.8
        with self.assertRaisesRegex(RolloverError,'stale'):
            self.audit()

    def test_26_missing_589_row_december_schedule_rejected(self):
        self.proposed['officer'].pop()
        with self.assertRaisesRegex(RolloverError,'Incomplete duty calendar'):
            self.audit()

    def test_27_wrong_pool_person_in_december_rejected(self):
        place(self.proposed,'officer',1,1,'SIM_D_048')
        with self.assertRaisesRegex(RolloverError,'wrong-pool'):
            self.audit()

    def test_28_reordered_december_schedule_rejected(self):
        rows=self.proposed['door']
        rows[0],rows[1] = rows[1],rows[0]
        with self.assertRaisesRegex(RolloverError,'reordered'):
            self.audit()

    def test_29_unknown_fictional_event_type_rejected(self):
        with self.assertRaisesRegex(RolloverError,'Unknown fictional event'):
            self.audit(invented_events=[{'pool':'door','person':'SIM_D_048',
                'kind':'unknown','start':'2026-12-01','end':'2026-12-01'}])

    def test_30_malformed_event_date_rejected(self):
        with self.assertRaisesRegex(RolloverError,'Invalid event calendar'):
            self.audit(invented_events=[{'pool':'door','person':'SIM_D_048',
                'kind':'leave','start':'2026-12-32','end':'2026-12-32'}])

    def test_31_unknown_person_event_rejected(self):
        with self.assertRaisesRegex(RolloverError,'not in duty pool'):
            self.audit(invented_events=[{'pool':'door','person':'ACTUAL_NAME',
                'kind':'leave','start':'2026-12-01','end':'2026-12-01'}])

    def test_32_changed_next_month_roster_rejected(self):
        self.next_source['pools']['officer'][0]['id']='SIM_O_099'
        with self.assertRaisesRegex(RolloverError,'identity/order changed'):
            self.audit()

    def test_33_manual_zero_override_preserved_but_not_a_permission(self):
        x=self.audit(manual_overrides={'door':{'SIM_D_000':0}})
        self.assertEqual(x['carry']['door']['SIM_D_000'],0)
        self.assertFalse(x['operationally_certified'])


if __name__=='__main__':
    unittest.main()
