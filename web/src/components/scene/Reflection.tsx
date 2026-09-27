"use client";
import { useEffect, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { BufferAttribute, Color, InstancedBufferAttribute, InstancedBufferGeometry, NormalBlending, ShaderMaterial, type PerspectiveCamera } from "three";
import { useStore } from "@/lib/store";
import { anim, now } from "@/lib/anim";
import { THEMES } from "@/lib/theme";
import { starData } from "@/lib/stars";
import { starLocal, type Placed, type V3 } from "@/lib/layout";

// The nebula's reflection in the water (docs/07-ui.md, Look): a thinned copy of the question dots, mirrored in the
// sea's surface and drawn as short vertical streaks that sway with the ripples, like harbor lights on a calm
// evening. It fades with depth below the surface. At night the colors glow a little (bioluminescence), by day
// they sink into the water's tint.
const EVERY = 18; // one reflected column per this many questions: the columns overlap, so fewer read as more

const vert = /* glsl */ `
  attribute vec3 aPos; attribute vec3 aLocal; attribute vec3 aColor; attribute float aSpin; attribute float aSeed;
  uniform float uTime; uniform float uSea; uniform float uScale; uniform float uPR; uniform float uAlpha; uniform float uGlow;
  varying vec3 vColor; varying float vA; varying float vSeed; varying vec2 vUv;
  void main() {
    vUv = position.xy + 0.5;
    float a = aSpin * uTime; float c = cos(a); float s = sin(a);
    vec3 p = aPos + vec3(c * aLocal.x + s * aLocal.z, aLocal.y, -s * aLocal.x + c * aLocal.z);
    float h = p.y - uSea; // height above the water; its image sits as far below
    if (h <= 0.0 || uAlpha <= 0.0) { gl_Position = vec4(2.0, 2.0, 2.0, 1.0); return; }
    vec3 m = vec3(p.x, uSea - h, p.z);
    // ripples: the image sways sideways, more the deeper it is, in slow waves that travel across the water
    float sway = sin(m.z * 0.021 + m.x * 0.004 + uTime * 0.9 + aSeed * 2.0) + 0.5 * sin(m.z * 0.057 - uTime * 1.7);
    m.x += sway * (0.8 + h * 0.035);
    // a light's image on rippled water is a tall, thin column (the higher the light, the longer), drawn as a
    // camera-facing quad and broken into wavelet dashes in the fragment shader
    vec4 mv = modelViewMatrix * vec4(m, 1.0);
    float perPx = -mv.z / uScale; // world units per screen pixel here
    float w = max(0.22 + h * 0.0018, 2.0 * perPx);
    float len = max(w * (9.0 + h * 0.04), 12.0 * perPx);
    mv.xy += position.xy * vec2(w, len);
    float shimmer = 0.75 + 0.25 * sin(uTime * (1.5 + aSeed * 2.5) + aSeed * 40.0);
    // swell lines: horizontal bands of rougher water where the reflection breaks up, drifting toward the viewer
    // Fresnel: water barely reflects looking straight down (~2%) and turns mirror-like only at grazing angles,
    // so from above the reflection all but vanishes and it shows as a glimmer when you look across the water
    float cosT = abs(normalize(m - cameraPosition).y);
    float fres = 0.02 + 0.98 * pow(1.0 - cosT, 5.0);
    float band = smoothstep(-0.2, 0.6, sin(m.z * 0.09 + m.x * 0.01 - uTime * 0.6) + 0.6 * sin(m.z * 0.23 + uTime * 0.4));
    vA = uAlpha * exp(-h / 300.0) * shimmer * mix(0.25, 1.0, band) * fres * (0.22 - 0.05 * uGlow);
    vColor = aColor;
    vSeed = aSeed;
    gl_Position = projectionMatrix * mv;
  }`;

// a column of short horizontal dashes, each wavelet shifted sideways a little and flickering, the way ripples
// break a light's reflection into a ladder of glints
const frag = /* glsl */ `
  uniform vec3 uWater; uniform float uGlow; uniform float uTime;
  varying vec3 vColor; varying float vA; varying float vSeed; varying vec2 vUv;
  float h1(float n) { return fract(sin(n) * 43758.5453); }
  void main() {
    vec2 q = vUv - 0.5;
    float rows = 16.0;
    float k = floor((q.y + 0.5) * rows);
    float fy = fract((q.y + 0.5) * rows) - 0.5;
    float t = floor(uTime * 3.0 + vSeed * 20.0);
    float jit = (h1(k * 7.1 + vSeed * 91.0 + t * 0.37) - 0.5) * 0.5;
    float wide = 0.2 + 0.3 * h1(k * 3.3 + vSeed * 17.0 + t);
    float dash = (1.0 - smoothstep(wide, wide + 0.12, abs(q.x - jit))) * (1.0 - smoothstep(0.1, 0.4, abs(fy)));
    dash *= step(0.3, h1(k * 5.7 + vSeed * 33.0 + t * 0.61)); // some wavelets catch no light at all
    float ends = smoothstep(0.5, 0.2, abs(q.y)); // the column fades out at both ends
    float a = dash * ends * vA;
    if (a < 0.02) discard;
    gl_FragColor = vec4(mix(mix(vColor, uWater, 0.2), vColor * 1.2, uGlow), a);
  }`;

export function Reflection({ placed }: { placed: Map<string, Placed> }) {
  const ready = useStore((s) => s.starsReady);
  const theme = useStore((s) => s.theme);
  const material = useMemo(
    () =>
      new ShaderMaterial({
        vertexShader: vert,
        fragmentShader: frag,
        transparent: true,
        depthWrite: false,
        blending: NormalBlending,
        uniforms: {
          uTime: { value: 0 }, uSea: { value: -300 }, uScale: { value: 500 }, uPR: { value: 1 }, uAlpha: { value: 0 },
          uGlow: { value: 0 }, uWater: { value: new Color() },
        },
      }),
    [],
  );

  const geometry = useMemo(() => {
    const d = starData();
    const g = new InstancedBufferGeometry();
    g.setAttribute("position", new BufferAttribute(new Float32Array([-0.5, -0.5, 0, 0.5, -0.5, 0, 0.5, 0.5, 0, -0.5, 0.5, 0]), 3));
    g.setIndex([0, 1, 2, 0, 2, 3]);
    if (!ready || !d || !placed.size) { g.instanceCount = 0; return g; }
    const n = Math.ceil(d.count / EVERY);
    const pos = new Float32Array(n * 3), local = new Float32Array(n * 3), col = new Float32Array(n * 3);
    const spin = new Float32Array(n), seed = new Float32Array(n);
    const nodes = useStore.getState().nodes;
    const T = THEMES[useStore.getState().theme];
    const c = new Color();
    const l: V3 = [0, 0, 0];
    let k = 0;
    for (let i = 0; i < d.count; i += EVERY, k++) {
      const id = d.nodeIds[d.node[i]];
      const p = placed.get(id);
      if (!p) continue;
      pos.set([p.x, p.y, p.z], k * 3);
      starLocal(d.local[i * 3], d.local[i * 3 + 1], d.local[i * 3 + 2], p, l);
      local.set(l, k * 3);
      c.set(T.hemi[nodes[id]?.hemisphere ?? "world"] ?? T.ink);
      col.set([c.r, c.g, c.b], k * 3);
      spin[k] = p.spin;
      seed[k] = ((i * 2654435761) % 1000003) / 1000003;
    }
    g.setAttribute("aPos", new InstancedBufferAttribute(pos, 3));
    g.setAttribute("aLocal", new InstancedBufferAttribute(local, 3));
    g.setAttribute("aColor", new InstancedBufferAttribute(col, 3));
    g.setAttribute("aSpin", new InstancedBufferAttribute(spin, 1));
    g.setAttribute("aSeed", new InstancedBufferAttribute(seed, 1));
    g.instanceCount = k;
    return g;
    // theme only recolors; rebuilding on it keeps the colors in step with the stars above
  }, [ready, placed, theme]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => geometry.dispose(), [geometry]);

  useEffect(() => {
    const T = THEMES[theme];
    material.uniforms.uWater.value.set(T.water);
    material.uniforms.uGlow.value = theme === "dark" ? 1 : 0;
  }, [material, theme]);

  useFrame(({ camera, gl }) => {
    const u = material.uniforms;
    const t = now();
    u.uTime.value = t;
    u.uSea.value = anim.sea;
    // the reflection gathers as the nebula forms, and is fully there once it has settled
    u.uAlpha.value = Number.isFinite(anim.intro.t0) ? Math.min(1, Math.max(0, (t - anim.intro.t0) / Math.max(0.1, anim.intro.end - anim.intro.t0))) : 0;
    u.uPR.value = gl.getPixelRatio();
    u.uScale.value = gl.domElement.height / (2 * Math.tan((((camera as PerspectiveCamera).fov ?? 45) * Math.PI) / 360));
  });

  return <mesh geometry={geometry} material={material} frustumCulled={false} renderOrder={-5} />;
}
