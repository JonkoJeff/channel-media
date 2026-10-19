import { createRequire } from 'module';
import path from 'path'; import url from 'url'; import fs from 'fs';
let chromium; try { ({ chromium } = createRequire(import.meta.url)('playwright')); } catch { ({ chromium } = createRequire(process.env.PW_REQUIRE || '/home/claude/.npm-global/lib/node_modules/')('playwright')); }
const HERE = path.dirname(url.fileURLToPath(import.meta.url));
// node thumbs.mjs <outdir> <episode.json>: long thumbnail from ep.thumb, one cover per Short from segment.short.cover
const out = process.argv[2], ep = JSON.parse(fs.readFileSync(process.argv[3])); fs.mkdirSync(out, { recursive: true });
const jobs = [[ep.id + '_long', ep.thumb, true], ...ep.segments.filter(s => s.short && s.short.cover).map(s => [ep.id + '_short_' + s.id, s.short.cover, false])];
const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
for (const [n, spec, long] of jobs) {
  const p = await b.newPage({ viewport: long ? { width: 1280, height: 720 } : { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.error('ERR', e.message));
  await p.goto('file://' + path.join(HERE, 'thumbs.html')); await p.waitForFunction(() => window.ready, null, { timeout: 20000 });
  await p.evaluate(([s, l]) => window.renderThumbSpec(s, l), [spec, long]);
  await p.screenshot({ path: `${out}/${n}.jpg`, type: 'jpeg', quality: 92 }); await p.close();
}
await b.close();
