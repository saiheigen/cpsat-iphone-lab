"""Only invented fixtures and tiny fake WASM; NOT a real solver acceptance."""
from __future__ import annotations
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'build'/'package_fictional_iphone_e2e.py'
spec=importlib.util.spec_from_file_location('fictional_iphone_overlay',MODULE)
pack=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)

class OfflineOverlayTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        p=Path(folder.name)
        self.base=p/'base.html';self.proof=p/'proof.json';self.report=p/'local_report.json';self.output=p/'new.html'
        wasm=b'\0asm\1\0\0\0';glue='var createMonthHardshipModule=function(){};'
        sha=hashlib.sha256(wasm).hexdigest()
        js_hash=hashlib.sha256(glue.encode()).hexdigest()
        self.base.write_text('<!doctype html><html><head><style></style></head><body><main>'+pack.HTML_PLACE+
             '</main><script id="phase5-wasm-glue">'+glue+'</script><script>\n'+
             'const ENCODED="'+base64.b64encode(wasm).decode()+'";\nconst WORKER_BOOTSTRAP="";\n'+
             'function solveWithMode(t,generation){}\nfunction independentlyAudit(t,got){}\n'+
             pack.SEPARATOR,encoding='utf-8')
        self.proof.write_text(json.dumps({'accepted':True,'contract':'guard-month-harsh-v4',
             'operationally_certified':False,'wasm_sha256':sha,'js_sha256':js_hash}))
        # CI has no access to local historical fixtures: construct equivalent
        # invented wire with deterministic sparse bits without names/events.
        frames={}
        for pool,n,staff,allowed,day,slot,idx in [('door',372,56,12,7,6,48),
                                                  ('officer',217,50,7,5,5,48)]:
            mask=['0']*(n*staff)
            pins=[-2]*n
            pins[((5-1)*12+8-1) if pool=='door' else ((6-1)*7+4-1)]=-1
            fixed=(day-1)*(12 if pool=='door' else 7)+slot-1
            mask[fixed*staff+idx]='1';pins[fixed]=idx
            for i in range(allowed-1):
                k=(i+1)%n
                if k==fixed:k=(k+1)%n
                mask[k*staff+(i%staff)]='1'
            wire='\n'.join(['guard-month-harsh-v4','2026-12',pool,f'{n} {staff}',
              ''.join(mask),','.join(map(str,pins)),','.join(['-1']*n),','.join(['0']*staff)])+'\n'
            frames[pool]={'wire':wire,'shift_count':n,'staff_count':staff,'sha256':pack.digest(wire.encode())}
        self.handoff={'invented_only':True,'operationally_certified':False,'frames':frames}
        self.good_report={'synthetic_only':True,'genuine_local_wasm_runtime_verified':True,
              'independent_november_december_audit':True,
              'solver_assignments_accepted':True,'operationally_certified':False,
              'real_v7_inputSig_verified':False,'wasm_sha256':sha,
              'staffed':4,'unfilled':585,'month_rows':589,'pool_staffed':{'door':3,'officer':1},
              'anonymous_input_sha256':{p:frame['sha256'] for p,frame in frames.items()}}
        self.report.write_text(json.dumps(self.good_report))

    def test_verified_base_and_both_immutable_fictional_frames(self):
        result=pack.make(self.base,self.proof,self.report,self.handoff,self.output)
        html=self.output.read_text()
        self.assertIn('一鍵求解目前的虛構條件',html)
        self.assertIn('id="fictional-edit-workspace"',html)
        self.assertIn('fictional-edit-apply',html)
        self.assertIn('fictional-edit-preset',html)
        self.assertIn('fictional-edit-undo',html)
        self.assertIn('fictional-edit-clear',html)
        self.assertIn('不得解除原本禁排',html)
        self.assertNotIn('type="file"',html)
        self.assertNotIn('name="person-name"',html)
        self.assertIn('independent_source_audit_repeated_on_device:false',html)
        self.assertIn('id="fictional-e2e-preview"',html)
        self.assertIn('function solveWithMode(',html)
        self.assertEqual(result['wasm_sha256'],self.good_report['wasm_sha256'])
        self.assertTrue(self.output.stat().st_size>self.base.stat().st_size)
        self.assertNotIn('__FICTIONAL_E2E_SPEC__',html)

    def test_reject_wasm_tamper_without_output(self):
        self.base.write_text(self.base.read_text().replace('AGFzbQE','AWFzbQE'))
        with self.assertRaisesRegex(ValueError,'differs'):
            pack.make(self.base,self.proof,self.report,self.handoff,self.output)
        self.assertFalse(self.output.exists())

    def test_reject_wrong_proof_without_output(self):
        p=json.loads(self.proof.read_text());p['accepted']=False;self.proof.write_text(json.dumps(p))
        with self.assertRaisesRegex(ValueError,'trusted'):
            pack.make(self.base,self.proof,self.report,self.handoff,self.output)
        self.assertFalse(self.output.exists())

    def test_reject_source_handoff_digest_mismatch(self):
        self.good_report['anonymous_input_sha256']['door']='0'*64
        self.report.write_text(json.dumps(self.good_report))
        with self.assertRaisesRegex(ValueError,'independently audited frame differ'):
            pack.make(self.base,self.proof,self.report,self.handoff,self.output)

    def test_never_accept_operational_source_or_false_crossmonth_attestation(self):
        self.good_report['independent_november_december_audit']=False
        self.report.write_text(json.dumps(self.good_report))
        with self.assertRaisesRegex(ValueError,'proof is missing'):
            pack.make(self.base,self.proof,self.report,self.handoff,self.output)
        self.handoff['operationally_certified']=True
        self.report.write_text(json.dumps({**self.good_report,'independent_november_december_audit':True}))
        with self.assertRaises(ValueError):
            pack.make(self.base,self.proof,self.report,self.handoff,self.output)

    def test_fail_if_overwrite_existing_html_or_reuse_injection(self):
        with self.assertRaisesRegex(ValueError,'overwrite'):
            pack.make(self.base,self.proof,self.report,self.handoff,self.base)
        pack.make(self.base,self.proof,self.report,self.handoff,self.output)
        twice=self.output.with_name('two.html')
        with self.assertRaisesRegex(ValueError,'already modified'):
            pack.make(self.output,self.proof,self.report,self.handoff,twice)
        self.assertFalse(twice.exists())

if __name__=='__main__': unittest.main()
