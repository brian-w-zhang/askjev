// Live-search harness (docs/07-ui.md, Search): types a query into the search box at a human pace and
// screenshots the map at chosen prefixes, then after Jev's pause, while logging search requests and long frames.
// Needs the dev server (npm run dev) and Playwright.
//   node web/scripts/ui_typing.mjs <outdir> ["query"] [theme] [url]
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const out = process.argv[2] ?? "/tmp/askjev-typing";
const query = process.argv[3] ?? "is a hot dog a sandwich";
const theme = process.argv[4] ?? "light";
const url = process.argv[5] ?? "https://askjev.localhost/";
const KEY_MS = 170; // ~70 wpm
mkdirSync(out, { recursive: true });

const b = await chromium.launch({ channel: "chrome" });
const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, ignoreHTTPSErrors: true });
const p = await ctx.newPage();
const errs = [];
const searches = [];
p.on("pageerror", (e) => errs.push(e.message));
p.on("request", (r) => { if (r.url().includes("/api/search")) searches.push({ q: new URL(r.url()).searchParams.get("q"), t: Date.now() }); });
await p.addInitScript((t) => localStorage.setItem("askjev.theme", t), theme);
await p.goto(url);
await p.waitForFunction(() => !!window.__cam, null, { timeout: 30000 });
await p.waitForTimeout(8000); // the opening
// long frames while typing (a frame over 50 ms is a visible hitch)
await p.evaluate(() => {
  window.__frames = [];
  let last = performance.now();
  const tick = (t) => { window.__frames.push(t - last); last = t; requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
});
const box = p.getByTestId("search");
await box.click();
const t0 = Date.now();
// shoot right after these prefixes (the words, and one half-typed word)
const shots = new Set(["is a hot", "is a hot d", "is a hot dog", "is a hot dog a sandwich"].filter((s) => query.startsWith(s)));
for (let i = 1; i <= query.length; i++) {
  await box.press(query[i - 1] === " " ? "Space" : query[i - 1]);
  await p.waitForTimeout(KEY_MS);
  const prefix = query.slice(0, i);
  if (shots.has(prefix)) {
    await p.waitForTimeout(250); // the heat eases in over ~300 ms
    await p.screenshot({ path: `${out}/${theme}_${prefix.replaceAll(" ", "_")}.png` });
  }
}
await p.waitForTimeout(2200); // Jev's pause + its reorder + the green path drawing in
await p.screenshot({ path: `${out}/${theme}_after_jev.png` });
const frames = await p.evaluate(() => window.__frames);
const long = frames.filter((f) => f > 50);
console.log(JSON.stringify({
  typedMs: Date.now() - t0,
  searches: searches.map((s) => s.q),
  frames: frames.length,
  medianFrameMs: +frames.slice().sort((a, b) => a - b)[frames.length >> 1].toFixed(1),
  longFrames: long.length,
  worstFrameMs: +Math.max(...frames).toFixed(1),
  errors: errs,
}, null, 1));
await b.close();
