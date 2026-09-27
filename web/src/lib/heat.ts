// Live search heat (docs/07-ui.md, Search): as you type, the current top 20 light up on the map. Each result
// warms its question dot and every branch on its path to the root, so branches shared by many results glow
// brightest, and the deepest topic holding most of the heat is named. Mutable state read every frame by the
// scene (like `anim`), eased so a new result set drifts in rather than blinking.
import type { SearchHit } from "./types";

export const HOT_SLOTS = 24; // question dots the star shader can light at once (top 20 + ones fading out)

interface Slot { star: number; k: number; to: number }

export const heat = {
  node: new Map<string, number>(), // node id -> current glow 0..1
  target: new Map<string, number>(),
  slots: Array.from({ length: HOT_SLOTS }, (): Slot => ({ star: -1, k: 0, to: 0 })),
  jev: { star: -1, k: 0, to: 0 } as Slot, // Jev's pick after the pause, in green
  focus: null as string | null, // the topic most of the results sit under
  level: 0, // 0..1: how much a live search owns the map (everything outside the heat fades by this much)
  soft: false, // a panel is open: the search stays as a lens, but the rest of the map fades less
  moving: false, // something is still easing
  version: 0, // bumps on every frame the values change (the scene rewrites its buffers only then)
  top: [] as string[], // result ids behind the current target, for hysteresis
};

const TOP = 10;

/**
 * Point the heat at a new result set. Near-identical sets (same #1, 7+ of the top 10 shared) keep the
 * current target, so the map holds still while the list reshuffles its tail.
 */
export function heatFrom(hits: SearchHit[]) {
  const ids = hits.slice(0, TOP).map((h) => h.id);
  const shared = ids.filter((id) => heat.top.includes(id)).length;
  if (ids.length && ids[0] === heat.top[0] && shared >= Math.min(7, ids.length)) return;
  heat.top = ids;
  const topSim = hits[0]?.sim || 1;
  const mass = new Map<string, number>();
  let total = 0;
  const depthOf = new Map<string, number>();
  hits.forEach((h, r) => {
    // closer and higher results weigh more; the 20th still leaves a faint trace
    const w = Math.pow(Math.max(0, h.sim / topSim), 3) / (1 + 0.15 * r);
    total += w;
    h.path.forEach((p, d) => {
      if (d === 0) return; // the root is on every path
      mass.set(p.id, (mass.get(p.id) ?? 0) + w);
      depthOf.set(p.id, d);
    });
  });
  const peak = Math.max(1e-9, ...[...mass.entries()].filter(([id]) => depthOf.get(id)! > 1).map(([, m]) => m));
  heat.target = new Map([...mass].map(([id, m]) => [id, Math.min(1, Math.sqrt(m / peak))]));
  // the category: the deepest topic that still holds over half of all the weight
  let focus: string | null = null;
  for (const [id, m] of mass) {
    if (m / total < 0.5) continue;
    if (!focus || depthOf.get(id)! > depthOf.get(focus)!) focus = id;
  }
  heat.focus = focus;
  const want = hits.slice(0, HOT_SLOTS).filter((h) => (h.star ?? -1) >= 0);
  const stars = new Set(want.map((h) => h.star!));
  for (const s of heat.slots) if (!stars.has(s.star)) s.to = 0;
  want.forEach((h, r) => {
    const level = 1 - 0.5 * (r / Math.max(1, want.length - 1));
    const have = heat.slots.find((s) => s.star === h.star);
    if (have) { have.to = level; return; }
    const free = heat.slots.reduce((a, b) => (b.k + b.to < a.k + a.to ? b : a));
    Object.assign(free, { star: h.star!, k: 0, to: level });
  });
  heat.moving = true;
}

/** Light Jev's pick (the #1 after its reorder) in green; -1 clears it. */
export function heatJev(star: number) {
  if (star === heat.jev.star) { heat.jev.to = star >= 0 ? 1 : 0; heat.moving = true; return; }
  heat.jev = { star, k: 0, to: star >= 0 ? 1 : 0 };
  heat.moving = true;
}

export function clearHeat() {
  heat.top = [];
  heat.target = new Map();
  heat.focus = null;
  for (const s of heat.slots) s.to = 0;
  heat.jev.to = 0;
  heat.moving = true;
}

/** Ease everything toward its target (~300 ms). Called once per frame, before the scene reads `heat`. */
export function stepHeat(dt: number) {
  if (!heat.moving) return;
  const k = 1 - Math.exp(-dt * 7);
  let moving = false;
  const ease = (from: number, to: number) => {
    const v = from + (to - from) * k;
    if (Math.abs(to - v) > 0.004) { moving = true; return v; }
    return to;
  };
  for (const id of new Set([...heat.node.keys(), ...heat.target.keys()])) {
    const v = ease(heat.node.get(id) ?? 0, heat.target.get(id) ?? 0);
    if (v > 0) heat.node.set(id, v);
    else heat.node.delete(id);
  }
  for (const s of heat.slots) {
    s.k = ease(s.k, s.to);
    if (s.k === 0 && s.to === 0) s.star = -1;
  }
  heat.jev.k = ease(heat.jev.k, heat.jev.to);
  heat.level = ease(heat.level, heat.target.size ? (heat.soft ? 0.45 : 1) : 0);
  heat.moving = moving;
  heat.version++;
}
