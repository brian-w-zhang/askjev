import { add, len, mul, sub, type V3 } from "./common";

// The Web layout's force simulation, kept free of the tree and the DOM so it can run in a worker
// (force.worker.ts): tree edges are springs, every node repels every other (Barnes-Hut octree, so it stays
// fast at thousands of nodes). A fixed number of steps from a fixed start, so it always settles the same way.

const STEPS = 160;
const SPRING = 0.12;
const CHARGE = 3; // repulsion strength (scaled by ball size)
const THETA = 1.0; // Barnes-Hut opening angle

/** Flat arrays so they cross into a worker cheaply. */
export interface SimInput {
  P: number[]; // start positions, xyz per node
  r: number[]; // ball radius per node
  edges: number[]; // [parent, child, rest length] per edge
  root: number; // the node that stays put
}

interface Oct { c: V3; h: number; m: number; cm: V3; body: number; kids: (Oct | null)[] | null }

/** Settled positions, xyz per node. */
export function simulate(inp: SimInput): number[] {
  const n = inp.r.length;
  const P: V3[] = Array.from({ length: n }, (_, i) => [inp.P[i * 3], inp.P[i * 3 + 1], inp.P[i * 3 + 2]]);
  const w = inp.r.map((b) => 1 + b); // charge ∝ size, so big topics claim more room
  const edges: [number, number, number][] = [];
  for (let e = 0; e < inp.edges.length; e += 3) edges.push([inp.edges[e], inp.edges[e + 1], inp.edges[e + 2]]);

  const build = (): Oct => {
    const lo: V3 = [Infinity, Infinity, Infinity], hi: V3 = [-Infinity, -Infinity, -Infinity];
    for (const p of P) for (let a = 0; a < 3; a++) { lo[a] = Math.min(lo[a], p[a]); hi[a] = Math.max(hi[a], p[a]); }
    const root: Oct = { c: mul(add(lo, hi), 0.5), h: Math.max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]) / 2 + 1, m: 0, cm: [0, 0, 0], body: -1, kids: null };
    const insert = (o: Oct, i: number, depth: number) => {
      o.cm = mul(add(mul(o.cm, o.m), mul(P[i], w[i])), 1 / (o.m + w[i]));
      o.m += w[i];
      if (!o.kids && o.body < 0 && o.m === w[i]) { o.body = i; return; }
      if (depth > 24) return; // coincident points: just add their mass
      if (!o.kids) {
        o.kids = new Array(8).fill(null);
        const old = o.body;
        o.body = -1;
        if (old >= 0) put(o, old, depth);
      }
      put(o, i, depth);
    };
    const put = (o: Oct, i: number, depth: number) => {
      const p = P[i];
      const q = (p[0] > o.c[0] ? 1 : 0) | (p[1] > o.c[1] ? 2 : 0) | (p[2] > o.c[2] ? 4 : 0);
      let k = o.kids![q];
      if (!k) {
        const h = o.h / 2;
        k = o.kids![q] = { c: [o.c[0] + (q & 1 ? h : -h), o.c[1] + (q & 2 ? h : -h), o.c[2] + (q & 4 ? h : -h)], h, m: 0, cm: [0, 0, 0], body: -1, kids: null };
      }
      insert(k, i, depth + 1);
    };
    P.forEach((_, i) => insert(root, i, 0));
    return root;
  };

  const F: V3[] = P.map(() => [0, 0, 0]);
  const repel = (o: Oct, i: number, alpha: number) => {
    if (!o.m || o.body === i) return;
    const d = sub(P[i], o.cm);
    const l2 = d[0] * d[0] + d[1] * d[1] + d[2] * d[2] + 0.5;
    if (o.kids && (2 * o.h) ** 2 / l2 > THETA * THETA) {
      for (const k of o.kids) if (k) repel(k, i, alpha);
      return;
    }
    const f = (CHARGE * alpha * w[i] * o.m) / (l2 * Math.sqrt(l2));
    F[i][0] += d[0] * f; F[i][1] += d[1] * f; F[i][2] += d[2] * f;
  };

  const root = inp.root;
  for (let s = 0; s < STEPS; s++) {
    const alpha = 1 - s / STEPS;
    for (const f of F) f[0] = f[1] = f[2] = 0;
    const tree = build();
    for (let i = 0; i < n; i++) repel(tree, i, alpha);
    for (const [a, b, rest] of edges) {
      const d = sub(P[b], P[a]);
      const l = len(d) || 1e-6;
      const f = (SPRING * (l - rest)) / l;
      F[a][0] += d[0] * f; F[a][1] += d[1] * f; F[a][2] += d[2] * f;
      F[b][0] -= d[0] * f; F[b][1] -= d[1] * f; F[b][2] -= d[2] * f;
    }
    for (let i = 0; i < n; i++) {
      if (i === root) continue;
      // cap the step so early, crowded frames can't fling anything across the sky
      const l = len(F[i]), cap = 2 * alpha + 0.2;
      const k = l > cap ? cap / l : 1;
      P[i] = add(P[i], mul(F[i], k / Math.sqrt(w[i])));
    }
  }
  return P.flat();
}
