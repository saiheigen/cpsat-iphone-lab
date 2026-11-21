// CI step after building the engine:
// node door-abort-stress.cjs v71.js v71.wasm door30.txt
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { spawnSync } = require('node:child_process');

async function replay(js, wasm, frame) {
  const engine = await require(js)({ wasmBinary: fs.readFileSync(wasm) });
  const reply = JSON.parse(engine.ccall('solve_guard_month_harsh_v4',
    'string', ['string'], [fs.readFileSync(frame, 'utf8')]));
  if (!['FEASIBLE', 'OPTIMAL', 'UNKNOWN'].includes(reply.status) || reply.error || reply.failed_stage) {
    throw new Error('Unexpected solver reply: ' + (reply.error || reply.failure_reason || reply.status));
  }
  console.log('REPLAY_DONE ' + reply.status);
}

function stress(files) {
  if (files.length !== 3) throw new Error('Usage: node door-abort-stress.cjs ENGINE.js ENGINE.wasm FRAME.txt');
  const paths = files.map(file => path.resolve(file));
  for (const file of paths) {
    const digest = createHash('sha256').update(fs.readFileSync(file)).digest('hex');
    console.log(path.basename(file), digest);
  }
  let failed = 0;
  for (let round = 1; round <= 10; round++) {
    const start = Date.now();
    const run = spawnSync(process.execPath, [__filename, '--once', ...paths], {
      encoding: 'utf8', timeout: 120000, killSignal: 'SIGKILL', maxBuffer: 8 * 1024 * 1024
    });
    const logs = [run.stdout || '', run.stderr || ''].join('\n');
    const done = /^REPLAY_DONE (FEASIBLE|OPTIMAL|UNKNOWN)\r?$/m.exec(run.stdout || '');
    const abort = run.signal === 'SIGABRT' || /Aborted\(|native code called abort\(/i.test(logs);
    const ok = !abort && !run.error && run.status === 0 && !!done;
    if (!ok) failed++;
    console.log(JSON.stringify({round, seconds:(Date.now()-start)/1000, ok, abort,
      lastPhase:[...logs.matchAll(/^solver_phase=(\w+)\r?$/gm)].at(-1)?.[1] || null,
      status:done?.[1] || null, exit:run.status, signal:run.signal, error:run.error?.code || null}));
    if (!ok) console.error(logs.slice(-4000));
  }
  console.log('Passed ' + (10-failed) + '/10, failed ' + failed);
  process.exitCode = failed ? 1 : 0;
}

if (process.argv[2] === '--once') {
  replay(...process.argv.slice(3)).catch(error => { console.error(error); process.exitCode = 1; });
} else {
  stress(process.argv.slice(2));
}
