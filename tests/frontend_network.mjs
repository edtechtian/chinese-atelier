import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(new URL('../public/lib.js', import.meta.url), 'utf8');
const {api, download} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const originalFetch = globalThis.fetch;
try {
  globalThis.fetch = async () => { throw new TypeError('Failed to fetch'); };
  for (const action of [() => api('/api/progress', {}), () => download('/api/export', 'test.json')]) {
    await assert.rejects(action, error => error.message.includes('local server is running') && error.message.includes('unsaved work'));
  }
  globalThis.fetch = async () => ({ok: false, json: async () => ({error: 'Complete the required sections first.'}), status: 409});
  await assert.rejects(() => api('/api/progress', {}), error => error.status === 409 && error.message === 'Complete the required sections first.');
} finally {
  globalThis.fetch = originalFetch;
}
console.log('Network failures give actionable guidance; server validation errors are preserved.');
