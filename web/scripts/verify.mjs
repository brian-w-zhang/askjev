// End-to-end check of the askjev UI with headless Playwright (Chromium installed under web/node_modules).
// Start a server first (`npm run dev` or `npm run build && npm start`), then:
//   node scripts/verify.mjs [--base http://localhost:3000] [--no-ask]
// Saves screenshots to ../docs/screenshots/*.png and prints timings as JSON.
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";

process.env.PLAYWRIGHT_BROWSERS_PATH ??= "0"; // browsers live in web/node_modules, not the user cache
const { chromium } = await import("@playwright/test");

const args = process.argv.slice(2);
const BASE = args.includes("--base") ? args[args.indexOf("--base") + 1] : process.env.BASE_URL ?? "http://localhost:3000";
const DO_ASK = !args.includes("--no-ask");
const OUT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../docs/screenshots");
fs.mkdirSync(OUT, { recursive: true });

const report = { base: BASE, steps: [], search_ms: [], errors: [] };
const step = (name, extra = {}) => { report.steps.push({ name, ...extra }); console.error(`ok  ${name}`, Object.keys(extra).length ? JSON.stringify(extra) : ""); };
const fail = (msg) => { report.errors.push(msg); console.error(`ERR ${msg}`); };

// channel "chromium" = full Chromium in new headless mode, which gets a real GPU (Metal on macOS);
// the headless shell falls back to SwiftShader, which says nothing about real frame rates.
const browser = await chromium.launch({ headless: true, channel: "chromium" });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
page.on("pageerror", (e) => fail(`pageerror: ${e.message}`));
page.on("console", (m) => { if (m.type() === "error") report.errors.push(`console: ${m.text().slice(0, 200)}`); });

async function fps(ms = 2000) {
  return page.evaluate((ms) => new Promise((res) => {
    const ts = [];
    const t0 = performance.now();
    const tick = (t) => { ts.push(t); if (t - t0 < ms) requestAnimationFrame(tick); else {
      const dts = ts.slice(1).map((x, i) => x - ts[i]).sort((a, b) => a - b);
      res({ fps: +((ts.length - 1) / ((ts.at(-1) - ts[0]) / 1000)).toFixed(1), p95_frame_ms: +dts[Math.floor(dts.length * 0.95)].toFixed(1) });
    } };
    requestAnimationFrame(tick);
  }), ms);
}
// the View tool starts collapsed to its title bar
const openView = async () => {
  const t = page.locator(".controls .wintitle");
  if ((await t.getAttribute("aria-expanded")) === "false") await t.click();
};
const shot = async (name) => { const p = path.join(OUT, name); await page.screenshot({ path: p }); step(`screenshot ${name}`); };

try {
  const t0 = Date.now();
  await page.goto(BASE, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("canvas", { timeout: 30000 });
  await page.waitForFunction(() => Number(document.querySelector("[data-testid=stage]")?.dataset.nodes) >= 30, null, { timeout: 30000 });
  const gl = await page.evaluate(() => {
    const c = document.createElement("canvas").getContext("webgl2");
    const d = c && c.getExtension("WEBGL_debug_renderer_info");
    return d ? c.getParameter(d.UNMASKED_RENDERER_WEBGL) : "unknown";
  });
  step("canvas ready", { ms: Date.now() - t0, renderer: gl });
  await page.waitForTimeout(3000); // intro flight
  report.fps_idle = await fps(2500);
  step("fps idle", report.fps_idle);
  await shot("01-overview.png");

  // Search latency: time from the last keystroke to rendered results.
  const input = page.getByTestId("search");
  for (const q of ["best season", "hot dog sandwich", "basketball greatest player", "refund request", "which season is the best of the year"]) {
    await input.fill("");
    await page.waitForTimeout(100);
    const ts = Date.now();
    await input.fill(q);
    await page.waitForSelector("#search-results [data-hit]", { timeout: 10000 });
    report.search_ms.push({ q, ui_ms: Date.now() - ts, fetch_ms: Number((await page.getByTestId("latency").textContent()).replace(/\D/g, "")) });
  }
  const sorted = report.search_ms.map((s) => s.fetch_ms).sort((a, b) => a - b);
  report.search_p50_ms = sorted[Math.floor(sorted.length / 2)];
  step("search", { p50_fetch_ms: report.search_p50_ms, all: report.search_ms.map((s) => s.fetch_ms) });

  try {
    await page.getByText(/Reordered by Jev/).waitFor({ timeout: 15000 });
    step("jev rerank", { status: await page.locator(".results-status .jev").textContent() });
  } catch { fail("rerank did not finish within 15 s"); }
  await shot("02-search.png");

  // Select the top result: human-paced light from the root, camera following.
  const tSel = Date.now();
  await input.press("Enter");
  await page.waitForTimeout(700);
  report.fps_path = await fps(1200);
  step("fps during path animation", report.fps_path);
  await shot("03-path-pulse.png");
  await page.getByTestId("question-card").waitFor({ timeout: 15000 });
  step("path animation landed, card open", { ms: Date.now() - tSel });
  try {
    await page.getByTestId("walkcard").getByText(/ends at/).waitFor({ timeout: 30000 });
    await page.waitForTimeout(3500);
    step("jev walk", { text: (await page.getByTestId("walkcard").textContent()).slice(0, 200) });
  } catch { fail("Jev walk did not finish within 30 s"); }
  await shot("04-question-card.png");

  // A query where Jev's own walk leaves the embedding path: the gold light forks.
  await input.fill("does this customer want their money back");
  await page.waitForSelector("#search-results [data-hit]", { timeout: 10000 });
  await page.waitForTimeout(300);
  await input.press("Enter");
  try {
    await page.getByTestId("walkcard").getByText(/ends at/).waitFor({ timeout: 30000 });
    await page.waitForTimeout(4500);
    step("jev walk (fork)", { text: (await page.getByTestId("walkcard").textContent()).slice(0, 220) });
  } catch { fail("Jev walk (fork) did not finish within 30 s"); }
  await shot("05-jev-path-fork.png");

  // Node view via breadcrumb, then color by an indicator.
  await page.locator(".crumbs button").nth(1).click();
  await page.getByTestId("node-view").waitFor({ timeout: 10000 });
  await page.waitForTimeout(1500);
  await openView();
  await page.getByRole("button", { name: "Stability", exact: true }).click();
  await page.waitForTimeout(600);
  await shot("06-node-view-stability.png");
  await page.getByRole("button", { name: "Hemisphere", exact: true }).click();

  // Open a question from the node list: Score card (bands) if present.
  const items = page.getByTestId("question-item");
  if (await items.count()) {
    await items.first().click();
    await page.getByTestId("question-card").waitFor({ timeout: 10000 });
    await page.waitForTimeout(2500);
    await shot("07-question-from-list.png");
  }

  // Score card (bands, never an interpolated number) and a card with a human overlay.
  async function openBySearch(text, name) {
    await input.fill(text);
    await page.waitForSelector("#search-results [data-hit]", { timeout: 10000 });
    await page.waitForTimeout(250);
    await input.press("Enter");
    await page.getByTestId("question-card").waitFor({ timeout: 15000 });
    await page.waitForTimeout(3000);
    await shot(name);
  }
  await page.getByRole("switch", { name: "Show Jev's path" }).click(); // lights only for the embedding path here
  await openBySearch("How well does this describe you: I am the life of the party", "11-score-bands.png");
  report.score_card_has_bands = (await page.locator(".band").count()) > 0;
  await openBySearch("rather be painted by Van Gogh or Da Vinci", "12-human-overlay.png");
  const most = page.getByRole("button", { name: "Most people" });
  if (await most.count()) { await most.click(); await page.waitForTimeout(700); await shot("13-most-people-frame.png"); }
  report.human_overlay_markers = await page.locator(".bar .human").count();
  await page.getByRole("switch", { name: "Show Jev's path" }).click();

  // Filters dim branches without matching questions.
  await page.getByLabel("Origin").selectOption("asked");
  await page.getByRole("button", { name: "Close panel" }).click();
  await page.waitForTimeout(1500);
  await page.getByRole("button", { name: "Hemisphere", exact: true }).click();
  await page.getByTestId("search").fill("");
  await page.mouse.move(700, 450);
  for (let i = 0; i < 6; i++) { await page.mouse.wheel(0, 400); await page.waitForTimeout(120); } // zoom out
  await page.waitForTimeout(1500);
  await shot("14-filter-asked.png");
  await page.getByLabel("Origin").selectOption("");

  if (DO_ASK) {
    // search and ask share one box: the last result row asks Jev
    await page.getByTestId("search").fill("Which breakfast is best on a cold morning?");
    await page.locator(".askrow").click();
    await page.getByTestId("ask-box").waitFor();
    await page.getByTestId("prim-choice").click();
    await page.getByTestId("ask-text").fill("Which breakfast is best on a cold morning?");
    await page.getByTestId("opt-0").fill("Oatmeal");
    await page.getByTestId("opt-1").fill("Pancakes");
    await page.getByRole("button", { name: "Add option" }).click();
    await page.getByTestId("opt-2").fill("Eggs and toast");
    await shot("08-ask-form.png");
    const ta = Date.now();
    await page.getByTestId("ask-submit").click();
    const res = await Promise.race([
      page.getByTestId("question-card").waitFor({ timeout: 180000 }).then(() => "card"),
      page.getByTestId("ask-error").waitFor({ timeout: 180000 }).then(() => "error"),
    ]);
    if (res === "card") {
      await page.waitForTimeout(4000);
      step("ask", { ms: Date.now() - ta, note: await page.locator(".notice").textContent().catch(() => "") });
      await shot("09-ask-result.png");
    } else fail(`ask failed: ${await page.getByTestId("ask-error").textContent()}`);
  }

  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(1200);
  await shot("10-mobile.png");
} catch (e) {
  fail(`fatal: ${e.message}`);
  await page.screenshot({ path: path.join(OUT, "error.png") }).catch(() => {});
} finally {
  await browser.close();
}
console.log(JSON.stringify(report, null, 2));
process.exit(report.errors.filter((e) => !e.startsWith("console:")).length ? 1 : 0);
