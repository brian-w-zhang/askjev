// Interaction sweep for docs/12-polish.md (C2, C3): clicks through the map, portrait and atlas the way a visitor
// would and records console errors, page errors, failed requests and failed steps, with a screenshot per step.
//   node scripts/portrait/interact.mjs <outdir> [base-url] [width] [theme]
import { mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";

const { chromium } = createRequire(new URL("../../web/package.json", import.meta.url))("playwright");
const out = process.argv[2] ?? "/tmp/interact";
const base = process.argv[3] ?? "http://localhost:4592";
const width = Number(process.argv[4] ?? 1440);
const theme = process.argv[5] ?? "light";
mkdirSync(out, { recursive: true });

const b = await chromium.launch({ channel: "chrome" });
const ctx = await b.newContext({ viewport: { width, height: width > 800 ? 900 : 844 } });
const p = await ctx.newPage();
const logs = [];
let step = "start";
const IGNORE = [/THREE\.Clock/];
p.on("console", (m) => { if (["error", "warning"].includes(m.type()) && !IGNORE.some((r) => r.test(m.text()))) logs.push(`[${step}] ${m.type()}: ${m.text().slice(0, 200)}`); });
p.on("pageerror", (e) => logs.push(`[${step}] pageerror: ${e.message.slice(0, 200)}`));
p.on("response", (r) => { if (r.status() >= 400) logs.push(`[${step}] http ${r.status()}: ${r.url().slice(0, 140)}`); });
await p.addInitScript((t) => localStorage.setItem("askjev.theme", t), theme);
if (process.env.ASKJEV_KEY) await p.goto(`${base}/?key=${encodeURIComponent(process.env.ASKJEV_KEY)}`); // private production: set the cookie first
let n = 0;
const results = [];
async function run(name, fn) {
  step = name;
  const t0 = Date.now();
  try { await fn(); results.push({ name, ok: true, ms: Date.now() - t0 }); }
  catch (e) { results.push({ name, ok: false, ms: Date.now() - t0, err: String(e.message).slice(0, 200) }); }
  await p.screenshot({ path: `${out}/${String(++n).padStart(2, "0")}_${name.replace(/\W+/g, "_")}.png` }).catch(() => {});
}
const sleep = (ms) => p.waitForTimeout(ms);

// ---- map ----
await run("map load", async () => { await p.goto(base + "/", { waitUntil: "networkidle" }); await p.waitForSelector("[data-testid=stage][data-nodes]"); await sleep(3000); });
await run("map search", async () => { await p.fill("input[aria-label='Search questions or ask Jev']", "cat or dog person"); await p.waitForSelector(".results", { timeout: 15000 }); await sleep(2500); });
await run("map open result", async () => { const r = await p.$$(".results button, .results li"); if (!r.length) throw new Error("no results"); await r[0].click(); await p.waitForSelector("[data-testid=panel][data-open=true]", { timeout: 15000 }); await sleep(2500); });
await run("map url follows panel", async () => { const u = new URL(p.url()); if (!u.searchParams.get("q") && !u.searchParams.get("node")) throw new Error(`url ${p.url()}`); });
await run("map panel back", async () => { const bb = await p.$("button[aria-label=Back]"); if (bb && !(await bb.isDisabled())) { await bb.click(); await sleep(1500); } });
await run("map escape", async () => { await p.keyboard.press("Escape"); await sleep(800); await p.keyboard.press("Escape"); await sleep(800); });
await run("map theme toggle", async () => {
  const before = await p.getAttribute(".themeswitch", "aria-checked");
  await p.click(".themeswitch"); await sleep(1200);
  if ((await p.getAttribute(".themeswitch", "aria-checked")) === before) throw new Error("theme didn't switch");
  await p.click(".themeswitch"); await sleep(800);
});
await run("map deep link node", async () => { await p.goto(base + "/?node=self.mind.happiness_wellbeing", { waitUntil: "networkidle" }); await p.waitForSelector("[data-testid=panel][data-open=true]", { timeout: 20000 }); await sleep(3000); });
await run("map deep link question", async () => { await p.goto(base + "/?q=a25ebfe342b6963c02b2dc2a", { waitUntil: "networkidle" }); await p.waitForSelector("[data-testid=panel][data-open=true]", { timeout: 20000 }); await sleep(3000); });
await run("map bad deep link", async () => { await p.goto(base + "/?node=does.not.exist", { waitUntil: "networkidle" }); await sleep(4000); });
await run("map nav to portrait", async () => { await p.goto(base + "/", { waitUntil: "networkidle" }); await p.click("nav.sitenav >> text=Portrait"); await p.waitForURL(/\/portrait$/); await sleep(1500); });

// ---- portrait ----
await run("portrait chapters", async () => {
  for (const id of ["meet", "why", "made", "jobs", "character", "taste", "words", "numbers", "knows", "morals", "pressure", "defaults", "work", "edges"]) if (!(await p.$(`#${id}`))) throw new Error(`missing #${id}`);
  const imgs = await p.$$eval("#taste img", (xs) => xs.length);
  if (imgs < 10) throw new Error(`only ${imgs} taste pictures`);
});
await run("portrait treemap", async () => {
  await p.$eval("#made", (e) => e.scrollIntoView());
  await p.click("#made .ls-mode button >> nth=1"); await sleep(400);
  await p.click("#made .ls-key button >> nth=0"); await sleep(700);
  if (!(await p.$("#made .ls-crumb b"))) throw new Error("no zoom");
  await p.click("#made .ls-crumb button"); await sleep(500);
});
await run("portrait question list", async () => {
  await p.$eval("#character", (e) => e.scrollIntoView());
  await p.click("#character .ql-b >> nth=1");
  await p.waitForSelector("#character .ql-rows .ex-q", { timeout: 20000 });
});
await run("portrait ruler", async () => {
  await p.$eval("#words", (e) => e.scrollIntoView()); await p.click("#words .pr .tf-tabs button:nth-child(2)"); await sleep(900);
});
await run("portrait case study link", async () => {
  const href = await p.$eval("#numbers .st-more-c", (a) => a.getAttribute("href"));
  if (!/^\/portrait\/atlas\/[a-z0-9_]+$/.test(href ?? "")) throw new Error(`link ${href}`);
});
await run("portrait keyboard", async () => { await p.$eval(".pt", (e) => { e.scrollTop = 0; }); await p.keyboard.press("Tab"); await p.keyboard.press("Tab"); await p.keyboard.press("Tab"); const f = await p.evaluate(() => document.activeElement?.tagName); if (!f || f === "BODY") throw new Error("focus lost"); });
// the portrait and atlas are dark only (ThemeToggle.tsx): check it switched, whatever theme the map was in
await run("portrait is dark", async () => { if ((await p.getAttribute("html", "data-theme")) !== "dark") throw new Error("portrait not dark"); });
await run("portrait to atlas", async () => { await p.click(".pt-nav >> text=Atlas"); await p.waitForURL(/atlas/); await sleep(1200); });

// ---- atlas ----
await run("atlas experiments search", async () => { await p.fill(".ex-search input", "humor"); await sleep(400); if (!(await p.$$(".ex-grid .ex-card")).length) throw new Error("no experiments for humor"); await p.fill(".ex-search input", ""); });
await run("atlas experiment family facet", async () => { const c = await p.$$(".ex-fams button"); if (c.length > 2) { await c[2].click(); await sleep(300); await c[0].click(); } });
await run("atlas experiment sorts", async () => {
  await p.selectOption(".ex-sort select", "describes"); await sleep(300);
  const t = await p.textContent(".ex-grid .ex-card .ex-metric");
  if (!/describes Jev: \d+%/.test(t ?? "")) throw new Error(`no metric on the sorted cards: ${t}`);
  await p.selectOption(".ex-sort select", "rank"); await sleep(300);
  if (await p.$(".ex-grid .ex-card .ex-metric")) throw new Error("metric shown on Jev's rank");
});
await run("atlas experiment page", async () => { await p.click(".ex-grid .ex-card"); await p.waitForURL(/\/portrait\/atlas\/[a-z0-9_]+$/); await p.waitForSelector(".ex-result"); await sleep(400); });
await run("experiment page sections", async () => {
  for (const sel of [".ex-result", ".ex-study", ".ex-take", ".ex-caveats", ".ex-where", ".ex-rows-sec", ".ex-answers"]) if (!(await p.$(sel))) throw new Error(`missing ${sel}`);
});
await run("experiment rows paging", async () => {
  await p.waitForSelector(".ex-qs .ex-q", { timeout: 20000 });
  const before = (await p.$$(".ex-qs .ex-q")).length;
  const more = await p.$(".ex-more .pt-btn");
  if (!more) return; // five or fewer questions
  await more.click();
  await p.waitForFunction((n) => document.querySelectorAll(".ex-qs .ex-q").length > n, before, { timeout: 20000 });
});
await run("experiment rows filter", async () => {
  const f = await p.$$(".ex-rhead .pt-filters .facet");
  if (f.length < 2) return;
  await f[1].click(); await sleep(1500);
  if (!(await p.$$(".ex-qs .ex-q")).length) throw new Error("filter shows no rows");
  await f[0].click(); await sleep(800);
});
await run("experiment page to map", async () => { const a = await p.$(".ex-where a.ex-chip"); if (!a) return; const href = await a.getAttribute("href"); if (!href?.includes("?node=")) throw new Error("bad map link"); });
await run("experiment page back to atlas", async () => { await p.click(".ex-crumb a"); await p.waitForURL(/\/portrait\/atlas$/); await sleep(800); });
await run("atlas tabs", async () => { for (const t of ["Coverage", "Topics", "Sources"]) { await p.click(`.tabs button:has-text("${t}")`); await sleep(300); } });
await run("atlas search", async () => { await p.click(`.tabs button:has-text("Topics")`); await sleep(400); const i = 'input[aria-label="Search topics"]'; await p.fill(i, "humor"); await sleep(400); if (!(await p.$$(".pt-table tbody tr")).length) throw new Error("no topics for humor"); await p.fill(i, ""); });
await run("atlas section filter", async () => { const c = await p.$$(".pt-filters button"); if (c.length > 2) { await c[2].click(); await sleep(300); await c[0].click(); } });
await run("atlas sort", async () => { await p.click(`.tabs button:has-text("Topics")`); await p.click(".pt-table th button:has-text('right')"); await sleep(300); await p.click(".pt-table th button:has-text('right')"); await sleep(300); });
await run("atlas topic link", async () => { const a = await p.$(".pt-table td a"); if (!a) throw new Error("no link"); await a.click(); await p.waitForURL(/\?node=/); await p.waitForSelector("[data-testid=panel][data-open=true]", { timeout: 20000 }); await sleep(2000); });

await b.close();
writeFileSync(`${out}/interact.json`, JSON.stringify({ results, logs }, null, 1));
for (const r of results) console.log(`${r.ok ? "✓" : "✗"} ${r.name} ${r.ms}ms${r.err ? " " + r.err : ""}`);
console.log(logs.length ? "logs:\n  " + [...new Set(logs)].join("\n  ") : "no console errors");
