"use client";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { THEMES } from "@/lib/theme";
import { OrbitControls } from "@react-three/drei";
import { EffectComposer } from "@react-three/postprocessing";
import { useStore, loadSemantic } from "@/lib/store";
import { anim, BURST, fireworks, now } from "@/lib/anim";
import { DEFAULT_LAYOUT, LAYOUT_KEY, LAYOUTS, layoutFor, type LayoutKind } from "@/lib/layout";
import { starData } from "@/lib/stars";
import { stepHeat } from "@/lib/heat";
import { deselect, selectNode } from "@/lib/actions";
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
import { Reflection } from "./Reflection";

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

// Eases the live search heat once per frame; mounted before everything that reads it.
function HeatClock() {
  useFrame((_, dt) => stepHeat(dt));
  return null;
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
    // Web and Meaning compute in workers (Meaning's coordinates come from the server)
    const want = layoutFor(kind, nodes, children, direct, semantic);
    // while a layout computes (Web, Meaning), keep showing the last one; only the very first view falls back
    return { placed: want ?? (anim.placed.size ? anim.placed : null) ?? layoutFor("balloon", nodes, children, direct)!, exact: !!want };
  }, [nodes, children, ready, kind, semantic, layoutTick]);
  const [formed, setFormed] = useState(false);
  const homed = useRef(false);
  useLayoutEffect(() => {
    anim.placed = placed;
    // the water sits well under the lowest ball, whatever the layout: a third of the nebula's height below it,
    // so reflections open up beneath the data instead of crowding into it
    let low = Infinity, high = -Infinity;
    for (const p of placed.values()) { low = Math.min(low, p.y - p.ball); high = Math.max(high, p.y + p.ball); }
    if (Number.isFinite(low)) {
      anim.seaTarget = low - Math.max(120, (high - low) * 0.33);
      if (!homed.current) anim.sea = anim.seaTarget;
    }
    // the opening waits for the layout it will end in, so it never forms one shape and jumps to another
    if (!ready || !placed.size || (!homed.current && !exact)) return;
    if (homed.current) {
      if (exact) home(1.4); // after a layout switch, reframe it (once it's actually there)
      return;
    }
    homed.current = true;
    // The opening (docs/07-ui.md): fireworks, breadth first. Each node flies out from its parent along its
    // branch and bursts on landing, its questions spraying out to their ball while its children launch; the
    // camera starts close on the root and pulls back to the home view as the show spreads.
    const t0 = now() + 0.15;
    const { launch, arrive, last } = fireworks(useStore.getState().children);
    anim.intro = { t0, end: t0 + last + BURST + 0.2, launch, arrive };
    const born: Record<string, number> = {};
    for (const [id, l] of launch) born[id] = (t0 + l) * 1000;
    useStore.getState().set({ born });
    const r = placed.get("root");
    const from = r ? { pos: [r.x + 30, r.y + 40, r.z + 165] as [number, number, number], target: [r.x, r.y, r.z] as [number, number, number] } : undefined;
    home(last + BURST * 0.7, 0.6, from);
    setFormed(true);
  }, [placed, ready, exact]);

  useEffect(() => {
    // a layout picked by ?layout= or last time (docs/07-ui.md, Layouts)
    let saved: string | null = new URLSearchParams(location.search).get("layout");
    try { saved ??= localStorage.getItem(LAYOUT_KEY); } catch {}
    if (saved && LAYOUTS.some((l) => l.id === saved)) useStore.getState().set({ layout: saved as LayoutKind });
  }, []);

  // Once the opening has played, compute the Meaning layout in the background (its coordinates from the server,
  // its overlap pass in a worker), so switching to it later is instant.
  useEffect(() => {
    if (!formed) return;
    const wait = Math.max(1500, (anim.intro.end - now()) * 1000 + 1500);
    const t = setTimeout(() => {
      loadSemantic()
        .then(() => {
          const s = useStore.getState();
          const d = starData();
          const direct = new Map<string, number>();
          if (d) for (const [id, [, n]] of d.offsets) direct.set(id, n);
          layoutFor("semantic", s.nodes, s.children, direct, s.semantic);
        })
        .catch(() => {});
    }, wait);
    return () => clearTimeout(t);
  }, [formed]);

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
          // a click on empty sky (not a drag, and not one that started on a star) deselects: panel, trail, landed dot
          const d = downAt.current;
          if (d && d.star < 0 && Math.hypot(e.clientX - d.x, e.clientY - d.y) < 5 && (s.panel.kind !== "none" || s.selected)) deselect();
        }}
      >
        <color attach="background" args={[THEMES[theme].sky]} />
        <Backdrop />
        <HeatClock />
        {formed && (
          <>
            <Reflection placed={placed} />
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
