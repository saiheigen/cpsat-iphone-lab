"""Only fabricated records; never upload real personnel or previous-month data."""
import copy
import unittest

from solver.phase20_synthetic_rollover import (
    RolloverError, invented_fixture, project_invented_rollover,
)


class SyntheticRolloverTests(unittest.TestCase):
    def setUp(self):
        self.prior, self.archive, self.next, self.anchor = invented_fixture()

    def project(self, **kwargs):
        return project_invented_rollover(self.prior, self.archive, self.next,
            independently_expected_archive_sha256=self.anchor, **kwargs)

    def test_complete_two_pool_handoff(self):
        result = self.project()
        self.assertEqual(result['format'], 'phase20-invented-rollover-preview-v1')
        self.assertEqual(result['month'], '2026-12')
        self.assertEqual(len(self.archive['schedule']['door']),360)
        self.assertEqual(len(self.archive['schedule']['officer']),210)
        self.assertEqual(result['pools']['door']['carry']['SIM_D_000'],2)
        self.assertEqual(result['pools']['officer']['carry']['SIM_O_000'],1)
        self.assertFalse(result['verified_real_v7_inputSig'])
        self.assertFalse(result['operationally_certified'])
        self.assertFalse(result['importable_as_v7_backup'])

    def test_credits_redistribute_only_soft_goals(self):
        result=self.project()
        door=result['pools']['door']
        self.assertGreater(door['base_goals']['SIM_D_000'],
                           door['actual_targets']['SIM_D_000'])
        self.assertEqual(sum(door['actual_targets'].values()),372)
        officer=result['pools']['officer']
        self.assertGreater(officer['base_goals']['SIM_O_000'],
                           officer['actual_targets']['SIM_O_000'])
        self.assertEqual(sum(officer['actual_targets'].values()),217)

    def test_manual_zero_override_wins_only_after_valid_archive(self):
        result=self.project(manual_overrides={'door':{'SIM_D_000':0}})
        self.assertEqual(result['pools']['door']['carry']['SIM_D_000'],0)
        bad=copy.deepcopy(self.archive)
        bad['locked']=False
        with self.assertRaisesRegex(RolloverError,'unlocked'):
            project_invented_rollover(self.prior,bad,self.next,
                independently_expected_archive_sha256=self.anchor,
                manual_overrides={'door':{'SIM_D_000':0}})

    def test_tampered_source_rejected(self):
        self.prior['revision']='SIMULATION-REV-002'
        with self.assertRaisesRegex(RolloverError,'version'):
            self.project()

    def test_original_source_changed_but_not_reanchored(self):
        self.prior['pools']['door'][0]['availability']-=1
        with self.assertRaisesRegex(RolloverError,'stale'):
            self.project()

    def test_wrong_expected_digest_rejected(self):
        self.anchor='0'*64
        with self.assertRaisesRegex(RolloverError,'expected digest'):
            self.project()

    def test_unlocked_snapshot_rejected(self):
        self.archive['locked']=False
        with self.assertRaisesRegex(RolloverError,'unlocked'):
            self.project()

    def test_missing_archive_pool_rejected(self):
        self.archive['schedule'].pop('officer')
        with self.assertRaises(RolloverError):self.project()

    def test_truncated_archive_rejected_even_if_refingerprinted(self):
        # Even a misleadingly updated archive fingerprint may not hide a missing shift.
        self.archive['schedule']['door'].pop()
        from solver.phase20_synthetic_rollover import _digest
        self.archive['schedule_digest']=_digest(self.archive['schedule'])
        self.anchor=_digest(self.archive)
        with self.assertRaisesRegex(RolloverError,'truncated'):
            self.project()

    def test_duplicate_shift_rejected_even_if_refingerprinted(self):
        self.archive['schedule']['door'][1]=list(self.archive['schedule']['door'][0])
        from solver.phase20_synthetic_rollover import _digest
        self.archive['schedule_digest']=_digest(self.archive['schedule'])
        self.anchor=_digest(self.archive)
        with self.assertRaisesRegex(RolloverError,'duplicated'):
            self.project()

    def test_unknown_person_rejected_even_if_refingerprinted(self):
        self.archive['schedule']['officer'][0][2]='SIM_D_000'
        from solver.phase20_synthetic_rollover import _digest
        self.archive['schedule_digest']=_digest(self.archive['schedule'])
        self.anchor=_digest(self.archive)
        with self.assertRaisesRegex(RolloverError,'Wrong-pool'):
            self.project()

    def test_changed_goals_rejected_even_if_refingerprinted(self):
        self.archive['goals']['door']['SIM_D_000']+=1
        from solver.phase20_synthetic_rollover import _digest
        self.anchor=_digest(self.archive)
        with self.assertRaisesRegex(RolloverError,'goals disagree'):
            self.project()

    def test_forged_compensation_rejected_even_if_refingerprinted(self):
        self.archive['compensation_out']['door']['SIM_D_000']=99
        from solver.phase20_synthetic_rollover import _digest
        self.anchor=_digest(self.archive)
        with self.assertRaisesRegex(RolloverError,'compensation disagrees'):
            self.project()

    def test_roster_identity_change_rejected(self):
        self.next['pools']['door'][0]['id']='SIM_D_099'
        with self.assertRaisesRegex(RolloverError,'identity/order changed'):
            self.project()

    def test_no_real_names_or_unknown_manual_carry_allowed(self):
        self.prior['pools']['officer'][0]['id']='actual_person'
        with self.assertRaisesRegex(RolloverError,'non-synthetic'):
            self.project()
        self.prior,self.archive,self.next,self.anchor=invented_fixture()
        with self.assertRaisesRegex(ValueError,'unknown staff'):
            self.project(manual_overrides={'officer':{'NOT_FAKE':3}})

    def test_missing_or_mislabelled_prior_month_rejected(self):
        self.archive['month']='2026-10'
        with self.assertRaisesRegex(RolloverError,'prior archive'):
            self.project()


if __name__=='__main__':
    unittest.main()
