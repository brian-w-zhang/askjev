import type { NextRequest } from "next/server";
import { q } from "@/lib/server/db";
import { questionFilters } from "@/lib/server/filters";

// GET /api/node/<id>?scope=subtree|direct&offset=0&limit=40 (+ question filters)
export async function GET(req: NextRequest, ctx: RouteContext<"/api/node/[id]">) {
  const { id } = await ctx.params;
  const sp = req.nextUrl.searchParams;
  const node = (
    await q(`select id, parent_id, path::text as path, depth, hemisphere, label, description, not_for, examples, source, locked, version
               from nodes where id = $1`, [id])
  )[0];
  if (!node) return Response.json({ error: `no node ${id}` }, { status: 404 });
  const limit = Math.min(Number(sp.get("limit") ?? 40), 200);
  const offset = Number(sp.get("offset") ?? 0);
  const scope = sp.get("scope") === "direct" ? "direct" : "subtree";
  const f = questionFilters(sp, "qq", 3);
  const scopeSql = scope === "direct" ? "qq.node_id = $1::text and $2::ltree is not null" : "qq.path <@ $2::ltree and $1::text is not null";
  const [stats, ancestors, children, questions, total] = await Promise.all([
    q(`select * from node_stats where node_id = $1`, [id]),
    q(`select a.id, a.label, a.depth from nodes a where a.path @> $1::ltree order by a.depth`, [node.path]),
    q(`select n.id, n.label, coalesce(s.n_questions,0) as n_questions from nodes n
         left join node_stats s on s.node_id = n.id and s.scope = 'subtree'
        where n.parent_id = $1 and n.status = 'active' order by n.ord nulls last, n.id`, [id]),
    q(`select qq.id, qq.node_id, qq.text, qq.primitive, qq.kind, qq.shape, qq.origin, qq.ask_count, qq.display_ok, qq.flags,
              m.top, m.p_top, m.stability, m.frame_gap, m.human_gap, m.correct, m.ambiguous
         from questions qq left join question_meta m on m.question_id = qq.id
        where ${scopeSql} and ${f.sql}
        order by (qq.node_id = $1) desc, qq.ask_count desc, qq.id
        limit ${limit} offset ${offset}`, [id, node.path, ...f.params]),
    q<{ n: number }>(`select count(*)::int as n from questions qq where ${scopeSql} and ${f.sql}`, [id, node.path, ...f.params]),
  ]);
  return Response.json({ node, stats, ancestors, children, questions, total: total[0].n, scope, offset, limit });
}
