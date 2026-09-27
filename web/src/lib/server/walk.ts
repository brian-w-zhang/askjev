import "server-only";
import { q } from "./db";
import { evaluate } from "./jev";

// Jev's beam walk down the tree (docs/02-tree.md §7), ported from src/askjev/place.py `place_one` so the site
// needs no Python: one Choice per beam node per level, all in one request per level, BEAM paths kept, a path
// stops at a node when no child (or "here") reaches MIN_STEP. Requests are built exactly as the Python ones
// are, so they hash the same and reuse its cached answers.

const BEAM = 3;
const MIN_STEP = 0.3;

interface Path { node: string; logp: number; steps: number; probs: [string, string, number][]; done: boolean }
const score = (p: Path) => (p.steps ? Math.exp(p.logp / p.steps) : 1);

interface Tree { label: Map<string, string>; card: Map<string, unknown>; kids: Map<string, string[]> }
let tree: { at: number; t: Tree } | null = null;

async function loadTree(): Promise<Tree> {
  if (tree && Date.now() - tree.at < 10 * 60_000) return tree.t;
  const rows = await q<{ id: string; parent_id: string | null; label: string; choice_card: unknown }>(
    "select id, parent_id, label, choice_card from nodes where status='active' order by ord",
  );
  const t: Tree = { label: new Map(), card: new Map(), kids: new Map() };
  for (const r of rows) {
    t.label.set(r.id, r.label);
    t.card.set(r.id, r.choice_card);
    if (r.parent_id) t.kids.set(r.parent_id, [...(t.kids.get(r.parent_id) ?? []), r.id]);
  }
  tree = { at: Date.now(), t };
  return t;
}

function question(t: Tree, nid: string) {
  const criteria: Record<string, unknown> = {};
  for (const k of t.kids.get(nid) ?? []) criteria[k.slice(k.lastIndexOf(".") + 1)] = t.card.get(k) ?? null;
  if (nid !== "root") {
    const lab = t.label.get(nid);
    criteria.here = { what: `The question is about ${lab} in general, or does not fit any one listed sub-area more specifically.` };
    criteria.none = { what: `The question does not belong under ${lab} at all.` };
  }
  const lab = nid !== "root" ? t.label.get(nid) : "all questions";
  return {
    type: "choice",
    instructions: {
      question: `Within ${lab}, which topic area does the question in \`question\` belong to?`,
      focus: "Judge what the question is about (its subject and what kind of judgment it asks for), not its wording. " +
        "If it needs a specific input such as a message or document, judge the domain of that input.",
    },
    criteria,
  };
}

export interface WalkResult { node: string; confidence: number; separation: number; runner_up?: string | null; path_probs: [string, string, number][] }

export async function walk(text: string, start = "root"): Promise<WalkResult> {
  const t = await loadTree();
  const state = { question: text };
  let beam: Path[] = [{ node: start, logp: 0, steps: 0, probs: [], done: false }];
  const finished: Path[] = [];
  for (let level = 0; level < 10; level++) {
    const live = beam.filter((p) => !p.done);
    if (!live.length) break;
    const expand = live.filter((p) => t.kids.get(p.node)?.length);
    for (const p of live) if (!t.kids.get(p.node)?.length) { p.done = true; finished.push(p); }
    if (!expand.length) break;
    const qs: Record<string, unknown> = {};
    expand.forEach((p, i) => (qs[`n${i}`] = question(t, p.node)));
    const { response } = await evaluate(state, qs as never);
    const cand: Path[] = [];
    expand.forEach((p, i) => {
      const a = response.answers?.[`n${i}`];
      const dist = (a?.probabilities ?? {}) as Record<string, number>;
      if (!a) return;
      const best = Math.max(0, ...Object.entries(dist).filter(([k]) => k !== "here" && k !== "none").map(([, v]) => v));
      for (const [key, prob] of Object.entries(dist)) {
        if (prob <= 0.01 || key === "none") continue;
        if (key === "here") {
          cand.push({ node: p.node, logp: p.logp + Math.log(prob), steps: p.steps + 1, probs: [...p.probs, [p.node, "here", prob]], done: true });
          continue;
        }
        const child = p.node !== "root" ? `${p.node}.${key}` : key;
        cand.push({ node: child, logp: p.logp + Math.log(prob), steps: p.steps + 1, probs: [...p.probs, [child, key, prob]], done: false });
      }
      const here = dist.here ?? 0;
      if (best < MIN_STEP && here < MIN_STEP)
        // low-confidence fork: stop at this node rather than guessing deeper
        cand.push({ node: p.node, logp: p.logp + Math.log(Math.max(best, here, 0.05)), steps: p.steps + 1, probs: [...p.probs, [p.node, "stop", best]], done: true });
    });
    cand.sort((a, b) => score(b) - score(a));
    beam = cand.slice(0, BEAM);
    finished.push(...beam.filter((c) => c.done));
  }
  finished.push(...beam.filter((p) => !p.done));
  if (!finished.length) return { node: start, confidence: 0, separation: 1, path_probs: [] };
  const best = new Map<string, Path>();
  for (const f of finished) if (!best.has(f.node) || score(f) > score(best.get(f.node)!)) best.set(f.node, f);
  const ranked = [...best.values()].sort((a, b) => score(b) - score(a));
  const top = ranked[0];
  const second = ranked[1] ? score(ranked[1]) : score(top) / 100;
  return {
    node: top.node,
    confidence: Math.round(score(top) * 1e4) / 1e4,
    separation: Math.round(Math.min(score(top) / Math.max(second, 1e-6), 100) * 1e3) / 1e3,
    runner_up: ranked[1]?.node ?? null,
    path_probs: top.probs,
  };
}
