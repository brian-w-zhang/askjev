import { add, ballOf, finish, hashDir, kidsFn, mul, preorder, relax, type Body, type LayoutInput, type Placed, type V3 } from "./common";

// Semantic map: each topic sits where its questions' meaning puts it (/api/layout: mean question
// embedding per node, projected to 3D), so neighbors ask similar things even across branches. The tree
// is still drawn as filaments, which now cross the sky wherever a branch's topics are far apart.

const FILL = 0.05; // share of the sky's volume the balls take up

export function semantic(inp: LayoutInput): Map<string, Placed> | null {
  const coords = inp.semantic;
  if (!coords) return null;
  const kids = kidsFn(inp);
  const order = preorder(inp);
  const vol = order.reduce((s, id) => s + ballOf(inp, id) ** 3, 0);
  const S = Math.cbrt(vol / FILL);

  const pos = new Map<string, V3>();
  for (const id of order) if (coords[id]) pos.set(id, mul(coords[id], S));
  // topics with no questions of their own: the middle of their children, else just beside their parent
  for (let i = order.length - 1; i >= 0; i--) {
    const id = order[i];
    if (pos.has(id)) continue;
    const ps = kids(id).map((k) => pos.get(k)).filter((p): p is V3 => !!p);
    if (ps.length) pos.set(id, mul(ps.reduce((a, b) => add(a, b), [0, 0, 0] as V3), 1 / ps.length));
  }
  for (const id of order) {
    if (pos.has(id)) continue;
    const par = inp.nodes[id].parent_id;
    pos.set(id, add(par && pos.get(par) ? pos.get(par)! : [0, 0, 0], mul(hashDir(id, 51), 3)));
  }
  const bodies: Body[] = order.map((id) => ({ p: pos.get(id)!, r: ballOf(inp, id) * 1.15 }));
  relax(bodies, 80, 0.3);
  order.forEach((id, i) => pos.set(id, bodies[i].p));
  return finish(inp, pos, { halo: true, squash: 0.3 });
}
