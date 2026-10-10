// Screenshots of public web pages for explainer videos (1920x1080, plus a full-page version). Cookie banners are dismissed when possible.
const { chromium } = require('playwright');
(async () => {
  const [name, ...urls] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1, locale: 'en-US' });
  for (const [i, u] of urls.entries()) {
    try {
      await p.goto(u, { waitUntil: 'networkidle', timeout: 60000 });
      for (const t of ['Accept', 'Accept all', 'I agree', 'Got it', 'OK']) { const btn = p.getByRole('button', { name: t, exact: true }); if (await btn.count()) { await btn.first().click().catch(() => {}); break; } }
      await p.waitForTimeout(1500);
      await p.screenshot({ path: `studio/shots/${name}-${i + 1}.png` });
      await p.screenshot({ path: `studio/shots/${name}-${i + 1}-full.png`, fullPage: true });
      console.log('ok', u);
    } catch (e) { console.log('::warning::' + u + ' ' + e.message.slice(0, 150)); }
  }
  await b.close();
})();
