"use client";
import { useEffect, useLayoutEffect, useMemo, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Stars as SkyStars } from "@react-three/drei";
import { Bloom, EffectComposer, Vignette } from "@react-three/postprocessing";
import { useStore, loadSubtree } from "@/lib/store";
import { anim } from "@/lib/anim";
import { layout } from "@/lib/layout";
import { loadStars, starData } from "@/lib/stars";
import { selectNode } from "@/lib/actions";
import { Edges } from "./Edges";
import { Nodes } from "./Nodes";
import { Labels } from "./Labels";
import { Comets } from "./Comets";
import { CameraRig, home } from "./CameraRig";
import { Hover } from "./Hover";
import { Stars } from "./Stars";
import { Gas } from "./Gas";
import { Backdrop } from "./Backdrop";
import { StarText } from "./StarText";

// The nebula (docs/07-ui.md): the whole tree and every displayable question, loaded once.
export default function Scene() {
  const nodes = useStore((s) => s.nodes);
  const children = useStore((s) => s.children);
  const ready = useStore((s) => s.starsReady);
  const placed = useMemo(() => {
    const d = ready ? starData() : null;
    const direct = new Map<string, number>();
    if (d) for (const [id, [, n]] of d.offsets) direct.set(id, n);
    return layout(nodes, children, direct);
  }, [nodes, children, ready]);
  const homed = useRef(false);
  useLayoutEffect(() => {
    anim.placed = placed;
    // first time everything is laid out: glide in from deep space
    if (ready && placed.size && !homed.current) {
      homed.current = true;
      home(3.2);
    }
  }, [placed, ready]);

  useEffect(() => {
    Promise.all([loadSubtree("root", 12), loadStars()]).then(() => useStore.getState().set({ starsReady: true }));
  }, []);

  return (
    <Canvas
      camera={{ position: [0, 420, 620], fov: 42, near: 0.1, far: 4000 }}
      dpr={[1, 1.75]}
      gl={{ antialias: true, powerPreference: "high-performance" }}
      onPointerMissed={() => useStore.getState().set({ hovered: null })}
    >
      <color attach="background" args={["#03040B"]} />
      <Backdrop />
      <SkyStars radius={900} depth={400} count={5000} factor={7} saturation={0.2} fade speed={0.3} />
      <Gas placed={placed} />
      <Edges placed={placed} />
      <Stars placed={placed} />
      <Nodes placed={placed} onPick={(id) => selectNode(id)} />
      <Labels placed={placed} />
      <StarText />
      <Comets />
      <Hover placed={placed} />
      <CameraRig />
      <OrbitControls makeDefault enableDamping dampingFactor={0.07} minDistance={1.2} maxDistance={900} autoRotateSpeed={0.18} zoomSpeed={1.1} />
      <EffectComposer multisampling={0}>
        <Bloom mipmapBlur intensity={1.25} luminanceThreshold={0.22} luminanceSmoothing={0.3} radius={0.78} />
        <Vignette eskil={false} offset={0.22} darkness={0.8} />
      </EffectComposer>
    </Canvas>
  );
}
