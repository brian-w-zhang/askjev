// How much does Jev's rerank change search results? For each mock query: the instant search (local
// embeddings + trigram), then the one Jev rerank request over its top 20, as the search box does.
//   NODE_EXTRA_CA_CERTS=~/.portless/ca.pem node web/scripts/rerank_eval.mjs [baseUrl]
const BASE = process.argv[2] ?? "https://askjev.localhost";
const QUERIES = [
  "best pizza topping", "is a hot dog a sandwich", "should I quit my job", "capital of australia",
  "is this email spam", "cats or dogs", "will AI take jobs", "how tall is mount everest",
  "is pineapple on pizza okay", "should tipping be mandatory", "favorite season", "is it rude to recline your seat",
  "best programming language", "does this code have a bug", "is the earth flat", "tea or coffee",
  "is lying ever okay", "introvert or extrovert", "sentiment of this review", "should I text my ex",
  "bitcoin price next year", "healthiest breakfast", "is math discovered or invented", "rate this joke",
  "should kids have phones", "are you a morning person", "is water wet", "best harry potter book",
  "do aliens exist", "which planet is the biggest",
];

const kendall = (a, b) => {
  const pos = new Map(b.map((id, i) => [id, i]));
  let c = 0, d = 0;
  for (let i = 0; i < a.length; i++) for (let j = i + 1; j < a.length; j++) {
    const s = Math.sign(pos.get(a[j]) - pos.get(a[i]));
    if (s > 0) c++; else if (s < 0) d++;
  }
  return (c - d) / Math.max(1, c + d);
};

const rows = [];
for (const q of QUERIES) {
  let t = performance.now();
  const s = await fetch(`${BASE}/api/search?q=${encodeURIComponent(q)}`).then((r) => r.json());
  const searchMs = performance.now() - t;
  const hits = (s.results ?? []).slice(0, 20);
  if (hits.length < 2) { rows.push({ q, n: hits.length, skipped: true }); continue; }
  t = performance.now();
  const r = await fetch(`${BASE}/api/rerank`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ q, candidates: hits.map((h) => ({ id: h.id, text: h.text })) }) }).then((x) => x.json());
  const rerankMs = performance.now() - t;
  if (r.error) { rows.push({ q, error: r.error }); continue; }
  const before = hits.map((h) => h.id);
  const after = r.order.map((o) => o.id);
  const text = new Map(hits.map((h) => [h.id, h.text]));
  const top = r.order[0], second = r.order[1];
  rows.push({
    q, n: hits.length, searchMs, rerankMs, cached: r.cached,
    top1Changed: before[0] !== after[0],
    jevTopWasRank: before.indexOf(after[0]) + 1, // where Jev's favorite sat in the embedding order
    top3Overlap: after.slice(0, 3).filter((id) => before.slice(0, 3).includes(id)).length,
    tau: kendall(before, after),
    meanShift: before.reduce((s, id, i) => s + Math.abs(after.indexOf(id) - i), 0) / before.length,
    pTop: top.p, margin: top.p - (second?.p ?? 0),
    embTop: text.get(before[0]), jevTop: text.get(after[0]),
    sim1: hits[0].sim, sim2: hits[1]?.sim ?? 0,
  });
}

const ok = rows.filter((r) => !r.skipped && !r.error);
const avg = (k) => ok.reduce((s, r) => s + r[k], 0) / ok.length;
const pct = (f) => `${Math.round((100 * ok.filter(f).length) / ok.length)}%`;
const med = (k) => { const v = ok.map((r) => r[k]).sort((a, b) => a - b); return v[Math.floor(v.length / 2)]; };
console.log(`queries ${QUERIES.length}, reranked ${ok.length}, skipped ${rows.filter((r) => r.skipped).length}, errors ${rows.filter((r) => r.error).length}`);
console.log(`top-1 changed by Jev: ${pct((r) => r.top1Changed)}`);
console.log(`Jev's top came from embedding rank: 1 → ${pct((r) => r.jevTopWasRank === 1)}, 2-3 → ${pct((r) => r.jevTopWasRank >= 2 && r.jevTopWasRank <= 3)}, 4-10 → ${pct((r) => r.jevTopWasRank >= 4 && r.jevTopWasRank <= 10)}, 11-20 → ${pct((r) => r.jevTopWasRank > 10)}`);
console.log(`top-3 overlap (of 3): mean ${avg("top3Overlap").toFixed(2)}`);
console.log(`Kendall tau (1 = same order): mean ${avg("tau").toFixed(2)}; mean |rank shift| ${avg("meanShift").toFixed(1)} places`);
console.log(`Jev's top probability: median ${med("pTop").toFixed(2)}; margin over #2: median ${med("margin").toFixed(2)}`);
console.log(`latency: search median ${Math.round(med("searchMs"))} ms, rerank median ${Math.round(med("rerankMs"))} ms (cached ${pct((r) => r.cached)})`);
console.log("\nquery | top-1 changed | Jev's pick came from | p | embedding #1 → Jev #1");
for (const r of ok) console.log(`${r.q} | ${r.top1Changed ? "yes" : "no"} | #${r.jevTopWasRank} | ${r.pTop.toFixed(2)} | ${(r.embTop ?? "").slice(0, 55)}${r.top1Changed ? "  →  " + (r.jevTop ?? "").slice(0, 55) : ""}`);
for (const r of rows.filter((x) => x.error || x.skipped)) console.log("!", r.q, r.error ?? `only ${r.n} results`);

// Gating rules: which calls could be skipped, and which of Jev's changes would survive
console.log("\nquery | search #1 similarity | gap to #2 | Jev p | top-1 changed");
for (const r of ok) console.log(`${r.q} | ${r.sim1.toFixed(3)} | ${(r.sim1 - r.sim2).toFixed(3)} | ${r.pTop.toFixed(2)} | ${r.top1Changed ? "yes" : "no"}`);
for (const [name, skip, keep] of [
  ["skip when search #1 similarity >= 0.95", (r) => r.sim1 >= 0.95, () => true],
  ["skip when #1 >= 0.93", (r) => r.sim1 >= 0.93, () => true],
  ["apply Jev only when p >= 0.5", () => false, (r) => r.pTop >= 0.5],
  ["skip >= 0.95 and apply only p >= 0.5", (r) => r.sim1 >= 0.95, (r) => r.pTop >= 0.5],
]) {
  const calls = ok.filter((r) => !skip(r)).length;
  const changes = ok.filter((r) => !skip(r) && keep(r) && r.top1Changed).map((r) => r.q);
  console.log(`\n${name}: Jev calls ${calls}/${ok.length}; top-1 changes kept ${changes.length}/${ok.filter((r) => r.top1Changed).length}: ${changes.join(", ")}`);
}
