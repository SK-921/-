// 白ネコを図形で描き直し、体のパーツごとに動かすアニメーションスタンプのコマを書き出す。
// 元のデザイン：ChatGPT が描いた白ネコ（outputs/line-stamp/cat/src/chatgpt-sheet.webp）
// 1個あたり 12コマ、320x270、背景透過。APNG への変換は make_apng.py が行う。
// 使い方: node outputs/line-stamp/cat-v2/src/frames.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const OUT = path.join(__dirname, '..', 'frames');
const N = 12;
const W = 320, H = 270;
const INK = '#5a4740';      // 輪郭線（こげ茶）
const FUR = '#fffaf6';      // 体（白）
const EAR = '#f7c4ca';      // 耳の内側
const CHEEK = '#f9c3cb';    // ほっぺ
const PAD = '#f3aab6';      // 肉球
const LW = 4.5;             // 線の太さ
const S = Math.sin, PI = Math.PI, TAU = 2 * Math.PI;

// ---------------- 顔のパーツ ----------------
function eyes(type, dx = 0) {
  const L = -28 + dx, R = 28 + dx, Y = -2;
  const both = (f) => f(L) + f(R);
  switch (type) {
    case 'happy': return both((x) => `<path d="M${x - 9} ${Y + 3} Q${x} ${Y - 8} ${x + 9} ${Y + 3}" fill="none" stroke="${INK}" stroke-width="${LW}" stroke-linecap="round"/>`);
    case 'sleep': return both((x) => `<path d="M${x - 9} ${Y} Q${x} ${Y + 6} ${x + 9} ${Y}" fill="none" stroke="${INK}" stroke-width="${LW}" stroke-linecap="round"/>`);
    case 'tight': return `<path d="M${L - 8} ${Y - 7} L${L + 6} ${Y} L${L - 8} ${Y + 7}" fill="none" stroke="${INK}" stroke-width="${LW}" stroke-linecap="round" stroke-linejoin="round"/>` +
                         `<path d="M${R + 8} ${Y - 7} L${R - 6} ${Y} L${R + 8} ${Y + 7}" fill="none" stroke="${INK}" stroke-width="${LW}" stroke-linecap="round" stroke-linejoin="round"/>`;
    case 'wide': return both((x) => `<circle cx="${x}" cy="${Y}" r="9" fill="#fff" stroke="${INK}" stroke-width="${LW}"/>`);
    case 'wink': return `<path d="M${L - 9} ${Y + 3} Q${L} ${Y - 8} ${L + 9} ${Y + 3}" fill="none" stroke="${INK}" stroke-width="${LW}" stroke-linecap="round"/>` +
                        `<ellipse cx="${R}" cy="${Y}" rx="6.5" ry="8" fill="${INK}"/><circle cx="${R + 2}" cy="${Y - 3}" r="2.2" fill="#fff"/>`;
    case 'blink': return both((x) => `<path d="M${x - 7} ${Y} L${x + 7} ${Y}" stroke="${INK}" stroke-width="${LW}" stroke-linecap="round"/>`);
    default: return both((x) => `<ellipse cx="${x}" cy="${Y}" rx="6.5" ry="8" fill="${INK}"/><circle cx="${x + 2}" cy="${Y - 3}" r="2.2" fill="#fff"/>`);
  }
}

function mouth(type, open = 0) {
  if (type === 'open') {
    const h = 6 + 8 * open;
    return `<path d="M-9 12 Q0 ${12 + h * 2} 9 12 Z" fill="#f28da0" stroke="${INK}" stroke-width="3.5" stroke-linejoin="round"/>`;
  }
  // ω の形
  return `<path d="M-10 11 Q-5 18 0 11 Q5 18 10 11" fill="none" stroke="${INK}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>`;
}

function whiskers() {
  const side = (sx) => [[-4, 0], [4, 3], [12, 6]].map(([y, a]) =>
    `<path d="M${sx * 62} ${y + 6} L${sx * 84} ${y + 6 + (a - 3) * sx * 0 + (y < 0 ? -4 : y > 6 ? 4 : 0)}" stroke="${INK}" stroke-width="2.6" stroke-linecap="round"/>`).join('');
  return side(-1) + side(1);
}

// 頭（中心が原点）。tilt は首のかしげ角度、ear は耳のぴくぴく（0〜1）
function head(o) {
  const p = Object.assign({ eyes: 'open', mouth: 'w', open: 0, blush: 0.85, look: 0, ear: 0, tilt: 0 }, o);
  const e = p.ear * 6;
  return `<g transform="rotate(${p.tilt})">
    <path d="M-66 -24 Q-74 -72 -56 -78 Q-38 -68 -24 -54" fill="${FUR}" stroke="${INK}" stroke-width="${LW}" stroke-linejoin="round" transform="rotate(${-e} -45 -50)"/>
    <path d="M-60 -36 Q-64 -64 -54 -68 Q-44 -60 -36 -52 Z" fill="${EAR}" transform="rotate(${-e} -45 -50)"/>
    <path d="M66 -24 Q74 -72 56 -78 Q38 -68 24 -54" fill="${FUR}" stroke="${INK}" stroke-width="${LW}" stroke-linejoin="round" transform="rotate(${e} 45 -50)"/>
    <path d="M60 -36 Q64 -64 54 -68 Q44 -60 36 -52 Z" fill="${EAR}" transform="rotate(${e} 45 -50)"/>
    <ellipse cx="0" cy="0" rx="80" ry="60" fill="${FUR}" stroke="${INK}" stroke-width="${LW}"/>
    <ellipse cx="-50" cy="16" rx="13" ry="8" fill="${CHEEK}" opacity="${p.blush}"/>
    <ellipse cx="50" cy="16" rx="13" ry="8" fill="${CHEEK}" opacity="${p.blush}"/>
    ${eyes(p.eyes, p.look)}${mouth(p.mouth, p.open)}${whiskers()}
  </g>`;
}

// 前足（腕）。肩の位置から下向きに伸び、angle は時計回り。pad=true で肉球を見せる
function paw(x, y, angle, pad = false) {
  return `<g transform="rotate(${angle} ${x} ${y})">
    <rect x="${x - 13}" y="${y - 6}" width="26" height="46" rx="13" fill="${FUR}" stroke="${INK}" stroke-width="${LW}"/>
    ${pad ? `<circle cx="${x}" cy="${y + 28}" r="6" fill="${PAD}"/><circle cx="${x - 7}" cy="${y + 18}" r="3" fill="${PAD}"/><circle cx="${x}" cy="${y + 15}" r="3" fill="${PAD}"/><circle cx="${x + 7}" cy="${y + 18}" r="3" fill="${PAD}"/>` : ''}
  </g>`;
}

// すわった体（頭の下）
function seated(cx, cy, o = {}) {
  const p = Object.assign({ armL: 20, armR: -20, padL: false, padR: false, sy: 1, armsFront: true }, o);
  const body = `<ellipse cx="${cx}" cy="${cy + 68}" rx="60" ry="${44 * p.sy}" fill="${FUR}" stroke="${INK}" stroke-width="${LW}"/>` +
    `<ellipse cx="${cx - 24}" cy="${cy + 108}" rx="16" ry="10" fill="${FUR}" stroke="${INK}" stroke-width="${LW}"/>` +
    `<ellipse cx="${cx + 24}" cy="${cy + 108}" rx="16" ry="10" fill="${FUR}" stroke="${INK}" stroke-width="${LW}"/>`;
  const arms = paw(cx - 54, cy + 52, p.armL, p.padL) + paw(cx + 54, cy + 52, p.armR, p.padR);
  return { body, arms };
}

// ---------------- 小物 ----------------
const txt = (s, x, y, size, color = INK, rot = 0) =>
  `<text x="${x}" y="${y}" font-family="IPAPGothic" font-weight="bold" font-size="${size}" text-anchor="middle" fill="${color}" stroke="#fff" stroke-width="6" stroke-linejoin="round" paint-order="stroke fill" transform="rotate(${rot} ${x} ${y})">${s}</text>`;
const heart = (x, y, s, op = 1, c = '#f48aa0') =>
  `<path transform="translate(${x} ${y}) scale(${s})" d="M0 6 C-9 -3 -16 4 -10 11 L0 20 L10 11 C16 4 9 -3 0 6 Z" fill="${c}" opacity="${op}"/>`;
const lines = (x, y, ang, len, color, n = 3, spread = 30, w = 4.5) => {
  let s = '';
  for (let k = 0; k < n; k++) {
    const a = (ang + (k - (n - 1) / 2) * spread) * PI / 180;
    const x1 = x + Math.cos(a) * 18, y1 = y + Math.sin(a) * 18;
    const x2 = x + Math.cos(a) * (18 + len), y2 = y + Math.sin(a) * (18 + len);
    s += `<path d="M${x1} ${y1} L${x2} ${y2}" stroke="${color}" stroke-width="${w}" stroke-linecap="round"/>`;
  }
  return s;
};
const sweat = (x, y, op = 1) => `<path transform="translate(${x} ${y})" d="M0 -12 C6 -3 9 2 9 6 A9 9 0 0 1 -9 6 C-9 2 -6 -3 0 -12 Z" fill="#8cc8f0" opacity="${op}"/>`;
const flower = (x, y, s, rot) => {
  let p = '';
  for (let k = 0; k < 5; k++) p += `<circle cx="${Math.cos(k * TAU / 5) * 7}" cy="${Math.sin(k * TAU / 5) * 7}" r="6" fill="#f7a8b8"/>`;
  return `<g transform="translate(${x} ${y}) rotate(${rot}) scale(${s})">${p}<circle r="4" fill="#fcd34d"/></g>`;
};
const zz = (x, y, s, op) => `<text x="${x}" y="${y}" font-family="IPAPGothic" font-weight="bold" font-size="${s}" fill="#7c93d6" stroke="#fff" stroke-width="4" paint-order="stroke fill" opacity="${op}">Z</text>`;
const note = (x, y, op = 1) => `<g transform="translate(${x} ${y})" opacity="${op}"><path d="M0 0 L0 -26 L12 -30 L12 -6" fill="none" stroke="#f48aa0" stroke-width="4" stroke-linecap="round"/><ellipse cx="-4" cy="2" rx="6" ry="5" fill="#f48aa0"/><ellipse cx="8" cy="-4" rx="6" ry="5" fill="#f48aa0"/></g>`;

// ---------------- 16個の動き ----------------
const C = 160; // 横の中心
const A = {
  '01-haai': (t) => { // はーい：右手をふる＋ウインク
    const s = seated(C, 140, { armR: -150 + 22 * S(TAU * t), padR: true, armL: 18 });
    return txt('はーい！', C, 44, 38) + lines(56, 92, 200, 16, '#f48aa0') + s.body + `<g transform="translate(${C} 140)">${head({ eyes: 'wink', mouth: 'open', open: 0.6 })}</g>` + s.arms;
  },
  '02-chira': (t) => { // ちらっ：台の上から顔を出し、目だけ左右を見る
    const up = 14 * S(PI * t) ** 2;
    const look = 6 * S(TAU * t);
    return txt('ちらっ', C, 44, 36) +
      `<g transform="translate(${C} ${168 - up})">${head({ look, ear: 0.5 * S(TAU * t) ** 2 })}</g>` +
      `<rect x="40" y="210" width="240" height="40" fill="#fff" opacity="0"/>` +
      `<path d="M30 214 L290 214" stroke="${INK}" stroke-width="${LW}" stroke-linecap="round"/>` +
      `<ellipse cx="${C - 36}" cy="${214 - up * 0.2}" rx="16" ry="10" fill="${FUR}" stroke="${INK}" stroke-width="${LW}"/>` +
      `<ellipse cx="${C + 36}" cy="${214 - up * 0.2}" rx="16" ry="10" fill="${FUR}" stroke="${INK}" stroke-width="${LW}"/>` +
      lines(40, 150, 180, 14, INK, 2, 24, 3.5);
  },
  '03-arigatou': (t) => { // ありがとう：ハートを抱えてどきどき、ハートが浮かぶ
    const beat = 1 + 0.08 * S(PI * t) ** 2;
    const s = seated(C, 128, { armL: -40, armR: 40 });
    let hs = '';
    for (let k = 0; k < 2; k++) { const ph = (t + k / 2) % 1; hs += heart([42, 270][k], 150 - 70 * ph, 1 + 0.4 * ph, 1 - ph); }
    return txt('ありがとう！', C, 44, 36) + hs + s.body + `<g transform="translate(${C} 128)">${head({ eyes: 'happy' })}</g>` +
      `<g transform="translate(${C} 212) scale(${beat})"><path d="M0 -10 C-24 -40 -58 -12 -34 16 L0 44 L34 16 C58 -12 24 -40 0 -10 Z" transform="translate(0 -18) scale(0.9)" fill="#f7a3b5" stroke="${INK}" stroke-width="4"/></g>` +
      paw(C - 40, 190, -60) + paw(C + 40, 190, 60);
  },
  '04-gomen': (t) => { // ごめん：ぺこり（頭が下がる）＋汗
    const b = S(PI * t) ** 2;
    return txt('ごめん…！', C, 44, 36) +
      `<ellipse cx="${C}" cy="214" rx="96" ry="34" fill="${FUR}" stroke="${INK}" stroke-width="${LW}"/>` +
      `<g transform="translate(${C} ${150 + 26 * b}) scale(1 ${1 - 0.12 * b})">${head({ eyes: 'sleep', blush: 0.4, ear: -0.6 * b })}</g>` +
      paw(C - 40, 220, -80) + paw(C + 40, 220, 80) + sweat(266, 96 + 30 * t, 1 - 0.5 * t) + lines(272, 150, -20, 12, INK, 2, 22, 3.5);
  },
  '05-tsukareta': (t) => { // つかれた：ぺたんと寝そべって、ぐったり呼吸
    const br = 1 + 0.04 * S(TAU * t);
    const sw = 360 * t;
    return txt('つかれた…', C + 10, 44, 34, '#6f8fd8') +
      `<g transform="translate(46 108) rotate(${sw})"><path d="M0 0 m-12 0 a12 12 0 1 0 24 0 a8 8 0 1 0 -16 0 a4 4 0 1 0 8 0" fill="none" stroke="#6f8fd8" stroke-width="4" stroke-linecap="round"/></g>` +
      `<g transform="translate(${C + 30} 220) scale(1 ${br}) translate(${-C - 30} -220)"><ellipse cx="${C + 30}" cy="200" rx="110" ry="36" fill="${FUR}" stroke="${INK}" stroke-width="${LW}"/></g>` +
      `<g transform="translate(118 190) scale(0.82)">${head({ eyes: 'sleep', mouth: 'w', blush: 0.5, ear: -0.4 })}</g>` +
      `<ellipse cx="74" cy="232" rx="20" ry="11" fill="${FUR}" stroke="${INK}" stroke-width="${LW}"/>`;
  },
  '06-ganbatte': (t) => { // がんばって：両手を交互に上げて応援
    const a = 18 * S(TAU * t);
    const s = seated(C, 140, { armL: 150 + a, armR: -150 + a, padL: true, padR: true });
    return txt('がんばってー！', C, 44, 34) + lines(40, 120, 220, 16, '#f5c542') + lines(280, 120, -40, 16, '#f5c542') +
      s.body + `<g transform="translate(${C} ${140 - 4 * Math.abs(S(TAU * t))})">${head({ eyes: 'tight', mouth: 'open', open: 0.5 + 0.5 * Math.abs(S(TAU * t)) })}</g>` + s.arms;
  },
  '07-yoroshiku': (t) => { // よろしくです：ゆっくりおじぎ＋花がくるくる
    const b = S(PI * t) ** 2;
    const s = seated(C, 140, { armL: -15, armR: 15 });
    return txt('よろしくです！', C, 44, 34, '#ec7a92') + flower(50, 130, 1, 360 * t) + flower(272, 120, 0.9, -360 * t) +
      s.body + `<g transform="translate(${C} ${140 + 14 * b}) rotate(0)">${head({ eyes: 'sleep', tilt: 0, ear: -0.5 * b })}</g>` + s.arms;
  },
  '08-jii': (t) => { // じー：壁からのぞき込み、まばたき
    const out = 22 * S(PI * t) ** 2;
    const blink = (t > 0.55 && t < 0.65);
    return `<g transform="translate(${150 + out} 150)">${head({ eyes: blink ? 'blink' : 'open', look: -4 })}</g>` +
      `<rect x="226" y="60" width="26" height="200" rx="4" fill="#d9cfc9" stroke="${INK}" stroke-width="${LW}"/>` +
      `<rect x="252" y="40" width="60" height="230" fill="#fff" opacity="0"/>` +
      paw(226, 176, 90) + txt('じー…', 286, 120, 30, INK, 90) + lines(70, 220, 160, 12, '#f5c542');
  },
  '09-e': (t) => { // えっ!?：びくっと跳ねる、耳が立つ、目がまんまる
    const j = S(PI * t);
    const s = seated(C, 146 - 12 * j, { armL: -35, armR: 35 });
    return txt('えっ!?', C, 44, 40) + `<path d="M54 120 L68 92 L76 112 L92 84" fill="none" stroke="#f5c542" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>` +
      s.body + `<g transform="translate(${C} ${146 - 12 * j})">${head({ eyes: 'wide', mouth: 'open', open: 0.6 * j + 0.2, ear: j })}</g>` + s.arms;
  },
  '10-oyasumi': (t) => { // おやすみ：ふとんの中ですやすや、Z が浮かぶ
    const br = 3 * S(TAU * t);
    let z = '';
    for (let k = 0; k < 3; k++) { const ph = (t + k / 3) % 1; z += zz(240 + 18 * ph, 130 - 50 * ph, 16 + 12 * ph, 1 - ph); }
    return txt('おやすみ〜', C - 16, 44, 34, '#6f8fd8') +
      `<path transform="translate(262 34)" d="M0 0 A16 16 0 1 0 14 22 A12 12 0 1 1 0 0 Z" fill="#fcd34d"/>` + z +
      `<g transform="translate(${C} ${158 + br * 0.4})">${head({ eyes: 'sleep', blush: 0.6 })}</g>` +
      `<path d="M30 250 Q40 196 ${C} ${192 - br} Q280 196 290 250 Z" fill="#a9c8f0" stroke="${INK}" stroke-width="${LW}" stroke-linejoin="round"/>`;
  },
  '11-ittekimasu': (t) => { // いってきます：前のめりで走る（体がはずむ）、けむり
    const bob = -6 * Math.abs(S(TAU * t));
    const leg = 30 * S(TAU * t);
    return txt('いってきます！', C, 44, 34) + lines(260, 150, 0, 22, '#f5c542', 2, 18) +
      `<g transform="translate(0 ${bob})">` +
      paw(112, 200, 70 + leg) + paw(200, 200, -70 - leg) +
      `<ellipse cx="${C}" cy="196" rx="70" ry="34" fill="${FUR}" stroke="${INK}" stroke-width="${LW}"/>` +
      `<g transform="translate(104 156) scale(0.82) rotate(-12)">${head({ eyes: 'happy', mouth: 'open', open: 0.4 })}</g></g>` +
      `<g opacity="${0.4 + 0.6 * (1 - t)}"><circle cx="${246 + 14 * t}" cy="226" r="${9 + 6 * t}" fill="#fff" stroke="${INK}" stroke-width="3"/><circle cx="${266 + 18 * t}" cy="216" r="${7 + 5 * t}" fill="#fff" stroke="${INK}" stroke-width="3"/></g>`;
  },
  '12-tadaima': (t) => { // ただいま：手をふる＋かばんがゆれる
    const sw = 14 * S(TAU * t);
    const s = seated(C, 140, { armL: 150 + sw, padL: true, armR: -10 });
    return txt('ただいまー！', C, 44, 36) + lines(48, 112, 210, 16, '#f59e42') + lines(272, 112, -30, 16, '#f59e42') +
      s.body + `<g transform="translate(${C} 140)">${head({ eyes: 'happy', mouth: 'open', open: 0.5 })}</g>` + s.arms +
      `<g transform="rotate(${-sw} 214 196)"><path d="M204 196 Q214 180 224 196" fill="none" stroke="#9c7b5b" stroke-width="4"/><rect x="198" y="196" width="34" height="44" rx="6" fill="#c9a27c" stroke="${INK}" stroke-width="3.5"/></g>`;
  },
  '13-oishii': (t) => { // おいしい：おにぎりをもぐもぐ（口が開閉）、ハート
    const chew = Math.abs(S(TAU * t));
    const s = seated(C, 136, { armL: -50, armR: 50 });
    let hs = '';
    for (let k = 0; k < 2; k++) { const ph = (t + k / 2) % 1; hs += heart([44, 268][k], 160 - 60 * ph, 1 + 0.3 * ph, 1 - ph); }
    return txt('おいしい！', C, 44, 36, '#ec7a92') + hs + s.body +
      `<g transform="translate(${C} 136)">${head({ eyes: 'happy', mouth: 'open', open: chew })}</g>` +
      `<g transform="translate(${C} ${206 - 3 * chew})"><path d="M0 -28 L26 16 Q28 22 20 22 L-20 22 Q-28 22 -26 16 Z" fill="#fff" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/><rect x="-18" y="4" width="36" height="18" rx="3" fill="#3b3b3b"/></g>` +
      paw(C - 46, 188, -45) + paw(C + 46, 188, 45);
  },
  '14-hatena': (t) => { // はてな：首をかしげる＋？がゆれる
    const tilt = -14 * S(PI * t) ** 2;
    const s = seated(C, 142, { armL: 20, armR: -40 });
    return `<g transform="rotate(${10 * S(TAU * t)} 70 70)">${txt('?', 70, 92, 64, '#6f8fd8')}</g>` +
      s.body + `<g transform="translate(${C} 142)">${head({ tilt, look: 3 * S(PI * t) ** 2 })}</g>` + s.arms;
  },
  '15-ryoukai': (t) => { // 了解：箱の中からこくこくうなずく
    const nod = 10 * S(PI * t) ** 2;
    return txt('了解！', C, 44, 40) + lines(78, 112, 210, 16, '#f5c542') +
      `<path d="M70 188 L36 150 L112 150 L140 188" fill="#d9a86c" stroke="${INK}" stroke-width="${LW}" stroke-linejoin="round"/>` +
      `<path d="M250 188 L284 150 L208 150 L180 188" fill="#d9a86c" stroke="${INK}" stroke-width="${LW}" stroke-linejoin="round"/>` +
      `<g transform="translate(${C} ${136 + nod})">${head({ eyes: 'open', ear: -0.3 * S(PI * t) ** 2 })}</g>` +
      `<path d="M66 188 L254 188 L246 262 L74 262 Z" fill="#e2b77f" stroke="${INK}" stroke-width="${LW}" stroke-linejoin="round"/>` +
      paw(C - 46, 186, -90) + paw(C + 46, 186, 90);
  },
  '16-nonbiri': (t) => { // のんびり：あおむけで足をぷらぷら、音符
    const k1 = 16 * S(TAU * t), k2 = 16 * S(TAU * t + PI);
    return txt('のんびり〜', C - 10, 44, 34) + note(268 + 4 * S(TAU * t), 70 - 6 * S(TAU * t)) +
      paw(214, 186, -150 + k1, true) + paw(246, 196, -130 + k2, true) +
      `<ellipse cx="${C + 20}" cy="208" rx="104" ry="38" fill="${FUR}" stroke="${INK}" stroke-width="${LW}"/>` +
      `<g transform="translate(108 184) scale(0.85) rotate(${-8 + 4 * S(TAU * t)})">${head({ eyes: 'happy' })}</g>`;
  },
};

const wrap = (inner) => `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${inner}</svg>`;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1, viewport: { width: W, height: H } });
  for (const [name, fn] of Object.entries(A)) {
    const dir = path.join(OUT, name);
    fs.mkdirSync(dir, { recursive: true });
    for (let i = 0; i < N; i++) {
      await page.setContent(`<html><body style="margin:0;background:transparent">${wrap(fn(i / N))}</body></html>`);
      await page.screenshot({ path: path.join(dir, `${String(i).padStart(2, '0')}.png`), omitBackground: true, clip: { x: 0, y: 0, width: W, height: H } });
    }
  }
  // タブ画像（96x74）：顔だけ
  await page.setViewportSize({ width: 96, height: 74 });
  await page.setContent(`<html><body style="margin:0;background:transparent"><svg xmlns="http://www.w3.org/2000/svg" width="96" height="74" viewBox="-92 -86 184 142"><g>${head({ eyes: 'happy' })}</g></svg></body></html>`);
  await page.screenshot({ path: path.join(OUT, 'tab.png'), omitBackground: true, clip: { x: 0, y: 0, width: 96, height: 74 } });
  await browser.close();
  console.log('frames done:', Object.keys(A).length);
})();
