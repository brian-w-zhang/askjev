"use client";
import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Mesh, Vector3, type Camera, type Group, type PerspectiveCamera } from "three";
import { anim, now, progress } from "@/lib/anim";
import { useStore } from "@/lib/store";
import { JEV_GREEN, THEMES } from "@/lib/theme";

// Rings in the sky: where Jev's walk leaves the tree path, and the selected node.

/** World units that cover `px` screen pixels at `at` (so rings keep one on-screen size). */
function pxToWorld(camera: Camera, at: Vector3, h: number, px: number) {
  const tanHalf = Math.tan((((camera as PerspectiveCamera).fov ?? 45) * Math.PI) / 360);
  return (px * 2 * camera.position.distanceTo(at) * tanHalf) / h;
}

/** Ring that marks where Jev's walk leaves the embedding path. */
function Fork() {
  const m = useRef<Mesh>(null);
  useFrame(({ camera, size }) => {
    const mesh = m.current;
    if (!mesh) return;
    const k = anim.fork;
    const id = k > 0 ? anim.B.path[k - 1] : undefined;
    const p = id ? anim.placed.get(id) : undefined;
    const visible = !!p && progress(anim.B) >= k - 1;
    mesh.visible = visible;
    if (!visible || !p) return;
    mesh.position.set(p.x, p.y, p.z);
    mesh.quaternion.copy(camera.quaternion);
    mesh.scale.setScalar((1.1 + 0.25 * Math.sin(now() * 4)) * pxToWorld(camera, mesh.position, size.height, 18));
  });
  return (
    <mesh ref={m} visible={false}>
      <ringGeometry args={[0.9, 1.05, 48]} />
      <meshBasicMaterial color={JEV_GREEN} transparent opacity={0.9} toneMapped={false} depthWrite={false} />
    </mesh>
  );
}

/**
 * Crop marks around the selected topic: four static corners, the same mark a landed question gets (typesafe.ai's
 * section corners), so "this is what you selected" looks alike for topics and questions. Always a fixed on-screen size.
 */
const CORNERS: [number, number, number, number][] = [];
for (const sx of [-1, 1]) for (const sy of [-1, 1]) {
  // each corner is two thin bars meeting at (sx, sy) on a unit square: [x, y, width, height] of each bar
  CORNERS.push([sx * (1 - 0.18), sy, 0.36, 0.1], [sx, sy * (1 - 0.18), 0.1, 0.36]);
}

function Selection() {
  const g = useRef<Group>(null);
  const theme = useStore((s) => s.theme);
  useFrame(({ camera, size }) => {
    const grp = g.current;
    if (!grp) return;
    const { selected: id, focusStar } = useStore.getState();
    const p = id ? anim.placed.get(id) : undefined;
    grp.visible = !!p && focusStar < 0; // a landed question has its own marker
    if (!p) return;
    grp.position.set(p.x, p.y, p.z);
    grp.quaternion.copy(camera.quaternion);
    grp.scale.setScalar(pxToWorld(camera, grp.position, size.height, 30)); // clear of the enlarged node marker
  });
  return (
    <group ref={g} visible={false}>
      {CORNERS.map(([x, y, w, h], k) => (
        <mesh key={k} position={[x, y, 0]} renderOrder={20}>
          <planeGeometry args={[w, h]} />
          <meshBasicMaterial color={THEMES[theme].ink} toneMapped={false} depthWrite={false} depthTest={false} transparent />
        </mesh>
      ))}
    </group>
  );
}

export function Comets() {
  return (
    <>
      <Fork />
      <Selection />
    </>
  );
}
