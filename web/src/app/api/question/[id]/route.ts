import { q } from "@/lib/server/db";

// GET /api/question/<id>: the question, its base-universe probes + answers, human dists,
// links (both directions), placements, and the request hashes behind every answer.
export async function GET(_req: Request, ctx: RouteContext<"/api/question/[id]">) {
  const { id } = await ctx.params;
  const question = (
    await q(`select id, node_id, path::text as path, hemisphere, kind, shape, primitive, text, options, state, template_id,
                    origin, source, source_item_id, license, truth, flags, display_ok, ask_count, meta, created_at
               from questions where id = $1`, [id])
  )[0];
  if (!question) return Response.json({ error: `no question ${id}` }, { status: 404 });
  const [meta, probes, human, links, placements, ancestors] = await Promise.all([
    q(`select * from question_meta where question_id = $1`, [id]),
    q(`select p.id, p.frame, p.variant_kind, p.variant_params, a.request_hash, a.model_served, a.distribution,
              a.confidence, a.option_order, a.created_at
         from probes p join answers a on a.probe_id = p.id
        where p.question_id = $1 and p.universe_id = 'base'
        order by p.frame, p.variant_kind, p.id`, [id]),
    q(`select population, n, distribution, source, wave from human_dists where question_id = $1 order by n desc nulls last`, [id]),
    q(`select l.from_id, l.to_id, l.type, l.condition, o.text as other_text, o.primitive as other_primitive,
              case when l.from_id = $1 then 'out' else 'in' end as direction
         from question_links l join questions o on o.id = case when l.from_id = $1 then l.to_id else l.from_id end
        where l.from_id = $1 or l.to_id = $1`, [id]),
    q(`select node_id, node_version, method, confidence, separation, path_probs, runner_up::text, created_at
         from placements where question_id = $1 order by created_at`, [id]),
    q(`select a.id, a.label, a.depth from nodes a where a.path @> $1::ltree order by a.depth`, [question.path]),
  ]);
  const hashes = [...new Set(probes.map((p) => p.request_hash as string))];
  const calls = hashes.length
    ? await q(`select request_hash, model_served, latency_ms, input_tokens, created_at from calls where request_hash = any($1)`, [hashes])
    : [];
  return Response.json({ question, meta: meta[0] ?? null, probes, human, links, placements, ancestors, calls });
}
