// Screenshots of every case study's chart window and meme, at desktop and phone width, for review by eye.
//   node scripts/portrait/case_shots.mjs <outdir> [base-url] [ids comma-separated]
import { mkdirSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";

const { chromium } = createRequire(new URL("../../web/package.json", import.meta.url))("playwright");
const out = process.argv[2] ?? "/tmp/case_shots";
const base = process.argv[3] ?? "http://localhost:4592";
const only = process.argv[4] ? process.argv[4].split(",") : null;
mkdirSync(out, { recursive: true });
const ids = only ?? JSON.parse(readFileSync(new URL("../../data/analysis/experiments.json", import.meta.url))).experiments.map((e) => e.id);

const b = await chromium.launch({ channel: "chrome" });
const desk = await (await b.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 })).newPage();
const phone = await (await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true })).newPage();
for (const id of ids) {
  for (const [p, tag] of [[desk, "d"], [phone, "m"]]) {
    try {
      await p.goto(`${base}/portrait/atlas/${id}`, { waitUntil: "networkidle", timeout: 120000 });
      const w = p.locator(".ex-window").first();
      await w.screenshot({ path: `${out}/${id}.chart.${tag}.png` });
      const m = p.locator(".ex-meme-slot").first();
      if (await m.count()) {
        await m.scrollIntoViewIfNeeded();
        await p.evaluate(() => { for (const i of document.images) i.loading = "eager"; });
        await p.waitForTimeout(500);
        await m.screenshot({ path: `${out}/${id}.meme.${tag}.png` });
      }
    } catch (e) { console.log(`${id} ${tag}: ${String(e.message).split("\n")[0]}`); }
  }
}
await b.close();
console.log(`${ids.length} cases shot`);
