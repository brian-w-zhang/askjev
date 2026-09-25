"use client";
import { useEffect, useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { Vector2, Vector3, type PerspectiveCamera } from "three";
import { Line2 } from "three/examples/jsm/lines/Line2.js";
import { LineGeometry } from "three/examples/jsm/lines/LineGeometry.js";
import { LineMaterial } from "three/examples/jsm/lines/LineMaterial.js";
import { useStore } from "@/lib/store";
import { anim, headPosition, now, progress } from "@/lib/anim";
import { edgePoint, INK, PATH_B_COLOR, type Placed } from "@/lib/layout";
import { cards, moveCard, publishWalker } from "@/lib/overlay";
import { starData, starWorld } from "@/lib/stars";

// The journey (docs/07-ui.md): the path walked so far is a thick lit trail (Jev green with a halo, or ink
// for the hop to where the chosen question lives), revealed as the walker moves; the walker and the
// destination dot are drawn in the HTML overlay so they glow crisply above the dither.
const SEG = 20;

function Trail({ which, placed }: { which: "A" | "B"; placed: Map<string, Placed> }) {
  const path = useStore((s) => (which === "A" ? s.pathA : s.pathB));
  const gl = useThree((s) => s.gl);
  const color = which === "B" ? PATH_B_COLOR : INK;
  const { lines, segs } = useMemo(() => {
    const pts: number[] = [];
    const pt: [number, number, number] = [0, 0, 0];
    for (let k = 0; k + 1 < path.length; k++) {
      const p = placed.get(path[k]);
      const c = placed.get(path[k + 1]);
      if (!p || !c) break;
      for (let s = k === 0 ? 0 : 1; s <= SEG; s++) pts.push(...edgePoint(p, c, s / SEG, pt));
    }
    const make = (width: number, opacity: number) => {
      const g = new LineGeometry();
      g.setPositions(pts.length >= 6 ? pts : [0, 0, 0, 0, 0, 0]);
      const m = new LineMaterial({ color, linewidth: width, transparent: true, opacity, depthTest: false, depthWrite: false });
      const l = new Line2(g, m);
      l.renderOrder = 6;
      l.frustumCulled = false;
      return l;
    };
    // a wide soft halo under the core line; the dither turns it into a halftone glow
    const halo = make(which === "B" ? 16 : 9, which === "B" ? 0.35 : 0.2);
    const core = make(which === "B" ? 5 : 3, 1);
    return { lines: [halo, core], segs: Math.max(0, pts.length / 3 - 1) };
  }, [path, placed, color, which]);
  useEffect(() => () => lines.forEach((l) => { l.geometry.dispose(); (l.material as LineMaterial).dispose(); }), [lines]);

  const res = useMemo(() => new Vector2(), []);
  useFrame(() => {
    gl.getDrawingBufferSize(res);
    const pr = progress(anim[which]);
    for (const l of lines) {
      (l.material as LineMaterial).resolution.copy(res);
      l.visible = pr >= 0 && segs > 0;
      (l.geometry as LineGeometry).instanceCount = Math.min(segs, Math.max(0, Math.round(pr * SEG)));
    }
  });
  return (
    <>
      {lines.map((l, i) => <primitive key={i} object={l} />)}
    </>
  );
}

/** Moves the walker and the destination (HTML, in <SkyOverlay>) to where they are in the sky. */
function Tracker() {
  const v = useMemo(() => new Vector3(), []);
  const w = useMemo<[number, number, number]>(() => [0, 0, 0], []);
  const lastKey = useRef("");
  useFrame(({ camera, size }) => {
    const cam = camera as PerspectiveCamera;
    const s = useStore.getState();
    const toScreen = (x: number, y: number, z: number) => {
      v.set(x, y, z).project(cam);
      return v.z > 1 ? null : { x: ((v.x + 1) / 2) * size.width, y: ((1 - v.y) / 2) * size.height };
    };
    const j = anim.journey;
    // walker: at the root while Jev reads, then at the head of whichever light is running
    let head: [number, number, number] | null = null;
    let who: "jev" | "path" = "jev";
    let at = "";
    if (j.phase === "thinking") {
      const r = anim.placed.get("root");
      if (r) head = [r.x, r.y, r.z];
      at = "root";
    } else if (j.phase === "jev" || j.phase === "hop") {
      const l = j.phase === "jev" ? anim.B : anim.A;
      head = headPosition(l);
      const pr = progress(l);
      at = pr >= 0 ? l.path[Math.min(l.path.length - 1, Math.round(pr))] : "";
      who = j.phase === "jev" ? "jev" : "path";
    }
    const sc = head ? toScreen(head[0], head[1], head[2]) : null;
    moveCard(cards.walker, sc ? sc.x : null, sc ? sc.y : 0, true);
    const key = `${j.phase}|${at}`;
    if (key !== lastKey.current) {
      lastKey.current = key;
      const n = s.nodes[at];
      const p = j.probs.get(at);
      publishWalker(
        j.phase === "idle" || j.phase === "landed"
          ? null
          : j.phase === "thinking"
            ? { who: "jev", label: "reading the question", p: null }
            : { who, label: at === "root" ? "Root" : n?.label ?? at, p: who === "jev" && p !== undefined ? p : null },
      );
    }
    // destination: the question dot the journey landed on
    const d = starData();
    const i = s.focusStar;
    const p = d && i >= 0 ? anim.placed.get(d.nodeIds[d.node[i]]) : undefined;
    if (p) {
      starWorld(i, p, now(), w);
      const ds = toScreen(w[0], w[1], w[2]);
      moveCard(cards.dest, ds ? ds.x : null, ds ? ds.y : 0, true);
    } else moveCard(cards.dest, null, 0);
  });
  return null;
}

export function Journey({ placed }: { placed: Map<string, Placed> }) {
  return (
    <>
      <Trail which="A" placed={placed} />
      <Trail which="B" placed={placed} />
      <Tracker />
    </>
  );
}
