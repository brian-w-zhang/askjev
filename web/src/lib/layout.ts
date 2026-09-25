import type { Hemisphere, TreeNode } from "./types";

// Nebula layout (docs/07-ui.md): a 3D balloon tree. Each node's own questions form a ball of stars
// (radius ∝ ∛count); its children sit on a spherical cap facing away from its parent, spread by
// repulsion so their subtrees don't overlap. Deterministic: the same tree always lands in the same place.

export const BALL_K = 0.3; // ball radius per ∛question
const GAP = 1.1;
const PACK = 1.0; // cap area / area the child subtrees need
// Subtrees fill the forward cone of their bounding sphere, not the whole sphere, so neighbours may
// share some of that empty space.
const SHARE = 0.9;

type V3 = [number, number, number];

export interface Placed {
  id: string;
  x: number; y: number; z: number;
  depth: number;
  dir: V3; // outward direction (parent → node)
  ball: number; // radius of the node's own star ball
  ext: number; // radius of the sphere holding the whole subtree
  spin: number; // rad/s: the ball turns slowly around its node
}

function hash01(s: string, salt = 0): number {
  let h = 2166136261 ^ salt;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return ((h >>> 0) % 100000) / 100000;
}

const norm = (v: V3): V3 => {
  const l = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0] / l, v[1] / l, v[2] / l];
};
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a: V3, b: V3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

const capOf = (depth: number) => (depth === 0 ? Math.PI : depth === 1 ? 1.65 : 1.4);

export const ballRadius = (direct: number) => BALL_K * Math.cbrt(Math.max(1, direct));

/**
 * `direct` = number of stars attached directly to each node (from the star index);
 * nodes without an entry get the minimum ball.
 */
export function layout(
  nodes: Record<string, TreeNode>,
  children: Record<string, string[]>,
  direct: Map<string, number>,
  rootId = "root",
): Map<string, Placed> {
  const out = new Map<string, Placed>();
  if (!nodes[rootId]) return out;
  const kidsOf = (id: string) => (children[id] ?? []).filter((k) => nodes[k]);

  // Bottom-up: ball, cap distance D, and subtree extent.
  const ball = new Map<string, number>();
  const D = new Map<string, number>();
  const ext = new Map<string, number>();
  const size = (id: string): number => {
    const b = ballRadius(direct.get(id) ?? 0);
    ball.set(id, b);
    const kids = kidsOf(id);
    if (!kids.length) {
      ext.set(id, b);
      return b;
    }
    const es = kids.map(size);
    const maxE = Math.max(...es);
    const maxBall = Math.max(...kids.map((k) => ball.get(k)!));
    const depth = nodes[id].depth;
    const cap = capOf(depth);
    const need = Math.sqrt((PACK * es.reduce((s, e) => s + (e * SHARE) ** 2, 0)) / (2 * (1 - Math.cos(cap))));
    // the children's own balls must clear this node's ball; their subtrees grow outward
    let d = Math.max(need, b + GAP + maxBall);
    if (depth === 0) {
      // three lobes 120° apart: chord = d·√3 must clear each pair (lobes fan outward, so their spheres may overlap a bit)
      for (let i = 0; i < es.length; i++) for (let j = i + 1; j < es.length; j++) d = Math.max(d, ((es[i] + es[j]) * 0.65) / Math.sqrt(3));
    }
    D.set(id, d);
    const e = d + maxE;
    ext.set(id, e);
    return e;
  };
  size(rootId);

  // Top-down: directions on each node's cap.
  const place = (id: string, pos: V3, dir: V3) => {
    const n = nodes[id];
    const b = ball.get(id)!;
    out.set(id, {
      id, x: pos[0], y: pos[1], z: pos[2], depth: n.depth, dir, ball: b, ext: ext.get(id)!,
      spin: (0.025 + 0.05 * hash01(id, 7)) * (hash01(id, 3) < 0.5 ? -1 : 1) * (1 + 0.25 * n.depth) / Math.max(1, Math.sqrt(b)),
    });
    const kids = kidsOf(id);
    if (!kids.length) return;
    const d = D.get(id)!;
    const es = kids.map((k) => ext.get(k)!);
    let dirs: V3[];
    if (n.depth === 0) {
      // World, Self, Machine: a slightly tilted triangle so the nebula isn't flat from any side
      dirs = kids.map((_, i) => norm([Math.cos(-Math.PI / 2 + (i * 2 * Math.PI) / 3), 0.18 * (i - 1), Math.sin(-Math.PI / 2 + (i * 2 * Math.PI) / 3)]));
    } else {
      dirs = capDirections(id, dir, kids.length, capOf(n.depth), es, d);
    }
    kids.forEach((k, i) => place(k, [pos[0] + dirs[i][0] * d, pos[1] + dirs[i][1] * d, pos[2] + dirs[i][2] * d], dirs[i]));
  };
  place(rootId, [0, 0, 0], [0, 1, 0]);
  return out;
}

/** k directions within `cap` radians of `axis`: a Fibonacci spiral, then pairwise repulsion by subtree size. */
function capDirections(id: string, axis: V3, k: number, cap: number, es: number[], d: number): V3[] {
  const ref: V3 = Math.abs(axis[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
  const twist = hash01(id, 11) * Math.PI * 2;
  let u = norm(cross(axis, ref));
  let v = cross(axis, u);
  [u, v] = [
    [u[0] * Math.cos(twist) + v[0] * Math.sin(twist), u[1] * Math.cos(twist) + v[1] * Math.sin(twist), u[2] * Math.cos(twist) + v[2] * Math.sin(twist)],
    [v[0] * Math.cos(twist) - u[0] * Math.sin(twist), v[1] * Math.cos(twist) - u[1] * Math.sin(twist), v[2] * Math.cos(twist) - u[2] * Math.sin(twist)],
  ];
  const golden = Math.PI * (3 - Math.sqrt(5));
  const cosCap = Math.cos(cap);
  const dirs: V3[] = [];
  for (let i = 0; i < k; i++) {
    // one child: straight out; otherwise fill the cap evenly
    const c = k === 1 ? 1 : 1 - (1 - cosCap) * ((i + 0.5) / k);
    const s = Math.sqrt(Math.max(0, 1 - c * c));
    const ph = i * golden;
    dirs.push(norm([
      axis[0] * c + (u[0] * Math.cos(ph) + v[0] * Math.sin(ph)) * s,
      axis[1] * c + (u[1] * Math.cos(ph) + v[1] * Math.sin(ph)) * s,
      axis[2] * c + (u[2] * Math.cos(ph) + v[2] * Math.sin(ph)) * s,
    ]));
  }
  if (k < 2) return dirs;
  // required angular separation for each pair so the subtree spheres don't touch
  const req = (i: number, j: number) => 2 * Math.asin(Math.min(1, ((es[i] + es[j]) * SHARE) / (2 * d)));
  for (let it = 0; it < 60; it++) {
    let moved = false;
    for (let i = 0; i < k; i++) {
      for (let j = i + 1; j < k; j++) {
        const a = dirs[i], b = dirs[j];
        const ang = Math.acos(Math.max(-1, Math.min(1, dot(a, b))));
        const r = req(i, j);
        if (ang >= r) continue;
        moved = true;
        const push = (r - ang) * 0.5 + 1e-4;
        // tangent from a away from b, and from b away from a
        let ta = norm([a[0] - b[0], a[1] - b[1], a[2] - b[2]]);
        if (!isFinite(ta[0])) ta = u;
        dirs[i] = norm([a[0] + ta[0] * push, a[1] + ta[1] * push, a[2] + ta[2] * push]);
        dirs[j] = norm([b[0] - ta[0] * push, b[1] - ta[1] * push, b[2] - ta[2] * push]);
      }
    }
    // keep everyone on the forward side of the cap (a little slack past the cap edge)
    for (let i = 0; i < k; i++) {
      const c = dot(dirs[i], axis);
      const lim = Math.cos(Math.min(Math.PI * 0.62, cap * 1.25));
      if (c < lim) {
        const t = norm([dirs[i][0] - axis[0] * c, dirs[i][1] - axis[1] * c, dirs[i][2] - axis[2] * c]);
        const s = Math.sqrt(1 - lim * lim);
        dirs[i] = norm([axis[0] * lim + t[0] * s, axis[1] * lim + t[1] * s, axis[2] * lim + t[2] * s]);
      }
    }
    if (!moved) break;
  }
  return dirs;
}

/** Point on the curved filament parent → child: a quadratic curve that leaves the parent along its outward direction. */
export function edgePoint(p: Placed, c: Placed, t: number, out: V3 = [0, 0, 0]): V3 {
  let cx = (p.x + c.x) / 2, cy = (p.y + c.y) / 2, cz = (p.z + c.z) / 2; // root: straight spokes
  if (p.depth > 0) {
    const k = Math.hypot(c.x - p.x, c.y - p.y, c.z - p.z) * 0.42;
    cx = p.x + p.dir[0] * k;
    cy = p.y + p.dir[1] * k;
    cz = p.z + p.dir[2] * k;
  }
  const a = (1 - t) * (1 - t), b = 2 * (1 - t) * t, d = t * t;
  out[0] = a * p.x + b * cx + d * c.x;
  out[1] = a * p.y + b * cy + d * c.y;
  out[2] = a * p.z + b * cz + d * c.z;
  return out;
}

export const HEMI_COLOR: Record<Hemisphere, string> = {
  root: "#1E1E1E",
  world: "#4B5BD6",
  self: "#F386A1",
  machine: "#E8663D",
};
export const INK = "#1E1E1E";
export const PATH_A_COLOR = "#1E1E1E"; // embedding path: ink
export const PATH_B_COLOR = "#03AA5C"; // Jev's walk: Jev green
