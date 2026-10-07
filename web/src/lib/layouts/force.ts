import { ballOf, finish, kidsFn, preorder, relax, type Body, type LayoutInput, type Placed, type V3 } from "./common";
import { simulate, type SimInput } from "./forceSim";

// Cosmic web (docs/07-ui.md, Layouts): a force simulation (forceSim.ts) that starts from the balloon tree,
// then a pass that keeps balls from overlapping. The browser runs the simulation in a worker (lib/layout.ts).

/** The simulation's input for this tree, starting from `start` (the balloon layout; without it, no start
 * positions: enough to finish from saved positions). */
export function forceInput(inp: LayoutInput, start?: Map<string, Placed>): { ids: string[]; sim: SimInput } {
  const kids = kidsFn(inp);
  const ids = preorder(inp);
  const idx = new Map(ids.map((id, i) => [id, i]));
  const r = ids.map((id) => ballOf(inp, id));
  const P: number[] = [];
  if (start) for (const id of ids) { const p = start.get(id)!; P.push(p.x, p.y, p.z); }
  const edges: number[] = [];
  for (const id of ids) for (const k of kids(id)) {
    const a = idx.get(id)!, b = idx.get(k)!;
    edges.push(a, b, r[a] + r[b] + 2 + 3 / (1 + inp.nodes[k].depth));
  }
  return { ids, sim: { P, r, edges, root: idx.get(inp.rootId)! } };
}

/** Settled positions → final positions: a pass that pushes overlapping balls apart (flat xyz per node, in `ids` order). */
export function forceRelax(sim: SimInput, settled: ArrayLike<number>): number[] {
  const bodies: Body[] = sim.r.map((r, i) => ({ p: [settled[i * 3], settled[i * 3 + 1], settled[i * 3 + 2]] as V3, r: r * 1.1, fixed: i === sim.root }));
  relax(bodies, 60, 0.3);
  return bodies.flatMap((b) => b.p);
}

/** Final positions (from forceRelax) → the layout. */
export function forcePlace(inp: LayoutInput, ids: string[], final: ArrayLike<number>): Map<string, Placed> {
  const pos = new Map<string, V3>(ids.map((id, i) => [id, [final[i * 3], final[i * 3 + 1], final[i * 3 + 2]] as V3]));
  return finish(inp, pos, { halo: true, squash: 0.3 });
}

/** Settled positions → the layout. */
export function forceFinish(inp: LayoutInput, ids: string[], sim: SimInput, settled: ArrayLike<number>): Map<string, Placed> {
  return forcePlace(inp, ids, forceRelax(sim, settled));
}

/** The whole layout, synchronously (no worker available). */
export function force(inp: LayoutInput, start: Map<string, Placed>): Map<string, Placed> {
  const { ids, sim } = forceInput(inp, start);
  return forceFinish(inp, ids, sim, simulate(sim));
}
