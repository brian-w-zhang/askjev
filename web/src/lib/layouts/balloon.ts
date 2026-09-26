import { add, ballOf, basis, dot, finish, hash01, kidsFn, len, mul, norm, relax, sub, type Body, type LayoutInput, type Placed, type V3 } from "./common";

// Balloon tree: each node's children sit on a spherical cap facing away from its parent.
//
// Every subtree is summarized by its real bounding sphere, which sits *ahead* of the node (center at
// node + axis·o, radius R), not by a sphere centered on the node. Siblings are spaced by those forward
// spheres at their actual distance, so a deep, narrow branch grows about linearly with depth instead of
// doubling its empty space at every level. The gap between a node and its children also shrinks with
// depth, and each child's distance varies a little, which keeps deep branches from looking like spokes.

const GAP = 1.1; // node ball → child ball, at the hemisphere level
const GAP_DECAY = 0.72; // per level below that
const HEMI_GAP = 7; // extra clearance between World, Self and Machine
const SHARE = 0.62; // subtree spheres are mostly empty, so neighbors may share a good part of them
const JITTER = 0.22; // child distance varies by up to this fraction
const HALO = 1.15; // stars in a haloed ball reach past its radius

const capOf = (depth: number) => (depth === 0 ? Math.PI : depth === 1 ? 1.65 : 1.4);
const gapOf = (depth: number) => Math.max(0.3, GAP * GAP_DECAY ** Math.max(0, depth - 1));

interface Arrangement { dirs: V3[]; dist: number[]; o: number; R: number }

export function balloon(inp: LayoutInput): Map<string, Placed> {
  const kids = kidsFn(inp);
  const arr = new Map<string, Arrangement>();

  // Bottom-up, in each node's local frame (node at the origin, facing +Y).
  const size = (id: string): Arrangement => {
    const depth = inp.nodes[id].depth;
    const b = ballOf(inp, id) * HALO;
    const ks = kids(id);
    if (!ks.length) {
      const a = { dirs: [], dist: [], o: 0, R: b };
      arr.set(id, a);
      return a;
    }
    const sub_ = ks.map(size);
    const R = sub_.map((a) => a.R), o = sub_.map((a) => a.o);
    const cap = capOf(depth);
    const root = depth === 0;
    // Cap distance: far enough that the children's subtree spheres fit on the cap, and clear of this
    // node's ball. Small subtrees sit closer in than big ones, and each child's distance varies a
    // little, so branches don't look like spokes.
    const dBall = ks.map((k) => b + gapOf(depth) + ballOf(inp, k) * HALO);
    const meanO = o.reduce((s, x) => s + x, 0) / ks.length;
    const need = Math.sqrt(sub_.reduce((s, a) => s + (a.R * SHARE) ** 2, 0) / (2 * (1 - Math.cos(cap))));
    const D = Math.max(...dBall, need - meanO);
    const maxR = Math.max(...R);
    const dist = ks.map((k, i) => Math.max(dBall[i], D * (0.55 + 0.45 * Math.sqrt(R[i] / maxR))) * (1 + (ks.length > 1 ? JITTER * hash01(k, 5) : 0)));
    // World, Self, Machine: a slightly tilted triangle so the nebula isn't flat from any side
    let dirs: V3[] = root
      ? ks.map((_, i) => norm([Math.cos(-Math.PI / 2 + (i * 2 * Math.PI) / 3), 0.18 * (i - 1), Math.sin(-Math.PI / 2 + (i * 2 * Math.PI) / 3)]))
      : ks.map(() => [0, 1, 0]);
    // then move everyone out together until no two subtree spheres collide
    for (let it = 0; it < 400 && ks.length > 1; it++) {
      const rho = dist.map((d, i) => d + o[i]);
      if (!root) dirs = capDirections(id, ks.length, cap, R, rho);
      const c = dirs.map((v, i) => mul(v, rho[i]));
      let clear = true;
      for (let i = 0; i < c.length && clear; i++) for (let j = i + 1; j < c.length; j++)
        if (len(sub(c[i], c[j])) < (root ? R[i] + R[j] + HEMI_GAP : (R[i] + R[j]) * SHARE)) { clear = false; break; }
      if (clear) break;
      if (root) {
        // each lobe moves only as far as its own collisions need, so a small hemisphere stays close
        for (let i = 0; i < c.length; i++) for (let j = 0; j < c.length; j++)
          if (i !== j && len(sub(c[i], c[j])) < R[i] + R[j] + HEMI_GAP) { dist[i] *= 1.02; break; }
      } else for (let i = 0; i < dist.length; i++) dist[i] *= 1.04;
    }
    // Smallest sphere centered on the axis that holds this ball and every child subtree sphere.
    const centers = dirs.map((v, i) => mul(v, dist[i] + o[i]));
    const reach = (off: number) => {
      let m = Math.abs(off) + b;
      centers.forEach((c, i) => { m = Math.max(m, Math.hypot(c[0], c[1] - off, c[2]) + R[i]); });
      return m;
    };
    let lo = 0, hi = root ? 0 : Math.max(...dist) + Math.max(...o);
    for (let it = 0; it < 40 && hi - lo > 1e-3; it++) {
      const m1 = lo + (hi - lo) / 3, m2 = hi - (hi - lo) / 3;
      if (reach(m1) < reach(m2)) hi = m2; else lo = m1;
    }
    const mid = (lo + hi) / 2;
    const a = { dirs, dist, o: mid, R: reach(mid) };
    arr.set(id, a);
    return a;
  };
  size(inp.rootId);

  // Top-down: turn each local arrangement onto the node's real outward axis.
  const pos = new Map<string, V3>();
  const place = (id: string, p: V3, axis: V3) => {
    pos.set(id, p);
    const a = arr.get(id)!;
    const ks = kids(id);
    if (!ks.length) return;
    const root = inp.nodes[id].depth === 0;
    const [u, v] = basis(axis);
    ks.forEach((k, i) => {
      const l = a.dirs[i];
      // local (x, y, z) with y along the axis → world
      const w: V3 = root ? l : norm(add(add(mul(u, l[0]), mul(axis, l[1])), mul(v, l[2])));
      place(k, add(p, mul(w, a.dist[i])), w);
    });
  };
  place(inp.rootId, [0, 0, 0], [0, 1, 0]);
  // sharing that empty space can bring two balls into contact: nudge those apart
  const ids = [...pos.keys()];
  const bodies: Body[] = ids.map((id) => ({ p: pos.get(id)!, r: ballOf(inp, id) * HALO, fixed: id === inp.rootId }));
  relax(bodies, 40, 0.3);
  ids.forEach((id, i) => pos.set(id, bodies[i].p));
  return finish(inp, pos, { halo: true, squash: 0.3 });
}

/**
 * k directions within `cap` radians of +Y: a Fibonacci spiral, then pairwise repulsion until subtree
 * spheres (radius R, at distance rho) stop overlapping.
 */
function capDirections(id: string, k: number, cap: number, R: number[], rho: number[]): V3[] {
  const twist = hash01(id, 11) * Math.PI * 2;
  const golden = Math.PI * (3 - Math.sqrt(5));
  const cosCap = Math.cos(cap);
  // biggest subtrees take the middle of the cap
  const order = R.map((_, i) => i).sort((a, b) => R[b] - R[a]);
  const dirs: V3[] = new Array(k);
  order.forEach((idx, i) => {
    const c = k === 1 ? 1 : 1 - (1 - cosCap) * ((i + 0.5) / k);
    const s = Math.sqrt(Math.max(0, 1 - c * c));
    const ph = twist + i * golden;
    dirs[idx] = [Math.cos(ph) * s, c, Math.sin(ph) * s];
  });
  if (k < 2) return dirs;
  const req = (i: number, j: number) => 2 * Math.asin(Math.min(1, ((R[i] + R[j]) * SHARE) / (2 * Math.min(rho[i], rho[j]))));
  const lim = Math.cos(Math.min(Math.PI * 0.62, cap * 1.25));
  for (let it = 0; it < 80; it++) {
    let moved = false;
    for (let i = 0; i < k; i++) {
      for (let j = i + 1; j < k; j++) {
        const a = dirs[i], b = dirs[j];
        const ang = Math.acos(Math.max(-1, Math.min(1, dot(a, b))));
        const r = req(i, j);
        if (ang >= r) continue;
        moved = true;
        const push = (r - ang) * 0.5 + 1e-4;
        let t = sub(a, b);
        if (len(t) < 1e-9) t = [Math.cos(i), 0, Math.sin(i)];
        t = norm(t);
        dirs[i] = norm(add(a, mul(t, push)));
        dirs[j] = norm(sub(b, mul(t, push)));
      }
    }
    // keep everyone on the forward side (a little slack past the cap edge)
    for (let i = 0; i < k; i++) {
      const c = dirs[i][1];
      if (c < lim) {
        const t = norm([dirs[i][0], 0, dirs[i][2]]);
        const s = Math.sqrt(1 - lim * lim);
        dirs[i] = [t[0] * s, lim, t[2] * s];
      }
    }
    if (!moved) break;
  }
  return dirs;
}
