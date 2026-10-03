// Responsiveness probe (docs/12-polish.md): how long the things a visitor waits on take, on a desktop and a phone.
// First dots on the map, a topic click until the side panel opens, a dot click (a tap on phones) until its card opens,
// and each nav switch (Map -> Portrait -> Atlas -> Map) until the next page is drawn. Prints one line per step.
//   node scripts/portrait/perf.mjs [base-url] [desktop|phone|both]
import { createRequire } from "node:module";

const { chromium } = createRequire(new URL("../../web/package.json", import.meta.url))("playwright");
const base = process.argv[2] ?? "http://localhost:4592";
const which = process.argv[3] ?? "both";
const PHONE = { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1" };
const DESKTOP = { viewport: { width: 1440, height: 900 } };

const b = await chromium.launch({ channel: "chrome", headless: !process.argv.includes("--headed") });
for (const [name, opts] of [["desktop", DESKTOP], ["phone", PHONE]]) {
  if (which !== "both" && which !== name) continue;
  const ctx = await b.newContext(opts);
  const p = await ctx.newPage();
  const errors = [];
  p.on("pageerror", (e) => errors.push(e.message.slice(0, 160)));
  // main-thread stalls: a click waits behind whatever task is running
  await p.addInitScript(() => {
    window.__long = [];
    new PerformanceObserver((l) => { for (const e of l.getEntries()) window.__long.push(Math.round(e.duration)); }).observe({ type: "longtask", buffered: true });
  });
  const stalls = async () => p.evaluate(() => { const l = window.__long ?? []; window.__long = []; return l.length ? `long tasks: ${l.length}, max ${Math.max(...l)} ms, total ${l.reduce((a, b) => a + b, 0)} ms` : "no long tasks"; }).catch(() => "");
  const phone = name === "phone";
  const line = (step, ms, note = "") => console.log(`${name.padEnd(7)} ${step.padEnd(26)} ${ms === null ? "  fail" : String(ms).padStart(6) + " ms"}  ${note}`);
  const until = async (fn, arg, timeout = 30000) => {
    const t0 = Date.now();
    try { await p.waitForFunction(fn, arg, { timeout, polling: 16 }); return Date.now() - t0; } catch { return null; }
  };
  const tap = (x, y) => (phone ? p.touchscreen.tap(x, y) : p.mouse.click(x, y));
  const panelOpen = () => document.querySelector("[data-testid=panel]")?.dataset.open === "true";

  // the map: first dots (the store's star snapshot is in and drawn)
  const t0 = Date.now();
  await p.goto(base + "/", { waitUntil: "commit" });
  const html = Date.now() - t0;
  line("map html", html);
  const nodes = await until(() => Number(document.querySelector("[data-testid=stage]")?.dataset.nodes) > 0);
  line("map tree loaded", nodes === null ? null : html + nodes);
  const labels = await until(() => [...document.querySelectorAll(".skylabel.d1")].some((e) => e.textContent && Number(getComputedStyle(e).opacity) > 0.5));
  line("map hemisphere labels", labels === null ? null : html + nodes + labels, "(after the intro animation) " + await stalls());

  // a topic: tap its label, time until the side panel is open
  await p.waitForTimeout(1500);
  for (const k of [0, 1]) {
    const r = await p.evaluate((k) => {
      const els = [...document.querySelectorAll(".skylabel.d1, .skylabel.d2")].filter((e) => e.textContent && Number(getComputedStyle(e).opacity) > 0.5);
      const e = els[k * 3 % Math.max(1, els.length)];
      if (!e) return null;
      const b = e.getBoundingClientRect();
      return { x: b.left + b.width / 2, y: b.top + b.height / 2, text: e.textContent };
    }, k);
    if (!r) { line(`topic click ${k + 1}`, null, "no label"); continue; }
    await p.evaluate(() => { window.__label = document.querySelector("[data-testid=panel] .panel-title")?.closest("aside")?.innerText.slice(0, 80) ?? ""; });
    await tap(r.x, r.y);
    const ms = await until(() => document.querySelector("[data-testid=panel]")?.dataset.open === "true"
      && document.querySelector("[data-testid=panel]")?.dataset.pending !== "true", undefined, 20000);
    line(`topic click ${k + 1}`, ms, `${r.text}; ${await stalls()}`);
    await p.waitForTimeout(1200);
  }
  await p.keyboard.press("Escape");
  await p.waitForTimeout(1500);

  // a dot: hover-and-click on desktop, a bare tap on a phone, at a grid of points until a card opens
  let dot = null;
  const W = opts.viewport.width, H = opts.viewport.height;
  outer: for (const fy of [0.45, 0.55, 0.35, 0.65]) {
    for (const fx of [0.5, 0.42, 0.58, 0.34, 0.66]) {
      const x = Math.round(W * fx), y = Math.round(H * fy);
      if (!phone) { await p.mouse.move(x, y); await p.waitForTimeout(120); }
      const hit = phone ? true : await p.evaluate(() => true);
      if (!hit) continue;
      const t = Date.now();
      await tap(x, y);
      const ms = await until(() => document.querySelector("[data-testid=panel]")?.dataset.open === "true"
        && !!document.querySelector("[data-testid=panel] .panel-title")?.textContent?.startsWith("Question"), undefined, 2500);
      if (ms !== null) { dot = Date.now() - t; break outer; }
      if (await p.evaluate(panelOpen)) { await p.keyboard.press("Escape"); await p.waitForTimeout(800); }
    }
  }
  line("dot click -> card", dot, dot === null ? "no dot opened at 20 points" : "");
  await p.keyboard.press("Escape");
  await p.waitForTimeout(800);

  // nav: Map -> Portrait -> Atlas -> Map, each until the next page has drawn its content
  const nav = async (label, ready) => {
    const t = Date.now();
    const link = p.locator(`nav a:has-text("${label}"), nav button:has-text("${label}")`).first();
    if (phone) await link.tap(); else await link.click();
    const ms = await until(ready, undefined, 30000);
    line(`nav -> ${label}`, ms === null ? null : Date.now() - t, await stalls());
  };
  await nav("Portrait", () => location.pathname === "/portrait" && document.querySelectorAll(".pt h1, .pt h2").length > 2);
  await p.waitForTimeout(800);
  await nav("Atlas", () => location.pathname === "/portrait/atlas" && document.querySelectorAll(".atlas-page a[href^='/portrait/atlas/']").length > 10);
  await p.waitForTimeout(800);
  await nav("Map", () => location.pathname === "/" && Number(document.querySelector("[data-testid=stage]")?.dataset.nodes) > 0 && !!document.querySelector(".stage canvas"));
  await p.waitForTimeout(800);
  await nav("Portrait", () => location.pathname === "/portrait" && document.querySelectorAll(".pt h1, .pt h2").length > 2);
  if (errors.length) console.log(`${name} page errors:\n  ` + errors.join("\n  "));
  await ctx.close();
}
await b.close();
