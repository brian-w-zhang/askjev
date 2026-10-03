import "server-only";
import { q } from "./db";
import { stars } from "./stars";

// Displayable question counts per topic, direct and whole-branch, computed once from one grouped count (~0.2 s)
// and kept in memory: counting a branch live took 0.5-1 s on the hemispheres and the root, on every panel open.
// Refreshed after TTL, so a pipeline write shows up within minutes locally. The production copy is read-only and
// its star snapshot counts exactly its shown questions (sync_prod.py uploads both), so there the counts come from the
// snapshot's 100 KB index instead: on a cold function the grouped count over a million rows took seconds.
const TTL = 5 * 60 * 1000;
let cache: { at: number; out: Promise<Counts> } | null = null;

export interface Counts { direct: Map<string, number>; subtree: Map<string, number> }

let fresh: Promise<Counts> | null = null; // a reload in flight

/** The counts; once loaded, a stale copy answers at once while a fresh one loads behind it. */
export function counts(): Promise<Counts> {
  if (!cache) {
    const out = load();
    cache = { at: Date.now(), out };
    out.catch(() => { if (cache?.out === out) cache = null; });
  } else if (Date.now() - cache.at > TTL && !fresh) {
    fresh = load();
    fresh.then((c) => { cache = { at: Date.now(), out: Promise.resolve(c) }; }, () => {}).finally(() => { fresh = null; });
  }
  return cache.out;
}

async function load(): Promise<Counts> {
  const [direct, nodes] = await Promise.all([
    process.env.STARS_URL
      ? stars().then((s) => new Map(s.index.nodes.map(([id, , n]) => [id, n])))
      : q<{ node_id: string; n: number }>(`select node_id, count(*)::int as n from questions where display_ok group by node_id`)
          .then((rows) => new Map(rows.map((r) => [r.node_id, r.n]))),
    q<{ id: string; parent_id: string | null; depth: number }>(`select id, parent_id, depth from nodes`),
  ]);
  const subtree = new Map<string, number>();
  const parent = new Map(nodes.map((n) => [n.id, n.parent_id]));
  // add each topic's own questions to it and every ancestor
  for (const [id, n] of direct) {
    for (let k: string | null | undefined = id; k; k = parent.get(k)) subtree.set(k, (subtree.get(k) ?? 0) + n);
  }
  return { direct, subtree };
}
