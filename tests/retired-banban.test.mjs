import test from 'node:test';
import assert from 'node:assert/strict';
import {onRequest} from '../functions/_middleware.js';

test('old Banban dashboard links are gone without calling assets or data', async () => {
  for (const path of ['/admin-reactions', '/admin-reactions.html', '/admin-reactions/']) {
    const response = await onRequest({request: new Request('https://iwata-monogatari.net' + path + '?site=banban'), next() { throw Error('must not read data'); }});
    assert.equal(response.status, 410);
    assert.equal(response.headers.get('Cache-Control'), 'no-store');
    assert.match(await response.text(), /公開を終了しました/);
  }
});

test('article dashboards keep their existing route', async () => {
  for (const site of ['iwata', 'oishi', 'all']) {
    const response = await onRequest({request: new Request('https://iwata-monogatari.net/admin-reactions?site=' + site), next() { return new Response('article-dashboard'); }});
    assert.equal(response.status, 200);
    assert.equal(await response.text(), 'article-dashboard');
  }
});
