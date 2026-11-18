/* Synthetic-only, offline single-thread CP-SAT WASM Worker.
   Emscripten module source is prepended by the proof-gated HTML packager.
   No network requests, external imports, real records or operational approval. */
"use strict";
let enginePromise=null;
self.postMessage({type:"ready"});
self.onmessage=async function(event){
 const data=event.data;
 if(!data||data.type!=="solve"||!Number.isInteger(data.id))return;
 try{
  if(typeof createMonthHardshipModule!=="function")throw Error("Worker CP-SAT module missing");
  if(typeof data.frame!=="string"||data.frame.length>150000)
   throw Error("Worker frame invalid");
  if(!enginePromise){
   if(!(data.wasm instanceof ArrayBuffer))throw Error("Worker WASM binary missing");
   const binary=new Uint8Array(data.wasm);
   if(!WebAssembly.validate(binary))throw Error("Worker WASM verification failed");
   enginePromise=createMonthHardshipModule({wasmBinary:binary,print:()=>{},printErr:()=>{}});
  }
  const engine=await enginePromise;
  const result=JSON.parse(engine.ccall("solve_guard_month_harsh_v4",
    "string",["string"],[data.frame]));
  self.postMessage({type:"result",id:data.id,result});
 }catch(e){
  self.postMessage({type:"error",id:data.id,error:String(e&&e.stack||e)});
 }
};
