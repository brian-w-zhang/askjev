"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { useFrame } from "@react-three/fiber";
import { Billboard, Text } from "@react-three/drei";
import { Vector3, type Group, type Mesh, type PerspectiveCamera } from "three";
import { useStore } from "@/lib/store";
import { anim } from "@/lib/anim";
import { HEMI_COLOR, type Placed } from "@/lib/layout";
import { nodeSize } from "./Nodes";
import { overlaps, uiRects } from "@/lib/uirects";
import type { TreeNode } from "@/lib/types";

const FONT = "/fonts/schibsted-grotesk-latin-500-normal.woff";
const SIZE = [0, 1.05, 0.62, 0.4, 0.36, 0.33];
// A label shows once its node's subtree (or star ball) covers this many px on screen, by depth.
const SHOW_PX = [0, 0, 0, 55, 70, 80];
// On-screen text size (px) stays within these bounds at any distance.
const MIN_PX = [0, 16, 12.5, 11.5, 11, 11];
const MAX_PX = [0, 26, 19, 15, 14, 13];
const BUDGET = 60;

type TroikaText = Mesh & { fillOpacity: number; outlineOpacity: number };

export function Labels({ placed }: { placed: Map<string, Placed> }) {
  const nodes = useStore((s) => s.nodes);
  const [registry] = useState(() => new Map<string, { g: Group; t: TroikaText; o: number }>());

  const frame = useRef(0);
  const shown = useRef(new Set<string>());
  const v = useMemo(() => new Vector3(), []);

  useFrame(({ camera, size, gl }, dt) => {
    const s = useStore.getState();
    const cam = camera as PerspectiveCamera;
    // Every few frames: pick which labels to show. Candidates within their fade distance are
    // placed greedily by priority in screen space, and any label that would overlap one already
    // placed is dropped, so dense rings stay legible.
    if (frame.current++ % 4 === 0) {
      const onPath = new Set([...anim.A.path, ...anim.B.path]);
      const sel = s.selected;
      const kids = new Set(sel ? s.children[sel] ?? [] : []);
      const cands: { id: string; pri: number; x: number; y: number; w: number; h: number }[] = [];
      const placedRects: { x0: number; x1: number; y0: number; y1: number; owner?: string }[] = [];
      const tanHalf = Math.tan(((cam.fov ?? 45) * Math.PI) / 360);
      // Stars on the lit path and the selected star block labels too, so nothing hides behind them.
      for (const id of new Set([...onPath, ...(sel ? [sel] : [])])) {
        const p = placed.get(id);
        const n = s.nodes[id];
        if (!p || !n) continue;
        v.set(p.x, p.y, p.z);
        const d = cam.position.distanceTo(v);
        v.project(cam);
        if (v.z > 1) continue;
        const rad = nodeSize(n) * 1.3 * (size.height / (2 * d * tanHalf)) + 3;
        const x = ((v.x + 1) / 2) * size.width;
        const y = ((1 - v.y) / 2) * size.height;
        placedRects.push({ x0: x - rad, x1: x + rad, y0: y - rad, y1: y + rad, owner: id });
      }
      for (const [id, r] of registry) {
        const n = s.nodes[id];
        if (!n) continue;
        const p = placed.get(id);
        if (!p) continue;
        const d = cam.position.distanceTo(r.g.position);
        const ppu = size.height / (2 * d * tanHalf);
        const di = Math.min(n.depth, SHOW_PX.length - 1);
        const extPx = (p.ext > p.ball + 0.01 ? p.ext : p.ball) * ppu;
        const forced = onPath.has(id) || sel === id || s.hovered === id;
        if (!forced && extPx < SHOW_PX[di] && !kids.has(id)) continue;
        v.copy(r.g.position).project(cam);
        if (v.z > 1 || Math.abs(v.x) > 1.1 || Math.abs(v.y) > 1.1) continue;
        const fs = SIZE[di];
        const px = Math.max(MIN_PX[di], Math.min(fs * ppu, MAX_PX[di]));
        r.g.scale.setScalar(px / (fs * ppu));
        const w = Math.min(n.label.length, 28) * px * 0.6;
        const h = px * 1.25;
        const pri = (forced ? 10000 : 0) + (kids.has(id) ? 3000 : 0) + (6 - n.depth) * 400 + Math.min(390, extPx);
        cands.push({ id, pri, x: ((v.x + 1) / 2) * size.width, y: ((1 - v.y) / 2) * size.height, w, h });
      }
      cands.sort((a, b) => b.pri - a.pri);
      const next = new Set<string>();
      const ui = uiRects(gl.domElement);
      const labelRects: typeof placedRects = [];
      for (const c of cands) {
        if (next.size >= BUDGET) break;
        const rect = { x0: c.x - c.w / 2 - 4, x1: c.x + c.w / 2 + 4, y0: c.y - c.h - 5, y1: c.y + 5 };
        if (!(c.pri >= 10000 && c.id === sel) && placedRects.some((o) => o.owner !== c.id && rect.x0 < o.x1 && rect.x1 > o.x0 && rect.y0 < o.y1 && rect.y1 > o.y0)) continue;
        if (overlaps(rect, ui)) continue;
        placedRects.push(rect);
        labelRects.push(rect);
        next.add(c.id);
      }
      shown.current = next;
      anim.labelRects = labelRects;
    }
    const k = 1 - Math.exp(-dt * 8);
    for (const [id, r] of registry) {
      const target = shown.current.has(id) ? 1 : 0;
      r.o += (target - r.o) * k;
      r.t.fillOpacity = r.o;
      r.t.outlineOpacity = r.o * 0.8;
      r.g.visible = r.o > 0.02;
    }
  });

  return (
    <group>
      {[...placed.values()].map((p) => {
        const n = nodes[p.id];
        if (!n || n.depth === 0) return null;
        return <Label key={p.id} id={p.id} p={p} n={n} registry={registry} />;
      })}
    </group>
  );
}

function Label({ id, p, n, registry }: { id: string; p: Placed; n: TreeNode; registry: Map<string, { g: Group; t: TroikaText; o: number }> }) {
  const g = useRef<Group>(null);
  const t = useRef<TroikaText>(null);
  useEffect(() => {
    if (!g.current || !t.current) return;
    const prev = registry.get(id);
    registry.set(id, { g: g.current, t: t.current, o: prev?.o ?? 0 });
    return () => { registry.delete(id); };
  }, [id, registry]);
  const size = SIZE[Math.min(n.depth, SIZE.length - 1)];
  return (
    <Billboard ref={g} position={[p.x, p.y + Math.max(nodeSize(n) * 1.9, p.ball * 1.05) + size * 0.5, p.z]}>
      <Text
        ref={t as never}
        font={FONT}
        fontSize={size}
        color={n.depth === 1 ? HEMI_COLOR[n.hemisphere] : "#D9DCEF"}
        anchorX="center"
        anchorY="bottom"
        letterSpacing={n.depth === 1 ? 0.02 : 0}
        outlineWidth={size * 0.12}
        outlineColor="#050811"
        fillOpacity={0}
        outlineOpacity={0}
        maxWidth={size * 14}
        textAlign="center"
        renderOrder={10}
        material-depthTest={false}
      >
        {n.label}
      </Text>
    </Billboard>
  );
}
