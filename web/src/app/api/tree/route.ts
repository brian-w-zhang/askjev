import type { NextRequest } from "next/server";
import { q } from "@/lib/server/db";
import { subtreeRows, treeRows } from "@/lib/server/tree";
import { questionFilters } from "@/lib/server/filters";

// GET /api/tree?root=<id>&depth=2          subtree of `root`, `depth` levels below it
// GET /api/tree?expand=<id>,<id>,...        children of each listed node (path loading)
// Filters (kind, primitive, origin, hidden) add `n_match`: matching questions in each node's subtree.
export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const expand = sp.get("expand");
  const rows = expand
    ? await treeRows("n.parent_id = any($1) or n.id = any($1)", [expand.split(",")], false)
    : await subtreeRows(sp.get("root") || "root", Number(sp.get("depth") ?? 2));
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
