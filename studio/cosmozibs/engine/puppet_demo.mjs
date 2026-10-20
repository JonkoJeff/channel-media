// node puppet_demo.mjs outdir [frames] : renders the puppet demo frames (1080x1920)
import { createRequire } from 'module'; import fs from 'fs'; import path from 'path'; import url from 'url';
let chromium; try { ({ chromium } = createRequire(import.meta.url)('playwright')); } catch { ({ chromium } = createRequire(process.env.PW_REQUIRE || '/home/claude/.npm-global/lib/node_modules/')('playwright')); }
const [,, out, list = ''] = process.argv; const HERE = path.dirname(url.fileURLToPath(import.meta.url)); fs.mkdirSync(out, { recursive: true });
const b = await chromium.launch({ args: ['--allow-file-access-from-files'] }); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
p.on('pageerror', e => console.error('ERR', e.message)); await p.goto('file://' + path.join(HERE, 'index.html')); await p.waitForFunction(() => window.ready, null, { timeout: 20000 });
const frames = list ? list.split(',').map(Number) : Array.from({ length: +(process.env.NFR || 120) }, (_, i) => i);
for (const f of frames) { await p.evaluate(([f, fn]) => window[fn](f), [f, process.env.FRAMEFN || "puppetFrame"]); await p.screenshot({ path: `${out}/f${String(f).padStart(4, '0')}.jpg`, type: 'jpeg', quality: 90 }); }
await b.close();
