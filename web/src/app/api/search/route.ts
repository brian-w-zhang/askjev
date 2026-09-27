import type { NextRequest } from "next/server";
import { q, toVector } from "@/lib/server/db";
import { nearest } from "@/lib/server/search";
import { embed } from "@/lib/server/embed";
import { starOf, stars } from "@/lib/server/stars";

// GET /api/search?q=...  local embedding → the 20 nearest questions, plus the closest nodes.
// Every result carries its node path (ids + labels) so the UI can animate root → ... → node at once.
export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const text = (sp.get("q") ?? "").trim();
  if (!text) return Response.json({ q: text, results: [], nodes: [], timing: {} });
  const hidden = sp.get("hidden") === "1";
  const t0 = performance.now();
  const vec = toVector(await embed(text));
  const t1 = performance.now();
  const [results, nodes, snap] = await Promise.all([
    nearest(vec, hidden),
    q<{ id: string; label: string; hemisphere: string; sim: number }>(
      `select id, label, hemisphere, 1 - (embedding <=> $1::vector) as sim from nodes
        where status = 'active' and embedding is not null order by embedding <=> $1::vector limit 5`, [vec]),
    stars(), // each result's dot, so the map can light it as you type
  ]);
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
    results: results.map((r) => ({ ...r, score: r.sim, star: starOf(snap, r.node_id, r.id), path: pathOf.get(r.node_id) ?? [] })),
    nodes: nodes.map((n) => ({ ...n, path: pathOf.get(n.id) ?? [] })),
    timing: { embed_ms: +(t1 - t0).toFixed(1), db_ms: +(t2 - t1).toFixed(1), total_ms: +(t2 - t0).toFixed(1) },
  });
}
