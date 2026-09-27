// Screenshot harness for the portrait (docs/11-portrait.md §9): one image per chapter, in both themes, at desktop and
// phone widths. Needs the dev server and Playwright.
//   node scripts/portrait/shots.mjs <outdir> [url] [only-chapter-ids] [themes] [widths]
// Playwright comes from web/'s dependencies.
import { mkdirSync } from "node:fs";
import { createRequire } from "node:module";

const { chromium } = createRequire(new URL("../../web/package.json", import.meta.url))("playwright");

const out = process.argv[2] ?? "/tmp/portrait-shots";
const url = process.argv[3] ?? "http://localhost:4592/portrait";
const only = process.argv[4] || null;
const themes = (process.argv[5] ?? "light,dark").split(",");
const widths = (process.argv[6] ?? "1440,390").split(",").map(Number);
mkdirSync(out, { recursive: true });

const b = await chromium.launch({ channel: "chrome" });
for (const theme of themes) {
  for (const width of widths) {
    const ctx = await b.newContext({ viewport: { width, height: width > 600 ? 900 : 844 }, deviceScaleFactor: width > 600 ? 1 : 2 });
    const p = await ctx.newPage();
    const errs = [];
    p.on("pageerror", (e) => errs.push(e.message));
    p.on("console", (m) => m.type() === "error" && errs.push(m.text()));
    await p.addInitScript((t) => localStorage.setItem("askjev.theme", t), theme);
    await p.goto(url, { waitUntil: "networkidle" });
    // the portrait scrolls inside its own container; unwrap it so element screenshots see the whole chapter
    await p.addStyleTag({ content: "html,body{overflow:visible!important;height:auto!important}.pt{position:static!important;overflow:visible!important}" });
    await p.waitForTimeout(600);
    const ids = await p.$$eval("section.pt-field", (s) => s.map((x, i) => x.id || `s${i}`));
    for (const [i, id] of ids.entries()) {
      if (only && !only.split(",").includes(id)) continue;
      const el = (await p.$$("section.pt-field"))[i];
      await el.screenshot({ path: `${out}/${String(i).padStart(2, "0")}_${id}_${theme}_${width}.png` });
    }
    if (errs.length) console.log(theme, width, "errors:", errs.slice(0, 5));
    await ctx.close();
  }
}
await b.close();
