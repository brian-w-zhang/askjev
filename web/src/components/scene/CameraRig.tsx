"use client";
import { useEffect, useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { Vector3, type PerspectiveCamera } from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { anim, headPosition, now, progress } from "@/lib/anim";
import { useStore } from "@/lib/store";
import { starData, starWorld } from "@/lib/stars";

const easeInOutCubic = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
// Preferred viewing direction: above the sky, tilted toward the viewer.
const UP_VIEW = new Vector3(0, 0.72, 0.69).normalize();

/** Fly the camera to look at `to` from `dist` away (eased), cancelled by any user drag. */
export function flyTo(to: [number, number, number], dist: number, dur = 1.1) {
  anim.follow = null;
  anim.flight = { to, dist, t0: now(), dur };
}

/** Distance that frames a node: its whole subtree for branches, its star ball for leaves. */
export function frameDist(id: string): number {
  const p = anim.placed.get(id);
  if (!p) return 60;
  if (p.depth === 0) return p.ext * 2.1;
  return Math.max(7, p.ext > p.ball + 0.01 ? p.ext * 2.0 : p.ball * 4.2);
}

/** The whole nebula: aim at the middle of its bounding box, back far enough to hold nearly every node. */
const smooth = (x: number) => x * x * (3 - 2 * x);

/** How far back the camera sits while following a walk past `id`: its subtree, a bit tighter than framing it. */
function followDist(id: string) {
  return Math.max(9, frameDist(id) * 0.75);
}

export function home(dur = 1.6) {
  const ps = [...anim.placed.values()];
  if (!ps.length) return;
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (const p of ps) {
    [p.x, p.y, p.z].forEach((v, i) => { lo[i] = Math.min(lo[i], v); hi[i] = Math.max(hi[i], v); });
  }
  const c: [number, number, number] = [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2];
  const d = ps.map((p) => Math.hypot(p.x - c[0], p.y - c[1], p.z - c[2])).sort((a, b) => a - b);
  const r = d[Math.floor(d.length * 0.95)];
  flyTo(c, (r * 1.2) / Math.tan((21 * Math.PI) / 180), dur);
}

export function CameraRig() {
  const controls = useThree((s) => s.controls) as unknown as OrbitControlsImpl | null;
  const tmpT = useMemo(() => new Vector3(), []);
  const tmpP = useMemo(() => new Vector3(), []);
  const dir = useMemo(() => new Vector3(), []);
  const star: [number, number, number] = useMemo(() => [0, 0, 0], []);
  const offset = useRef(0);

  useEffect(() => {
    if (!controls) return;
    const stop = () => {
      anim.follow = null;
      anim.flight = null;
      anim.trackStar = -1;
      anim.userMoved = now();
    };
    controls.addEventListener("start", stop);
    return () => controls.removeEventListener("start", stop);
  }, [controls]);

  useFrame(({ camera, size }, dt) => {
    // Keep the focus centered in the part of the sky the side panel leaves visible.
    const panelOpen = useStore.getState().panel.kind !== "none";
    const want = panelOpen && size.width > 800 ? 220 : 0;
    offset.current += (want - offset.current) * (1 - Math.exp(-dt * 6));
    const cam = camera as PerspectiveCamera;
    if (Math.abs(offset.current) > 0.5) cam.setViewOffset(size.width, size.height, offset.current, 0, size.width, size.height);
    else if (cam.view?.enabled) cam.clearViewOffset();

    if (!controls) return;
    const t = now();
    const f = anim.flight;
    if (f) {
      if (!f.from) f.from = { pos: camera.position.toArray() as [number, number, number], target: controls.target.toArray() as [number, number, number] };
      const x = Math.min(1, (t - f.t0) / f.dur);
      const e = easeInOutCubic(x);
      tmpT.fromArray(f.from.target).lerp(tmpP.fromArray(f.to), e);
      // keep the current viewing angle, blended toward the preferred tilt, at the new distance
      dir.fromArray(f.from.pos).sub(tmpP.fromArray(f.from.target)).normalize().lerp(UP_VIEW, 0.35 * e).normalize();
      const d0 = new Vector3().fromArray(f.from.pos).distanceTo(new Vector3().fromArray(f.from.target));
      const d = d0 + (f.dist - d0) * e;
      controls.target.copy(tmpT);
      camera.position.copy(tmpT).addScaledVector(dir, d);
      if (x >= 1) anim.flight = null;
      controls.update();
    } else if (anim.follow) {
      const l = anim[anim.follow];
      const h = headPosition(l, t);
      if (h) {
        const pr = Math.max(0, progress(l, t));
        const i = Math.min(Math.floor(pr), l.path.length - 1);
        const j = Math.min(i + 1, l.path.length - 1);
        const e = smooth(pr - i);
        // look a little ahead of the walker, toward the node it is heading for
        const next = anim.placed.get(l.path[j]);
        tmpT.set(h[0], h[1], h[2]);
        if (next) tmpT.lerp(tmpP.set(next.x, next.y, next.z), 0.22 * (1 - e));
        // distance glides between the framing of this level and the next (log space, so zooming feels even)
        const d = Math.exp(Math.log(followDist(l.path[i])) * (1 - e) + Math.log(followDist(l.path[j])) * e);
        const k = 1 - Math.exp(-dt * 2.6); // critically damped: no jumps between levels
        controls.target.lerp(tmpT, k);
        dir.copy(camera.position).sub(controls.target).normalize().lerp(UP_VIEW, 0.012).normalize();
        camera.position.lerp(tmpP.copy(controls.target).addScaledVector(dir, d), k);
        controls.update();
      }
    }

    // After landing on a question: keep its dot centered as its ball slowly turns.
    if (!f && !anim.follow && anim.trackStar >= 0) {
      const d = starData();
      const p = d ? anim.placed.get(d.nodeIds[d.node[anim.trackStar]]) : undefined;
      if (p) {
        const w = starWorld(anim.trackStar, p, t, star);
        tmpT.set(w[0], w[1], w[2]).sub(controls.target);
        controls.target.add(tmpT);
        camera.position.add(tmpT);
        controls.update();
      }
    }

    // Idle: the nebula turns slowly on its own after a while without input.
    controls.autoRotate = !anim.flight && !anim.follow && anim.trackStar < 0 && t - anim.userMoved > 12;
  });
  return null;
}
