import type { NextRequest } from "next/server";
import { q } from "@/lib/server/db";
import { questionFilters } from "@/lib/server/filters";
import { counts } from "@/lib/server/counts";

type Row = Record<string, unknown> & { id: string; ask_count: number };

const COLS = `qq.id, qq.node_id, qq.text, qq.primitive, qq.kind, qq.shape, qq.origin, qq.ask_count, qq.display_ok, qq.flags,
              m.top, m.p_top, m.stability, m.frame_gap, m.human_gap, m.correct, m.ambiguous
         from questions qq left join question_meta m on m.question_id = qq.id`;

// GET /api/node/<id>?scope=subtree|direct&limit=40&after=<cursor>&page=1 (+ question filters)
// The list is the topic's own questions first (most asked first), then the rest of its branch in id order.
// It pages by cursor, not offset: `after` continues right after the last row (d:<ask_count>:<id> while still in
// the topic's own questions, r:<id> in the rest of the branch), so every page is an index lookup of a few ms,
// even on the whole tree. `page=1` returns just the next page, without the topic's stats and counts.
export async function GET(req: NextRequest, ctx: RouteContext<"/api/node/[id]">) {
  const { id } = await ctx.params;
  const sp = req.nextUrl.searchParams;
  const node = (
    await q(`select id, parent_id, path::text as path, depth, hemisphere, label, description, not_for, examples, source, locked, version
               from nodes where id = $1`, [id])
  )[0];
  if (!node) return Response.json({ error: `no node ${id}` }, { status: 404 });
  const limit = Math.min(Number(sp.get("limit") ?? 40), 200);
  const scope = sp.get("scope") === "direct" ? "direct" : "subtree";
  const f = questionFilters(sp, "qq", 3);
  const base = [id, node.path, ...f.params];
  const k = base.length + 1; // first free parameter number

  async function page(after: string | null): Promise<{ rows: Row[]; next: string | null }> {
    const [phase, a, b] = (after ?? "").split(":");
    let rows: Row[] = [];
    if (!after || phase === "d") {
      const keyset = after ? `and (qq.ask_count < $${k} or (qq.ask_count = $${k} and qq.id > $${k + 1}))` : "";
      rows = await q<Row>(
        `select ${COLS} where qq.node_id = $1 and $2::ltree is not null and ${f.sql} ${keyset}
          order by qq.ask_count desc, qq.id limit ${limit}`,
        after ? [...base, Number(a), b] : base,
      );
      const last = rows[rows.length - 1];
      if (rows.length === limit) return { rows, next: `d:${last.ask_count}:${last.id}` };
      if (scope === "direct") return { rows, next: null };
    }
    const left = limit - rows.length;
    const from = phase === "r" ? a : null;
    const rest = await q<Row>(
      `select ${COLS} where qq.path <@ $2::ltree and qq.node_id <> $1 and ${f.sql} ${from ? `and qq.id > $${k}` : ""}
        order by qq.id limit ${left}`,
      from ? [...base, from] : base,
    );
    const next = rest.length === left ? `r:${rest[rest.length - 1].id}` : null;
    return { rows: [...rows, ...rest], next };
  }

  if (sp.get("page") === "1") {
    const { rows, next } = await page(sp.get("after"));
    return Response.json({ questions: rows, next });
  }

  const scopeSql = scope === "direct" ? "qq.node_id = $1::text and $2::ltree is not null" : "qq.path <@ $2::ltree and $1::text is not null";
  // unfiltered counts come from the in-memory per-topic counts (instant); only a filtered list is counted live
  const plain = !f.active && sp.get("hidden") !== "1";
  const [stats, ancestors, children, first, total, c] = await Promise.all([
    q(`select * from node_stats where node_id = $1`, [id]),
    q(`select a.id, a.label, a.depth from nodes a where a.path @> $1::ltree order by a.depth`, [node.path]),
    q(`select n.id, n.label, coalesce(s.n_questions,0) as n_questions from nodes n
         left join node_stats s on s.node_id = n.id and s.scope = 'subtree'
        where n.parent_id = $1 and n.status = 'active' order by n.ord nulls last, n.id`, [id]),
    page(null),
    plain ? Promise.resolve(null) : q<{ n: number }>(`select count(*)::int as n from questions qq where ${scopeSql} and ${f.sql}`, base),
    counts(),
  ]);
  // the header's count: displayable questions in the whole branch (the stats rollup also counts hidden ones)
  const shown = c.subtree.get(id) ?? 0;
  const listTotal = total ? total[0].n : scope === "direct" ? c.direct.get(id) ?? 0 : shown;
  return Response.json({
    node, stats, ancestors, children, questions: first.rows, next: first.next,
    total: listTotal, shown, scope, limit,
  });
}
