// Records the opening as a frame strip: node web/scripts/ui_intro.mjs <outdir> [label] [url]
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
const out = process.argv[2] ?? "/tmp/askjev-intro";
const label = process.argv[3] ?? "intro";
const url = process.argv[4] ?? "https://askjev.localhost/?layout=balloon";
mkdirSync(out, { recursive: true });
const b = await chromium.launch({ channel: "chrome" });
for (const theme of ["light", "dark"]) {
  const ctx = await b.newContext({ viewport: { width: 1280, height: 800 }, ignoreHTTPSErrors: true });
  const p = await ctx.newPage();
  await p.addInitScript((t) => localStorage.setItem("askjev.theme", t), theme);
  await p.goto(url);
  const t0 = Date.now();
  for (let i = 0; i < 16; i++) {
    await p.screenshot({ path: `${out}/${label}_${theme}_${String(i).padStart(2, "0")}.png`, caret: "initial" }); // hiding the caret restyles inputs mid-hydration
    await p.waitForTimeout(700);
  }
  console.log(theme, "recorded over", ((Date.now() - t0) / 1000).toFixed(1), "s");
  await ctx.close();
}
await b.close();
