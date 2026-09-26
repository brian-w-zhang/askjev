import { ballOf, finish, kidsFn, mul, norm, preorder, relax, type Body, type LayoutInput, type Placed, type V3 } from "./common";

// Onion: depth is distance from the center. The root sits in the middle, every level of the tree is a
// shell around it, and each topic owns a patch of the sky (a wedge of the sphere) sized by how much its
// subtree holds. World, Self and Machine split the sphere into three wedges; each wedge is cut again for
// their children, and so on outward. Cells are cut in balanced halves, so they stay close to square.

const Z_MAX = 0.94; // keep off the poles, where wedges pinch
const SHELL_GAP = 2.5;
const FILL = 2.4; // shell area per node's footprint

interface Cell { l0: number; l1: number; z0: number; z1: number } // longitude, and z = sin(latitude): equal-area

export function onion(inp: LayoutInput): Map<string, Placed> {
  const kids = kidsFn(inp);
  const order = preorder(inp);
  const depthOf = (id: string) => inp.nodes[id].depth;

  // what each subtree needs on the sky: the footprint of every ball in it
  const foot = new Map<string, number>();
  for (let i = order.length - 1; i >= 0; i--) {
    const id = order[i];
    const b = ballOf(inp, id);
    foot.set(id, (2 * b + 0.8) ** 2 + kids(id).reduce((s, k) => s + foot.get(k)!, 0));
  }

  // shell radii: each level far enough out to hold its nodes' footprints, and clear of the level below
  const maxD = Math.max(...order.map(depthOf));
  const need = new Array(maxD + 1).fill(0), big = new Array(maxD + 1).fill(0);
  for (const id of order) {
    const d = depthOf(id), b = ballOf(inp, id);
    need[d] += (2 * b + 0.8) ** 2 * FILL;
    big[d] = Math.max(big[d], b);
  }
  const shell = [0];
  for (let d = 1; d <= maxD; d++)
    shell[d] = Math.max(shell[d - 1] + big[d - 1] + big[d] + SHELL_GAP, Math.sqrt(need[d] / (4 * Math.PI * Z_MAX)));

  const cellOf = new Map<string, Cell>();
  const split = (ids: string[], c: Cell) => {
    if (!ids.length) return;
    if (ids.length === 1) {
      cellOf.set(ids[0], c);
      return;
    }
    const total = ids.reduce((s, k) => s + foot.get(k)!, 0);
    // halve the list by weight, then cut the cell across its longer side in the same proportion
    let acc = 0, cut = 1;
    for (let i = 0; i < ids.length - 1; i++) {
      acc += foot.get(ids[i])!;
      cut = i + 1;
      if (acc >= total / 2) break;
    }
    const left = ids.slice(0, cut), right = ids.slice(cut);
    const f = left.reduce((s, k) => s + foot.get(k)!, 0) / total;
    const zc = (c.z0 + c.z1) / 2;
    const wide = (c.l1 - c.l0) * Math.sqrt(1 - zc * zc); // arc widths on the unit sphere
    const tall = Math.asin(Math.min(1, c.z1)) - Math.asin(Math.max(-1, c.z0));
    if (wide >= tall) {
      const m = c.l0 + (c.l1 - c.l0) * f;
      split(left, { ...c, l1: m });
      split(right, { ...c, l0: m });
    } else {
      const m = c.z0 + (c.z1 - c.z0) * f;
      split(left, { ...c, z1: m });
      split(right, { ...c, z0: m });
    }
  };
  // hemispheres are three longitude wedges (not balanced halves), so each one is a clean slice of sky
  const hemis = kids(inp.rootId);
  const tot = hemis.reduce((s, h) => s + foot.get(h)!, 0);
  let l = -Math.PI / 2;
  for (const h of hemis) {
    const w = (foot.get(h)! / tot) * Math.PI * 2;
    cellOf.set(h, { l0: l, l1: l + w, z0: -Z_MAX, z1: Z_MAX });
    l += w;
  }
  for (const id of order) if (id !== inp.rootId && cellOf.has(id)) split(kids(id), cellOf.get(id)!);

  const pos = new Map<string, V3>();
  const at = (c: Cell, r: number): V3 => {
    const lon = (c.l0 + c.l1) / 2, z = (c.z0 + c.z1) / 2, s = Math.sqrt(1 - z * z);
    return [r * s * Math.cos(lon), r * z, r * s * Math.sin(lon)];
  };
  pos.set(inp.rootId, [0, 0, 0]);
  for (const id of order) if (cellOf.has(id)) pos.set(id, at(cellOf.get(id)!, shell[depthOf(id)]));

  // slide crowded neighbors apart along their shell
  const ids = order.filter((id) => id !== inp.rootId);
  const bodies: Body[] = ids.map((id) => ({ p: pos.get(id)!, r: ballOf(inp, id) }));
  relax(bodies, 50, 0.3, (i, p) => mul(norm(p), shell[depthOf(ids[i])]));
  ids.forEach((id, i) => pos.set(id, bodies[i].p));
  return finish(inp, pos);
}
