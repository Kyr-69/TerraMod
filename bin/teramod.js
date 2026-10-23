#!/usr/bin/env node
/**
 * bin/teramod.js
 * Node.js runner for TerraMod.
 * Automatically detects CLI vs MCP Server execution mode.
 */
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT_DIR = path.resolve(__dirname, '..');
const SERVER_PY = path.join(ROOT_DIR, 'server.py');
const CLI_PY = path.join(ROOT_DIR, 'cli.py');

// Verify python3 availability
const pythonBin = process.env.PYTHON || 'python3';

const args = process.argv.slice(2);

// Mode detection:
// If stdin is NOT a TTY (piped by MCP client like Hermes/Claude/Cursor) or --mcp flag passed:
// Run server.py as MCP Server over stdio.
// Otherwise, run cli.py.
const isMcpMode = args.includes('--mcp') || (!process.stdin.isTTY && args.length === 0);

if (isMcpMode) {
  const child = spawn(pythonBin, [SERVER_PY], {
    stdio: ['pipe', 'pipe', 'inherit'],
    cwd: ROOT_DIR
  });

  process.stdin.pipe(child.stdin);
  child.stdout.pipe(process.stdout);

  child.on('error', (err) => {
    console.error(`[teramod] Failed to launch python backend: ${err.message}`);
    process.exit(1);
  });

  child.on('exit', (code) => {
    process.exit(code || 0);
  });
} else {
  const cleanArgs = args.filter((a) => a !== '--mcp');
  const child = spawn(pythonBin, [CLI_PY, ...cleanArgs], {
    stdio: 'inherit',
    cwd: process.cwd()
  });

  child.on('error', (err) => {
    console.error(`[teramod] Failed to execute CLI: ${err.message}`);
    process.exit(1);
  });

  child.on('exit', (code) => {
    process.exit(code || 0);
  });
}
