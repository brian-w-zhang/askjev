import type { TreeNode } from "./types";
import { balloon } from "./layouts/balloon";
import { galaxy } from "./layouts/galaxy";
import { pack } from "./layouts/pack";
import { onion } from "./layouts/onion";
import { force, forceFinish, forceInput } from "./layouts/force";
import { useStore } from "./store";
import { semantic } from "./layouts/semantic";
import type { LayoutInput, Placed, V3 } from "./layouts/common";

// Nebula layouts (docs/07-ui.md, Layouts). Every layout places node centers and star-ball sizes; stars,
// edges, labels and the camera all read the same Placed map, so layouts can be swapped live to compare.
// Deterministic: the same tree always lands in the same place.

export type { Placed, V3 } from "./layouts/common";
export { ballRadius, BALL_K } from "./layouts/common";

export type LayoutKind = "force" | "balloon" | "galaxy" | "pack" | "onion" | "semantic";
export const DEFAULT_LAYOUT: LayoutKind = "force";
export const LAYOUT_KEY = "askjev.layout2"; // the layout someone picked (v2: the default changed to Web)

export const LAYOUTS: { id: LayoutKind; label: string; hint: string }[] = [
  { id: "force", label: "Web", hint: "Force-directed: springs along the tree, everything repels" },
  { id: "balloon", label: "Balloon", hint: "Children on a cap facing away from their parent" },
  { id: "galaxy", label: "Galaxy", hint: "Three spiral galaxies; each top-level topic is an arm" },
  { id: "pack", label: "Bubbles", hint: "Nested spheres: every topic holds its subtopics" },
  { id: "onion", label: "Onion", hint: "Depth is distance from the center; topics own a patch of sky" },
  { id: "semantic", label: "Meaning", hint: "Topics placed by what their questions ask, across branches" },
];

const cache = new Map<string, Map<string, Placed>>();

function treeKey(inp: LayoutInput): string {
  let h = 0, n = 0, total = 0;
  for (const [id, ks] of Object.entries(inp.children)) {
    n += ks.length;
    for (let i = 0; i < id.length; i++) h = (Math.imul(h, 31) + id.charCodeAt(i)) | 0;
  }
  for (const v of inp.direct.values()) total += v;
  return `${Object.keys(inp.nodes).length}:${n}:${h}:${total}:${inp.semantic ? 1 : 0}`;
}

/** Node placement for `kind`; null while that layout is still being computed (Web) or loaded (Meaning). */
export function layoutFor(
  kind: LayoutKind,
  nodes: Record<string, TreeNode>,
  children: Record<string, string[]>,
  direct: Map<string, number>,
  semanticCoords: Record<string, V3> | null = null,
  rootId = "root",
): Map<string, Placed> | null {
  if (!nodes[rootId]) return new Map();
  const inp: LayoutInput = { nodes, children, direct, rootId, semantic: kind === "semantic" ? semanticCoords : null };
  const key = kind + "|" + treeKey(inp);
  const hit = cache.get(key);
  if (hit) return hit;
  let out: Map<string, Placed> | null;
  switch (kind) {
    case "galaxy": out = galaxy(inp); break;
    case "pack": out = pack(inp); break;
    case "onion": out = onion(inp); break;
    case "force": out = forceAsync(key, inp, () => layoutFor("balloon", nodes, children, direct, null, rootId)!); break;
    case "semantic": out = semantic(inp); break;
    default: out = balloon(inp);
  }
  if (out) {
    if (cache.size > 16) cache.clear();
    cache.set(key, out);
  }
  return out;
}

const FORCE_KEY = "askjev.force:"; // settled Web layouts, per browser, keyed by the tree's shape
const pending = new Set<string>();

/**
 * The Web layout without blocking the page: the simulation runs in a worker (about 2-3 s) and the result is
 * kept in this browser, so later visits are instant. Null until it's ready; the Scene re-renders then.
 */
function forceAsync(key: string, inp: LayoutInput, startOf: () => Map<string, Placed>): Map<string, Placed> | null {
  try {
    const saved = localStorage.getItem(FORCE_KEY + key);
    const P = saved ? (JSON.parse(saved) as number[]) : null;
    const { ids, sim } = forceInput(inp); // saved positions need no start layout
    if (P && P.length === ids.length * 3) return forceFinish(inp, ids, sim, P);
  } catch {}
  if (pending.has(key)) return null;
  const start = startOf();
  if (typeof Worker === "undefined") return force(inp, start);
  const { ids, sim } = forceInput(inp, start);
  pending.add(key);
  const done = (layout: Map<string, Placed>) => {
    pending.delete(key);
    cache.set(key, layout);
    useStore.getState().set({ layoutTick: useStore.getState().layoutTick + 1 });
  };
  const worker = new Worker(new URL("./layouts/force.worker.ts", import.meta.url), { type: "module" });
  worker.onmessage = (e: MessageEvent<number[]>) => {
    worker.terminate();
    try {
      for (let i = localStorage.length - 1; i >= 0; i--) { const k = localStorage.key(i); if (k?.startsWith(FORCE_KEY)) localStorage.removeItem(k); }
      localStorage.setItem(FORCE_KEY + key, JSON.stringify(e.data.map((v) => Math.round(v * 100) / 100)));
    } catch {}
    done(forceFinish(inp, ids, sim, e.data));
  };
  worker.onerror = () => {
    worker.terminate();
    done(force(inp, start)); // no worker after all: do it here
  };
  worker.postMessage(sim);
  return null;
}

/**
 * A star's offset from its node: its unit-ball position (from scripts/star_layout.py) with the layout's
 * star profile and ball shape applied. The star shader and picking both use this.
 */
export function starLocal(ux: number, uy: number, uz: number, p: Placed, out: V3): V3 {
  let x = ux, y = uy, z = uz;
  if (p.halo) {
    // the evenly filled ball becomes a dense core with a soft halo (about 90% of stars inside the radius)
    const r = Math.hypot(x, y, z);
    if (r > 1e-6) {
      const u = Math.min(0.9999, Math.max(1e-6, r * r * r));
      let f = 1 / Math.sqrt(u ** (-2 / 3) - 1) / 3.71;
      if (f > 1) f = 1 + 0.35 * Math.tanh((f - 1) / 0.35);
      const k = (0.35 * r + 0.65 * f) / r;
      x *= k; y *= k; z *= k;
    }
  }
  const m = p.form;
  if (m) {
    out[0] = m[0] * x + m[1] * y + m[2] * z;
    out[1] = m[3] * x + m[4] * y + m[5] * z;
    out[2] = m[6] * x + m[7] * y + m[8] * z;
  } else {
    out[0] = x * p.ball; out[1] = y * p.ball; out[2] = z * p.ball;
  }
  return out;
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
