"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { Vector3, type PerspectiveCamera } from "three";
import { useStore } from "@/lib/store";
import { anim, now } from "@/lib/anim";
import { starAttention } from "@/lib/color";
import { loadTexts, metric, starData, starText, starWorld } from "@/lib/stars";
import { landOnStar, openQuestion } from "@/lib/actions";
import { overlaps, uiRects } from "@/lib/uirects";
import { assign, cards, moveCard, place, publish, STAR_LABELS, starSlots } from "@/lib/overlay";
import type { Placed } from "@/lib/layout";
import type { Indicator } from "@/lib/types";

// Question text on approach (docs/07-ui.md): close to a topic, its texts load and the stars nearest
// the middle of the screen (and the ones worth a look) get labels, never overlapping, at most POOL.
const POOL = STAR_LABELS;
const TEXT_PX = 90; // a node's ball must cover this radius on screen before its texts load
const PICK_PX = 12; // ...and this much before its stars can be hovered one by one
const LABEL_PX = 16; // VT323 at 16px
const CHARS_PER_LINE = 36;
const MAX_CHARS = 90;

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
  const slots = starSlots;
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
          const cw = Math.min(text.length, CHARS_PER_LINE) * LABEL_PX * 0.42 + 10;
          const lines = Math.min(3, Math.ceil(Math.min(text.length, MAX_CHARS) / CHARS_PER_LINE));
          cands.push({ i, pri: -center * 2 - dist * 0.02 + a * 1.2, x, y, w: cw, h: lines * LABEL_PX + 4 });
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
      assign(slots, [...chosen]);
    }
    const k = 1 - Math.exp(-dt * 7);
    // text and class go to React (only renders when they change); position and fade go straight to the ref
    publish("stars", slots.map((sl) => {
      if (sl.key === null) return { text: "", cls: "" };
      const a = starAttention(starMetric(s.indicator, sl.key), s.indicator) ?? 0;
      return { text: trim(starText(sl.key)?.label ?? ""), cls: "q" + (a > 0.6 ? " hot" : "") };
    }));
    for (const sl of slots) {
      if (sl.key === null) continue;
      const p = anim.placed.get(d.nodeIds[d.node[sl.key]]);
      if (!p) { place(sl, null, 0, k); continue; }
      starWorld(sl.key, p, t, w);
      v.set(w[0], w[1], w[2]).project(cam);
      if (v.z > 1) { place(sl, null, 0, k); continue; }
      place(sl, ((v.x + 1) / 2) * size.width, ((1 - v.y) / 2) * size.height - 7, k);
    }
  });

  return <StarPicker />;
}

/** Hover a star to read it; click to open its question card. */
function StarPicker() {
  const { gl, camera, size } = useThree();
  const mouse = useRef<{ x: number; y: number; dirty: boolean; down: [number, number] | null }>({ x: -1, y: -1, dirty: false, down: null });
  const v = useMemo(() => new Vector3(), []);
  const w: [number, number, number] = useMemo(() => [0, 0, 0], []);
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
      loadTexts(nodeId).then(async () => {
        const q = starText(i);
        if (!q) return;
        s.set({ selected: nodeId });
        await landOnStar(i, 1.0);
        openQuestion(q.id);
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
    // the hover card (rendered by <SkyOverlay>) follows the star
    const p = d && s.hoverStar >= 0 ? anim.placed.get(d.nodeIds[d.node[s.hoverStar]]) : undefined;
    if (!p) return moveCard(cards.star, null, 0);
    starWorld(s.hoverStar, p, t, w);
    v.set(w[0], w[1], w[2]).project(camera);
    moveCard(cards.star, v.z > 1 ? null : ((v.x + 1) / 2) * size.width, ((1 - v.y) / 2) * size.height);
  });

  return null;
}
