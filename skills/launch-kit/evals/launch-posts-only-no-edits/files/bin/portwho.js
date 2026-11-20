#!/usr/bin/env node
'use strict';
// portwho: which process is holding a port? No dependencies.
const { execFileSync } = require('node:child_process');
const os = require('node:os');

const args = process.argv.slice(2);
const flags = new Set(args.filter((a) => a.startsWith('--')));
const ports = args.filter((a) => /^\d+$/.test(a)).map(Number);

if (flags.has('--help') || ports.length === 0) {
  console.log('Usage: portwho <port> [more ports] [--kill] [--json]');
  process.exit(ports.length === 0 && !flags.has('--help') ? 2 : 0);
}
if (os.platform() === 'win32') {
  console.error('portwho: Windows is not supported yet.');
  process.exit(2);
}

function sh(cmd, argv) {
  try {
    return execFileSync(cmd, argv, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
  } catch {
    return '';
  }
}

function lookup(port) {
  if (os.platform() === 'darwin') {
    // lsof prints: COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
    return sh('lsof', ['-nP', `-iTCP:${port}`, '-sTCP:LISTEN'])
      .split('\n').slice(1).filter(Boolean)
      .map((l) => l.trim().split(/\s+/))
      .map((c) => ({ port, pid: Number(c[1]), command: c[0], user: c[2] }));
  }
  // Linux: ss -ltnpH  ->  ... users:(("node",pid=48213,fd=23))
  return sh('ss', ['-ltnpH', `sport = :${port}`])
    .split('\n').filter(Boolean)
    .map((l) => /users:\(\("([^"]+)",pid=(\d+)/.exec(l))
    .filter(Boolean)
    .map((m) => ({ port, pid: Number(m[2]), command: m[1], user: sh('ps', ['-o', 'user=', '-p', m[2]]).trim() }));
}

const seen = new Set();
const rows = ports.flatMap(lookup).filter((r) => !seen.has(r.pid + ':' + r.port) && seen.add(r.pid + ':' + r.port));

if (flags.has('--json')) {
  console.log(JSON.stringify(rows, null, 2));
} else if (rows.length === 0) {
  console.log(`Nothing is listening on ${ports.join(', ')}.`);
} else {
  const pad = (s, n) => String(s).padEnd(n);
  console.log(pad('PORT', 7) + pad('PID', 8) + pad('COMMAND', 16) + 'USER');
  for (const r of rows) console.log(pad(r.port, 7) + pad(r.pid, 8) + pad(r.command, 16) + r.user);
}

if (flags.has('--kill')) {
  for (const r of rows) {
    try {
      process.kill(r.pid, 'SIGTERM');
      console.log(`Sent SIGTERM to ${r.pid} (${r.command}).`);
    } catch (e) {
      console.error(`Could not kill ${r.pid}: ${e.message}`);
      process.exitCode = 1;
    }
  }
}
