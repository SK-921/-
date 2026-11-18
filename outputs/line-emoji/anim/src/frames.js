// オリジナルキャラ「もちびっと」のアニメーション絵文字のコマを書き出す。
// 1個あたり 12コマ（180x180、背景透過）。APNG への変換は make_apng.py が行う。
// 使い方: node outputs/line-emoji/anim/src/frames.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const OUT = path.join(__dirname, '..', 'frames');
const N = 12;
const INK = '#1e3a5f';
const BODY = '#8fd3fe';
const S = Math.sin;
const PI = Math.PI;

// ---------- 部品 ----------
function eyes(type) {
  const L = 68, R = 112, Y = 95;
  const pair = (f) => f(L) + f(R);
  switch (type) {
    case 'happy':
      return pair((x) => `<path d="M${x - 8} ${Y + 3} Q${x} ${Y - 8} ${x + 8} ${Y + 3}" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`);
    case 'closed':
      return pair((x) => `<path d="M${x - 8} ${Y} Q${x} ${Y + 6} ${x + 8} ${Y}" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`);
    case 'tight': // ＞＜
      return `<path d="M60 88 L74 95 L60 102" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>` +
             `<path d="M120 88 L106 95 L120 102" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>`;
    default: // open
      return pair((x) => `<ellipse cx="${x}" cy="${Y}" rx="7.5" ry="10" fill="${INK}"/><circle cx="${x + 2.5}" cy="${Y - 4}" r="2.8" fill="#fff"/>`);
  }
}

function mouth(type) {
  switch (type) {
    case 'open': return `<path d="M81 111 Q90 126 99 111 Z" fill="#e11d48" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/>`;
    case 'small': return `<ellipse cx="90" cy="116" rx="4" ry="5" fill="${INK}"/>`;
    case 'flat': return `<path d="M83 115 L97 115" stroke="${INK}" stroke-width="4.5" stroke-linecap="round"/>`;
    case 'wavy': return `<path d="M79 116 q5.5 -6 11 0 t11 0" fill="none" stroke="${INK}" stroke-width="4.5" stroke-linecap="round"/>`;
    default: return `<path d="M82 111 Q90 120 98 111" fill="none" stroke="${INK}" stroke-width="4.5" stroke-linecap="round"/>`;
  }
}

function arm(side, angle) {
  // 肩から下向きに伸びる腕。angle は時計回りの角度（右腕を上げるときはマイナス）
  const sx = side === 'L' ? 33 : 147, sy = 106;
  return `<g transform="rotate(${angle} ${sx} ${sy})"><rect x="${sx - 8}" y="${sy - 6}" width="16" height="36" rx="8" fill="${BODY}" stroke="${INK}" stroke-width="4.5"/></g>`;
}

function character(o) {
  const p = Object.assign({ dy: 0, sx: 1, sy: 1, rot: 0, armL: 25, armR: -25, eyes: 'open', mouth: 'smile', blush: 0.85, front: '' }, o);
  const squash = `translate(90 162) scale(${p.sx} ${p.sy}) translate(-90 -162)`;
  return `<g transform="translate(0 ${p.dy}) rotate(${p.rot} 90 162) ${squash}">
    <ellipse cx="66" cy="160" rx="16" ry="9" fill="${BODY}" stroke="${INK}" stroke-width="4.5"/>
    <ellipse cx="114" cy="160" rx="16" ry="9" fill="${BODY}" stroke="${INK}" stroke-width="4.5"/>
    <path d="M90 46 L90 26" stroke="${INK}" stroke-width="4.5" stroke-linecap="round"/>
    <circle cx="90" cy="20" r="9" fill="#facc15" stroke="${INK}" stroke-width="4.5"/>
    <path d="M28 104 C28 64 54 44 90 44 C126 44 152 64 152 104 C152 140 126 158 90 158 C54 158 28 140 28 104 Z" fill="${BODY}" stroke="${INK}" stroke-width="5"/>
    <ellipse cx="50" cy="112" rx="9" ry="5.5" fill="#f9a8d4" opacity="${p.blush}"/>
    <ellipse cx="130" cy="112" rx="9" ry="5.5" fill="#f9a8d4" opacity="${p.blush}"/>
    ${eyes(p.eyes)}${mouth(p.mouth)}
    ${arm('L', p.armL)}${arm('R', p.armR)}
    ${p.front}
  </g>`;
}

const heart = (x, y, s, op) =>
  `<path transform="translate(${x} ${y}) scale(${s})" d="M0 6 C-9 -3 -16 4 -10 11 L0 20 L10 11 C16 4 9 -3 0 6 Z" fill="#f43f5e" stroke="${INK}" stroke-width="2.5" opacity="${op}"/>`;
const zText = (x, y, s, op) =>
  `<text x="${x}" y="${y}" font-family="IPAPGothic" font-weight="bold" font-size="${s}" fill="#6366f1" stroke="#fff" stroke-width="3" paint-order="stroke fill" opacity="${op}">Z</text>`;
const sparkle = (x, y, s, op) =>
  `<path transform="translate(${x} ${y}) scale(${s})" d="M0 -10 L3 -3 L10 0 L3 3 L0 10 L-3 3 L-10 0 L-3 -3 Z" fill="#facc15" stroke="${INK}" stroke-width="2" opacity="${op}"/>`;

// ---------- 8種類の動き（t は 0〜1） ----------
const ANIMS = {
  '001-yaa': (t) => character({ // 手をふる「やあ」
    rot: 3 * S(2 * PI * t), armL: 25, armR: -140 + 28 * S(4 * PI * t), eyes: 'happy', mouth: 'open',
  }),
  '002-yatta': (t) => { // ぴょんと跳ねる「やった」
    const h = S(PI * t);
    const land = h < 0.2;
    return character({
      dy: -6 * h, sx: land ? 1.06 : 1, sy: land ? 0.92 : 1,
      armL: 40 + 110 * h, armR: -(40 + 110 * h), eyes: 'happy', mouth: 'open',
    }) + sparkle(22, 30, 0.6 + 0.6 * h, h) + sparkle(158, 36, 0.5 + 0.6 * h, h);
  },
  '003-ryokai': (t) => { // うなずく「了解」
    const b = Math.max(0, S(4 * PI * t));
    const s = Math.min(1, t * 3);
    return character({ dy: 7 * b, sy: 1 - 0.05 * b, eyes: 'happy', mouth: 'smile', armL: 15, armR: -15 }) +
      `<g transform="translate(150 34) scale(${s})"><circle r="22" fill="#22c55e" stroke="${INK}" stroke-width="4"/>` +
      `<path d="M-10 0 L-3 8 L11 -8" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></g>`;
  },
  '004-gomen': (t) => { // ぺこり「ごめん」
    const b = S(PI * t);
    return character({ dy: 9 * b, sy: 1 - 0.14 * b, eyes: 'tight', mouth: 'wavy', armL: -25, armR: 25, blush: 0.4 }) +
      `<path transform="translate(150 ${34 + 34 * t})" d="M0 -12 C6 -3 9 2 9 6 A9 9 0 0 1 -9 6 C-9 2 -6 -3 0 -12 Z" fill="#7dd3fc" stroke="${INK}" stroke-width="3" opacity="${1 - t * 0.6}"/>`;
  },
  '005-nemui': (t) => { // ゆらゆら「ねむい」
    let zs = '';
    for (let k = 0; k < 3; k++) {
      const ph = (t + k / 3) % 1;
      zs += zText(128 + 18 * ph, 66 - 52 * ph, 14 + 12 * ph, 1 - ph);
    }
    return character({ rot: 7 * S(2 * PI * t), eyes: 'closed', mouth: 'small', armL: 10, armR: -10, blush: 0.5 }) + zs;
  },
  '006-arigato': (t) => { // ハートが出る「ありがと」
    let hs = '';
    for (let k = 0; k < 3; k++) {
      const ph = (t + k / 3) % 1;
      const x = [24, 150, 140][k] + 6 * S(2 * PI * ph);
      hs += heart(x, 70 - 58 * ph, 0.8 + 0.5 * ph, 1 - ph * 0.8);
    }
    return character({ dy: -5 * Math.abs(S(2 * PI * t)), eyes: 'happy', mouth: 'smile', blush: 1, armL: -35, armR: 35 }) + hs;
  },
  '007-debug': (t) => { // パソコンをカタカタ「作業中」
    const a = 18 * S(4 * PI * t);
    const lid = `<rect x="50" y="122" width="80" height="44" rx="6" fill="#64748b" stroke="${INK}" stroke-width="4.5"/>` +
                `<circle cx="90" cy="144" r="5" fill="#cbd5e1"/>`;
    const dots = Math.floor(t * 3) + 1;
    let d = '';
    for (let k = 0; k < dots; k++) d += `<circle cx="${140 + k * 11}" cy="30" r="4.5" fill="${INK}"/>`;
    return character({ eyes: 'open', mouth: 'flat', armL: -35 + a, armR: 35 + a, front: lid, blush: 0.5 }) +
      `<rect x="126" y="16" width="44" height="28" rx="14" fill="#fff" stroke="${INK}" stroke-width="3.5"/>` + d;
  },
  '008-banzai': (t) => { // ばんざいと紙吹雪「おめでとう」
    const colors = ['#f43f5e', '#facc15', '#22c55e', '#3b82f6', '#a855f7'];
    let c = '';
    for (let k = 0; k < 10; k++) {
      const x = 10 + k * 17 + 6 * S(2 * PI * t + k);
      const y = ((k * 37 + 180 * t) % 190) - 10;
      c += `<rect x="${x}" y="${y}" width="9" height="5" rx="1.5" fill="${colors[k % 5]}" transform="rotate(${(k * 40 + 360 * t) % 360} ${x + 4} ${y + 2})"/>`;
    }
    return character({
      dy: -8 * Math.abs(S(2 * PI * t)), eyes: 'happy', mouth: 'open',
      armL: 150 + 18 * S(2 * PI * t), armR: -(150 + 18 * S(2 * PI * t + PI)),
    }) + c;
  },
};

const wrap = (inner, w = 180, h = 180) =>
  `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 180 180">${inner}</svg>`;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1, viewport: { width: 180, height: 180 } });
  for (const [name, fn] of Object.entries(ANIMS)) {
    const dir = path.join(OUT, name);
    fs.mkdirSync(dir, { recursive: true });
    for (let i = 0; i < N; i++) {
      await page.setContent(`<html><body style="margin:0;background:transparent">${wrap(fn(i / N))}</body></html>`);
      await page.screenshot({ path: path.join(dir, `${String(i).padStart(2, '0')}.png`), omitBackground: true, clip: { x: 0, y: 0, width: 180, height: 180 } });
    }
  }
  // タブ画像（96x74）：表情だけを大きく
  await page.setViewportSize({ width: 96, height: 74 });
  await page.setContent(`<html><body style="margin:0;background:transparent">
    <svg xmlns="http://www.w3.org/2000/svg" width="96" height="74" viewBox="22 8 136 106">${character({ eyes: 'happy', mouth: 'smile' })}</svg></body></html>`);
  await page.screenshot({ path: path.join(OUT, 'tab.png'), omitBackground: true, clip: { x: 0, y: 0, width: 96, height: 74 } });
  await browser.close();
  console.log('frames done:', Object.keys(ANIMS).join(', '));
})();
