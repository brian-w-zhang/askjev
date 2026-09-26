import type { TreeNode } from "../types";

// Shared by every nebula layout (docs/07-ui.md, Layouts): a layout turns the tree plus each node's direct
// question count into node centers and star-ball sizes. Everything else (edges, labels, camera) reads Placed.

export type V3 = [number, number, number];

export interface Placed {
  id: string;
  x: number; y: number; z: number;
  depth: number;
  dir: V3; // outward direction (parent → node)
  ball: number; // radius of the node's own star ball
  ext: number; // radius around the node that holds its whole subtree
  spin: number; // rad/s: the ball turns slowly around its node
  halo?: boolean; // stars gather in a dense core with a soft halo instead of filling the ball evenly
  form?: number[]; // 3×3 row-major: unit-ball offset → local offset (a squashed, turned ball); default is ×ball
}

export interface LayoutInput {
  nodes: Record<string, TreeNode>;
  children: Record<string, string[]>;
  direct: Map<string, number>; // stars attached directly to each node
  rootId: string;
  semantic?: Record<string, V3> | null; // node → unit-scale 3D position from question embeddings
}

export const BALL_K = 0.3; // ball radius per ∛question
export const ballRadius = (direct: number) => BALL_K * Math.cbrt(Math.max(1, direct));

export function hash01(s: string, salt = 0): number {
  let h = 2166136261 ^ salt;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return ((h >>> 0) % 100000) / 100000;
}

export const add = (a: V3, b: V3): V3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
export const sub = (a: V3, b: V3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
export const mul = (a: V3, k: number): V3 => [a[0] * k, a[1] * k, a[2] * k];
export const dot = (a: V3, b: V3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
export const len = (a: V3) => Math.hypot(a[0], a[1], a[2]);
export const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
export const norm = (v: V3): V3 => {
  const l = len(v) || 1;
  return [v[0] / l, v[1] / l, v[2] / l];
};

/** Two unit vectors perpendicular to `axis` (and to each other), turned by `twist` radians. */
export function basis(axis: V3, twist = 0): [V3, V3] {
  const ref: V3 = Math.abs(axis[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
  const u0 = norm(cross(axis, ref));
  const v0 = cross(axis, u0);
  const c = Math.cos(twist), s = Math.sin(twist);
  return [add(mul(u0, c), mul(v0, s)), sub(mul(v0, c), mul(u0, s))];
}

/** Deterministic unit vector for `id`. */
export function hashDir(id: string, salt = 0): V3 {
  const z = hash01(id, salt) * 2 - 1, t = hash01(id, salt + 1) * Math.PI * 2, s = Math.sqrt(1 - z * z);
  return [s * Math.cos(t), z, s * Math.sin(t)];
}

export const kidsFn = (inp: LayoutInput) => (id: string) => (inp.children[id] ?? []).filter((k) => inp.nodes[k]);

export const ballOf = (inp: LayoutInput, id: string) => ballRadius(inp.direct.get(id) ?? 0);

/** Every node under `rootId`, parents before children. */
export function preorder(inp: LayoutInput): string[] {
  const kids = kidsFn(inp);
  const out: string[] = [];
  const stack = [inp.rootId];
  while (stack.length) {
    const id = stack.pop()!;
    out.push(id);
    const k = kids(id);
    for (let i = k.length - 1; i >= 0; i--) stack.push(k[i]);
  }
  return out;
}

export const spinOf = (id: string, depth: number, ball: number) =>
  (0.025 + 0.05 * hash01(id, 7)) * (hash01(id, 3) < 0.5 ? -1 : 1) * (1 + 0.25 * depth) / Math.max(1, Math.sqrt(ball));

/** A ball stretched along one hashed axis and flattened along another (volume kept), for organic layouts. */
export function squashForm(id: string, ball: number, strength = 0.28, axis?: V3): number[] {
  const a = axis ?? hashDir(id, 21);
  const [u, v] = basis(a, hash01(id, 23) * Math.PI * 2);
  const k = 1 + strength * (0.5 + hash01(id, 25));
  const s = [1 / k, k ** 0.7, k ** 0.3]; // flat along `a`, longest along u; volume unchanged
  const sa = s[0] * ball, su = s[1] * ball, sv = s[2] * ball;
  // M = sa·a aᵀ + su·u uᵀ + sv·v vᵀ
  const m: number[] = [];
  for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) m.push(sa * a[r] * a[c] + su * u[r] * u[c] + sv * v[r] * v[c]);
  return m;
}

export interface Style { halo?: boolean; squash?: number; flatAxis?: (id: string) => V3 | undefined }

/**
 * Positions → Placed. Outward direction is parent → node, and `ext` is how far the subtree reaches from
 * the node (for camera framing and label culling).
 */
export function finish(inp: LayoutInput, pos: Map<string, V3>, style: Style = {}): Map<string, Placed> {
  const kids = kidsFn(inp);
  const out = new Map<string, Placed>();
  const order = preorder(inp).filter((id) => pos.has(id));
  const dirOf = new Map<string, V3>();
  for (const id of order) {
    const n = inp.nodes[id];
    const p = pos.get(id)!;
    const par = n.parent_id ? pos.get(n.parent_id) : undefined;
    const off = par ? sub(p, par) : ([0, 0, 0] as V3);
    const dir: V3 = len(off) > 1e-6 ? norm(off) : (n.parent_id && dirOf.get(n.parent_id)) || [0, 1, 0];
    dirOf.set(id, dir);
    const b = ballOf(inp, id);
    out.set(id, {
      id, x: p[0], y: p[1], z: p[2], depth: n.depth, dir, ball: b, ext: b, spin: spinOf(id, n.depth, b),
      halo: style.halo,
      form: style.squash ? squashForm(id, b, style.squash, style.flatAxis?.(id)) : undefined,
    });
  }
  for (let i = order.length - 1; i >= 0; i--) {
    const p = out.get(order[i])!;
    const reach = style.halo ? p.ball * 1.3 : p.ball;
    let e = reach;
    for (const k of kids(p.id)) {
      const c = out.get(k);
      if (c) e = Math.max(e, Math.hypot(c.x - p.x, c.y - p.y, c.z - p.z) + c.ext);
    }
    p.ext = e;
  }
  return out;
}

export interface Body { p: V3; r: number; fixed?: boolean }

/**
 * Push overlapping spheres apart (a spatial hash on flat arrays, so each pass is about linear and allocates
 * nothing per pair). `project` can pull each moved point back onto a surface (the onion's shells).
 */
export function relax(bodies: Body[], iters = 40, pad = 0.2, project?: (i: number, p: V3) => V3) {
  const n = bodies.length;
  if (n < 2) return;
  const X = new Float64Array(n * 3);
  const R = new Float64Array(n);
  const W = new Float64Array(n); // share of each push this body takes (0 = fixed)
  let maxR = 0;
  bodies.forEach((b, i) => {
    X[i * 3] = b.p[0]; X[i * 3 + 1] = b.p[1]; X[i * 3 + 2] = b.p[2];
    R[i] = b.r;
    W[i] = b.fixed ? 0 : 1;
    maxR = Math.max(maxR, b.r);
  });
  const cell = Math.max(0.5, (maxR + pad) * 2);
  const grid = new Map<number, number[]>();
  const key = (x: number, y: number, z: number) => ((x * 73856093) ^ (y * 19349663) ^ (z * 83492791)) | 0;
  for (let it = 0; it < iters; it++) {
    grid.clear();
    for (let i = 0; i < n; i++) {
      const k = key(Math.floor(X[i * 3] / cell), Math.floor(X[i * 3 + 1] / cell), Math.floor(X[i * 3 + 2] / cell));
      const l = grid.get(k);
      if (l) l.push(i); else grid.set(k, [i]);
    }
    let moved = false;
    for (let i = 0; i < n; i++) {
      const cx = Math.floor(X[i * 3] / cell), cy = Math.floor(X[i * 3 + 1] / cell), cz = Math.floor(X[i * 3 + 2] / cell);
      for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) for (let dz = -1; dz <= 1; dz++) {
        const l = grid.get(key(cx + dx, cy + dy, cz + dz));
        if (!l) continue;
        for (const j of l) {
          if (j <= i) continue;
          let ex = X[j * 3] - X[i * 3], ey = X[j * 3 + 1] - X[i * 3 + 1], ez = X[j * 3 + 2] - X[i * 3 + 2];
          const need = R[i] + R[j] + pad;
          let d2 = ex * ex + ey * ey + ez * ez;
          if (d2 >= need * need) continue;
          const wi = W[i], wj = W[j];
          if (!wi && !wj) continue;
          if (d2 < 1e-12) { ex = hash01(String(i), j) - 0.5; ey = hash01(String(j), i) - 0.5; ez = 0.1; d2 = ex * ex + ey * ey + ez * ez; }
          const dist = Math.sqrt(d2);
          const push = (need - dist) / dist;
          const si = wi && wj ? 0.5 : wi ? 1 : 0, sj = wi && wj ? 0.5 : wj ? 1 : 0;
          X[i * 3] -= ex * push * si; X[i * 3 + 1] -= ey * push * si; X[i * 3 + 2] -= ez * push * si;
          X[j * 3] += ex * push * sj; X[j * 3 + 1] += ey * push * sj; X[j * 3 + 2] += ez * push * sj;
          moved = true;
        }
      }
    }
    if (project) {
      for (let i = 0; i < n; i++) {
        if (!W[i]) continue;
        const q = project(i, [X[i * 3], X[i * 3 + 1], X[i * 3 + 2]]);
        X[i * 3] = q[0]; X[i * 3 + 1] = q[1]; X[i * 3 + 2] = q[2];
      }
    }
    if (!moved) break;
  }
  bodies.forEach((b, i) => { b.p = [X[i * 3], X[i * 3 + 1], X[i * 3 + 2]]; });
}
