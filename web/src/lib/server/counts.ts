import "server-only";
import { q } from "./db";

// Displayable question counts per topic, direct and whole-branch, computed once from one grouped count (~0.2 s)
// and kept in memory: counting a branch live took 0.5-1 s on the hemispheres and the root, on every panel open.
// Refreshed after TTL, so a pipeline write shows up within minutes locally; the production copy is read-only.
const TTL = 5 * 60 * 1000;
let cache: { at: number; out: Promise<Counts> } | null = null;

export interface Counts { direct: Map<string, number>; subtree: Map<string, number> }

export function counts(): Promise<Counts> {
  if (!cache || Date.now() - cache.at > TTL) {
    const out = load();
    cache = { at: Date.now(), out };
    out.catch(() => { if (cache?.out === out) cache = null; });
  }
  return cache.out;
}

async function load(): Promise<Counts> {
  const [rows, nodes] = await Promise.all([
    q<{ node_id: string; n: number }>(`select node_id, count(*)::int as n from questions where display_ok group by node_id`),
    q<{ id: string; parent_id: string | null; depth: number }>(`select id, parent_id, depth from nodes`),
  ]);
  const direct = new Map(rows.map((r) => [r.node_id, r.n]));
  const subtree = new Map<string, number>();
  const parent = new Map(nodes.map((n) => [n.id, n.parent_id]));
  // add each topic's own questions to it and every ancestor
  for (const [id, n] of direct) {
    for (let k: string | null | undefined = id; k; k = parent.get(k)) subtree.set(k, (subtree.get(k) ?? 0) + n);
  }
  return { direct, subtree };
}
