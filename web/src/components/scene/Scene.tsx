"use client";
import { useEffect, useLayoutEffect, useMemo, useRef } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { EffectComposer } from "@react-three/postprocessing";
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
import { Stars } from "./Stars";
import { Gas } from "./Gas";
import { Backdrop } from "./Backdrop";
import { StarText } from "./StarText";
import { Dither } from "./Dither";
import { SkyOverlay } from "./SkyOverlay";

/** Everything in the canvas is dithered onto TypeSafe's palette in 2 CSS px cells (docs/07-ui.md, Look). */
function DitherPass() {
  const dpr = useThree((s) => s.viewport.dpr);
  return (
    <EffectComposer multisampling={0}>
      <Dither cell={2 * dpr} spread={0.2} />
    </EffectComposer>
  );
}

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
    <>
      <Canvas
        camera={{ position: [0, 420, 620], fov: 42, near: 0.1, far: 4000 }}
        dpr={[1, 1.75]}
        gl={{ antialias: true, powerPreference: "high-performance" }}
        onPointerMissed={() => useStore.getState().set({ hovered: null })}
      >
        <color attach="background" args={["#D6EAF8"]} />
        <Backdrop />
        <Gas placed={placed} />
        <Edges placed={placed} />
        <Stars placed={placed} />
        <Nodes placed={placed} onPick={(id) => selectNode(id)} />
        <Labels placed={placed} />
        <StarText />
        <Comets />
        <CameraRig />
        <OrbitControls makeDefault enableDamping dampingFactor={0.07} minDistance={1.2} maxDistance={900} autoRotateSpeed={0.18} zoomSpeed={1.1} />
        <DitherPass />
      </Canvas>
      <SkyOverlay />
    </>
  );
}
