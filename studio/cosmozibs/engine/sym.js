const star = (cx, cy, r, fill = '#f4c542') => {
  const pts = [];
  for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * .45 : r; pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr]); }
  return poly(pts, fill, 6);
};
const staff = (x1, y1, x2, y2) => limb(x1, y1, x2, y2, 12, '#8a5a34');

function symbol(type, cx, cy) {
  let g = '';
  if (type === 'stars') g += star(cx - 70, cy + 10, 30) + star(cx, cy - 22, 40) + star(cx + 74, cy + 14, 28);
  if (type === 'ark') {
    g += path(`M${cx - 80},${cy} L${cx + 80},${cy} Q${cx + 60},${cy + 56} ${cx},${cy + 58} Q${cx - 60},${cy + 56} ${cx - 80},${cy}Z`, '#a9764b');
    g += poly([[cx - 38, cy], [cx - 38, cy - 40], [cx + 38, cy - 40], [cx + 38, cy]], '#d2a36a');
    g += poly([[cx - 48, cy - 40], [cx, cy - 74], [cx + 48, cy - 40]], '#8a5a34');
    g += `<path d="M${cx - 110},${cy + 66} q18,-16 36,0 t36,0 t36,0 t36,0 t36,0" fill="none" stroke="#3b88c3" stroke-width="7" stroke-linecap="round"/>`;
  }
  if (type === 'tablets') {
    g += path(`M${cx - 78},${cy + 40} L${cx - 78},${cy - 30} Q${cx - 38},${cy - 62} ${cx + 2},${cy - 30} L${cx + 2},${cy + 40}Z`, '#d9d4c8');
    g += path(`M${cx + 14},${cy + 40} L${cx + 14},${cy - 30} Q${cx + 54},${cy - 62} ${cx + 94},${cy - 30} L${cx + 94},${cy + 40}Z`, '#d9d4c8');
    for (let i = 0; i < 3; i++) g += `<line x1="${cx - 60}" y1="${cy - 8 + i * 18}" x2="${cx - 16}" y2="${cy - 8 + i * 18}" stroke="${INK}" stroke-width="5" stroke-linecap="round"/><line x1="${cx + 32}" y1="${cy - 8 + i * 18}" x2="${cx + 76}" y2="${cy - 8 + i * 18}" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`;
  }
  if (type === 'lotus') {
    for (const a of [-60, -30, 0, 30, 60]) g += `<g transform="translate(${cx},${cy + 40}) rotate(${a})"><path d="M0,0 Q-30,-50 0,-96 Q30,-50 0,0Z" fill="#f59ac0" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/></g>`;
    g += `<path d="M${cx - 90},${cy + 46} q90,24 180,0" fill="none" stroke="#3b88c3" stroke-width="7" stroke-linecap="round"/>`;
  }
  if (type === 'bow') {
    g += path(`M${cx - 26},${cy - 70} Q${cx + 80},${cy} ${cx - 26},${cy + 70}`, 'none', 10);
    g += `<line x1="${cx - 26}" y1="${cy - 70}" x2="${cx - 26}" y2="${cy + 70}" stroke="${INK}" stroke-width="4"/>`;
    g += arrow(cx - 80, cy, 200, 0);
  }
  if (type === 'lily') {
    g += `<line x1="${cx}" y1="${cy + 70}" x2="${cx}" y2="${cy + 4}" stroke="#2e9d4f" stroke-width="10" stroke-linecap="round"/>`;
    for (const a of [-40, 0, 40]) g += `<g transform="translate(${cx},${cy + 6}) rotate(${a})"><path d="M0,0 Q-30,-40 0,-82 Q30,-40 0,0Z" fill="#fff" stroke="${INK}" stroke-width="6" stroke-linejoin="round"/></g>`;
    g += `<circle cx="${cx}" cy="${cy - 24}" r="6" fill="#f4c542"/>`;
  }
  return g;
}

