"""Offline fictional Python -> JS v4 wire conformance; no military data / cloud CI."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from solver.phase22_synthetic_solver_handoff import fictional_source_fixture, build_fictional_handoff

ROOT=Path(__file__).resolve().parents[1]
JS='''const fs=require('node:fs');
const {parseFictionalV4Wire}=require('./integration/v4_frame_contract.cjs');
const {normalize}=require('./integration/phase5_synthetic_adapter.cjs');
const request=JSON.parse(fs.readFileSync(0,'utf8'));
try{
 const result=parseFictionalV4Wire(request.wire,{synthetic_only:true});
 if(normalize(result)!==request.wire)throw Error('wire roundtrip changed');
 process.stdout.write(JSON.stringify({ok:true,staff:result.staff,shifts:result.shifts,
  pool:result.pool,pins:result.pins,hints:result.hints,targets:result.targets}));
}catch(error){process.stdout.write(JSON.stringify({ok:false,error:error.message}));}
'''

@unittest.skipUnless(shutil.which('node'), 'Node.js needed for Python/JS conformance')
class V4WireContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parts=fictional_source_fixture()
        p,a,n,e,pins,anchors=cls.parts
        cls.handoff=build_fictional_handoff(p,a,n,e,pins,expected_anchors=anchors)

    def check_js(self,wire):
        proc=subprocess.run(['node','-e',JS],input=json.dumps({'wire':wire}),
            cwd=ROOT,capture_output=True,text=True,timeout=30,check=True)
        return json.loads(proc.stdout)

    def test_both_original_full_months_are_byte_identical(self):
        for pool in ('door','officer'):
            with self.subTest(pool=pool):
                frame=self.handoff['frames'][pool]
                result=self.check_js(frame['wire'])
                self.assertTrue(result['ok'],result)
                self.assertEqual(result['pool'],pool)
                self.assertEqual(result['staff'],frame['staff_count'])
                self.assertEqual(result['shifts'],frame['shift_count'])
                self.assertEqual(len(result['pins']),frame['shift_count'])
                self.assertEqual(len(result['hints']),frame['shift_count'])
                self.assertEqual(len(result['targets']),frame['staff_count'])

    def test_forced_blanks_and_fixed_people_preserved(self):
        for pool,day,slot,expected in (('door',5,8,-1),('door',7,6,48),
                                        ('officer',6,4,-1),('officer',5,5,48)):
            with self.subTest(pool=pool,day=day,slot=slot):
                result=self.check_js(self.handoff['frames'][pool]['wire'])
                self.assertTrue(result['ok'])
                slots=12 if pool=='door' else 7
                self.assertEqual(result['pins'][(day-1)*slots+slot-1],expected)

    def test_truncated_or_noncanonical_frames_fail_closed(self):
        wire=self.handoff['frames']['door']['wire']
        for invalid in (wire.rstrip('\n'), wire.replace('\n','\r\n'),
                        wire.replace('guard-month-harsh-v4','guard-month-v2',1),
                        wire.replace('372 56','372 057',1),
                        wire.replace('2026-12\n','2026-13\n',1)):
            with self.subTest(example=invalid[:35]):
                self.assertFalse(self.check_js(invalid)['ok'])

    def test_conflicting_hints_and_pins_fail_closed(self):
        original=self.handoff['frames']['door']['wire'].splitlines()
        # Fixture has one pinned, available person; a hint to another eligible
        # person must never override the fixed original assignment.
        row=(7-1)*12+6-1
        pin=int(original[5].split(',')[row])
        mask=original[4]
        alternate=next(p for p in range(56) if p!=pin and mask[row*56+p]=='1')
        hints=original[6].split(','); hints[row]=str(alternate)
        changed=original[:];changed[6]=','.join(hints)
        self.assertFalse(self.check_js('\n'.join(changed)+'\n')['ok'])
        blankrow=(5-1)*12+8-1
        hints=original[6].split(',');hints[blankrow]='0'
        changed=original[:];changed[6]=','.join(hints)
        self.assertFalse(self.check_js('\n'.join(changed)+'\n')['ok'])

if __name__=='__main__':
    unittest.main()
