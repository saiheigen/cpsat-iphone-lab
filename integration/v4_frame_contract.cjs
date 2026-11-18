'use strict';
// Synthetic-only, strict anonymous v4 wire decoding. This is NOT verification
// of original v7 inputSig, history, approvals or genuine solver execution.
const {normalize}=require('./phase5_synthetic_adapter.cjs');
const VERSION='guard-month-harsh-v4';
function requireField(ok,message){if(!ok)throw Error(message);}
function parseList(line,pattern,message){
 requireField(pattern.test(line),message);
 return line.split(',').map(Number);
}
function parseFictionalV4Wire(wire,{synthetic_only=false}={}){
 requireField(synthetic_only===true,'Synthetic-only wire required');
 requireField(typeof wire==='string' && wire.length<=150000 &&
  /^[\x20-\x7e\n]+$/.test(wire),'Invalid ASCII wire');
 const parts=wire.split('\n');
 requireField(parts.length===9 && parts[8]==='','Expected eight newline-terminated lines');
 const [version,ym,pool,dimensions,mask,pinsLine,hintsLine,targetsLine]=parts;
 requireField(version===VERSION,'Unsupported v4 contract');
 requireField(/^(20\d\d|2100)-(0[1-9]|1[0-2])$/.test(ym),'Invalid month');
 requireField(pool==='door'||pool==='officer','Unknown duty pool');
 requireField(/^[1-9]\d* [1-9]\d*$/.test(dimensions),'Malformed dimensions');
 const [shifts,staff]=dimensions.split(' ').map(Number);
 const pins=parseList(pinsLine,/^-?(?:0|[1-9]\d*)(?:,-?(?:0|[1-9]\d*))*$/,'Malformed pins');
 const hints=parseList(hintsLine,/^-?(?:0|[1-9]\d*)(?:,-?(?:0|[1-9]\d*))*$/,'Malformed hints');
 const targets=parseList(targetsLine,/^(?:0|[1-9]\d*)(?:,(?:0|[1-9]\d*))*$/,'Malformed targets');
 const result={synthetic_only:true,contract:VERSION,
  year:Number(ym.slice(0,4)),month:Number(ym.slice(5)),pool,
  shifts,staff,mask,pins,hints,targets};
 requireField(normalize(result)===wire,'Non-canonical v4 wire');
 return result;
}
module.exports={parseFictionalV4Wire};
