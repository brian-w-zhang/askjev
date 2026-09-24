"use client";
import { useEffect, useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { Vector3, type PerspectiveCamera } from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { anim, headPosition, now, progress } from "@/lib/anim";
import { loadSubtree, useStore } from "@/lib/store";

const easeInOutCubic = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
// Preferred viewing direction: above the sky, tilted toward the viewer.
const UP_VIEW = new Vector3(0, 0.72, 0.69).normalize();

/** Fly the camera to look at `to` from `dist` away (eased), cancelled by any user drag. */
export function flyTo(to: [number, number, number], dist: number, dur = 1.1) {
  anim.follow = null;
  anim.flight = { to, dist, t0: now(), dur };
}

export function CameraRig() {
  const controls = useThree((s) => s.controls) as unknown as OrbitControlsImpl | null;
  const tmpT = useMemo(() => new Vector3(), []);
  const tmpP = useMemo(() => new Vector3(), []);
  const dir = useMemo(() => new Vector3(), []);
  const lastLoad = useRef(0);
  const offset = useRef(0);

  useEffect(() => {
    if (!controls) return;
    const stop = () => {
      anim.follow = null;
      anim.flight = null;
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
        const pr = progress(l, t);
        const k = 1 - Math.exp(-dt * 3.5);
        controls.target.lerp(tmpT.set(h[0], h[1], h[2]), k);
        const want = Math.max(18, 62 - pr * 11);
        dir.copy(camera.position).sub(controls.target).normalize().lerp(UP_VIEW, 0.02).normalize();
        camera.position.lerp(tmpP.copy(controls.target).addScaledVector(dir, want), k);
        controls.update();
      }
    }

    // Lazy rings: when zoomed in, load two more levels under nodes near the view target.
    if (t - lastLoad.current > 0.4) {
      lastLoad.current = t;
      const dist = camera.position.distanceTo(controls.target);
      if (dist < 48) {
        const s = useStore.getState();
        let n = 0;
        for (const p of anim.placed.values()) {
          const node = s.nodes[p.id];
          if (!node || node.n_children === 0 || s.children[p.id]) continue;
          const dx = p.x - controls.target.x;
          const dz = p.z - controls.target.z;
          if (Math.hypot(dx, dz) < dist * 0.55) {
            loadSubtree(p.id, 2);
            if (++n >= 4) break;
          }
        }
      }
    }
  });
  return null;
}
