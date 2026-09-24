"use client";
import { Html } from "@react-three/drei";
import { useStore } from "@/lib/store";
import type { Placed } from "@/lib/layout";

export function Hover({ placed }: { placed: Map<string, Placed> }) {
  const id = useStore((s) => s.hovered);
  const n = useStore((s) => (id ? s.nodes[id] : undefined));
  const p = id ? placed.get(id) : undefined;
  if (!n || !p) return null;
  return (
    <Html position={[p.x, p.y, p.z]} style={{ pointerEvents: "none" }} zIndexRange={[20, 0]}>
      <div className="hovercard">
        <div className="hovercard-label">{n.label}</div>
        <div className="hovercard-meta">
          {n.n_questions} question{n.n_questions === 1 ? "" : "s"}
          {n.n_children ? `, ${n.n_desc} topics below` : ""}
        </div>
      </div>
    </Html>
  );
}
