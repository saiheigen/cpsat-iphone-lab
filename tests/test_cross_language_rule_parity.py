"""Synthetic same-month temporal rule truth table: independent Python vs JS.

No OR-Tools dependency. Does NOT certify operational v7, cross-month history,
or C++ WASM runtime. It checks parity for the shared partial rule subset.
"""
from __future__ import annotations
from datetime import date
import json
from pathlib import Path
import shutil
import subprocess
import unittest

from solver.phase21_synthetic_cross_month_gate import _conflict, _standby

ROOT=Path(__file__).resolve().parents[1]
JS=r"""
'use strict';
const fs=require('node:fs');
const {independentlyAudit}=require('./integration/month_audit.cjs');
const cases=JSON.parse(fs.readFileSync(0,'utf8'));
const errors=[];
for(let i=0;i<cases.length;i++){
 const t=cases[i],slots=t.pool==='door'?12:7,days=31,n=slots*days;
 const allowed=Array(n).fill('0'),assignments=Array(n).fill(-1),pins=Array(n).fill(-2);
 for(const [day,slot] of t.duties){
  const index=(day-1)*slots+slot-1;
  allowed[index]='1';assignments[index]=0;
 }
 let legal=true;
 try{independentlyAudit({year:2026,month:12,pool:t.pool,staff:1,
    shiftCount:n,allowed:allowed.join(''),pins,hints:Array(n).fill(-1)},
    {assignments,filled:t.duties.length,missing:n-t.duties.length});}
 catch(_){legal=false;}
 if(legal!==t.expected_legal)errors.push({case:i,pool:t.pool,duties:t.duties,
    python_legal:t.expected_legal,js_legal:legal});
}
process.stdout.write(JSON.stringify({count:cases.length,errors}));
"""

@unittest.skipUnless(shutil.which('node'), 'Node.js required for JS rule parity')
class CrossLanguageTemporalRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=[]
        day_pairs=((1,1),(1,2),(1,3),(1,4),(6,13),(6,20),
                   (13,20),(20,27),(24,31),(30,31),(1,31))
        for pool,slots in (('door',12),('officer',7)):
            for da,db in day_pairs:
                for sa in range(1,slots+1):
                    for sb in range(1,slots+1):
                        if da==db and sa==sb:
                            continue
                        a=(pool,'SIM_RULE_PERSON',date(2026,12,da),sa)
                        b=(pool,'SIM_RULE_PERSON',date(2026,12,db),sb)
                        cls.cases.append({'pool':pool,'duties':[[da,sa],[db,sb]],
                                          'expected_legal':not _conflict(a,b)})

    def test_cross_language_same_month_conflict_truth_table(self):
        res=subprocess.run(['node','-e',JS],input=json.dumps(self.cases),
            text=True,capture_output=True,cwd=ROOT,timeout=30,check=True)
        actual=json.loads(res.stdout)
        self.assertEqual(actual['count'],len(self.cases))
        self.assertEqual(actual['errors'],[],actual['errors'][:8])

    def test_sunday_edges_are_explicit(self):
        self.assertTrue(_standby('door',date(2026,12,6),5))
        self.assertTrue(_standby('door',date(2026,12,13),11))
        self.assertFalse(_standby('door',date(2026,12,6),12))
        self.assertTrue(_standby('officer',date(2026,12,6),7))
        self.assertFalse(_standby('officer',date(2026,12,6),6))
        self.assertTrue(_conflict(('door','SIM',date(2026,12,6),5),
                                  ('door','SIM',date(2026,12,13),11)))
        self.assertFalse(_conflict(('door','SIM',date(2026,12,6),5),
                                   ('door','SIM',date(2026,12,6),10)))

    def test_fixed_month_full_grid_is_not_the_entire_v7_scope(self):
        self.assertGreater(len(self.cases),1000)
        self.assertEqual({x['pool'] for x in self.cases},{'door','officer'})

if __name__=='__main__':
    unittest.main()
