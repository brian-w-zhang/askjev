import type { Hemisphere, TreeNode } from "./types";

// Radial "constellation" layout: root at the origin, hemispheres as arms, depth = radius,
// each child's angular span ∝ a log-scaled subtree size. Layout of a node depends only on its
// ancestors' siblings, so lazily loaded rings never move what is already on screen.
export const RADII = [0, 6, 13, 20.5, 27, 32.5, 37, 41, 44.5];
const TAU = Math.PI * 2;

export interface Placed { id: string; x: number; y: number; z: number; r: number; a: number; a0: number; a1: number; depth: number }

export function weight(n: TreeNode): number {
  return 1 + Math.log2(1 + n.n_desc) + 0.6 * Math.log2(1 + n.n_questions);
}

function hash01(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return ((h >>> 0) % 10000) / 10000;
}

export function heightAt(depth: number, id: string): number {
  // a shallow bowl, plus a small deterministic lift per node so the sky reads as 3D
  return -0.9 * depth + (depth > 0 ? (hash01(id) - 0.5) * 1.4 : 0);
}

export function layout(nodes: Record<string, TreeNode>, children: Record<string, string[]>, rootId = "root"): Map<string, Placed> {
  const out = new Map<string, Placed>();
  const root = nodes[rootId];
  if (!root) return out;
  const place = (id: string, a0: number, a1: number) => {
    const n = nodes[id];
    const a = (a0 + a1) / 2;
    const r = RADII[Math.min(n.depth, RADII.length - 1)];
    out.set(id, { id, r, a, a0, a1, depth: n.depth, x: r * Math.cos(a), z: r * Math.sin(a), y: heightAt(n.depth, id) });
    const kids = (children[id] ?? []).filter((k) => nodes[k]);
    if (!kids.length) return;
    const total = kids.reduce((s, k) => s + weight(nodes[k]), 0);
    // Keep a gap between sibling fans so arms read as separate; the top split uses the full circle.
    const span = a1 - a0;
    const pad = n.depth === 0 ? 0 : span * 0.04;
    let cur = a0 + pad;
    const usable = span - 2 * pad;
    for (const k of kids) {
      const w = (weight(nodes[k]) / total) * usable;
      place(k, cur, cur + w);
      cur += w;
    }
  };
  // Start the World arm at the top-left so the three arms sit evenly around the center.
  place(rootId, -Math.PI / 2 - TAU / 6, -Math.PI / 2 - TAU / 6 + TAU);
  return out;
}

/** Point on the curved edge parent → child: polar interpolation with an eased angle (a spiral arc). */
export function edgePoint(p: Placed, c: Placed, t: number, out: [number, number, number] = [0, 0, 0]): [number, number, number] {
  const r = p.r + (c.r - p.r) * t;
  const e = t * t * (3 - 2 * t);
  const a = p.depth === 0 ? c.a : p.a + (c.a - p.a) * e;
  out[0] = r * Math.cos(a);
  out[2] = r * Math.sin(a);
  out[1] = p.y + (c.y - p.y) * t;
  return out;
}

export const HEMI_COLOR: Record<Hemisphere, string> = {
  root: "#EDEBFA",
  world: "#62C6E8",
  self: "#F3A861",
  machine: "#A993FF",
};
export const PATH_A_COLOR = "#E9F6FF"; // embedding path: cold white
export const PATH_B_COLOR = "#FFD27A"; // Jev's walk: gold
