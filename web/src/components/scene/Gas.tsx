"use client";
import { useEffect, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { NormalBlending, Color, InstancedBufferAttribute, InstancedBufferGeometry, PlaneGeometry, ShaderMaterial } from "three";
import { useStore } from "@/lib/store";
import { now } from "@/lib/anim";
import { attention, branchColor, rampColor } from "@/lib/color";
import { edgePoint, type Placed } from "@/lib/layout";
import { branchShades } from "./Stars";

// Clouds (docs/07-ui.md): slowly drifting cumulus puffs around every node's ball and along the big branches,
// in the hemisphere's color, or by the node's indicator, so where Jev is jagged shows as weather from far away.
const vert = /* glsl */ `
  attribute vec3 aPos; attribute vec3 aColor; attribute float aSize; attribute float aAlpha; attribute float aSeed;
  uniform float uTime;
  varying vec2 vUv; varying vec3 vColor; varying float vAlpha; varying float vSeed;
  void main() {
    vUv = uv; vColor = aColor; vAlpha = aAlpha; vSeed = aSeed;
    vec3 drift = 0.35 * aSize * vec3(sin(uTime * 0.05 + aSeed * 40.0), sin(uTime * 0.04 + aSeed * 23.0), cos(uTime * 0.045 + aSeed * 31.0));
    vec4 mv = modelViewMatrix * vec4(aPos + drift * 0.3, 1.0);
    float breathe = 1.0 + 0.08 * sin(uTime * 0.3 + aSeed * 9.0);
    mv.xy += position.xy * aSize * breathe; // camera-facing quad
    // fade puffs as the camera enters them, so you never fly into a flat wall of fog
    float dist = -mv.z;
    vAlpha *= smoothstep(aSize * 0.9, aSize * 3.2, dist);
    gl_Position = projectionMatrix * mv;
  }`;

const frag = /* glsl */ `
  uniform float uTime;
  varying vec2 vUv; varying vec3 vColor; varying float vAlpha; varying float vSeed;
  float h(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float n(vec2 p) { vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
  float fbm(vec2 p) { float v = 0.0; float a = 0.5; for (int i = 0; i < 4; i++) { v += a * n(p); p *= 2.03; a *= 0.5; } return v; }
  void main() {
    vec2 q = vUv - 0.5;
    float r = length(q) * 2.0;
    float fall = exp(-r * r * 3.2);
    // cumulus: billowy fbm edges inside a soft falloff (the dither pass turns it into stipple)
    float billow = fbm(q * 2.6 + vSeed * 17.0 + vec2(uTime * 0.01, -uTime * 0.008));
    float a = smoothstep(0.28, 0.72, fall * 0.9 + billow * 0.55 - 0.18) * vAlpha;
    if (a < 0.002) discard;
    gl_FragColor = vec4(vColor, a);
  }`;

/** mulberry32: a small seeded generator, so the gas looks the same on every load. */
function rnd(seed: number) {
  let a = seed | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function hashStr(id: string) {
  let h = 2166136261;
  for (let i = 0; i < id.length; i++) h = Math.imul(h ^ id.charCodeAt(i), 16777619);
  return h >>> 0;
}

interface Puff { x: number; y: number; z: number; size: number; alpha: number; seed: number; node: string }

export function Gas({ placed }: { placed: Map<string, Placed> }) {
  const nodes = useStore((s) => s.nodes);
  const indicator = useStore((s) => s.indicator);

  const material = useMemo(
    () => new ShaderMaterial({ vertexShader: vert, fragmentShader: frag, transparent: true, depthWrite: false, blending: NormalBlending, uniforms: { uTime: { value: 0 } } }),
    [],
  );

  const puffs = useMemo(() => {
    const out: Puff[] = [];
    const pt: [number, number, number] = [0, 0, 0];
    for (const p of placed.values()) {
      const n = nodes[p.id];
      if (!n || p.depth === 0) continue;
      const r = rnd(hashStr(p.id));
      // around the node's own ball
      const k = Math.min(10, 2 + Math.round(p.ball * 1.8));
      for (let i = 0; i < k; i++) {
        const u = r() * 2 - 1, th = r() * Math.PI * 2, rad = p.ball * 0.8 * Math.cbrt(r());
        const s = Math.sqrt(1 - u * u);
        out.push({ x: p.x + rad * s * Math.cos(th), y: p.y + rad * u, z: p.z + rad * s * Math.sin(th), size: p.ball * (1.4 + r() * 1.4) + 0.8, alpha: 0.1 + 0.06 * r(), seed: r(), node: p.id });
      }
      // along the branch from the parent, for the big arms (hemisphere → L1 → L2)
      const parent = n.parent_id ? placed.get(n.parent_id) : undefined;
      if (parent && p.depth <= 3) {
        const m = p.depth === 1 ? 9 : p.depth === 2 ? 5 : 2;
        for (let i = 0; i < m; i++) {
          edgePoint(parent, p, 0.15 + 0.75 * ((i + r()) / m), pt);
          const scale = p.depth === 1 ? 7 : p.depth === 2 ? 4 : 2.2;
          out.push({ x: pt[0] + (r() - 0.5) * scale, y: pt[1] + (r() - 0.5) * scale, z: pt[2] + (r() - 0.5) * scale, size: scale * (1.6 + r()), alpha: p.depth === 1 ? 0.07 : 0.05, seed: r(), node: p.id });
        }
      }
    }
    // big faint clouds over each hemisphere's whole lobe, so the three read as nebulae from far away
    for (const h of ["world", "self", "machine"]) {
      const hp = placed.get(h);
      if (!hp) continue;
      const members = [...placed.values()].filter((p) => p.id.startsWith(h + "."));
      if (!members.length) continue;
      const c = [0, 0, 0];
      for (const p of members) { c[0] += p.x / members.length; c[1] += p.y / members.length; c[2] += p.z / members.length; }
      let spread = 0;
      for (const p of members) spread += Math.hypot(p.x - c[0], p.y - c[1], p.z - c[2]) / members.length;
      const r = rnd(hashStr(h + ":lobe"));
      for (let i = 0; i < 14; i++) {
        const u = r() * 2 - 1, th = r() * Math.PI * 2, rad = spread * 0.9 * Math.cbrt(r());
        const s = Math.sqrt(1 - u * u);
        out.push({ x: c[0] + rad * s * Math.cos(th), y: c[1] + rad * u, z: c[2] + rad * s * Math.sin(th), size: spread * (0.6 + 0.4 * r()), alpha: 0.04, seed: r(), node: h });
      }
    }
    return out;
  }, [placed, nodes]);

  const geometry = useMemo(() => {
    const g = new InstancedBufferGeometry();
    const plane = new PlaneGeometry(2, 2);
    g.index = plane.index;
    g.setAttribute("position", plane.getAttribute("position"));
    g.setAttribute("uv", plane.getAttribute("uv"));
    const n = puffs.length;
    const pos = new Float32Array(n * 3), size = new Float32Array(n), alpha = new Float32Array(n), seed = new Float32Array(n);
    puffs.forEach((p, i) => {
      pos.set([p.x, p.y, p.z], i * 3);
      size[i] = p.size;
      alpha[i] = p.alpha;
      seed[i] = p.seed;
    });
    g.setAttribute("aPos", new InstancedBufferAttribute(pos, 3));
    g.setAttribute("aSize", new InstancedBufferAttribute(size, 1));
    g.setAttribute("aAlpha", new InstancedBufferAttribute(alpha, 1));
    g.setAttribute("aSeed", new InstancedBufferAttribute(seed, 1));
    g.setAttribute("aColor", new InstancedBufferAttribute(new Float32Array(n * 3), 3));
    g.instanceCount = n;
    return g;
  }, [puffs]);
  useEffect(() => () => geometry.dispose(), [geometry]);

  useEffect(() => {
    const col = geometry.getAttribute("aColor") as InstancedBufferAttribute;
    const shade = branchShades(nodes);
    const c = new Color();
    const white = new Color("#FEFEFE");
    puffs.forEach((p, i) => {
      const n = nodes[p.node];
      if (!n) return;
      const a = indicator === "hemisphere" ? null : attention(n, indicator);
      if (a === null) {
        if (indicator === "hemisphere") branchColor(n.hemisphere, shade.get(n.id) ?? 0.5, c);
        else c.set("#FEFEFE"); // no data: plain white cloud
      } else rampColor(a, c);
      c.lerp(white, 0.55); // a pale halo: the particles are the cloud, the gas only softens it
      col.setXYZ(i, c.r, c.g, c.b);
    });
    col.needsUpdate = true;
  }, [geometry, puffs, nodes, indicator]);

  useFrame(() => {
    material.uniforms.uTime.value = now();
  });

  return <mesh geometry={geometry} material={material} frustumCulled={false} renderOrder={-1} />;
}
