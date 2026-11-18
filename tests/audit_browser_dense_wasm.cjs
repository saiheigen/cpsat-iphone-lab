// Independently audit *actual browser* WASM results against the full
// fictional input and every currently implemented hard constraint.
// No solver code or JS mock. Not iPhone Safari and not production certified.
'use strict';
const fs=require('node:fs');
const crypto=require('node:crypto');
const {createScenario}=require('./wasm_dense_month_benchmark.cjs');
const {independentlyAudit}=require('./month_real_wasm.cjs');

function audit(source) {
 const data=JSON.parse(fs.readFileSync(source,'utf8'));
 if(data.browser_engine!=='actual-offline-Chromium'||
    data.real_iphone_safari!==false||data.synthetic_only!==true||
    data.actual_cpsat_execution!==true)
   throw Error('Untrusted or incorrectly scoped browser provenance');
 const expected=new Set();
 for(const p of ['door','officer'])
  for(const v of ['blackouts-hints','blackouts-no-hints','forced-vacancies'])
   expected.add(p+'|'+v);
 if(!Array.isArray(data.runs)||data.runs.length!==2)
   throw Error('Two real browser profiles required');
 const seenProfiles=new Set();
 const summary=[];
 for(const profile of data.runs){
  if(!profile.completed||!Array.isArray(profile.cases)||profile.cases.length!==6)
   throw Error('Incomplete browser run '+profile.profile);
  if(!['desktop-chromium','mobile-chromium-emulation'].includes(profile.profile)||
     seenProfiles.has(profile.profile))
   throw Error('Unexpected/duplicated browser profile');
  seenProfiles.add(profile.profile);
  const seen=new Set();
  for(const result of profile.cases){
   const key=result.pool+'|'+result.variant;
   if(!expected.has(key)||seen.has(key))throw Error('Missing/duplicate scenario');
   seen.add(key);
   const synthetic=createScenario(result.pool,result.variant);
   const reference=synthetic.witness.filter(x=>x>=0).length;
   if(result.reference_filled!==reference ||
      result.shifts!==synthetic.shiftCount ||
      result.staff!==synthetic.staff)
     throw Error('Incorrect scenario shape or independent witness: '+key);
   const status=result.status,raw=result.solver_response;
   if(!raw||raw.status!==status)throw Error('Status tampering '+key);
   let actual=null;
   let proven=false;
   if(status==='OPTIMAL'||status==='FEASIBLE'){
    actual=independentlyAudit(synthetic,raw);
    if(actual>reference)throw Error('Impossible excess fill '+key);
    if(status==='OPTIMAL'&&actual!==reference)
     throw Error('Incorrect OPTIMAL claim under proven feasible witness '+key);
    proven=actual===reference;
   }else if(status==='UNKNOWN'){
    if(raw.assignments!==undefined||raw.filled!==undefined)
     throw Error('Unknown was presented as a filled roster');
   }else throw Error('Demonstrably feasible benchmark declared '+status);
   summary.push({profile:profile.profile,pool:result.pool,
    variant:result.variant,status,actual_filled:actual,
    independently_validated:actual!==null,
    witness_fill:reference,proven_best_fill:proven,
    elapsed_ms:result.elapsed_ms});
  }
  if(seen.size!==expected.size)throw Error('Missing scenarios for browser profile');
 }
 if(seenProfiles.size!==2||summary.length!==12)
  throw Error('Incomplete synthetic browser acceptance');
 if(!summary.some(x=>x.profile==='desktop-chromium'&&x.proven_best_fill)||
    !summary.some(x=>x.profile==='mobile-chromium-emulation'&&x.proven_best_fill))
  throw Error('Neither/one browser profile reached any proven best fill');
 const report={browser_wasm_independent_audit_passed:true,
  actual_offline_chromium:true,
  actual_iphone_safari:false,
  all_fairness_rules_tested:false,
  full_operational_rules_tested:false,
  complete_cases:summary.length,
  proven_best_cases:summary.filter(s=>s.proven_best_fill).length,
  unknown_cases:summary.filter(s=>s.status==='UNKNOWN').length,
  results:summary};
 return report;
}
const [input,output]=process.argv.slice(2);
if(!input||!output)throw Error('Usage: node audit_browser_dense_wasm.cjs raw_browser_results.json audit_proof.json');
try{
 const result=audit(input);
 fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify(result,null,2));
}catch(e){
 console.error('Independent real-browser WASM audit FAILED:',e);
 process.exitCode=1;
}
