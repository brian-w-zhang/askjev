"use client";
import { useEffect, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { BufferAttribute, BufferGeometry, Color, DataTexture, FloatType, NearestFilter, NormalBlending, RedFormat, ShaderMaterial, type PerspectiveCamera, type Vector3 } from "three";
import { useStore } from "@/lib/store";
import { anim, BURST, now } from "@/lib/anim";
import { heat, HOT_SLOTS } from "@/lib/heat";
import { branchColor, rampColor, starAttention } from "@/lib/color";
import { JEV_COLOR, THEMES } from "@/lib/theme";
import { metric, starData } from "@/lib/stars";
import { starLocal, type Placed, type V3 } from "@/lib/layout";
import type { Indicator } from "@/lib/types";

// Every displayable question as one colored particle, in a single draw call (docs/07-ui.md).
// Dots twinkle by instability, flare magenta at random as if asked again, and turn slowly around their node.
const HEAT_TEX = 4096; // node slots in the heat texture (the tree has ~1,700 nodes)

const vert = /* glsl */ `
  attribute vec3 aLocal; attribute vec3 aColor; attribute float aDelay;
  attribute float aSpin; attribute float aSize; attribute float aTw; attribute float aSeed; attribute float aDim; attribute float aNode;
  uniform float uTime; uniform float uScale; uniform float uPR; uniform float uSel; uniform float uSelK; uniform float uPrev; uniform float uPrevK; uniform float uFocus; uniform float uIntro0; uniform float uForm;
  // live search: the current results' dots (index + level, eased on the CPU), and Jev's pick after the pause
  uniform float uHotI[${HOT_SLOTS}]; uniform float uHotK[${HOT_SLOTS}]; uniform float uJevI; uniform float uJevK;
  uniform vec3 uInk; uniform vec3 uJev;
  uniform sampler2D uHeat; uniform float uLevel; // per-node heat (by aNode), and how much the search owns the map
  varying vec3 vColor; varying float vAlpha; varying float vHot;
  float hash(float n) { return fract(sin(n) * 43758.5453); }
  void main() {
    // the opening: when its node lands, each star bursts out of it like a firework spark, overshoots its
    // place a little and settles, with a pink flash at the moment of the burst
    float k = clamp((uTime - uIntro0 - aDelay) / uForm, 0.0, 1.0);
    if (k <= 0.0) { gl_PointSize = 0.0; gl_Position = vec4(2.0, 2.0, 2.0, 1.0); return; }
    float x = k - 1.0;
    float burst = 1.0 + 2.2 * x * x * x + 1.2 * x * x; // ease out with a small overshoot
    float bang = exp(-k * 9.0) * step(uTime - uIntro0, 30.0);
    float a = aSpin * uTime; float c = cos(a); float s = sin(a);
    vec3 p = position + vec3(c * aLocal.x + s * aLocal.z, aLocal.y, -s * aLocal.x + c * aLocal.z) * burst;
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    float tw = 1.0 + aTw * 0.6 * sin(uTime * (1.2 + aSeed * 2.9) + aSeed * 61.0);
    float ph = uTime * 0.28 + aSeed * 17.0;
    float flare = step(hash(aSeed * 977.0 + floor(ph) * 13.1), 0.0003) * sin(3.14159 * fract(ph));
    // the selected topic's stars ease up (and the previous one's ease back), never popping
    float sel = step(abs(aNode - uSel), 0.5) * uSelK + step(abs(aNode - uPrev), 0.5) * uPrevK;
    float vid = float(gl_VertexID);
    float hot = 0.0;
    for (int j = 0; j < ${HOT_SLOTS}; j++) hot = max(hot, step(abs(vid - uHotI[j]), 0.5) * uHotK[j]);
    float jev = step(abs(vid - uJevI), 0.5) * uJevK;
    float nh = texture2D(uHeat, vec2((aNode + 0.5) / ${HEAT_TEX}.0, 0.5)).r;
    float context = mix(1.0, 0.15 + 0.85 * min(1.0, nh * 2.0), uLevel); // stars outside the heat fade back
    float size = aSize * (1.0 + flare * 3.5 + bang * 2.5) * (1.0 + 0.35 * sel) * (1.0 + 2.2 * max(hot, jev)) * (0.55 + 0.45 * context);
    float px = size * uScale / -mv.z;
    float minPx = max(1.0, 1.5 * uPR); // never below one cell (the canvas renders one pixel per dither cell)
    // Stars smaller than one cell are drawn by chance instead of faintly: a star covering a third of a
    // cell shows up a third of the time (fixed per star, so nothing flickers). Distant clusters keep the
    // same brightness as stipple, and the GPU skips most of their pixels.
    float cover = px / minPx;
    if (cover < 1.0 && fract(aSeed * 7919.0) > max(cover, 0.03) && flare < 0.01 && bang < 0.05 && sel < 0.01 && hot + jev < 0.01) {
      gl_PointSize = 0.0;
      gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
      return;
    }
    // aerial perspective: stars well behind what you're looking at fade a little, so depth reads
    float haze = 1.0 - 0.5 * smoothstep(uFocus * 1.15, uFocus * 3.0, -mv.z);
    vAlpha = mix(aDim * tw * haze * (1.0 + flare * 2.5) * (1.0 + 0.7 * sel) * context, 1.0, max(hot, jev)) * smoothstep(0.0, 0.05, k);
    vHot = max(flare, bang * 0.9);
    vColor = mix(mix(aColor, uInk, 0.7 * hot), uJev, jev);
    gl_PointSize = clamp(px, minPx + 3.0 * max(hot, jev) * uPR, (7.5 + 14.0 * flare + 4.0 * max(hot, jev)) * uPR);
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

function heatTexture() {
  const t = new DataTexture(new Float32Array(HEAT_TEX), HEAT_TEX, 1, RedFormat, FloatType);
  t.magFilter = t.minFilter = NearestFilter;
  t.needsUpdate = true;
  return t;
}

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
        uniforms: { uTime: { value: 0 }, uScale: { value: 500 }, uPR: { value: 1 }, uSel: { value: -1 }, uSelK: { value: 0 }, uPrev: { value: -1 }, uPrevK: { value: 0 }, uFocus: { value: 100 }, uIntro0: { value: 1e9 }, uForm: { value: BURST },
          uHotI: { value: new Array(HOT_SLOTS).fill(-1) }, uHotK: { value: new Array(HOT_SLOTS).fill(0) }, uJevI: { value: -1 }, uJevK: { value: 0 },
          uInk: { value: new Color(THEMES.light.ink) }, uJev: { value: new Color(JEV_COLOR) },
          uHeat: { value: heatTexture() }, uLevel: { value: 0 } },
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
      delay[i] = (anim.intro.arrive.get(d.nodeIds[d.node[i]]) ?? 0.25 + (tree[d.nodeIds[d.node[i]]]?.depth ?? 1) * 0.6) + seed[i] * 0.08;
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
    const u = material.uniforms;
    heat.slots.forEach((sl, j) => { u.uHotI.value[j] = sl.star; u.uHotK.value[j] = sl.k; });
    u.uJevI.value = heat.jev.star;
    u.uLevel.value = heat.level;
    const d = starData();
    const tex = u.uHeat.value as DataTexture;
    if (d && tex.userData.seen !== heat.version) {
      tex.userData.seen = heat.version;
      const px = tex.image.data as Float32Array;
      for (let i = 0; i < d.nodeIds.length && i < HEAT_TEX; i++) px[i] = heat.node.get(d.nodeIds[i]) ?? 0;
      tex.needsUpdate = true;
    }
    u.uJevK.value = heat.jev.k;
    u.uInk.value.set(THEMES[useStore.getState().theme].ink);
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
