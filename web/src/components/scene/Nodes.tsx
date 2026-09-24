"use client";
import { useEffect, useMemo, useRef } from "react";
import { useFrame, type ThreeEvent } from "@react-three/fiber";
import { Color, InstancedMesh, Object3D, type PerspectiveCamera } from "three";
import { useStore } from "@/lib/store";
import { anim, now, progress } from "@/lib/anim";
import { nodeColor } from "@/lib/color";
import { INK, PATH_B_COLOR, type Placed } from "@/lib/layout";
import type { TreeNode } from "@/lib/types";

const MAX = 4096;
// On-screen radius bounds (px) by depth: node stars stay points of light, never planets or specks.
const MAX_PX = [16, 12, 9, 7, 6, 5];
const MIN_PX = 1.6;

export function nodeSize(n: TreeNode): number {
  // the bright star at the heart of each node's ball; capped per depth so parents stay brighter
  if (n.depth === 0) return 1.4;
  if (n.depth === 1) return 1.1;
  const cap = n.depth === 2 ? 0.7 : n.depth === 3 ? 0.45 : 0.32;
  const base = n.depth === 2 ? 0.4 : 0.18;
  return Math.min(cap, base + 0.03 * Math.log2(1 + n.n_questions));
}

const back = (x: number) => 1 + 2.2 * Math.pow(x - 1, 3) + 1.2 * Math.pow(x - 1, 2);

export function Nodes({ placed, onPick }: { placed: Map<string, Placed>; onPick: (id: string) => void }) {
  const ref = useRef<InstancedMesh>(null);
  const ids = useMemo(() => [...placed.keys()], [placed]);
  const dummy = useMemo(() => new Object3D(), []);
  const c = useMemo(() => new Color(), []);
  const colors = useMemo(() => new Float32Array(MAX * 3), []);

  useEffect(() => {
    const m = ref.current;
    if (!m) return;
    m.count = ids.length;
    // seed matrices so the raycast bounds are right before the first frame
    ids.forEach((id, i) => {
      const p = placed.get(id)!;
      dummy.position.set(p.x, p.y, p.z);
      dummy.scale.setScalar(1);
      dummy.updateMatrix();
      m.setMatrixAt(i, dummy.matrix);
    });
    m.instanceMatrix.needsUpdate = true;
    m.computeBoundingSphere();
  }, [ids, placed, dummy]);

  useFrame(({ camera, size }) => {
    const m = ref.current;
    if (!m) return;
    const s = useStore.getState();
    const tanHalf = Math.tan((((camera as PerspectiveCamera).fov ?? 45) * Math.PI) / 360);
    const t = now();
    const pa = progress(anim.A, t);
    const pb = progress(anim.B, t);
    const idxA = new Map(anim.A.path.map((id, i) => [id, i]));
    const idxB = new Map(anim.B.path.map((id, i) => [id, i]));
    const filtersActive = !!(s.filters.kind || s.filters.primitive || s.filters.origin);
    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      const n = s.nodes[id];
      const p = placed.get(id);
      if (!n || !p) continue;
      const age = (t * 1000 - (s.born[id] ?? 0)) / 450;
      const grow = age >= 1 ? 1 : Math.max(0, back(Math.max(0, age)));
      let k = 1;
      let tone: "ink" | "path" | "jev" | "sel" | "dim" = "ink";
      const ka = idxA.get(id);
      const kb = idxB.get(id);
      if (ka !== undefined && pa >= ka) {
        const since = pa - ka;
        k *= 1 + 0.9 * Math.exp(-since * 3) + 0.25;
        tone = "path";
      }
      if (kb !== undefined && pb >= kb) {
        k *= 1.2;
        if (tone !== "path") tone = "jev";
      }
      if (s.hovered === id) k *= 1.35;
      if (s.selected === id) { k *= 1.3; tone = "sel"; }
      if (filtersActive && n.n_match === 0) tone = "dim";
      const twinkle = 1 + 0.05 * Math.sin(t * 1.7 + i * 1.37);
      dummy.position.set(p.x, p.y, p.z);
      const ppu = size.height / (2 * Math.max(0.1, camera.position.distanceTo(dummy.position)) * tanHalf);
      const r = Math.min(Math.max(nodeSize(n), MIN_PX / ppu), MAX_PX[Math.min(n.depth, MAX_PX.length - 1)] / ppu);
      dummy.scale.setScalar(r * k * grow * twinkle);
      dummy.quaternion.copy(camera.quaternion); // squares face the camera
      dummy.updateMatrix();
      m.setMatrixAt(i, dummy.matrix);
      // ink squares like the slider markers on typesafe.ai; Jev green where Jev is (its walk, the selection)
      if (tone === "jev" || tone === "sel") c.set(PATH_B_COLOR);
      else if (tone === "dim") c.set("#C9C9C9");
      else if (s.indicator === "hemisphere" || tone === "path") c.set(INK);
      else nodeColor(n, s.indicator, c);
      m.setColorAt(i, c);
    }
    m.count = ids.length;
    m.instanceMatrix.needsUpdate = true;
    if (m.instanceColor) m.instanceColor.needsUpdate = true;
  });

  const idAt = (e: ThreeEvent<PointerEvent | MouseEvent>) => (e.instanceId !== undefined ? ids[e.instanceId] : undefined);

  return (
    <instancedMesh
      ref={ref}
      args={[undefined, undefined, MAX]}
      frustumCulled={false}
      onClick={(e) => {
        e.stopPropagation();
        const id = idAt(e);
        if (id) onPick(id);
      }}
      onPointerMove={(e) => {
        e.stopPropagation();
        const id = idAt(e) ?? null;
        if (useStore.getState().hovered !== id) useStore.getState().set({ hovered: id });
        document.body.style.cursor = id ? "pointer" : "";
      }}
      onPointerOut={() => {
        useStore.getState().set({ hovered: null });
        document.body.style.cursor = "";
      }}
    >
      <instancedBufferAttribute attach="instanceColor" args={[colors, 3]} />
      <boxGeometry args={[1.5, 1.5, 1.5]} />
      <meshBasicMaterial toneMapped={false} />
    </instancedMesh>
  );
}
