// Web Vitals for docs/12-polish.md (C4): LCP, CLS, TTFB, DOM ready and bytes transferred per route, median of a few
// cold loads. ASKJEV_KEY opens private production first.
//   node scripts/portrait/vitals.mjs [base-url] [runs]
import { createRequire } from "node:module";

const { chromium } = createRequire(new URL("../../web/package.json", import.meta.url))("playwright");
const base = process.argv[2] ?? "http://localhost:4592";
const runs = Number(process.argv[3] ?? 3);
const med = (xs) => xs.sort((a, b) => a - b)[Math.floor(xs.length / 2)];
const b = await chromium.launch({ channel: "chrome" });
for (const route of ["/", "/portrait", "/portrait/atlas"]) {
  const res = [];
  for (let i = 0; i < runs; i++) {
    const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
    const p = await ctx.newPage();
    if (process.env.ASKJEV_KEY) { await p.goto(`${base}/?key=${encodeURIComponent(process.env.ASKJEV_KEY)}`); await p.goto("about:blank"); }
    await p.addInitScript(() => {
      window.__v = { lcp: 0, cls: 0 };
      new PerformanceObserver((l) => { for (const e of l.getEntries()) window.__v.lcp = e.startTime; }).observe({ type: "largest-contentful-paint", buffered: true });
      new PerformanceObserver((l) => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__v.cls += e.value; }).observe({ type: "layout-shift", buffered: true });
    });
    let bytes = 0;
    p.on("response", async (r) => { const h = await r.headerValue("content-length").catch(() => null); bytes += Number(h || 0); });
    await p.goto(base + route, { waitUntil: "networkidle", timeout: 90000 });
    await p.waitForTimeout(1500);
    const v = await p.evaluate(() => {
      const n = performance.getEntriesByType("navigation")[0];
      const kb = performance.getEntriesByType("resource").reduce((s, e) => s + (e.transferSize || 0), n.transferSize || 0) / 1024;
      return { lcp: window.__v.lcp, cls: window.__v.cls, ttfb: n.responseStart, dom: n.domContentLoadedEventEnd, kb };
    });
    res.push(v);
    await ctx.close();
  }
  const m = (k) => med(res.map((r) => r[k]));
  console.log(`${route.padEnd(16)} LCP ${m("lcp").toFixed(0)}ms  CLS ${m("cls").toFixed(3)}  TTFB ${m("ttfb").toFixed(0)}ms  DOM ${m("dom").toFixed(0)}ms  ${m("kb").toFixed(0)} KB`);
}
await b.close();
