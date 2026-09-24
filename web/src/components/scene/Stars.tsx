"use client";
import { useEffect, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { AdditiveBlending, BufferAttribute, BufferGeometry, Color, ShaderMaterial, type PerspectiveCamera } from "three";
import { useStore } from "@/lib/store";
import { now } from "@/lib/anim";
import { branchColor, rampColor, starAttention } from "@/lib/color";
import { metric, starData } from "@/lib/stars";
import type { Placed } from "@/lib/layout";
import type { Indicator } from "@/lib/types";

// Every displayable question as one star, in a single draw call (docs/07-ui.md).
// Stars twinkle by instability, flare at random as if asked again, and turn slowly around their node.
const vert = /* glsl */ `
  attribute vec3 aLocal; attribute vec3 aColor;
  attribute float aSpin; attribute float aSize; attribute float aTw; attribute float aSeed; attribute float aDim; attribute float aNode;
  uniform float uTime; uniform float uScale; uniform float uPR; uniform float uSel;
  varying vec3 vColor; varying float vAlpha; varying float vHot;
  float hash(float n) { return fract(sin(n) * 43758.5453); }
  void main() {
    float a = aSpin * uTime; float c = cos(a); float s = sin(a);
    vec3 p = position + vec3(c * aLocal.x + s * aLocal.z, aLocal.y, -s * aLocal.x + c * aLocal.z);
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    float tw = 1.0 + aTw * 0.6 * sin(uTime * (1.2 + aSeed * 2.9) + aSeed * 61.0);
    float ph = uTime * 0.28 + aSeed * 17.0;
    float flare = step(hash(aSeed * 977.0 + floor(ph) * 13.1), 0.0003) * sin(3.14159 * fract(ph));
    float sel = step(abs(aNode - uSel), 0.5);
    float size = aSize * (1.0 + flare * 3.5) * (1.0 + 0.35 * sel);
    float px = size * uScale / -mv.z;
    float minPx = 1.5 * uPR;
    // sub-pixel stars keep a minimum size but fade, so distant clusters read as glowing dust
    vAlpha = clamp(px / minPx, 0.06, 1.0) * aDim * tw * (1.0 + flare * 2.5) * (1.0 + 0.7 * sel);
    vHot = flare;
    vColor = aColor;
    gl_PointSize = clamp(px, minPx, (16.0 + 40.0 * flare) * uPR);
    gl_Position = projectionMatrix * mv;
  }`;

const frag = /* glsl */ `
  varying vec3 vColor; varying float vAlpha; varying float vHot;
  void main() {
    vec2 q = gl_PointCoord - 0.5;
    float d = dot(q, q) * 4.0;
    float core = exp(-d * 16.0);
    float halo = exp(-d * 3.2) * 0.38;
    float a = (core + halo) * vAlpha;
    if (a < 0.003) discard;
    vec3 col = mix(vColor, vec3(1.0), core * (0.45 + 0.5 * vHot));
    gl_FragColor = vec4(col, a);
  }`;

const BASE = 0.085;

export function Stars({ placed }: { placed: Map<string, Placed> }) {
  const ready = useStore((s) => s.starsReady);
  const nodes = useStore((s) => s.nodes);
  const indicator = useStore((s) => s.indicator);
  const filters = useStore((s) => s.filters);
  const selected = useStore((s) => s.selected);

  const material = useMemo(
    () =>
      new ShaderMaterial({
        vertexShader: vert,
        fragmentShader: frag,
        transparent: true,
        depthWrite: false,
        blending: AdditiveBlending,
        uniforms: { uTime: { value: 0 }, uScale: { value: 500 }, uPR: { value: 1 }, uSel: { value: -1 } },
      }),
    [],
  );

  // Static geometry: node centers, scaled local offsets, spin, seed.
  const geometry = useMemo(() => {
    const d = starData();
    const g = new BufferGeometry();
    if (!ready || !d || !placed.size) return g;
    const n = d.count;
    const pos = new Float32Array(n * 3);
    const local = new Float32Array(n * 3);
    const spin = new Float32Array(n);
    const seed = new Float32Array(n);
    const nodeIdx = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const p = placed.get(d.nodeIds[d.node[i]]);
      if (!p) continue;
      pos[i * 3] = p.x; pos[i * 3 + 1] = p.y; pos[i * 3 + 2] = p.z;
      local[i * 3] = d.local[i * 3] * p.ball;
      local[i * 3 + 1] = d.local[i * 3 + 1] * p.ball;
      local[i * 3 + 2] = d.local[i * 3 + 2] * p.ball;
      spin[i] = p.spin;
      seed[i] = ((i * 2654435761) % 1000003) / 1000003;
      nodeIdx[i] = d.node[i];
    }
    g.setAttribute("position", new BufferAttribute(pos, 3));
    g.setAttribute("aLocal", new BufferAttribute(local, 3));
    g.setAttribute("aSpin", new BufferAttribute(spin, 1));
    g.setAttribute("aSeed", new BufferAttribute(seed, 1));
    g.setAttribute("aNode", new BufferAttribute(nodeIdx, 1));
    for (const [name, k] of [["aColor", 3], ["aSize", 1], ["aTw", 1], ["aDim", 1]] as const)
      g.setAttribute(name, new BufferAttribute(new Float32Array(n * k), k));
    return g;
  }, [ready, placed]);
  useEffect(() => () => geometry.dispose(), [geometry]);

  // Color, size, twinkle, and filter dimming.
  useEffect(() => {
    const d = starData();
    if (!d || !geometry.getAttribute("aColor")) return;
    const col = geometry.getAttribute("aColor") as BufferAttribute;
    const size = geometry.getAttribute("aSize") as BufferAttribute;
    const tw = geometry.getAttribute("aTw") as BufferAttribute;
    const dim = geometry.getAttribute("aDim") as BufferAttribute;
    const shade = branchShades(nodes);
    const c = new Color();
    const hemiDim = new Color();
    const prim = filters.primitive ? { noul: 0, choice: 1, score: 2 }[filters.primitive] : undefined;
    const nodeMetric = (ind: Indicator, i: number) =>
      ind === "stability" ? metric(d.stability[i]) : ind === "human_gap" ? metric(d.humanGap[i]) : ind === "frame_gap" ? metric(d.frameGap[i])
        : ind === "placement_conf" ? metric(d.placement[i]) : null;
    for (let i = 0; i < d.count; i++) {
      const nid = d.nodeIds[d.node[i]];
      const n = nodes[nid];
      const seed = ((i * 2654435761) % 1000003) / 1000003;
      const tint = shade.get(nid) ?? 0.5;
      branchColor(n?.hemisphere ?? "root", Math.min(1, Math.max(0, tint + (seed - 0.5) * 0.18)), hemiDim);
      let s = BASE * (0.7 + 0.6 * seed);
      if (indicator === "hemisphere" || indicator === "calibration_ece") {
        c.copy(hemiDim);
        if (indicator === "calibration_ece" && d.correct[i] === 2) { c.set("#FF5D86"); s *= 1.6; }
        else if (indicator === "calibration_ece") c.multiplyScalar(0.35);
      } else {
        const a = starAttention(nodeMetric(indicator, i), indicator);
        if (a === null) {
          c.copy(hemiDim).multiplyScalar(0.28);
        } else {
          rampColor(a, c);
          s *= 0.8 + 1.8 * a * a;
        }
      }
      const st = metric(d.stability[i]);
      tw.array[i] = st === null ? 0.12 : Math.min(1, 0.1 + (1 - st) * 1.8);
      col.array[i * 3] = c.r; col.array[i * 3 + 1] = c.g; col.array[i * 3 + 2] = c.b;
      size.array[i] = s;
      const filtered = (prim !== undefined && d.prim[i] !== prim) || (!!(filters.kind || filters.origin) && n?.n_match === 0);
      dim.array[i] = filtered ? 0.12 : 1;
    }
    col.needsUpdate = size.needsUpdate = tw.needsUpdate = dim.needsUpdate = true;
  }, [geometry, nodes, indicator, filters]);

  useEffect(() => {
    const d = starData();
    material.uniforms.uSel.value = d && selected ? d.nodeIds.indexOf(selected) : -1;
  }, [selected, material, ready]);

  useFrame(({ camera, gl }) => {
    const cam = camera as PerspectiveCamera;
    material.uniforms.uTime.value = now();
    material.uniforms.uPR.value = gl.getPixelRatio();
    material.uniforms.uScale.value = gl.domElement.height / (2 * Math.tan(((cam.fov ?? 45) * Math.PI) / 360));
  });

  return <points geometry={geometry} material={material} frustumCulled={false} />;
}

/** node id -> its L1 branch's position (0..1) among the hemisphere's branches. */
export function branchShades(nodes: Record<string, { id: string; depth: number; parent_id: string | null; hemisphere: string; ord: number | null }>) {
  const l1 = Object.values(nodes).filter((n) => n.depth === 2);
  const byHemi = new Map<string, typeof l1>();
  for (const n of l1) byHemi.set(n.parent_id ?? "", [...(byHemi.get(n.parent_id ?? "") ?? []), n]);
  const t = new Map<string, number>();
  for (const list of byHemi.values()) {
    list.sort((a, b) => (a.ord ?? 999) - (b.ord ?? 999) || a.id.localeCompare(b.id));
    list.forEach((n, i) => t.set(n.id, list.length > 1 ? i / (list.length - 1) : 0.5));
  }
  const out = new Map<string, number>();
  for (const n of Object.values(nodes)) {
    const parts = n.id.split(".");
    out.set(n.id, parts.length >= 2 ? t.get(parts.slice(0, 2).join(".")) ?? 0.5 : 0.5);
  }
  return out;
}
