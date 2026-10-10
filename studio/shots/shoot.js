// Takes the screenshots listed in studio/channels/<ch>/shots.json ([{file, url}]) that don't exist yet (1920 wide, full page).
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, locale: 'en-US' });
  for (const ch of fs.readdirSync('studio/channels')) {
    const list = path.join('studio/channels', ch, 'shots.json'); if (!fs.existsSync(list)) continue;
    const dir = path.join('studio/channels', ch, 'shots'); fs.mkdirSync(dir, { recursive: true });
    for (const s of JSON.parse(fs.readFileSync(list))) {
      const out = path.join(dir, s.file); if (fs.existsSync(out)) continue;
      try {
        await p.goto(s.url, { waitUntil: 'networkidle', timeout: 60000 });
        for (const t of ['Accept', 'Accept all', 'Accept All', 'I agree', 'Got it', 'OK']) { const x = p.getByRole('button', { name: t, exact: true }); if (await x.count()) { await x.first().click().catch(() => {}); break; } }
        await p.waitForTimeout(1500); await p.screenshot({ path: out, fullPage: true }); console.log('ok', s.url);
      } catch (e) { console.log('::warning::' + s.url + ' ' + e.message.slice(0, 150)); }
    }
  }
  await b.close();
})();
