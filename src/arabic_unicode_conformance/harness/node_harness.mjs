// Copyright 2026 Bayanat Labs
// SPDX-License-Identifier: Apache-2.0
// Node adapter process.
//   node node_harness.mjs icu                      String.prototype.normalize (the ICU library built into Node)
//   node node_harness.mjs arabic-normalize <dir>   the JavaScript port of arabic-normalize, loaded from <dir>/src/index.js
// Protocol: JSON lines {"id", "pipeline", "text" | "bytes_hex"} on stdin, {"id", "pipeline", "output", "error"} on
// stdout. Add --version to print the versions instead.
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';
import { join, resolve } from 'node:path';

const [mode, dir] = process.argv.slice(2);
const versionOnly = process.argv.includes('--version');
let lib = null;
if (mode === 'arabic-normalize') {
  lib = await import(pathToFileURL(join(resolve(dir), 'src', 'index.js')).href);
} else if (mode !== 'icu') {
  console.error('mode must be icu or arabic-normalize');
  process.exit(2);
}

if (versionOnly) {
  const v = { node: process.versions.node, icu: process.versions.icu, icu_unicode: process.versions.unicode };
  if (lib) Object.assign(v, { tool: 'arabic-normalize (JavaScript)', version: lib.LIB_VERSION, unicode: lib.UNICODE_VERSION });
  else Object.assign(v, { tool: 'Node.js String.prototype.normalize (ICU)', version: process.versions.icu });
  console.log(JSON.stringify(v));
  process.exit(0);
}

const decode = (hex) => new TextDecoder('utf-8', { fatal: true }).decode(Uint8Array.from(Buffer.from(hex, 'hex')));

function apply(pipeline, rec) {
  if (mode === 'icu') {
    const text = rec.bytes_hex !== undefined ? decode(rec.bytes_hex) : rec.text;
    if (pipeline === 'icu-nfc') return text.normalize('NFC');
    if (pipeline === 'icu-nfkc') return text.normalize('NFKC');
  } else {
    if (pipeline === 'an-js-nfc' || pipeline === 'an-js-nfkc') {
      const text = rec.bytes_hex !== undefined ? decode(rec.bytes_hex) : rec.text;
      return lib.normalizeForm(text, pipeline === 'an-js-nfc' ? 'NFC' : 'NFKC');
    }
    const policy = pipeline.slice('an-js-'.length);
    if (rec.bytes_hex !== undefined) return lib.normalizeBytes(Uint8Array.from(Buffer.from(rec.bytes_hex, 'hex')), policy);
    return lib.normalize(rec.text, policy);
  }
  throw new Error(`unknown pipeline ${pipeline}`);
}

const rl = createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of rl) {
  if (!line.trim()) continue;
  const rec = JSON.parse(line);
  const out = { id: rec.id, pipeline: rec.pipeline, output: null, error: null };
  try {
    out.output = apply(rec.pipeline, rec);
  } catch (e) {
    out.error = `${e.name}: ${e.reason ?? e.message}`;
  }
  process.stdout.write(JSON.stringify(out) + '\n');
}
