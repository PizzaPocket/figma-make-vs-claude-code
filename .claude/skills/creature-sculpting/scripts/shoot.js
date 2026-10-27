// Render shots of a model in a headless browser.
//   node shoot.js PAGE.html SHOTS.json [POSES.json]
// PAGE.html must mount a viewer and set window.api = { shot(cam, target, pose, fov) } and window.ready.
// SHOTS.json: [{cam:[x,y,z], target:[x,y,z], fov, pose: "name" | {...}, out: "file.png"}]
// POSES.json: a design file with expressions.poses (named poses), optional.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const [page, shotsFile, posesFile] = process.argv.slice(2);
  const shots = JSON.parse(fs.readFileSync(shotsFile));
  const poses = posesFile ? (JSON.parse(fs.readFileSync(posesFile)).expressions || {}).poses || {} : {};
  const b = await chromium.launch({ executablePath: process.env.CLAY_CHROMIUM || undefined, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 700, height: 520 } });
  const logs = [];
  p.on('pageerror', e => logs.push(e.message));
  p.on('console', m => { if (m.type() === 'error') logs.push(m.text().slice(0, 300)); });
  const origin = process.env.CLAY_RENDER_ORIGIN;
  const relativePage = path.relative(process.env.CLAY_RENDER_ROOT || '/tmp', path.resolve(page));
  if (origin && (relativePage.startsWith('..') || path.isAbsolute(relativePage))) throw new Error('Page is outside CLAY_RENDER_ROOT');
  await p.goto(origin ? new URL(relativePage.split(path.sep).join('/'), origin).href : 'file://' + path.resolve(page));
  await p.waitForFunction(() => window.ready || (window.errors && window.errors.length), null, { timeout: 180000 });
  const errs = await p.evaluate(() => window.errors || []);
  if (errs.length || logs.length) console.error('viewer errors:', errs, logs.slice(0, 5));
  for (const s of shots) {
    const pose = typeof s.pose === 'string' ? (poses[s.pose] || {}) : (s.pose || {});
    await p.evaluate(([s, pose]) => window.api.shot(s.cam, s.target, pose, s.fov), [s, pose]);
    await p.waitForTimeout(250);
    await p.screenshot({ path: s.out, timeout: 180000 });
  }
  await b.close();
})();
