const W = 1080, H = 1920, FPS = 24, INK = '#1b1b1b', SW = 8;
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const lerp = (a, b, t) => a + (b - a) * t;
const eo3 = t => 1 - Math.pow(1 - clamp(t), 3);
const eoBack = t => { t = clamp(t); const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
const eio = t => { t = clamp(t); return t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; };
const rnd = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const r1 = n => Math.round(n * 10) / 10;

/* ---------- drawing primitives ---------- */
const limb = (x1, y1, x2, y2, w, fill) =>
  `<line x1="${r1(x1)}" y1="${r1(y1)}" x2="${r1(x2)}" y2="${r1(y2)}" stroke="${INK}" stroke-width="${w + SW * 2}" stroke-linecap="round"/>` +
  `<line x1="${r1(x1)}" y1="${r1(y1)}" x2="${r1(x2)}" y2="${r1(y2)}" stroke="${fill}" stroke-width="${w}" stroke-linecap="round"/>`;
const poly = (pts, fill, sw = SW) =>
  `<polygon points="${pts.map(p => r1(p[0]) + ',' + r1(p[1])).join(' ')}" fill="${fill}" stroke="${INK}" stroke-width="${sw}" stroke-linejoin="round"/>`;
const path = (d, fill = 'none', sw = SW) =>
  `<path d="${d}" fill="${fill}" stroke="${INK}" stroke-width="${sw}" stroke-linejoin="round" stroke-linecap="round"/>`;
const circ = (cx, cy, r, fill, sw = SW) =>
  `<circle cx="${r1(cx)}" cy="${r1(cy)}" r="${r1(r)}" fill="${fill}" stroke="${INK}" stroke-width="${sw}"/>`;
const eye = (cx, cy, r, lx = .5, ly = .1) =>
  circ(cx, cy, r, '#fff', 7) + `<circle cx="${r1(cx + lx * r * .45)}" cy="${r1(cy + ly * r * .45)}" r="${r1(r * .16)}" fill="${INK}"/>`;
const text = (str, x, y, size, fill = INK, anchor = 'middle', stroke = 0) =>
  `<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="CapFont, Inter, sans-serif" font-weight="900" font-size="${size}" fill="${fill}"` +
  (stroke ? ` stroke="${INK}" stroke-width="${stroke}" paint-order="stroke" stroke-linejoin="round"` : '') + `>${str}</text>`;

const arrow = (x, y, len = 280, ang = 0, head = true, col = '#e2433a') =>
  `<g transform="translate(${r1(x)},${r1(y)}) rotate(${r1(ang)})">` +
  `<line x1="0" y1="0" x2="${len}" y2="0" stroke="${INK}" stroke-width="7" stroke-linecap="round"/>` +
  (head ? `<polygon points="${len - 2},-13 ${len + 30},0 ${len - 2},13" fill="${INK}"/>` : '') +
  `<polygon points="-6,0 -10,-17 30,-17 42,0 30,17 -10,17" fill="${col}" stroke="${INK}" stroke-width="5" stroke-linejoin="round"/></g>`;

