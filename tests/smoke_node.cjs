'use strict';
// Requires emcc-generated dist/smoke.js (SINGLE_FILE=1).
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
async function main() {
  const p = path.resolve(__dirname, '../dist/smoke.js');
  assert.ok(fs.existsSync(p), 'Missing compiled Emscripten JS');
  const createModule = require(p);
  assert.equal(typeof createModule, 'function', 'Expected modularized WASM factory');
  const instance = await createModule();
  assert.equal(typeof instance._smoke_add, 'function', 'Missing exported C function');
  assert.equal(instance._smoke_add(17, 25), 42);
  console.log('PASS: native Node runtime executed Emscripten WebAssembly, 17+25=42');
  console.log('NOT A CP-SAT TEST');
}
main().catch(e => { console.error(e); process.exitCode = 1; });
