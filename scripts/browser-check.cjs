/* Run with Playwright available and a local server on the supplied URL. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const base = process.argv[2] || 'http://127.0.0.1:8768/';
const data = JSON.parse(fs.readFileSync(path.join(__dirname, '../content/data.json'), 'utf8'));

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, permissions: ['clipboard-read','clipboard-write'] });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.goto(base);
  assert.equal(await page.locator('.home-cards .topic-card').count(), 3);
  await page.getByRole('button', { name: '加入我们' }).click();
  assert.equal(await page.locator('#join-dialog').evaluate(el => el.open), true);
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('#join-dialog').evaluate(el => el.open), false);
  await page.getByRole('button', { name: '切换深浅色' }).click();
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
  await page.screenshot({ path: '/tmp/guanlan-complete-dark.png', fullPage: true });
  await page.getByRole('button', { name: '切换深浅色' }).click();

  for (const topic of data.topics) {
    const response = await page.goto(base + 'topics/' + topic.id + '/');
    assert.equal(response.status(), 200);
    assert.equal(await page.locator('h1').count(), 1);
    assert.equal(await page.getByRole('link', { name: '为什么这样整理 →' }).count(), 1);
    assert.equal(await page.locator('.voice').count() > 0, true);
  }
  await page.goto(base + 'topics/t19/');
  await page.getByRole('link', { name: '为什么这样整理 →' }).click();
  assert(page.url().endsWith('/topics/t19/analysis/'));
  assert.equal(await page.locator('.prose').first().locator('section').count(), 3);
  await page.getByRole('button', { name: '收藏这篇', exact: true }).click();
  await page.goto(base + 'saved/');
  assert.equal(await page.locator('#saved-list li').count(), 1);
  await page.locator('#saved-list a').click();
  assert(page.url().endsWith('/topics/t19/'));
  await page.getByRole('button', { name: '复制链接' }).click();
  await page.waitForFunction(() => document.querySelector('[data-copy-link]').textContent === '链接已复制');
  assert.equal(await page.evaluate(() => navigator.clipboard.readText()), page.url());

  await page.goto(base + 'search/?q=' + encodeURIComponent('99'));
  assert(await page.locator('#search-results li').count() > 0);
  assert((await page.locator('#search-results').innerText()).includes('99'));
  await page.locator('#search-input').fill('不存在的词123zzz');
  await page.locator('#search-form button').click();
  assert((await page.locator('#search-count').innerText()).includes('没有找到'));
  await page.goto(base + '#source/s43');
  await page.waitForURL('**/sources/s43/');
  assert.equal(await page.locator('blockquote').innerText(), data.sources.find(s => s.id === 's43').text);
  await page.goto(base + '#read');
  await page.waitForURL('**/topics/');

  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    for (const route of ['', 'topics/', 'categories/workflow/', 'topics/t19/', 'topics/t16/analysis/', 'people/p01/', 'sources/s80/', 'skills/', 'community/', 'practice/', 'search/?q=AI']) {
      await page.goto(base + route);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
      assert.equal(overflow, false, `${width}px overflow: ${route}`);
    }
  }
  await page.setViewportSize({ width:390, height:844 });
  await page.goto(base);
  await page.getByRole('button', { name: '加入我们' }).click();
  await page.locator('#join-dialog img').screenshot({ path: '/tmp/guanlan-live-mobile-qr.png' });
  await page.getByRole('button', { name: '关闭', exact:true }).click();

  const expiredContext = await browser.newContext();
  await expiredContext.addInitScript(() => {
    const NativeDate = Date;
    window.Date = class extends NativeDate { constructor(...args) { super(...(args.length ? args : ['2026-10-02T00:00:00Z'])); } static now() { return new NativeDate('2026-10-02T00:00:00Z').getTime(); } };
  });
  const expiredPage = await expiredContext.newPage();
  await expiredPage.goto(base + 'join/');
  assert.equal(await expiredPage.locator('main [data-qr-expired]').isVisible(), true);
  assert.equal(await expiredPage.locator('main [data-qr-current]').isVisible(), false);
  await expiredContext.close();

  const noJsContext = await browser.newContext({ javaScriptEnabled:false });
  const noJsPage = await noJsContext.newPage();
  await noJsPage.goto(base + 'topics/t19/analysis/');
  assert((await noJsPage.locator('main').innerText()).includes('写代码省下的时间'));
  await noJsContext.close();
  assert.deepEqual(errors, []);
  await browser.close();
  console.log('PASS: all 38 topics, reading/source navigation, search, legacy links, saved items, copy, themes, mobile widths, QR expiry, and no-JS reading.');
})().catch(error => { console.error(error); process.exit(1); });
