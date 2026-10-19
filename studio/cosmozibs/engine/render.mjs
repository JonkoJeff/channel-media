// node render.mjs <timeline.json> <long|short> <outdir> <from> <to> [shortTitle] [frameList]
import { createRequire } from 'module';
import fs from 'fs'; import path from 'path'; import url from 'url';
let chromium; try { ({ chromium } = createRequire(import.meta.url)('playwright')); } catch { ({ chromium } = createRequire(process.env.PW_REQUIRE || '/home/claude/.npm-global/lib/node_modules/')('playwright')); }
const [,, tlPath, layout, out, from, to, title = '', list = ''] = process.argv;
const HERE = path.dirname(url.fileURLToPath(import.meta.url));
const tl = JSON.parse(fs.readFileSync(tlPath)); fs.mkdirSync(out, { recursive: true });
const [W, H] = layout === 'long' ? [1920, 1080] : [1080, 1920];
const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
const p = await b.newPage({ viewport: { width: W, height: H } });
p.on('pageerror', e => console.error('ERR', e.message));
await p.goto('file://' + path.join(HERE, 'index.html'));
await p.waitForFunction(() => window.ready, null, { timeout: 20000 });
await p.evaluate(([tl, l, t]) => window.setup(tl, l, t), [tl, layout, title]);
const n = tl.talk.length, frames = list ? list.split(',').map(Number) : Array.from({ length: Math.min(n, +to) - +from }, (_, i) => +from + i);
for (const f of frames) { await p.evaluate(f => window.renderFrame(f), f); await p.screenshot({ path: `${out}/f${String(f).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 88 }); }
await b.close();
