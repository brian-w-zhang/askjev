"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { Billboard, Html, Text } from "@react-three/drei";
import { Vector3, type Group, type Mesh, type PerspectiveCamera } from "three";
import { useStore } from "@/lib/store";
import { anim, now } from "@/lib/anim";
import { starAttention } from "@/lib/color";
import { loadTexts, metric, starData, starText, starWorld } from "@/lib/stars";
import { openQuestion } from "@/lib/actions";
import { flyTo } from "./CameraRig";
import { overlaps, uiRects } from "@/lib/uirects";
import type { Placed } from "@/lib/layout";
import type { Indicator } from "@/lib/types";

// Question text on approach (docs/07-ui.md): close to a topic, its texts load and the stars nearest
// the middle of the screen (and the ones worth a look) get labels, never overlapping, at most POOL.
const FONT = "/fonts/schibsted-grotesk-latin-500-normal.woff";
const POOL = 24;
const TEXT_PX = 90; // a node's ball must cover this radius on screen before its texts load
const PICK_PX = 12; // ...and this much before its stars can be hovered one by one
const LABEL_PX = 11.5;
const MAX_CHARS = 90;

type TroikaText = Mesh & { fillOpacity: number; outlineOpacity: number; text: string; sync: () => void };

const trim = (s: string) => (s.length > MAX_CHARS ? s.slice(0, MAX_CHARS - 1).trimEnd() + "…" : s);

function starMetric(ind: Indicator, i: number): number | null {
  const d = starData()!;
  switch (ind) {
    case "stability": return metric(d.stability[i]);
    case "human_gap": return metric(d.humanGap[i]);
    case "frame_gap": return metric(d.frameGap[i]);
    case "placement_conf": return metric(d.placement[i]);
    default: return null;
  }
}

/** Nodes whose star ball covers at least `minPx` on screen, biggest first. */
function nodesOnScreen(cam: PerspectiveCamera, w: number, h: number, minPx: number, v: Vector3) {
  const d = starData();
  if (!d) return [];
  const tanHalf = Math.tan(((cam.fov ?? 45) * Math.PI) / 360);
  const out: { p: Placed; px: number; sx: number; sy: number }[] = [];
  for (const id of d.nodeIds) {
    const p = anim.placed.get(id);
    if (!p) continue;
    v.set(p.x, p.y, p.z);
    const dist = cam.position.distanceTo(v);
    const px = (p.ball * h) / (2 * Math.max(0.01, dist - p.ball * 0.5) * tanHalf);
    if (px < minPx) continue;
    v.project(cam);
    const m = 1 + (2 * px) / h;
    if (v.z > 1 || Math.abs(v.x) > m || Math.abs(v.y) > m) continue;
    out.push({ p, px, sx: ((v.x + 1) / 2) * w, sy: ((1 - v.y) / 2) * h });
  }
  return out.sort((a, b) => b.px - a.px);
}

export function StarText() {
  const ready = useStore((s) => s.starsReady);
  const [, bump] = useState(0);
  // label slots: fixed objects mutated every frame (never through React state)
  const [slots] = useState<{ g: Group | null; t: TroikaText | null; star: number; o: number; want: boolean }[]>(() =>
    Array.from({ length: POOL }, () => ({ g: null, t: null, star: -1, o: 0, want: false })),
  );
  const frame = useRef(0);
  const v = useMemo(() => new Vector3(), []);
  const w: [number, number, number] = useMemo(() => [0, 0, 0], []);

  useFrame(({ camera, size, gl }, dt) => {
    const d = starData();
    if (!ready || !d) return;
    const cam = camera as PerspectiveCamera;
    const t = now();
    const s = useStore.getState();
    if (frame.current++ % 8 === 0) {
      const near = nodesOnScreen(cam, size.width, size.height, TEXT_PX, v).slice(0, 5);
      for (const { p } of near) loadTexts(p.id).then(() => bump((x) => x + 1));
      // candidates: stars with loaded text, projected
      const cands: { i: number; pri: number; x: number; y: number; w: number; h: number }[] = [];
      for (const { p } of near) {
        const off = d.offsets.get(p.id);
        if (!off || !starText(off[0])) continue;
        for (let i = off[0]; i < off[0] + off[1]; i++) {
          starWorld(i, p, t, w);
          v.set(w[0], w[1], w[2]);
          const dist = cam.position.distanceTo(v);
          v.project(cam);
          if (v.z > 1 || Math.abs(v.x) > 0.8 || Math.abs(v.y) > 0.8 || i === s.hoverStar) continue;
          const x = ((v.x + 1) / 2) * size.width;
          const y = ((1 - v.y) / 2) * size.height;
          const center = Math.hypot(v.x, v.y);
          const a = starAttention(starMetric(s.indicator, i), s.indicator) ?? 0;
          const text = starText(i)!.label;
          const cw = Math.min(text.length, 34) * LABEL_PX * 0.52;
          const lines = Math.min(3, Math.ceil(Math.min(text.length, MAX_CHARS) / 34));
          cands.push({ i, pri: -center * 2 - dist * 0.02 + a * 1.2, x, y, w: cw, h: lines * LABEL_PX * 1.25 });
        }
      }
      cands.sort((a, b) => b.pri - a.pri);
      const rects = [...uiRects(gl.domElement), ...anim.labelRects];
      const chosen = new Set<number>();
      for (const c of cands) {
        if (chosen.size >= POOL) break;
        const r = { x0: c.x - c.w / 2 - 6, x1: c.x + c.w / 2 + 6, y0: c.y - c.h - 8, y1: c.y + 4 };
        if (overlaps(r, rects)) continue;
        rects.push(r);
        chosen.add(c.i);
      }
      // keep stars that stay chosen in their slot; hand free slots to new ones
      const pool = slots;
      for (const sl of pool) sl.want = sl.star >= 0 && chosen.has(sl.star);
      for (const sl of pool) if (sl.want) chosen.delete(sl.star);
      const fresh = [...chosen];
      for (const sl of pool) {
        if (sl.want || sl.o > 0.05 || !fresh.length) continue;
        sl.star = fresh.pop()!;
        sl.want = true;
        if (sl.t) {
          sl.t.text = trim(starText(sl.star)?.label ?? "");
          sl.t.sync();
        }
      }
    }
    const k = 1 - Math.exp(-dt * 7);
    const tanHalf = Math.tan(((cam.fov ?? 45) * Math.PI) / 360);
    for (const sl of slots) {
      if (!sl.g || !sl.t) continue;
      sl.o += ((sl.want ? 1 : 0) - sl.o) * k;
      sl.g.visible = sl.o > 0.02 && sl.star >= 0;
      if (!sl.g.visible) continue;
      const p = anim.placed.get(d.nodeIds[d.node[sl.star]]);
      if (!p) continue;
      starWorld(sl.star, p, t, w);
      sl.g.position.set(w[0], w[1], w[2]);
      const dist = cam.position.distanceTo(sl.g.position);
      const ppu = size.height / (2 * dist * tanHalf);
      sl.g.scale.setScalar(LABEL_PX / ppu); // constant on-screen size
      sl.t.fillOpacity = sl.o * 0.92;
      sl.t.outlineOpacity = sl.o * 0.7;
    }
  });

  return (
    <group>
      {slots.map((sl, i) => (
        <Billboard key={i} ref={(g) => { sl.g = g; }} visible={false}>
          <Text
            ref={(t) => { sl.t = t as unknown as TroikaText; }}
            font={FONT}
            fontSize={1}
            position={[0, 0.9, 0]}
            color="#E6E8F7"
            anchorX="center"
            anchorY="bottom"
            maxWidth={20}
            textAlign="center"
            lineHeight={1.15}
            outlineWidth={0.14}
            outlineColor="#050811"
            fillOpacity={0}
            outlineOpacity={0}
            renderOrder={11}
            material-depthTest={false}
          >
            {" "}
          </Text>
        </Billboard>
      ))}
      <StarPicker />
    </group>
  );
}

/** Hover a star to read it; click to open its question card. */
function StarPicker() {
  const { gl, camera, size } = useThree();
  const hoverStar = useStore((s) => s.hoverStar);
  const [, loaded] = useState(0);
  const mouse = useRef<{ x: number; y: number; dirty: boolean; down: [number, number] | null }>({ x: -1, y: -1, dirty: false, down: null });
  const v = useMemo(() => new Vector3(), []);
  const w: [number, number, number] = useMemo(() => [0, 0, 0], []);
  const marker = useRef<Group>(null);

  useEffect(() => {
    const el = gl.domElement;
    const move = (e: PointerEvent) => {
      const r = el.getBoundingClientRect();
      mouse.current.x = e.clientX - r.left;
      mouse.current.y = e.clientY - r.top;
      mouse.current.dirty = true;
    };
    const leave = () => useStore.getState().set({ hoverStar: -1 });
    const down = (e: PointerEvent) => (mouse.current.down = [e.clientX, e.clientY]);
    const up = (e: PointerEvent) => {
      const dn = mouse.current.down;
      mouse.current.down = null;
      if (!dn || Math.hypot(e.clientX - dn[0], e.clientY - dn[1]) > 5) return; // a drag, not a click
      const s = useStore.getState();
      const d = starData();
      if (s.hoverStar < 0 || s.hovered || !d) return;
      const i = s.hoverStar;
      const nodeId = d.nodeIds[d.node[i]];
      loadTexts(nodeId).then(() => {
        const q = starText(i);
        if (!q) return;
        s.set({ selected: nodeId });
        openQuestion(q.id);
        const p = anim.placed.get(nodeId);
        if (p) {
          starWorld(i, p, now() + 1.1, w);
          flyTo([w[0], w[1], w[2]], Math.max(2.5, p.ball * 0.9), 1.1);
        }
      });
    };
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerleave", leave);
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointerup", up);
    return () => {
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerleave", leave);
      el.removeEventListener("pointerdown", down);
      el.removeEventListener("pointerup", up);
    };
  }, [gl, w]);

  // hover text comes from the text cache; this only makes sure the node's texts are loading
  useEffect(() => {
    const d = starData();
    if (hoverStar < 0 || !d || starText(hoverStar)) return;
    let live = true;
    loadTexts(d.nodeIds[d.node[hoverStar]]).then(() => live && loaded((x) => x + 1));
    return () => { live = false; };
  }, [hoverStar]);
  const text = hoverStar >= 0 ? starText(hoverStar) : undefined;

  useFrame(() => {
    const d = starData();
    const t = now();
    const s = useStore.getState();
    const m = mouse.current;
    if (d && m.dirty && !m.down) {
      m.dirty = false;
      let best = -1;
      let bestD = PICK_PX;
      if (!s.hovered) {
        for (const { p, px, sx, sy } of nodesOnScreen(camera as PerspectiveCamera, size.width, size.height, PICK_PX, v)) {
          if (Math.hypot(sx - m.x, sy - m.y) > px * 1.15 + PICK_PX) continue; // pointer isn't over this ball
          const off = d.offsets.get(p.id)!;
          for (let i = off[0]; i < off[0] + off[1]; i++) {
            starWorld(i, p, t, w);
            v.set(w[0], w[1], w[2]).project(camera);
            if (v.z > 1) continue;
            const dx = ((v.x + 1) / 2) * size.width - m.x;
            const dy = ((1 - v.y) / 2) * size.height - m.y;
            const dd = Math.hypot(dx, dy);
            if (dd < bestD) { bestD = dd; best = i; }
          }
        }
      }
      if (best !== s.hoverStar) s.set({ hoverStar: best });
      document.body.style.cursor = best >= 0 || s.hovered ? "pointer" : "";
    }
    const g = marker.current;
    if (!g) return;
    g.visible = !!d && s.hoverStar >= 0;
    if (!g.visible || !d) return;
    const p = anim.placed.get(d.nodeIds[d.node[s.hoverStar]]);
    if (!p) return;
    starWorld(s.hoverStar, p, t, w);
    g.position.set(w[0], w[1], w[2]);
  });

  return (
    <group ref={marker} visible={false}>
      <Html style={{ pointerEvents: "none" }} zIndexRange={[20, 0]}>
        {text ? (
          <div className="hovercard star-card">
            {text.text}
            {text.label !== text.text && <div className="hovercard-meta">{text.label}</div>}
          </div>
        ) : null}
      </Html>
    </group>
  );
}
