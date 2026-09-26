"use client";
import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Mesh, Vector3, type Camera, type PerspectiveCamera } from "three";
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

/** Slow halo around the selected node. */
function Selection() {
  const m = useRef<Mesh>(null);
  const theme = useStore((s) => s.theme);
  useFrame(({ camera, size }) => {
    const mesh = m.current;
    if (!mesh) return;
    const { selected: id, focusStar } = useStore.getState();
    const p = id ? anim.placed.get(id) : undefined;
    mesh.visible = !!p && focusStar < 0; // a landed question has its own marker
    if (!p) return;
    mesh.position.set(p.x, p.y, p.z);
    mesh.quaternion.copy(camera.quaternion);
    mesh.rotateZ(now() * 0.6);
    mesh.scale.setScalar(pxToWorld(camera, mesh.position, size.height, 22));
  });
  return (
    <mesh ref={m} visible={false}>
      <ringGeometry args={[1.25, 1.32, 64, 1, 0, Math.PI * 1.6]} />
      <meshBasicMaterial color={THEMES[theme].ink} transparent opacity={0.95} toneMapped={false} depthWrite={false} />
    </mesh>
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
