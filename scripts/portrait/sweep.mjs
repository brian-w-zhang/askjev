// UI sweep for docs/12-polish.md (C1-C3): every route at five widths and both themes. Collects console errors and
// warnings, page errors, failed requests, horizontal overflow, elements running past the viewport, images without
// alt text and unnamed controls, and saves a viewport screenshot per case. Needs the dev server and Playwright.
//   node scripts/portrait/sweep.mjs <outdir> [base-url] [routes] [widths] [themes]
import { mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";

const { chromium } = createRequire(new URL("../../web/package.json", import.meta.url))("playwright");
const out = process.argv[2] ?? "/tmp/sweep";
const base = process.argv[3] ?? "http://localhost:4592";
const routes = (process.argv[4] ?? "/,/portrait,/portrait/atlas").split(",");
const widths = (process.argv[5] ?? "1440,1024,768,390,360").split(",").map(Number);
const themes = (process.argv[6] ?? "light,dark").split(",");
mkdirSync(out, { recursive: true });

const b = await chromium.launch({ channel: "chrome" });
const report = [];
for (const route of routes) for (const theme of themes) for (const w of widths) {
  const ctx = await b.newContext({ viewport: { width: w, height: w > 800 ? 900 : 844 }, deviceScaleFactor: 1 });
  const p = await ctx.newPage();
  const logs = [];
  p.on("console", (m) => { if (["error", "warning"].includes(m.type())) logs.push(`${m.type()}: ${m.text().slice(0, 240)}`); });
  p.on("pageerror", (e) => logs.push(`pageerror: ${e.message.slice(0, 240)}`));
  p.on("requestfailed", (r) => logs.push(`failed: ${r.url().slice(0, 160)} ${r.failure()?.errorText}`));
  p.on("response", (r) => { if (r.status() >= 400) logs.push(`http ${r.status()}: ${r.url().slice(0, 160)}`); });
  await p.addInitScript((t) => localStorage.setItem("askjev.theme", t), theme);
  const t0 = Date.now();
  await p.goto(base + route, { waitUntil: "networkidle", timeout: 90000 });
  const loadMs = Date.now() - t0;
  await p.waitForTimeout(route === "/" ? 5000 : 1200);
  // walk the portrait so lazy things mount, then come back up
  if (route.startsWith("/portrait")) {
    await p.evaluate(async () => {
      const el = document.querySelector(".pt"); if (!el) return;
      for (let y = 0; y < el.scrollHeight; y += 700) { el.scrollTop = y; await new Promise((r) => setTimeout(r, 40)); }
      el.scrollTop = 0;
    });
  }
  const checks = await p.evaluate((vw) => {
    const over = [];
    const root = document.querySelector(".pt") ?? document.documentElement;
    const hscroll = root.scrollWidth > root.clientWidth + 1 || document.documentElement.scrollWidth > vw + 1;
    for (const el of document.querySelectorAll("body *")) {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      const cs = getComputedStyle(el);
      if (cs.position === "fixed" || cs.visibility === "hidden") continue;
      if (r.right > vw + 2 || r.left < -2) {
        // only report elements that are not inside something that clips them
        let clipped = false;
        for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
          const s = getComputedStyle(a);
          if (/(hidden|auto|scroll|clip)/.test(s.overflowX)) { const ar = a.getBoundingClientRect(); if (ar.right <= vw + 2 && ar.left >= -2) { clipped = true; break; } }
        }
        if (!clipped) over.push(`${el.tagName.toLowerCase()}.${String(el.className).slice(0, 40)} [${Math.round(r.left)},${Math.round(r.right)}]`);
      }
    }
    const noAlt = [...document.querySelectorAll("img")].filter((i) => !i.getAttribute("alt")).map((i) => i.src.slice(-40));
    const unnamed = [...document.querySelectorAll("button, a, input, select")].filter((e) => {
      const name = (e.getAttribute("aria-label") || e.textContent || e.getAttribute("title") || e.getAttribute("placeholder") || "").trim();
      return !name;
    }).map((e) => `${e.tagName.toLowerCase()}.${String(e.className).slice(0, 30)}`);
    return { hscroll, over: [...new Set(over)].slice(0, 12), noAlt, unnamed: [...new Set(unnamed)].slice(0, 10) };
  }, w);
  const name = `${route.replace(/\W+/g, "_") || "_"}_${theme}_${w}`;
  await p.screenshot({ path: `${out}/${name}.png` });
  report.push({ route, theme, w, loadMs, logs: [...new Set(logs)].slice(0, 15), ...checks });
  await ctx.close();
}
await b.close();
writeFileSync(`${out}/report.json`, JSON.stringify(report, null, 1));
for (const r of report) {
  const bad = r.logs.length || r.hscroll || r.over.length || r.noAlt.length || r.unnamed.length;
  console.log(`${bad ? "✗" : "✓"} ${r.route} ${r.theme} ${r.w} load ${r.loadMs}ms` + (bad ? `\n   logs ${JSON.stringify(r.logs)}\n   hscroll ${r.hscroll} over ${JSON.stringify(r.over)}\n   noAlt ${JSON.stringify(r.noAlt)} unnamed ${JSON.stringify(r.unnamed)}` : ""));
}
