"use client";
import { useEffect, useMemo, useRef } from "react";
import { useFrame, type ThreeEvent } from "@react-three/fiber";
import { Color, InstancedMesh, Object3D } from "three";
import { useStore } from "@/lib/store";
import { anim, now, progress } from "@/lib/anim";
import { nodeColor } from "@/lib/color";
import type { Placed } from "@/lib/layout";
import type { TreeNode } from "@/lib/types";

const MAX = 4096;

export function nodeSize(n: TreeNode): number {
  if (n.depth === 0) return 0.9;
  if (n.depth === 1) return 0.55;
  return 0.14 + 0.07 * Math.log2(1 + n.n_questions) + (n.depth === 2 ? 0.12 : 0);
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

  useFrame(() => {
    const m = ref.current;
    if (!m) return;
    const s = useStore.getState();
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
      let bright = n.depth <= 1 ? 1.6 : 1.15;
      const ka = idxA.get(id);
      const kb = idxB.get(id);
      if (ka !== undefined && pa >= ka) {
        const since = pa - ka;
        k *= 1 + 0.9 * Math.exp(-since * 3) + 0.25;
        bright = 2.4;
      }
      if (kb !== undefined && pb >= kb) {
        k *= 1.2;
        bright = Math.max(bright, 2.2);
      }
      if (s.hovered === id) k *= 1.35;
      if (s.selected === id) { k *= 1.3; bright = Math.max(bright, 2.2); }
      if (filtersActive && n.n_match === 0) bright *= 0.22;
      const twinkle = 1 + 0.05 * Math.sin(t * 1.7 + i * 1.37);
      dummy.position.set(p.x, p.y, p.z);
      dummy.scale.setScalar(nodeSize(n) * k * grow * twinkle);
      dummy.updateMatrix();
      m.setMatrixAt(i, dummy.matrix);
      nodeColor(n, s.indicator, c);
      if (kb !== undefined && pb >= kb && !(ka !== undefined && pa >= ka)) c.set("#FFD27A");
      c.multiplyScalar(bright);
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
      <icosahedronGeometry args={[1, 3]} />
      <meshBasicMaterial toneMapped={false} />
    </instancedMesh>
  );
}
