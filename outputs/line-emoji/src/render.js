// LINE絵文字の試作：180x180 の透過PNGを8個と、タブ画像（96x74）を作る。
// 使い方: node outputs/line-emoji/src/render.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const OUT = path.join(__dirname, '..', 'sample');

// [ファイル名, 行の配列, 文字色]
const EMOJI = [
  ['001', ['了解'], '#2563eb'],
  ['002', ['あり', 'がと'], '#e11d48'],
  ['003', ['おつ', 'かれ'], '#ea580c'],
  ['004', ['OK!'], '#16a34a'],
  ['005', ['ごめん'], '#7c3aed'],
  ['006', ['やった', 'ー！'], '#db2777'],
  ['007', ['ねむい'], '#0891b2'],
  ['008', ['がん', 'ばる'], '#ca8a04'],
];

function svg(lines, color, w, h) {
  const n = lines.length;
  const maxLen = Math.max(...lines.map((l) => [...l].length));
  // 文字数と行数から、はみ出さない最大の文字サイズを決める
  const size = Math.floor(Math.min((w * 0.86) / Math.max(maxLen, 1.6), (h * 0.84) / n));
  const lineH = size * 1.02;
  const top = h / 2 - (lineH * (n - 1)) / 2;
  const texts = lines
    .map((l, i) => `<text x="${w / 2}" y="${top + i * lineH}" font-size="${size}">${l}</text>`)
    .join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
  <g font-family="IPAPGothic" font-weight="bold" text-anchor="middle" dominant-baseline="central"
     fill="${color}" stroke="#ffffff" stroke-width="${Math.max(4, size * 0.16)}" stroke-linejoin="round"
     paint-order="stroke fill">${texts}</g></svg>`;
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  const shoot = async (name, markup, w, h) => {
    await page.setViewportSize({ width: w, height: h });
    await page.setContent(`<html><body style="margin:0;background:transparent">${markup}</body></html>`);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(OUT, name), omitBackground: true, clip: { x: 0, y: 0, width: w, height: h } });
  };
  for (const [name, lines, color] of EMOJI) {
    await shoot(`${name}.png`, svg(lines, color, 180, 180), 180, 180);
  }
  await shoot('tab.png', svg(['了解'], '#2563eb', 96, 74), 96, 74);

  // 確認用：白とダークの背景に並べた一覧
  const b64 = (n) => fs.readFileSync(path.join(OUT, `${n}.png`)).toString('base64');
  const cells = EMOJI.map(([n]) => `<img src="data:image/png;base64,${b64(n)}" width="90">`).join('');
  await page.setViewportSize({ width: 800, height: 260 });
  await page.setContent(`<html><body style="margin:0;font-family:IPAPGothic">
    <div style="background:#ffffff;padding:14px;display:flex;gap:6px">${cells}</div>
    <div style="background:#1f2937;padding:14px;display:flex;gap:6px">${cells}</div></body></html>`);
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(OUT, '..', 'preview.png'), fullPage: true });
  await browser.close();
  console.log('done');
})();
