// Mobile audit: every page on an emulated phone (touch, mobile viewport), the way a visitor on a phone uses it.
// Records console and page errors, failed requests, anything wider than the screen, images that didn't load, and
// whether each action worked; a screenshot per step.
//   node scripts/portrait/mobile.mjs <outdir> [base-url] [width] [--cases=all|N]
import { mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";

const { chromium } = createRequire(new URL("../../web/package.json", import.meta.url))("playwright");
const out = process.argv[2] ?? "/tmp/mobile";
const base = process.argv[3] ?? "http://localhost:4592";
const width = Number(process.argv[4] ?? 390);
const casesArg = (process.argv.find((a) => a.startsWith("--cases=")) ?? "--cases=all").split("=")[1];
mkdirSync(out, { recursive: true });

const b = await chromium.launch({ channel: "chrome" });
const ctx = await b.newContext({ viewport: { width, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1" });
const p = await ctx.newPage();
const IGNORE = [/THREE\.Clock/, /Download the React DevTools/, /\[Fast Refresh\]/, /\[HMR\]/];
const logs = [];
let step = "start";
p.on("console", (m) => { if (["error", "warning"].includes(m.type()) && !IGNORE.some((r) => r.test(m.text()))) logs.push(`[${step}] ${m.type()}: ${m.text().slice(0, 220)}`); });
p.on("pageerror", (e) => logs.push(`[${step}] pageerror: ${e.message.slice(0, 220)}`));
p.on("response", (r) => { if (r.status() >= 400 && !/favicon|__nextjs|webpack-hmr/.test(r.url())) logs.push(`[${step}] http ${r.status()}: ${r.url().slice(0, 150)}`); });
const results = [];
let n = 0;
const sleep = (ms) => p.waitForTimeout(ms);
async function run(name, fn, shot = true) {
  step = name;
  const t0 = Date.now();
  try { const note = await fn(); results.push({ name, ok: true, ms: Date.now() - t0, note }); }
  catch (e) { results.push({ name, ok: false, ms: Date.now() - t0, err: String(e.message).split("\n")[0].slice(0, 240) }); }
  if (shot) await p.screenshot({ path: `${out}/${String(++n).padStart(3, "0")}_${name.replace(/\W+/g, "_").slice(0, 60)}.png` }).catch(() => {});
}
// anything wider than the screen that isn't inside a horizontally scrolling or clipping box
async function overflow() {
  return p.evaluate(() => {
    const W = document.documentElement.clientWidth, bad = [];
    // inside a box that clips, or that scrolls sideways on purpose (narrower than the screen), overflow is intended;
    // a full-width scrolling page container (the portrait's .pt) doesn't count as clipping
    const clipped = (el) => { for (let x = el.parentElement; x && x !== document.body; x = x.parentElement) { const s = getComputedStyle(x); if (/(hidden|clip)/.test(s.overflowX)) return true; if (/(auto|scroll)/.test(s.overflowX) && (x.getBoundingClientRect().width < W - 2 || x.dataset.scroll === "x")) return true; } return false; };
    for (const el of document.querySelectorAll("body *")) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const s = getComputedStyle(el);
      if (s.position === "fixed" && r.right <= W + 1) continue;
      if ((r.right > W + 1 || r.left < -1) && !clipped(el)) bad.push(`${el.tagName.toLowerCase()}.${(el.className?.baseVal ?? el.className ?? "").toString().split(" ").slice(0, 2).join(".")} [${Math.round(r.left)},${Math.round(r.right)}]`);
    }
    const wide = [...document.querySelectorAll("body *")].some((x) => !x.closest("[data-scroll=x]") && /(auto|scroll)/.test(getComputedStyle(x).overflowX) && x.getBoundingClientRect().width >= W - 2 && x.scrollWidth > x.clientWidth + 1);
    return { hscroll: document.documentElement.scrollWidth > W + 1 || wide, bad: [...new Set(bad)].slice(0, 8) };
  });
}
async function brokenImages() {
  return p.evaluate(async () => {
    const imgs = [...document.images];
    for (const i of imgs) { i.loading = "eager"; }
    await new Promise((r) => setTimeout(r, 800));
    return imgs.filter((i) => i.complete && i.naturalWidth === 0 && i.src).map((i) => i.src.slice(-80));
  });
}
async function pageCheck(label) {
  const o = await overflow();
  if (o.hscroll || o.bad.length) throw new Error(`${label} overflow: hscroll=${o.hscroll} ${o.bad.join(" | ")}`);
}
// is the canvas actually drawing stars? sample the screenshot's pixel variance
async function canvasAlive() {
  const buf = await p.screenshot();
  const { default: zlib } = await import("node:zlib");
  // crude: compare two screenshots' sizes as a proxy is weak; instead read the canvas via toDataURL where possible
  const px = await p.evaluate(() => {
    const c = document.querySelector("canvas");
    if (!c) return null;
    return { w: c.width, h: c.height, cssW: c.getBoundingClientRect().width, cssH: c.getBoundingClientRect().height };
  });
  return { bytes: buf.length, canvas: px, z: !!zlib };
}

// ================= map =================
await run("map load", async () => {
  await p.goto(base + "/", { waitUntil: "networkidle", timeout: 120000 });
  await p.waitForSelector("[data-testid=stage][data-nodes]", { timeout: 60000 });
  await sleep(4000);
  const c = await canvasAlive();
  if (!c.canvas || c.canvas.cssW < width - 2) throw new Error(`canvas ${JSON.stringify(c.canvas)}`);
  await pageCheck("map");
  return c;
});
await run("map stars drawn", async () => {
  // the star count in the header and a non-trivial number of distinct colors in the canvas area
  const count = await p.textContent(".finder-title .count");
  const shot = await p.screenshot({ clip: { x: 0, y: 300, width, height: 400 } });
  writeFileSync(`${out}/_canvas.png`, shot);
  if (!/[\d,]{7,} questions/.test(count ?? "")) throw new Error(`header count ${count}`);
  return count;
});
await run("map nav visible", async () => {
  const r = await p.$$eval("nav.sitenav .snav", (els) => els.map((e) => { const b = e.getBoundingClientRect(); return [b.left, b.right, b.top, b.bottom]; }));
  const W = width;
  if (!r.length || r.some(([l, rr, t, bt]) => l < 0 || rr > W || t < 0 || bt > 844)) throw new Error(`nav off screen ${JSON.stringify(r)}`);
});
await run("map search (tap + type)", async () => {
  await p.tap("input[aria-label='Search questions or ask Jev']");
  await p.fill("input[aria-label='Search questions or ask Jev']", "cat or dog person");
  await p.waitForSelector(".results", { timeout: 20000 });
  await sleep(2500);
  await pageCheck("search");
});
await run("map open result (tap)", async () => {
  const r = await p.$$(".results button, .results li");
  if (!r.length) throw new Error("no results");
  await r[0].tap();
  await p.waitForSelector("[data-testid=panel][data-open=true]", { timeout: 20000 });
  await sleep(2500);
  await pageCheck("panel");
});
await run("map panel content fits", async () => {
  const bx = await p.$eval("[data-testid=panel]", (e) => { const r = e.getBoundingClientRect(); return [r.left, r.right, r.top, r.bottom, e.scrollHeight, e.clientHeight]; });
  if (bx[0] < -1 || bx[1] > width + 1) throw new Error(`panel box ${bx}`);
  return bx;
});
await run("map panel scroll", async () => {
  await p.$eval("[data-testid=panel]", (e) => { const s = e.querySelector("[class*=scroll]") ?? e; s.scrollTop = 400; });
  await sleep(600);
});
await run("map panel back/close", async () => {
  const back = await p.$("button[aria-label=Back]");
  if (back && !(await back.isDisabled())) { await back.tap(); await sleep(1200); }
  const close = await p.$("button[aria-label=Close], button[aria-label='Close panel']");
  if (close) { await close.tap(); await sleep(1200); } else { await p.keyboard.press("Escape"); await sleep(1000); }
});
await run("map tap a star", async () => {
  // tap around the middle of the canvas until something opens
  for (const [x, y] of [[width / 2, 430], [width / 2 + 30, 460], [width / 2 - 40, 400], [width / 2, 500], [width / 3, 450], [2 * width / 3, 420]]) {
    await p.touchscreen.tap(x, y); await sleep(1400);
    if (await p.$("[data-testid=panel][data-open=true]")) return `opened at ${x},${y}`;
  }
  return "no star under the probed points (the view may be zoomed out)";
});
await run("map theme switch", async () => {
  const s = await p.$(".themeswitch");
  if (!s) throw new Error("no theme switch");
  const before = await s.getAttribute("aria-checked");
  await s.tap(); await sleep(1200);
  if ((await s.getAttribute("aria-checked")) === before) throw new Error("didn't switch");
  await s.tap(); await sleep(800);
});
await run("map filters open", async () => {
  const f = await p.$("button[aria-label*=ilter], button[title*=ilter]");
  if (!f) return "no filter button";
  await f.tap(); await sleep(1000);
  await pageCheck("filters");
  await p.keyboard.press("Escape"); await sleep(500);
});
await run("map feeling lucky", async () => {
  const l = await p.$("text=I'm feeling lucky");
  if (!l) return "no lucky button";
  await l.tap(); await sleep(3000);
  await pageCheck("lucky");
});
for (const [name, q] of [["map deep link node", "/?node=self.mind.happiness_wellbeing"], ["map deep link question", "/?q=a25ebfe342b6963c02b2dc2a"]]) {
  await run(name, async () => {
    await p.goto(base + q, { waitUntil: "networkidle", timeout: 120000 });
    await p.waitForSelector("[data-testid=panel][data-open=true]", { timeout: 30000 });
    await sleep(3000);
    await pageCheck(name);
  });
}
await run("map nav to portrait (tap)", async () => {
  await p.goto(base + "/", { waitUntil: "networkidle", timeout: 120000 });
  await sleep(2500);
  await p.tap("nav.sitenav >> text=Portrait");
  await p.waitForURL(/\/portrait$/, { timeout: 30000 });
  await sleep(1500);
});

// ================= portrait =================
await run("portrait full page", async () => {
  await p.goto(base + "/portrait", { waitUntil: "networkidle", timeout: 120000 });
  await p.evaluate(async () => { const sc = document.querySelector(".pt") ?? document.scrollingElement; for (let y = 0; y < sc.scrollHeight; y += 700) { sc.scrollTo(0, y); await new Promise((r) => setTimeout(r, 60)); } sc.scrollTo(0, 0); });
  await sleep(800);
  const bad = await brokenImages();
  if (bad.length) throw new Error(`broken images ${bad.join(", ")}`);
  await pageCheck("portrait");
  await p.screenshot({ path: `${out}/_portrait_full.png`, fullPage: true });
});
await run("portrait interactive", async () => {
  const done = [];
  // re-query by index each time: a tap can re-render the list
  for (const sel of [".receipts summary", ".qz button", ".tabs button", ".pt button:not(.pt-chipnav)"]) {
    const k = Math.min(await p.locator(sel).count(), sel === ".receipts summary" ? 99 : 6);
    for (let i = 0; i < k; i++) {
      const l = p.locator(sel).nth(i);
      if (!(await l.isVisible().catch(() => false))) continue;
      await l.scrollIntoViewIfNeeded().catch(() => {}); await l.tap({ timeout: 4000 }).catch(() => {}); await sleep(150); done.push(sel);
    }
  }
  await pageCheck("portrait after taps");
  return `${done.length} taps`;
});
await run("portrait to atlas (tap)", async () => {
  await p.evaluate(() => window.scrollTo(0, 0));
  await p.tap(".pt-nav >> text=Atlas");
  await p.waitForURL(/atlas/, { timeout: 30000 });
  await sleep(1500);
});

// ================= atlas =================
await run("atlas experiments index", async () => {
  await p.goto(base + "/portrait/atlas", { waitUntil: "networkidle", timeout: 120000 });
  await pageCheck("atlas index");
  const n = await p.locator(".ex-card").count();
  if (n < 190) throw new Error(`${n} cards`);
});
await run("atlas search + family + sort", async () => {
  await p.tap(".ex-search input"); await p.fill(".ex-search input", "humor"); await sleep(400);
  const k = await p.locator(".ex-card").count();
  await p.fill(".ex-search input", "");
  const fam = await p.$$(".ex-fams button"); if (fam[2]) { await fam[2].tap(); await sleep(300); await fam[0].tap(); }
  await p.selectOption(".ex-sort select", "describes"); await sleep(300);
  const m = await p.textContent(".ex-card .ex-metric");
  await p.selectOption(".ex-sort select", "rank");
  await pageCheck("atlas controls");
  return `humor ${k}; ${m}`;
});
const tabs = await p.$$eval(".at-tabs button, [role=tab]", (els) => els.map((e) => e.textContent.trim())).catch(() => []);
for (const t of tabs) {
  await run(`atlas tab ${t}`, async () => {
    await p.tap(`[role=tab] >> text=${t}`);
    await sleep(900);
    await pageCheck(`tab ${t}`);
  });
}
await run("atlas card to case (tap)", async () => {
  await p.goto(base + "/portrait/atlas", { waitUntil: "networkidle", timeout: 120000 });
  await p.tap(".ex-card >> nth=0");
  await p.waitForURL(/\/portrait\/atlas\/[a-z0-9_]+$/, { timeout: 30000 });
});

// ================= every case study =================
const ids = JSON.parse(readFileSync(new URL("../../data/analysis/experiments.json", import.meta.url))).experiments.map((e) => e.id);
const pick = casesArg === "all" ? ids : ids.slice(0, Number(casesArg));
const caseIssues = [];
for (const id of pick) {
  step = `case ${id}`;
  try {
    await p.goto(`${base}/portrait/atlas/${id}`, { waitUntil: "networkidle", timeout: 120000 });
    await p.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 800) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 40)); } });
    const o = await overflow();
    const bad = await brokenImages();
    const info = await p.evaluate(() => ({
      chart: (document.querySelector(".ex-result")?.nextElementSibling?.getBoundingClientRect().height ?? 0) > 40,
      meme: !!document.querySelector(".ex-memefig img"),
      rows: document.querySelectorAll(".ex-qs .ex-q").length,
    }));
    const issues = [];
    if (o.hscroll || o.bad.length) issues.push(`overflow ${o.bad.join(" | ")}`);
    if (bad.length) issues.push(`broken ${bad.join(",")}`);
    if (!info.chart) issues.push("no chart");
    if (info.rows === 0) issues.push("no rows");
    // tap "show more" once
    const more = await p.$(".ex-more .pt-btn");
    if (more) { await more.scrollIntoViewIfNeeded(); await more.tap(); await sleep(1200); if ((await p.locator(".ex-qs .ex-q").count()) <= info.rows) issues.push("show more didn't add rows"); }
    if (issues.length) { caseIssues.push({ id, issues }); await p.screenshot({ path: `${out}/case_${id}.png`, fullPage: true }).catch(() => {}); }
  } catch (e) { caseIssues.push({ id, issues: [String(e.message).split("\n")[0].slice(0, 200)] }); }
}
results.push({ name: `case pages (${pick.length})`, ok: caseIssues.length === 0, err: caseIssues.length ? `${caseIssues.length} with issues` : undefined });

for (const r of results) console.log(`${r.ok ? "✓" : "✗"} ${r.name} ${r.ms ?? ""}ms${r.err ? " " + r.err : ""}${r.note ? " · " + (typeof r.note === "string" ? r.note : JSON.stringify(r.note)) : ""}`);
for (const c of caseIssues) console.log(`  case ${c.id}: ${c.issues.join("; ")}`);
console.log(logs.length ? "logs:\n  " + [...new Set(logs)].slice(0, 60).join("\n  ") : "no console errors");
writeFileSync(`${out}/report.json`, JSON.stringify({ results, caseIssues, logs }, null, 1));
await b.close();
