import type { NextRequest } from "next/server";
import { q } from "@/lib/server/db";
import { questionFilters } from "@/lib/server/filters";

// GET /api/tree?root=<id>&depth=2          subtree of `root`, `depth` levels below it
// GET /api/tree?expand=<id>,<id>,...        children of each listed node (path loading)
// Filters (kind, primitive, origin, hidden) add `n_match`: matching questions in each node's subtree.
export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const expand = sp.get("expand");
  let where: string;
  let params: unknown[];
  if (expand) {
    where = "n.parent_id = any($1) or n.id = any($1)";
    params = [expand.split(",")];
  } else {
    const root = sp.get("root") || "root";
    const depth = Math.min(Math.max(Number(sp.get("depth") ?? 2), 0), 12);
    where = "n.path <@ r.path and n.depth <= r.depth + $2";
    params = [root, depth];
  }
  const rootJoin = expand ? "" : "join nodes r on r.id = $1";
  const rows = await q<Record<string, unknown>>(
    `select n.id, n.parent_id, n.path::text as path, n.depth, n.hemisphere, n.label, n.description, n.ord, n.source,
            coalesce(s.n_questions, 0) as n_questions, coalesce(s.n_asked, 0) as n_asked, s.kind_counts,
            s.stability, s.frame_gap, s.human_gap, s.calibration_ece, s.placement_conf, s.fragile_share,
            (select count(*)::int from nodes c where c.parent_id = n.id and c.status = 'active') as n_children,
            (select count(*)::int from nodes d where d.path <@ n.path and d.status = 'active') - 1 as n_desc
       from nodes n ${rootJoin}
       left join node_stats s on s.node_id = n.id and s.scope = 'subtree'
      where n.status = 'active' and (${where})
      order by n.depth, n.ord nulls last, n.id`,
    params,
  );
  const f = questionFilters(sp, "qq", 2);
  if (f.active && rows.length) {
    const counts = await q<{ id: string; n: number }>(
      `select n.id, count(qq.id)::int as n from nodes n join questions qq on qq.path <@ n.path
        where n.id = any($1) and ${f.sql} group by n.id`,
      [rows.map((r) => r.id), ...f.params],
    );
    const m = new Map(counts.map((c) => [c.id, c.n]));
    for (const r of rows) r.n_match = m.get(r.id as string) ?? 0;
  }
  return Response.json({ nodes: rows });
}
