"use client";
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { AdditiveBlending, CanvasTexture, Group, Mesh, Sprite, Vector3, type Camera, type PerspectiveCamera } from "three";
import { anim, headPosition, now, progress } from "@/lib/anim";
import { useStore } from "@/lib/store";
import { PATH_A_COLOR, PATH_B_COLOR } from "@/lib/layout";

function glowTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 128;
  const g = c.getContext("2d")!;
  const grd = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grd.addColorStop(0, "rgba(255,255,255,1)");
  grd.addColorStop(0.18, "rgba(255,255,255,0.55)");
  grd.addColorStop(0.5, "rgba(255,255,255,0.12)");
  grd.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = grd;
  g.fillRect(0, 0, 128, 128);
  return new CanvasTexture(c);
}

/** World units that cover `px` screen pixels at `at` (so rings and comets keep one on-screen size). */
function pxToWorld(camera: Camera, at: Vector3, h: number, px: number) {
  const tanHalf = Math.tan((((camera as PerspectiveCamera).fov ?? 45) * Math.PI) / 360);
  return (px * 2 * camera.position.distanceTo(at) * tanHalf) / h;
}

function Comet({ which, color }: { which: "A" | "B"; color: string }) {
  const g = useRef<Group>(null);
  const sprite = useRef<Sprite>(null);
  const core = useRef<Mesh>(null);
  const tex = useMemo(() => glowTexture(), []);
  useFrame(({ camera, size }) => {
    const l = anim[which];
    const h = headPosition(l);
    if (!g.current) return;
    g.current.visible = !!h;
    if (!h) return;
    g.current.position.set(h[0], h[1], h[2]);
    const pr = progress(l);
    const moving = pr < l.path.length - 1;
    const unit = pxToWorld(camera, g.current.position, size.height, 1);
    const s = (moving ? 46 : 32 + 6 * Math.sin(now() * 3)) * unit;
    sprite.current?.scale.set(s, s, 1);
    core.current?.scale.setScalar(4 * unit);
  });
  return (
    <group ref={g} visible={false}>
      <sprite ref={sprite}>
        <spriteMaterial map={tex} color={color} transparent depthWrite={false} blending={AdditiveBlending} toneMapped={false} />
      </sprite>
      <mesh ref={core}>
        <sphereGeometry args={[1, 16, 16]} />
        <meshBasicMaterial color={color} toneMapped={false} />
      </mesh>
    </group>
  );
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
      <meshBasicMaterial color={PATH_B_COLOR} transparent opacity={0.9} toneMapped={false} depthWrite={false} />
    </mesh>
  );
}

/** Slow halo around the selected node. */
function Selection() {
  const m = useRef<Mesh>(null);
  useFrame(({ camera, size }) => {
    const mesh = m.current;
    if (!mesh) return;
    const id = useStore.getState().selected;
    const p = id ? anim.placed.get(id) : undefined;
    mesh.visible = !!p;
    if (!p) return;
    mesh.position.set(p.x, p.y, p.z);
    mesh.quaternion.copy(camera.quaternion);
    mesh.rotateZ(now() * 0.6);
    mesh.scale.setScalar(pxToWorld(camera, mesh.position, size.height, 22));
  });
  return (
    <mesh ref={m} visible={false}>
      <ringGeometry args={[1.25, 1.32, 64, 1, 0, Math.PI * 1.6]} />
      <meshBasicMaterial color="#EDEBFA" transparent opacity={0.8} toneMapped={false} depthWrite={false} />
    </mesh>
  );
}

export function Comets() {
  return (
    <>
      <Comet which="A" color={PATH_A_COLOR} />
      <Comet which="B" color={PATH_B_COLOR} />
      <Fork />
      <Selection />
    </>
  );
}
