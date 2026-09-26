import { add, ballOf, finish, hash01, kidsFn, len, mul, relax, sub, type Body, type LayoutInput, type Placed, type V3 } from "./common";

// Nested bubbles (3D circle packing): every topic is a sphere holding its own question ball and its
// children's spheres, packed tightly together. No empty space between levels, so size
// reads directly as how much the topic holds.

const PAD = 0.35; // between sibling bubbles
const RIM = 0.5; // inside a bubble's edge

interface Bubble { R: number; c: V3; off: V3[] } // radius; bubble center and each child's node, relative to this node

export function pack(inp: LayoutInput): Map<string, Placed> {
  const kids = kidsFn(inp);
  const bub = new Map<string, Bubble>();

  const size = (id: string): number => {
    const b = ballOf(inp, id);
    const ks = kids(id);
    if (!ks.length) {
      bub.set(id, { R: b + RIM * 0.5, c: [0, 0, 0], off: [] });
      return b + RIM * 0.5;
    }
    const rs = ks.map(size);
    // this node's own ball packs in with its children's bubbles (it fills a gap between them rather than
    // sitting in the middle): start on a hashed Fibonacci sphere, then alternate pulling everyone toward
    // the middle and pushing overlaps apart — a cheap, deterministic sphere packing
    const all = [b, ...rs];
    const order = all.map((_, i) => i).sort((x, y) => all[y] - all[x]);
    const golden = Math.PI * (3 - Math.sqrt(5));
    const tw = hash01(id, 41) * Math.PI * 2;
    const bodies: Body[] = all.map(() => ({ p: [0, 0, 0] as V3, r: 0 }));
    order.forEach((bi, i) => {
      const z = 1 - (2 * (i + 0.5)) / all.length;
      const s = Math.sqrt(1 - z * z), ph = tw + i * golden;
      bodies[bi] = { p: mul([Math.cos(ph) * s, z, Math.sin(ph) * s], i ? all[order[0]] + all[bi] + PAD : 0), r: all[bi] };
    });
    for (let round = 0; round < 30; round++) {
      const cm = centroid(bodies);
      for (const bd of bodies) bd.p = add(cm, mul(sub(bd.p, cm), 0.85));
      relax(bodies, 10, PAD);
    }
    relax(bodies, 80, PAD);
    // smallest enclosing sphere, approximately: start at the centroid and walk toward the farthest body
    let c = centroid(bodies);
    for (let it = 0; it < 200; it++) {
      let far = 0, fi = 0;
      bodies.forEach((bd, i) => { const d = len(sub(bd.p, c)) + bd.r; if (d > far) { far = d; fi = i; } });
      c = add(c, mul(sub(bodies[fi].p, c), 0.5 / (it + 2)));
    }
    const R = Math.max(...bodies.map((bd) => len(sub(bd.p, c)) + bd.r)) + RIM;
    const me = bodies[0].p;
    // children are packed by their bubbles; their nodes sit off-center inside them
    const off = ks.map((k, i) => sub(sub(bodies[i + 1].p, bub.get(k)!.c), me));
    bub.set(id, { R, c: sub(c, me), off });
    return R;
  };
  size(inp.rootId);

  const pos = new Map<string, V3>();
  const place = (id: string, p: V3) => {
    pos.set(id, p);
    const { off } = bub.get(id)!;
    kids(id).forEach((k, i) => place(k, add(p, off[i])));
  };
  place(inp.rootId, [0, 0, 0]);
  return finish(inp, pos);
}

function centroid(bodies: Body[]): V3 {
  let m = 0;
  let c: V3 = [0, 0, 0];
  for (const bd of bodies) { const w = bd.r ** 3 + 1e-6; c = add(c, mul(bd.p, w)); m += w; }
  return mul(c, 1 / m);
}
