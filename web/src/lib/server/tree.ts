import "server-only";
import { q } from "./db";

// The topic rows behind /api/tree, shared with /api/layout/web (which lays out the same tree the map loads).

export async function treeRows(where: string, params: unknown[], joinRoot: boolean): Promise<Record<string, unknown>[]> {
  return q<Record<string, unknown>>(
    `select n.id, n.parent_id, n.path::text as path, n.depth, n.hemisphere, n.label, n.description, n.ord, n.source,
            coalesce(s.n_questions, 0) as n_questions, coalesce(s.n_asked, 0) as n_asked, s.kind_counts,
            s.stability, s.frame_gap, s.human_gap, s.calibration_ece, s.placement_conf, s.fragile_share,
            (select count(*)::int from nodes c where c.parent_id = n.id and c.status = 'active') as n_children,
            (select count(*)::int from nodes d where d.path <@ n.path and d.status = 'active') - 1 as n_desc
       from nodes n ${joinRoot ? "join nodes r on r.id = $1" : ""}
       left join node_stats s on s.node_id = n.id and s.scope = 'subtree'
      where n.status = 'active' and (${where})
      order by n.depth, n.ord nulls last, n.id`,
    params,
  );
}

/** `root` and up to `depth` levels below it (at most 12). */
export function subtreeRows(root: string, depth: number): Promise<Record<string, unknown>[]> {
  const d = Math.min(Math.max(Number.isFinite(depth) ? depth : 2, 0), 12);
  return treeRows("n.path <@ r.path and n.depth <= r.depth + $2", [root, d], true);
}
