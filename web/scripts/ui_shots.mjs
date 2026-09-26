// Screenshot harness for the nebula's look (docs/07-ui.md): renders a fixed set of camera poses in light and
// dark mode and tiles them into one contact sheet per theme. Needs the dev server (npm run dev) and Playwright.
//   node web/scripts/ui_shots.mjs <outdir> [label] [url]
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const out = process.argv[2] ?? "/tmp/askjev-shots";
const label = process.argv[3] ?? "shot";
const url = process.argv[4] ?? "https://askjev.localhost/?layout=balloon";
mkdirSync(out, { recursive: true });

// [name, camera position, look-at target]
const POSES = [
  ["home", [0, 125, 690], [0, 0, 0]],
  ["high", [0, 900, 200], [0, 0, 0]],
  ["level", [0, 40, 520], [0, 30, 0]],
  ["side-up", [480, -60, 260], [0, 80, 0]],
  ["close", [60, 60, 110], [0, 20, 0]],
  ["far", [-500, 500, -700], [0, 0, 0]],
];

const b = await chromium.launch({ channel: "chrome" });
for (const theme of ["light", "dark"]) {
  const ctx = await b.newContext({ viewport: { width: 1280, height: 800 }, ignoreHTTPSErrors: true });
  const p = await ctx.newPage();
  const errs = [];
  p.on("pageerror", (e) => errs.push(e.message));
  await p.addInitScript((t) => localStorage.setItem("askjev.theme", t), theme);
  await p.goto(url);
  await p.waitForFunction(() => !!window.__cam, null, { timeout: 30000 });
  await p.waitForTimeout(7000);
  for (const [name, pos, target] of POSES) {
    await p.evaluate(([a, t]) => window.__cam.set(a, t), [pos, target]);
    await p.waitForTimeout(900);
    await p.screenshot({ path: `${out}/${label}_${theme}_${name}.png`, caret: "initial" }); // hiding the caret restyles inputs mid-hydration
  }
  if (errs.length) console.log(theme, "errors:", errs);
  await ctx.close();
}
await b.close();
console.log("done", out);
