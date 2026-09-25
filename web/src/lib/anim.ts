// Mutable animation state shared by the 3D scene (read every frame, never through React state).
export interface Light { path: string[]; t0: number; per: number; active: boolean }

export const anim = {
  A: { path: [], t0: 0, per: 0.4, active: false } as Light,
  B: { path: [], t0: 0, per: 0.4, active: false } as Light,
  follow: null as null | "A" | "B",
  flight: null as null | { to: [number, number, number]; dist: number; t0: number; dur: number; from?: { pos: [number, number, number]; target: [number, number, number] } },
  fork: -1, // index in pathB where it leaves pathA (-1: none)
  userMoved: 0,
  // the journey in progress (docs/07-ui.md): who is walking, and Jev's confidence at each node it chose
  journey: { phase: "idle", probs: new Map() } as { phase: "idle" | "thinking" | "jev" | "hop" | "landed"; probs: Map<string, number> },
  trackStar: -1, // camera keeps this question dot centered as it drifts (-1: off; any drag stops it)
  placed: new Map() as Map<string, import("./layout").Placed>,
  labelRects: [] as import("./uirects").Rect[], // node labels on screen (question labels avoid them)
};

export const now = () => performance.now() / 1000;
const easeInOut = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

/** Light progress in depth units: 0 = root, k = path[k]. Eased within each level. -1 when idle. */
export function progress(l: Light, t = now()): number {
  if (!l.active || l.path.length < 1) return -1;
  const total = l.path.length - 1;
  const el = Math.max(0, t - l.t0) / l.per;
  if (el >= total) return total;
  const i = Math.floor(el);
  return i + easeInOut(el - i);
}

export function startLight(which: "A" | "B", path: string[], perLevel = 0.4) {
  const l = anim[which];
  l.path = path;
  l.t0 = now() + 0.05;
  l.per = perLevel;
  l.active = path.length > 0;
}

export function lightDone(which: "A" | "B"): boolean {
  const l = anim[which];
  return !l.active || progress(l) >= l.path.length - 1;
}

/** Duration of a light's run in ms (for UI timing). */
export const lightMs = (n: number, per = 0.4) => Math.max(0, n - 1) * per * 1000;

import { edgePoint } from "./layout";
const tmp: [number, number, number] = [0, 0, 0];
/** World position of a light's head, or null when idle / not laid out. */
export function headPosition(l: Light, t = now()): [number, number, number] | null {
  const pr = progress(l, t);
  if (pr < 0) return null;
  const i = Math.min(Math.floor(pr), l.path.length - 1);
  const f = pr - i;
  const p = anim.placed.get(l.path[i]);
  if (!p) return null;
  if (f <= 0 || i >= l.path.length - 1) return [p.x, p.y, p.z];
  const c = anim.placed.get(l.path[i + 1]);
  if (!c) return [p.x, p.y, p.z];
  edgePoint(p, c, f, tmp);
  return [tmp[0], tmp[1], tmp[2]];
}
