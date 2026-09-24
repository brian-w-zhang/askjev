import type { NextRequest } from "next/server";
import { q, toVector } from "@/lib/server/db";
import { embed } from "@/lib/server/embed";

type Hit = { id: string; text: string; primitive: string; node_id: string; hemisphere: string; sim: number; trgm: number };

// GET /api/search?q=...  local embedding → pgvector top 20 ∪ pg_trgm top 10, plus the closest nodes.
// Every result carries its node path (ids + labels) so the UI can animate root → ... → node at once.
export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const text = (sp.get("q") ?? "").trim();
  if (!text) return Response.json({ q: text, results: [], nodes: [], timing: {} });
  const hidden = sp.get("hidden") === "1";
  const t0 = performance.now();
  const vec = toVector(await embed(text));
  const t1 = performance.now();
  const vis = hidden ? "true" : "display_ok";
  // Trigram catches exact keywords (names, jargon) the embedding can blur. Full-string similarity
  // on long queries is slow on a GIN index and adds little over the embedding, so keep it to short ones.
  const useTrgm = text.split(/\s+/).length <= 4;
  const [byVec, byTrgm, nodes] = await Promise.all([
    q<Hit>(`select id, text, primitive, node_id, hemisphere, 1 - (embedding <=> $1::vector) as sim, similarity(text, $2) as trgm
              from questions where embedding is not null and ${vis}
             order by embedding <=> $1::vector limit 20`, [vec, text]),
    useTrgm
      ? q<Hit>(`select id, text, primitive, node_id, hemisphere, coalesce(1 - (embedding <=> $1::vector), 0) as sim, similarity(text, $2) as trgm
                  from questions where text % $2 and ${vis} order by similarity(text, $2) desc limit 10`, [vec, text])
      : Promise.resolve([] as Hit[]),
    q<{ id: string; label: string; hemisphere: string; sim: number }>(
      `select id, label, hemisphere, 1 - (embedding <=> $1::vector) as sim from nodes
        where status = 'active' and embedding is not null order by embedding <=> $1::vector limit 5`, [vec]),
  ]);
  const merged = new Map<string, Hit & { score: number }>();
  for (const h of [...byVec, ...byTrgm]) {
    if (!merged.has(h.id)) merged.set(h.id, { ...h, score: h.sim + 0.3 * h.trgm });
  }
  const results = [...merged.values()].sort((a, b) => b.score - a.score).slice(0, 20);
  const nodeIds = [...new Set([...results.map((r) => r.node_id), ...nodes.map((n) => n.id)])];
  const paths = nodeIds.length
    ? await q<{ nid: string; id: string; label: string }>(
        `select n.id as nid, a.id, a.label from nodes n join nodes a on a.path @> n.path
          where n.id = any($1) order by n.id, a.depth`, [nodeIds])
    : [];
  const pathOf = new Map<string, { id: string; label: string }[]>();
  for (const p of paths) {
    if (!pathOf.has(p.nid)) pathOf.set(p.nid, []);
    pathOf.get(p.nid)!.push({ id: p.id, label: p.label });
  }
  const t2 = performance.now();
  return Response.json({
    q: text,
    results: results.map((r) => ({ ...r, path: pathOf.get(r.node_id) ?? [] })),
    nodes: nodes.map((n) => ({ ...n, path: pathOf.get(n.id) ?? [] })),
    timing: { embed_ms: +(t1 - t0).toFixed(1), db_ms: +(t2 - t1).toFixed(1), total_ms: +(t2 - t0).toFixed(1) },
  });
}
