import type { NextRequest } from "next/server";
import { q, toVector } from "@/lib/server/db";
import { nearest, vectors, type Hit } from "@/lib/server/search";
import { embed } from "@/lib/server/embed";
import { starOf, stars } from "@/lib/server/stars";

// Rewordings of one question sit at cosine ≥ 0.95 to each other (e.g. "Is a hotdog a sandwich?" / "Are hot-dogs
// sandwiches?" 0.95-0.99), while genuinely different questions next to them stay below ~0.93 ("…or taco?" 0.92).
const SAME = 0.95;
const SHOWN = 20; // groups returned; candidates are fetched deeper so grouping still fills the list

type Answer = { label: string; p: number } | null;

/** Length of the common opening of two normalized texts. */
function sharedStem(a: string, b: string) {
  let k = 0;
  while (k < a.length && k < b.length && a[k] === b[k]) k++;
  return k;
}

/** Jev's stored top answer as words: Yes / No, the option's label, or the Score level's text. */
function answerOf(primitive: string, options: unknown, top: string | null, p: number | null): Answer {
  if (top === null || p === null) return null;
  // option keys are snake_case ("don_t_care"): restore contractions, then spaces
  const words = (v: unknown, k: string) => (typeof v === "string" ? v : (v as { what?: string } | null)?.what ?? k.replace(/([a-z])_t(?=_|$)/g, "$1't").replace(/_/g, " "));
  let label = top;
  if (primitive === "noul") label = top === "true" ? "Yes" : top === "false" ? "No" : top;
  else if (primitive === "score" && Array.isArray(options)) label = words(options[Number(top)], top);
  else if (options && typeof options === "object" && !Array.isArray(options)) label = words((options as Record<string, unknown>)[top], top);
  label = label.replace(/\s+/g, " ").trim();
  label = label.charAt(0).toUpperCase() + label.slice(1);
  return { label: label.length > 28 ? label.slice(0, 27) + "…" : label, p };
}

// GET /api/search?q=...  local embedding → the nearest questions, near-duplicates grouped (the best-matching
// wording leads each group), each with Jev's stored answer, plus the closest topics.
// Every result carries its node path so the UI can animate root → ... → node at once.
export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const text = (sp.get("q") ?? "").trim();
  if (!text) return Response.json({ q: text, results: [], nodes: [], timing: {} });
  const hidden = sp.get("hidden") === "1";
  const t0 = performance.now();
  const vec = toVector(await embed(text));
  const t1 = performance.now();
  const [cands, nodes, snap] = await Promise.all([
    nearest(vec, hidden, 40),
    q<{ id: string; label: string; hemisphere: string; sim: number }>(
      `select id, label, hemisphere, 1 - (embedding <=> $1::vector) as sim from nodes
        where status = 'active' and embedding is not null order by embedding <=> $1::vector limit 5`, [vec]),
    stars(), // each result's dot, so the map can light it as you type
  ]);

  // group rewordings (and same-text variants with different options) under the best-matching one, greedily
  const vecs = await vectors(cands.map((c) => c.id));
  const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  const cos = (a: Float32Array, b: Float32Array) => { let s = 0, na = 0, nb = 0; for (let i = 0; i < a.length; i++) { s += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i]; } return s / Math.sqrt(na * nb); };
  const groups: { lead: Hit; more: Hit[] }[] = [];
  for (const c of cands) {
    const v = vecs.get(c.id);
    const g = groups.find(({ lead }) => {
      if (norm(lead.text) === norm(c.text)) return true;
      // items of one instrument share a long fixed stem and differ in a short slot ("How much do you experience
      // 'fence' / 'yard' by hearing?" sit at 0.98), so a shared opening of 20+ characters means different items
      if (sharedStem(norm(lead.text), norm(c.text)) >= 20) return false;
      const lv = vecs.get(lead.id);
      return !!(v && lv && cos(v, lv) >= SAME);
    });
    if (g) g.more.push(c);
    else if (groups.length < SHOWN) groups.push({ lead: c, more: [] });
  }

  const shown = groups.flatMap((g) => [g.lead, ...g.more]);
  const ids = shown.map((h) => h.id);
  const nodeIds = [...new Set([...groups.map((g) => g.lead.node_id), ...nodes.map((n) => n.id)])];
  const [paths, meta] = await Promise.all([
    nodeIds.length
      ? q<{ nid: string; id: string; label: string }>(
          `select n.id as nid, a.id, a.label from nodes n join nodes a on a.path @> n.path
            where n.id = any($1) order by n.id, a.depth`, [nodeIds])
      : Promise.resolve([]),
    q<{ id: string; options: unknown; top: string | null; p_top: number | null }>(
      `select q.id, q.options, m.top, m.p_top from questions q left join question_meta m on m.question_id = q.id where q.id = any($1)`, [ids]),
  ]);
  const pathOf = new Map<string, { id: string; label: string }[]>();
  for (const p of paths) {
    if (!pathOf.has(p.nid)) pathOf.set(p.nid, []);
    pathOf.get(p.nid)!.push({ id: p.id, label: p.label });
  }
  const answers = new Map(meta.map((m) => [m.id, { top: m.top, a: answerOf(shown.find((h) => h.id === m.id)!.primitive, m.options, m.top, m.p_top) }]));
  const t2 = performance.now();
  return Response.json({
    q: text,
    results: groups.map(({ lead, more }) => {
      // agreement only across true rewordings: same-text variants have different options, so their answers differ by design
      const tops = [lead, ...more.filter((h) => norm(h.text) !== norm(lead.text))].map((h) => answers.get(h.id)?.top).filter((t): t is string => t != null);
      return {
        ...lead, score: lead.sim, star: starOf(snap, lead.node_id, lead.id), path: pathOf.get(lead.node_id) ?? [],
        answer: answers.get(lead.id)?.a ?? null,
        similar: more.map((h) => ({ id: h.id, text: h.text, variant: norm(h.text) === norm(lead.text) })),
        // do Jev's answers to the rewordings agree? (null: fewer than two answered)
        agree: tops.length < 2 ? null : tops.every((t) => t === tops[0]),
      };
    }),
    nodes: nodes.map((n) => ({ ...n, path: pathOf.get(n.id) ?? [] })),
    timing: { embed_ms: +(t1 - t0).toFixed(1), db_ms: +(t2 - t1).toFixed(1), total_ms: +(t2 - t0).toFixed(1) },
  });
}
