// figures.html の各図を PNG に書き出す。
// 使い方: node outputs/fe/images/src/render.js
const path = require('path');
const { chromium } = require('playwright');

const SRC = path.join(__dirname, 'figures.html');
const OUT = path.join(__dirname, '..');

const targets = [
  ['#cover', '00-cover.png'],
  ['#fig1', '01-kisu-henkan.png'],
  ['#fig2', '02-stack-queue.png'],
  ['#fig3', '03-memory.png'],
  ['#fig4', '04-osi.png'],
  ['#fig5', '05-keys.png'],
  ['#fig6', '06-sql-order.png'],
  ['#fig7', '07-availability.png'],
  ['#insta', '08-instagram.png'],
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 900, height: 1200 }, deviceScaleFactor: 2 });
  await page.goto('file://' + SRC);
  await page.evaluate(() => document.fonts.ready);
  for (const [sel, name] of targets) {
    const el = await page.$(sel);
    await el.screenshot({ path: path.join(OUT, name) });
    const box = await el.boundingBox();
    console.log(name, Math.round(box.width * 2) + 'x' + Math.round(box.height * 2));
  }
  await browser.close();
})();
