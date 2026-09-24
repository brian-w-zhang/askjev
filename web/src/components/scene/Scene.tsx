"use client";
import { useEffect, useLayoutEffect, useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
import { Bloom, EffectComposer, Vignette } from "@react-three/postprocessing";
import { useStore, loadSubtree } from "@/lib/store";
import { anim } from "@/lib/anim";
import { layout } from "@/lib/layout";
import { selectNode } from "@/lib/actions";
import { Edges } from "./Edges";
import { Nodes } from "./Nodes";
import { Labels } from "./Labels";
import { Comets } from "./Comets";
import { CameraRig, flyTo } from "./CameraRig";
import { Hover } from "./Hover";

export default function Scene() {
  const nodes = useStore((s) => s.nodes);
  const children = useStore((s) => s.children);
  const placed = useMemo(() => layout(nodes, children), [nodes, children]);
  useLayoutEffect(() => {
    anim.placed = placed;
  }, [placed]);

  useEffect(() => {
    loadSubtree("root", 2).then(() => flyTo([0, -2, 0], 58, 2.4));
  }, []);

  return (
    <Canvas
      camera={{ position: [0, 190, 140], fov: 42, near: 0.5, far: 1200 }}
      dpr={[1, 1.75]}
      gl={{ antialias: true, powerPreference: "high-performance" }}
      onPointerMissed={() => useStore.getState().set({ hovered: null })}
    >
      <color attach="background" args={["#05070F"]} />
      <Stars radius={260} depth={80} count={2600} factor={4} saturation={0} fade speed={0.35} />
      <Edges placed={placed} />
      <Nodes placed={placed} onPick={(id) => selectNode(id)} />
      <Labels placed={placed} />
      <Comets />
      <Hover placed={placed} />
      <CameraRig />
      <OrbitControls makeDefault enableDamping dampingFactor={0.08} minDistance={6} maxDistance={220} maxPolarAngle={Math.PI * 0.62} />
      <EffectComposer multisampling={0}>
        <Bloom mipmapBlur intensity={1.15} luminanceThreshold={0.32} luminanceSmoothing={0.25} radius={0.72} />
        <Vignette eskil={false} offset={0.2} darkness={0.75} />
      </EffectComposer>
    </Canvas>
  );
}
