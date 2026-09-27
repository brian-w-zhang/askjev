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
const IGNORE = [/THREE\.Clock/];
p.on("console", (m) => { if (["error", "warning"].includes(m.type()) && !IGNORE.some((r) => r.test(m.text()))) logs.push(`[${step}] ${m.type()}: ${m.text().slice(0, 200)}`); });
p.on("pageerror", (e) => logs.push(`[${step}] pageerror: ${e.message.slice(0, 200)}`));
p.on("response", (r) => { if (r.status() >= 400) logs.push(`[${step}] http ${r.status()}: ${r.url().slice(0, 140)}`); });
await p.addInitScript((t) => localStorage.setItem("askjev.theme", t), theme);
if (process.env.ASKJEV_KEY) await p.goto(`${base}/?key=${encodeURIComponent(process.env.ASKJEV_KEY)}`); // private production: set the cookie first
let step = "start", n = 0;
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
await run("map theme toggle", async () => { await p.click(".themebtn"); await sleep(1200); await p.click(".themebtn"); await sleep(800); });
await run("map deep link node", async () => { await p.goto(base + "/?node=self.mind.happiness_wellbeing", { waitUntil: "networkidle" }); await p.waitForSelector("[data-testid=panel][data-open=true]", { timeout: 20000 }); await sleep(3000); });
await run("map deep link question", async () => { await p.goto(base + "/?q=a25ebfe342b6963c02b2dc2a", { waitUntil: "networkidle" }); await p.waitForSelector("[data-testid=panel][data-open=true]", { timeout: 20000 }); await sleep(3000); });
await run("map bad deep link", async () => { await p.goto(base + "/?node=does.not.exist", { waitUntil: "networkidle" }); await sleep(4000); });
await run("map nav to portrait", async () => { await p.goto(base + "/", { waitUntil: "networkidle" }); await p.click("nav.sitenav >> text=Portrait"); await p.waitForURL(/\/portrait$/); await sleep(1500); });

// ---- portrait ----
await run("portrait receipts", async () => {
  const s = await p.$$(".receipts summary"); if (!s.length) throw new Error("no receipts");
  for (const x of s) { await x.scrollIntoViewIfNeeded(); await x.click(); }
  await sleep(500);
});
await run("portrait quiz", async () => {
  await p.$eval("#quiz", (e) => e.scrollIntoView());
  for (const q of await p.$$(".qz")) { const o = await q.$$("button.o"); if (o.length) await o[0].click(); await sleep(100); }
  if ((await p.$$(".qz .res")).length < 5) throw new Error("quiz did not reveal all");
});
await run("portrait you vs jev", async () => { await p.$eval("#you", (e) => e.scrollIntoView()); await sleep(400); if (!(await p.$(".youvs"))) throw new Error("no summary"); });
await run("portrait calibration", async () => {
  await p.$eval("#calibration", (e) => e.scrollIntoView()); await sleep(400);
  const svg = await p.$("#calibration svg"); const bb = await svg.boundingBox();
  for (const [fx, fy] of [[0.5, 0.5], [0.6, 0.45], [0.72, 0.35], [0.84, 0.25], [0.95, 0.12]]) await p.mouse.click(bb.x + bb.width * fx, bb.y + bb.height * fy);
  await p.click("#calibration .pt-btn"); await sleep(400);
});
await run("portrait keyboard", async () => { await p.$eval(".pt", (e) => { e.scrollTop = 0; }); await p.keyboard.press("Tab"); await p.keyboard.press("Tab"); await p.keyboard.press("Tab"); const f = await p.evaluate(() => document.activeElement?.tagName); if (!f || f === "BODY") throw new Error("focus lost"); });
await run("portrait theme", async () => { await p.click(".pt-nav .pt-chipnav.dark"); await sleep(600); await p.click(".pt-nav .pt-chipnav.dark"); await sleep(400); });
await run("portrait to atlas", async () => { await p.click(".pt-nav >> text=Atlas"); await p.waitForURL(/atlas/); await sleep(1200); });

// ---- atlas ----
await run("atlas tabs", async () => { for (const t of ["Coverage", "Topics", "Sources", "Findings"]) { await p.click(`.tabs button:has-text("${t}")`); await sleep(300); } });
await run("atlas search", async () => { await p.fill(".pt-input", "humor"); await sleep(400); if (!(await p.$$(".claimgrid .claim, .pt-table tbody tr")).length) throw new Error("no findings for humor"); await p.fill(".pt-input", ""); });
await run("atlas section filter", async () => { const c = await p.$$(".pt-filters button"); if (c.length > 2) { await c[2].click(); await sleep(300); await c[0].click(); } });
await run("atlas sort", async () => { await p.click(`.tabs button:has-text("Topics")`); await p.click(".pt-table th button:has-text('right')"); await sleep(300); await p.click(".pt-table th button:has-text('right')"); await sleep(300); });
await run("atlas topic link", async () => { const a = await p.$(".pt-table td a"); if (!a) throw new Error("no link"); await a.click(); await p.waitForURL(/\?node=/); await p.waitForSelector("[data-testid=panel][data-open=true]", { timeout: 20000 }); await sleep(2000); });

await b.close();
writeFileSync(`${out}/interact.json`, JSON.stringify({ results, logs }, null, 1));
for (const r of results) console.log(`${r.ok ? "✓" : "✗"} ${r.name} ${r.ms}ms${r.err ? " " + r.err : ""}`);
console.log(logs.length ? "logs:\n  " + [...new Set(logs)].join("\n  ") : "no console errors");
