"use client";
import { useEffect, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { AdditiveBlending, BufferAttribute, BufferGeometry, Color, ShaderMaterial } from "three";
import { useStore } from "@/lib/store";
import { anim, now, progress } from "@/lib/anim";
import { edgePoint, HEMI_COLOR, PATH_A_COLOR, PATH_B_COLOR, type Placed } from "@/lib/layout";

const SEG = 24;

const vert = /* glsl */ `
  attribute float aT; attribute float aDepth; attribute float aA; attribute float aB;
  attribute float aBorn; attribute float aDim; attribute float aRel; attribute vec3 aColor;
  varying float vT; varying float vPos; varying float vA; varying float vB; varying float vBorn;
  varying float vDim; varying float vRel; varying vec3 vColor;
  void main() {
    vT = aT; vPos = aDepth - 1.0 + aT; vA = aA; vB = aB; vBorn = aBorn; vDim = aDim; vRel = aRel; vColor = aColor;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }`;

// A light pulse travels along a path: `uProgA`/`uProgB` are positions in depth units
// (k = the k-th node on the path). Behind the head the path stays lit (the trail).
const frag = /* glsl */ `
  uniform float uTime; uniform float uProgA; uniform float uProgB;
  uniform vec3 uColA; uniform vec3 uColB;
  varying float vT; varying float vPos; varying float vA; varying float vB; varying float vBorn;
  varying float vDim; varying float vRel; varying vec3 vColor;
  void main() {
    float grown = clamp((uTime - vBorn) / 0.7, 0.0, 1.0);
    if (vT > grown * 1.05) discard;                         // new branches draw outward from the parent
    float drift = 0.5 + 0.5 * sin(vPos * 9.0 - uTime * 1.4); // slow outward flow on every branch
    vec3 col = vColor * (0.20 + 0.06 * drift + 0.55 * vRel) * vDim;
    float alpha = (0.30 + 0.45 * vRel) * vDim;
    if (vA > 0.5 && uProgA >= 0.0) {
      float trail = step(vPos, uProgA);
      float d = (vPos - uProgA) * 4.5;
      float head = exp(-d * d);
      col += uColA * (trail * 0.85 + head * 3.2);
      alpha = max(alpha, max(trail * 0.9, head));
    }
    if (vB > 0.5 && uProgB >= 0.0) {
      float trail = step(vPos, uProgB);
      float d = (vPos - uProgB) * 4.5;
      float head = exp(-d * d);
      col += uColB * (trail * 0.85 + head * 3.2);
      alpha = max(alpha, max(trail * 0.9, head));
    }
    gl_FragColor = vec4(col, alpha);
  }`;

export function Edges({ placed }: { placed: Map<string, Placed> }) {
  const nodes = useStore((s) => s.nodes);
  const born = useStore((s) => s.born);
  const pathA = useStore((s) => s.pathA);
  const pathB = useStore((s) => s.pathB);
  const relevance = useStore((s) => s.relevance);
  const filtersActive = useStore((s) => !!(s.filters.kind || s.filters.primitive || s.filters.origin));

  const material = useMemo(
    () =>
      new ShaderMaterial({
        vertexShader: vert,
        fragmentShader: frag,
        transparent: true,
        depthWrite: false,
        blending: AdditiveBlending,
        uniforms: {
          uTime: { value: 0 },
          uProgA: { value: -1 },
          uProgB: { value: -1 },
          uColA: { value: new Color(PATH_A_COLOR) },
          uColB: { value: new Color(PATH_B_COLOR) },
        },
      }),
    [],
  );

  const { geometry, ranges } = useMemo(() => {
    const edges: [Placed, Placed, string][] = [];
    for (const [id, c] of placed) {
      const pid = nodes[id]?.parent_id;
      const p = pid ? placed.get(pid) : undefined;
      if (p) edges.push([p, c, id]);
    }
    const nv = edges.length * SEG * 2;
    const pos = new Float32Array(nv * 3);
    const col = new Float32Array(nv * 3);
    const aT = new Float32Array(nv);
    const aDepth = new Float32Array(nv);
    const aBorn = new Float32Array(nv);
    const ranges = new Map<string, [number, number]>();
    const pt: [number, number, number] = [0, 0, 0];
    const c = new Color();
    let v = 0;
    for (const [p, ch, id] of edges) {
      const start = v;
      c.set(HEMI_COLOR[nodes[id].hemisphere]);
      const b = (born[id] ?? 0) / 1000;
      for (let s = 0; s < SEG; s++) {
        for (const t of [s / SEG, (s + 1) / SEG]) {
          edgePoint(p, ch, t, pt);
          pos.set(pt, v * 3);
          col.set([c.r, c.g, c.b], v * 3);
          aT[v] = t;
          aDepth[v] = ch.depth;
          aBorn[v] = b;
          v++;
        }
      }
      ranges.set(id, [start, v - start]);
    }
    const g = new BufferGeometry();
    g.setAttribute("position", new BufferAttribute(pos, 3));
    g.setAttribute("aColor", new BufferAttribute(col, 3));
    g.setAttribute("aT", new BufferAttribute(aT, 1));
    g.setAttribute("aDepth", new BufferAttribute(aDepth, 1));
    g.setAttribute("aBorn", new BufferAttribute(aBorn, 1));
    for (const name of ["aA", "aB", "aDim", "aRel"]) g.setAttribute(name, new BufferAttribute(new Float32Array(nv), 1));
    return { geometry: g, ranges };
  }, [placed, nodes, born]);

  useEffect(() => () => geometry.dispose(), [geometry]);

  // Path membership, relevance and filter dimming live in per-vertex attributes.
  useEffect(() => {
    const A = geometry.getAttribute("aA") as BufferAttribute;
    const B = geometry.getAttribute("aB") as BufferAttribute;
    const D = geometry.getAttribute("aDim") as BufferAttribute;
    const R = geometry.getAttribute("aRel") as BufferAttribute;
    const onA = new Set(pathA.slice(1));
    const onB = new Set(pathB.slice(1));
    for (const [id, [start, count]] of ranges) {
      const n = nodes[id];
      const dim = filtersActive && n && n.n_match !== undefined && n.n_match === 0 ? 0.25 : 1;
      const a = onA.has(id) ? 1 : 0;
      const b = onB.has(id) ? 1 : 0;
      const r = Math.min(1, relevance[id] ?? 0);
      for (let i = start; i < start + count; i++) {
        A.array[i] = a;
        B.array[i] = b;
        D.array[i] = dim;
        R.array[i] = r;
      }
    }
    A.needsUpdate = B.needsUpdate = D.needsUpdate = R.needsUpdate = true;
  }, [geometry, ranges, pathA, pathB, nodes, filtersActive, relevance]);

  useFrame(() => {
    const t = now();
    material.uniforms.uTime.value = t;
    material.uniforms.uProgA.value = progress(anim.A, t);
    material.uniforms.uProgB.value = progress(anim.B, t);
  });

  return <lineSegments geometry={geometry} material={material} frustumCulled={false} />;
}
