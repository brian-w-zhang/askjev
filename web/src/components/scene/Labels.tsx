"use client";
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Vector3, type PerspectiveCamera } from "three";
import { useStore } from "@/lib/store";
import { anim, introDone, now } from "@/lib/anim";
import type { Placed } from "@/lib/layout";
import { overlaps, uiRects, type Rect } from "@/lib/uirects";
import { assign, cards, moveCard, NODE_LABELS, nodeSlots, place, publish } from "@/lib/overlay";

// Node labels (docs/07-ui.md): a label shows once its subtree (or star ball) covers SHOW_PX on screen;
// candidates are placed greedily by priority, never overlapping each other or the UI, at most BUDGET.
// Hemispheres read as big grotesk type, branches as black pixel chips, deep topics as grey chips.
const SHOW_PX = [0, 0, 0, 55, 70, 80];
const FONT_PX = [0, 34, 20, 18, 17, 17];
const CHAR_W = [0, 0.5, 0.42, 0.42, 0.42, 0.42]; // average glyph width / font size (Inter Tight, VT323)
const BUDGET = NODE_LABELS;

const cls = (depth: number) => (depth <= 1 ? "d1" : depth === 2 ? "d2" : depth === 3 ? "d3" : "d4");

export function Labels({ placed }: { placed: Map<string, Placed> }) {
  const slots = nodeSlots;
  const frame = useRef(0);
  const v = useMemo(() => new Vector3(), []);

  useFrame(({ camera, size, gl }, dt) => {
    const s = useStore.getState();
    const cam = camera as PerspectiveCamera;
    const tanHalf = Math.tan(((cam.fov ?? 45) * Math.PI) / 360);
    const screen = (p: Placed) => {
      v.set(p.x, p.y, p.z);
      const d = cam.position.distanceTo(v);
      v.project(cam);
      if (v.z > 1) return null;
      const ppu = size.height / (2 * d * tanHalf);
      return { x: ((v.x + 1) / 2) * size.width, y: ((1 - v.y) / 2) * size.height, ppu };
    };
    const lift = (p: Placed, ppu: number) => Math.max(p.ball * ppu, 7) + 5; // sit just above the ball

    if (frame.current++ % 4 === 0) {
      const onPath = new Set([...anim.A.path, ...anim.B.path]);
      const sel = s.selected;
      const kids = new Set(sel ? s.children[sel] ?? [] : []);
      const cands: { id: string; pri: number; r: Rect }[] = [];
      for (const p of placed.values()) {
        const n = s.nodes[p.id];
        if (!n || n.depth === 0) continue;
        const sc = screen(p);
        if (!sc || sc.x < -40 || sc.x > size.width + 40 || sc.y < -40 || sc.y > size.height + 40) continue;
        const di = Math.min(n.depth, SHOW_PX.length - 1);
        const extPx = (p.ext > p.ball + 0.01 ? p.ext : p.ball) * sc.ppu;
        const forced = onPath.has(p.id) || sel === p.id || s.hovered === p.id;
        if (!forced && extPx < SHOW_PX[di] && !kids.has(p.id)) continue;
        // while forming, only the three hemispheres are named, each once its questions have gathered
        if (!introDone() && (n.depth > 1 || now() * 1000 < (s.born[p.id] ?? 0) + 900)) continue;
        const w = Math.min(n.label.length, 34) * FONT_PX[di] * CHAR_W[di] + 12;
        const h = FONT_PX[di] + 4;
        const y = sc.y - lift(p, sc.ppu);
        const pri = (forced ? 10000 : 0) + (kids.has(p.id) ? 3000 : 0) + (6 - n.depth) * 400 + Math.min(390, extPx);
        cands.push({ id: p.id, pri, r: { x0: sc.x - w / 2 - 3, x1: sc.x + w / 2 + 3, y0: y - h - 2, y1: y + 2 } });
      }
      cands.sort((a, b) => b.pri - a.pri);
      const taken: Rect[] = [];
      const ui = uiRects(gl.domElement);
      const chosen: string[] = [];
      for (const c of cands) {
        if (chosen.length >= BUDGET) break;
        if (overlaps(c.r, taken) || overlaps(c.r, ui)) continue;
        taken.push(c.r);
        chosen.push(c.id);
      }
      anim.labelRects = taken;
      assign(slots, chosen);
    }

    const k = 1 - Math.exp(-dt * 9);
    const onB = new Set(anim.B.path);
    // text and class go to React (only renders when they change); position and fade go straight to the ref
    publish("nodes", slots.map((sl) => {
      const n = sl.key !== null ? s.nodes[sl.key] : undefined;
      return n ? { text: n.label, cls: cls(n.depth) + (s.selected === sl.key || onB.has(sl.key!) ? " sel" : "") } : { text: "", cls: "" };
    }));
    for (const sl of slots) {
      if (sl.key === null) continue;
      const p = placed.get(sl.key);
      const sc = p ? screen(p) : null;
      if (!p || !sc) { place(sl, null, 0, k); continue; }
      place(sl, sc.x, sc.y - lift(p, sc.ppu), k);
    }
    // hover card for the node under the pointer
    const hp = s.hovered ? placed.get(s.hovered) : undefined;
    const hs = hp ? screen(hp) : null;
    moveCard(cards.node, hs ? hs.x : null, hs ? hs.y : 0);
  });

  return null;
}
