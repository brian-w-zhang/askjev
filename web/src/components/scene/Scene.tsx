"use client";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { THEMES } from "@/lib/theme";
import { OrbitControls } from "@react-three/drei";
import { EffectComposer } from "@react-three/postprocessing";
import { useStore, loadSubtree, loadSemantic } from "@/lib/store";
import { anim, INTRO_FORM, introDelay, now } from "@/lib/anim";
import { DEFAULT_LAYOUT, LAYOUT_KEY, LAYOUTS, layoutFor, type LayoutKind } from "@/lib/layout";
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
import { Journey } from "./Journey";

// Everything in the canvas is dithered onto TypeSafe's palette in 2 CSS px cells (docs/07-ui.md, Look).
// The scene renders at exactly one pixel per cell (half the CSS size) and the canvas is scaled up with
// crisp pixels, so the GPU shades a quarter of the CSS pixels (a 12th on a 1.75× retina screen) and every
// star lands on a whole cell instead of being sampled away between cell centers.
const CELL_DPR = 0.5;

function DitherPass() {
  const theme = useStore((s) => s.theme);
  return (
    <EffectComposer multisampling={0}>
      <Dither cell={1} palette={THEMES[theme].dither} />
    </EffectComposer>
  );
}

// The nebula (docs/07-ui.md): the whole tree and every displayable question, loaded once.
export default function Scene() {
  const nodes = useStore((s) => s.nodes);
  const children = useStore((s) => s.children);
  const ready = useStore((s) => s.starsReady);
  const kind = useStore((s) => s.layout);
  const theme = useStore((s) => s.theme);
  const downAt = useRef<{ x: number; y: number; star: number } | null>(null);
  const semantic = useStore((s) => s.semantic);
  const layoutTick = useStore((s) => s.layoutTick);
  const { placed, exact } = useMemo(() => {
    void layoutTick; // a layout finished in the background
    const d = ready ? starData() : null;
    const direct = new Map<string, number>();
    if (d) for (const [id, [, n]] of d.offsets) direct.set(id, n);
    // Web settles in a worker and Meaning loads from the server; show the balloon tree meanwhile
    const want = layoutFor(kind, nodes, children, direct, semantic);
    return { placed: want ?? layoutFor("balloon", nodes, children, direct)!, exact: !!want };
  }, [nodes, children, ready, kind, semantic, layoutTick]);
  const [formed, setFormed] = useState(false);
  const homed = useRef(false);
  useLayoutEffect(() => {
    anim.placed = placed;
    // the opening waits for the layout it will end in, so it never forms one shape and jumps to another
    if (!ready || !placed.size || (!homed.current && !exact)) return;
    if (homed.current) {
      home(1.4); // after a layout switch, reframe it
      return;
    }
    homed.current = true;
    // The opening (docs/07-ui.md): the nebula forms a tree level at a time (stars spiral out from the center,
    // branches and node markers grow in step) while the camera cranes up from the water to the home view.
    const t0 = now() + 0.15;
    const nodes = useStore.getState().nodes;
    const maxDepth = Math.max(...Object.values(nodes).map((n) => n.depth));
    anim.intro = { t0, end: t0 + introDelay(maxDepth) + INTRO_FORM + 0.3 };
    const born: Record<string, number> = {};
    for (const n of Object.values(nodes)) born[n.id] = (t0 + introDelay(n.depth)) * 1000;
    useStore.getState().set({ born });
    home(5.2, 1);
    setFormed(true);
  }, [placed, ready, exact]);

  useEffect(() => {
    Promise.all([loadSubtree("root", 12), loadStars()]).then(() => useStore.getState().set({ starsReady: true }));
    // a layout picked by ?layout= or last time (docs/07-ui.md, Layouts)
    let saved: string | null = new URLSearchParams(location.search).get("layout");
    try { saved ??= localStorage.getItem(LAYOUT_KEY); } catch {}
    if (saved && LAYOUTS.some((l) => l.id === saved)) useStore.getState().set({ layout: saved as LayoutKind });
  }, []);

  useEffect(() => {
    if (kind === "semantic" && !semantic) loadSemantic().catch(() => useStore.getState().set({ layout: DEFAULT_LAYOUT }));
  }, [kind, semantic]);

  return (
    <>
      <Canvas
        camera={{ position: [0, 28, 1500], fov: 42, near: 0.1, far: 4000 }}
        dpr={CELL_DPR}
        gl={{ antialias: false, powerPreference: "high-performance" }}
        style={{ imageRendering: "pixelated" }}
        onPointerDown={(e) => { downAt.current = { x: e.clientX, y: e.clientY, star: useStore.getState().hoverStar }; }}
        onPointerMissed={(e) => {
          const s = useStore.getState();
          s.set({ hovered: null });
          // a click on empty sky (not a drag, and not one that started on a star) closes the side panel
          const d = downAt.current;
          if (d && d.star < 0 && Math.hypot(e.clientX - d.x, e.clientY - d.y) < 5 && s.panel.kind !== "none") s.set({ panel: { kind: "none" } });
        }}
      >
        <color attach="background" args={[THEMES[theme].sky]} />
        <Backdrop />
        {formed && (
          <>
            <Gas placed={placed} />
            <Edges placed={placed} />
            <Stars placed={placed} />
            <Nodes placed={placed} onPick={(id) => selectNode(id)} />
            <Labels placed={placed} />
          </>
        )}
        <StarText />
        <Comets />
        <Journey placed={placed} />
        <CameraRig />
        <OrbitControls makeDefault target={[0, 60, 0]} enableDamping dampingFactor={0.07} minDistance={1.2} maxDistance={900} autoRotateSpeed={0.18} zoomSpeed={1.25} zoomToCursor />
        <DitherPass />
      </Canvas>
      <SkyOverlay />
    </>
  );
}
