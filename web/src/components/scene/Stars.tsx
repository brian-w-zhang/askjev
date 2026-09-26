"use client";
import { useEffect, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { BufferAttribute, BufferGeometry, Color, NormalBlending, ShaderMaterial, type PerspectiveCamera, type Vector3 } from "three";
import { useStore } from "@/lib/store";
import { anim, INTRO_FORM, introDelay, now } from "@/lib/anim";
import { branchColor, rampColor, starAttention } from "@/lib/color";
import { THEMES } from "@/lib/theme";
import { metric, starData } from "@/lib/stars";
import { starLocal, type Placed, type V3 } from "@/lib/layout";
import type { Indicator } from "@/lib/types";

// Every displayable question as one colored particle, in a single draw call (docs/07-ui.md).
// Dots twinkle by instability, flare magenta at random as if asked again, and turn slowly around their node.
const vert = /* glsl */ `
  attribute vec3 aLocal; attribute vec3 aColor; attribute float aDelay;
  attribute float aSpin; attribute float aSize; attribute float aTw; attribute float aSeed; attribute float aDim; attribute float aNode;
  uniform float uTime; uniform float uScale; uniform float uPR; uniform float uSel; uniform float uSelK; uniform float uPrev; uniform float uPrevK; uniform float uFocus; uniform float uIntro0; uniform float uForm;
  varying vec3 vColor; varying float vAlpha; varying float vHot;
  float hash(float n) { return fract(sin(n) * 43758.5453); }
  void main() {
    // the opening: each star spirals out from the center to its place, a tree level at a time
    float k = clamp((uTime - uIntro0 - aDelay) / uForm, 0.0, 1.0);
    if (k <= 0.0) { gl_PointSize = 0.0; gl_Position = vec4(2.0, 2.0, 2.0, 1.0); return; }
    float ek = 1.0 - pow(1.0 - k, 3.0);
    float sw = (1.0 - ek) * 2.4;
    vec3 center = vec3(cos(sw) * position.x + sin(sw) * position.z, position.y, -sin(sw) * position.x + cos(sw) * position.z) * ek;
    float a = aSpin * uTime; float c = cos(a); float s = sin(a);
    vec3 p = center + vec3(c * aLocal.x + s * aLocal.z, aLocal.y, -s * aLocal.x + c * aLocal.z) * mix(0.15, 1.0, ek);
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    float tw = 1.0 + aTw * 0.6 * sin(uTime * (1.2 + aSeed * 2.9) + aSeed * 61.0);
    float ph = uTime * 0.28 + aSeed * 17.0;
    float flare = step(hash(aSeed * 977.0 + floor(ph) * 13.1), 0.0003) * sin(3.14159 * fract(ph));
    // the selected topic's stars ease up (and the previous one's ease back), never popping
    float sel = step(abs(aNode - uSel), 0.5) * uSelK + step(abs(aNode - uPrev), 0.5) * uPrevK;
    float size = aSize * (1.0 + flare * 3.5) * (1.0 + 0.35 * sel);
    float px = size * uScale / -mv.z;
    float minPx = max(1.0, 1.5 * uPR); // never below one cell (the canvas renders one pixel per dither cell)
    // Stars smaller than one cell are drawn by chance instead of faintly: a star covering a third of a
    // cell shows up a third of the time (fixed per star, so nothing flickers). Distant clusters keep the
    // same brightness as stipple, and the GPU skips most of their pixels.
    float cover = px / minPx;
    if (cover < 1.0 && fract(aSeed * 7919.0) > max(cover, 0.03) && flare < 0.01 && sel < 0.01) {
      gl_PointSize = 0.0;
      gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
      return;
    }
    // aerial perspective: stars well behind what you're looking at fade a little, so depth reads
    float haze = 1.0 - 0.5 * smoothstep(uFocus * 1.15, uFocus * 3.0, -mv.z);
    vAlpha = aDim * tw * haze * (1.0 + flare * 2.5) * (1.0 + 0.7 * sel) * smoothstep(0.0, 0.3, k);
    vHot = flare;
    vColor = aColor;
    gl_PointSize = clamp(px, minPx, (7.5 + 14.0 * flare) * uPR);
    gl_Position = projectionMatrix * mv;
  }`;

// ink stipple: a hard round dot with a one-pixel soft edge (the dither pass does the rest)
const frag = /* glsl */ `
  varying vec3 vColor; varying float vAlpha; varying float vHot;
  void main() {
    vec2 q = gl_PointCoord - 0.5;
    float r = length(q) * 2.0;
    float a = (1.0 - smoothstep(0.72, 1.0, r)) * vAlpha;
    if (a < 0.02) discard;
    gl_FragColor = vec4(mix(vColor, vec3(0.83, 0.357, 0.714), vHot), min(1.0, a));
  }`;

const BASE = 0.085;

export function Stars({ placed }: { placed: Map<string, Placed> }) {
  const ready = useStore((s) => s.starsReady);
  const nodes = useStore((s) => s.nodes);
  const indicator = useStore((s) => s.indicator);
  const filters = useStore((s) => s.filters);
  const selected = useStore((s) => s.selected);
  const theme = useStore((s) => s.theme);

  const material = useMemo(
    () =>
      new ShaderMaterial({
        vertexShader: vert,
        fragmentShader: frag,
        transparent: true,
        depthWrite: false,
        blending: NormalBlending,
        uniforms: { uTime: { value: 0 }, uScale: { value: 500 }, uPR: { value: 1 }, uSel: { value: -1 }, uSelK: { value: 0 }, uPrev: { value: -1 }, uPrevK: { value: 0 }, uFocus: { value: 100 }, uIntro0: { value: 1e9 }, uForm: { value: INTRO_FORM } },
      }),
    [],
  );

  // Static geometry: node centers, shaped local offsets, spin, seed.
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
    const delay = new Float32Array(n);
    const tree = useStore.getState().nodes;
    const l: V3 = [0, 0, 0];
    for (let i = 0; i < n; i++) {
      const p = placed.get(d.nodeIds[d.node[i]]);
      if (!p) continue;
      pos[i * 3] = p.x; pos[i * 3 + 1] = p.y; pos[i * 3 + 2] = p.z;
      starLocal(d.local[i * 3], d.local[i * 3 + 1], d.local[i * 3 + 2], p, l);
      local[i * 3] = l[0]; local[i * 3 + 1] = l[1]; local[i * 3 + 2] = l[2];
      spin[i] = p.spin;
      seed[i] = ((i * 2654435761) % 1000003) / 1000003;
      nodeIdx[i] = d.node[i];
      delay[i] = introDelay(tree[d.nodeIds[d.node[i]]]?.depth ?? 1) + seed[i] * 0.35;
    }
    g.setAttribute("position", new BufferAttribute(pos, 3));
    g.setAttribute("aLocal", new BufferAttribute(local, 3));
    g.setAttribute("aSpin", new BufferAttribute(spin, 1));
    g.setAttribute("aSeed", new BufferAttribute(seed, 1));
    g.setAttribute("aNode", new BufferAttribute(nodeIdx, 1));
    g.setAttribute("aDelay", new BufferAttribute(delay, 1));
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
    const c = new Color();
    const shade = branchShades(nodes);
    const T = THEMES[theme];
    const prim = filters.primitive ? { noul: 0, choice: 1, score: 2 }[filters.primitive] : undefined;
    const nodeMetric = (ind: Indicator, i: number) =>
      ind === "stability" ? metric(d.stability[i]) : ind === "human_gap" ? metric(d.humanGap[i]) : ind === "frame_gap" ? metric(d.frameGap[i])
        : ind === "placement_conf" ? metric(d.placement[i]) : null;
    for (let i = 0; i < d.count; i++) {
      const nid = d.nodeIds[d.node[i]];
      const n = nodes[nid];
      const seed = ((i * 2654435761) % 1000003) / 1000003;
      let s = BASE * (0.7 + 0.6 * seed);
      if (indicator === "hemisphere") {
        // the questions themselves are the cloud: colored particles, like the typesafe.ai header
        branchColor(n?.hemisphere ?? "root", Math.min(1, Math.max(0, (shade.get(nid) ?? 0.5) + (seed - 0.5) * 0.3)), theme, c);
      } else if (indicator === "calibration_ece") {
        if (d.correct[i] === 2) { c.set("#D45BB6"); s *= 1.6; }
        else c.set(d.correct[i] === 1 ? T.hemi.world : T.nodata);
      } else {
        const a = starAttention(nodeMetric(indicator, i), indicator);
        if (a === null) {
          c.set(T.nodata);
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
  }, [geometry, nodes, indicator, filters, theme]);

  useEffect(() => {
    const d = starData();
    const u = material.uniforms;
    const next = d && selected ? d.nodeIds.indexOf(selected) : -1;
    if (next === u.uSel.value) return;
    u.uPrev.value = u.uSel.value;
    u.uPrevK.value = u.uSelK.value;
    u.uSel.value = next;
    u.uSelK.value = 0;
  }, [selected, material, ready]);

  useFrame(({ camera, gl, controls }, dt) => {
    const k = 1 - Math.exp(-dt * 5);
    material.uniforms.uSelK.value += (1 - material.uniforms.uSelK.value) * k;
    material.uniforms.uPrevK.value -= material.uniforms.uPrevK.value * k;
    const cam = camera as PerspectiveCamera;
    const target = (controls as unknown as { target?: Vector3 } | null)?.target;
    material.uniforms.uFocus.value = target ? cam.position.distanceTo(target) : 100;
    material.uniforms.uTime.value = now();
    material.uniforms.uIntro0.value = Number.isFinite(anim.intro.t0) ? anim.intro.t0 : 1e9;
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
