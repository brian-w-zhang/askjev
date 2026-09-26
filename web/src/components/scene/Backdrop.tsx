"use client";
import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { BackSide, Color, ShaderMaterial, Vector3, type Camera, type Mesh } from "three";
import { now } from "@/lib/anim";
import { useStore } from "@/lib/store";
import { THEMES } from "@/lib/theme";

// The sky (docs/07-ui.md, Look): twilight over a still sea. The sun has just set in one fixed direction, so
// the scene has a warm side and a cool side and reads as a place as you orbit:
// - the dome runs warm at the horizon to cool overhead, with the twilight glow low on the sun's side and,
//   opposite it, the Belt of Venus (a pink band) over Earth's shadow (a blue-grey one);
// - a band of cumulus sits low in the sky: toward the light they are silhouettes with bright pink rims, away
//   from it their faces are lit; thin cirrus streaks higher up;
// - below the horizon a calm sea mirrors all of it, with ripple streaks tied to the water (they slide as the
//   camera moves), darkening as you look straight down.
// Pink stays in the glow, the belt and the cloud rims. Light mode is an evening in typesafe.ai's hero colors;
// dark mode is the same place later, in their dark docs site's aubergine with a hot-pink afterglow.
const vert = /* glsl */ `
  varying vec3 vDir;
  void main() {
    vDir = position;
    vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    gl_Position = p.xyww;
  }`;

const frag = /* glsl */ `
  uniform float uTime; uniform vec3 uCam; uniform vec3 uSun; uniform float uStars;
  uniform vec3 uR0; uniform vec3 uR1; uniform vec3 uR2; uniform vec3 uR3; uniform vec3 uR4;
  uniform vec3 uGlow; uniform vec3 uGlowCore; uniform vec3 uBelt; uniform vec3 uShadow;
  uniform vec3 uLit; uniform vec3 uDark; uniform vec3 uRim; uniform vec3 uWater;
  varying vec3 vDir;
  const float SEA = -700.0;

  float h2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float n2(vec2 p) { vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(h2(i), h2(i + vec2(1, 0)), f.x), mix(h2(i + vec2(0, 1)), h2(i + vec2(1, 1)), f.x), f.y); }
  float fbm(vec2 p) { float v = 0.0; float a = 0.5; for (int i = 0; i < 5; i++) { v += a * n2(p); p = p * 2.03 + 17.0; a *= 0.5; } return v; }

  // horizon (e = 0) to zenith (e = 1); bands bunch up low, where the color is
  vec3 ramp(float e) {
    float x = pow(clamp(e, 0.0, 1.0), 0.5) * 4.0;
    if (x < 1.0) return mix(uR0, uR1, x);
    if (x < 2.0) return mix(uR1, uR2, x - 1.0);
    if (x < 3.0) return mix(uR2, uR3, x - 2.0);
    return mix(uR3, uR4, min(x - 3.0, 1.0));
  }

  vec3 sky(vec3 d, float stars) {
    float e = max(d.y, 0.0);
    vec2 hz = normalize(d.xz + vec2(1e-5));
    vec2 sz = normalize(uSun.xz);
    float toward = dot(hz, sz); // 1 facing the sunset, -1 facing away
    float sunSide = smoothstep(-0.3, 1.0, toward);
    float anti = smoothstep(0.0, 1.0, -toward);
    vec3 col = ramp(e);
    // twilight glow low on the sun's side, with its hot line right at the horizon
    float wrap = 0.5 + 0.5 * toward;
    col = mix(col, uGlow, wrap * wrap * exp(-e * 6.0) * 0.9);
    col = mix(col, uGlowCore, pow(max(toward, 0.0), 4.0) * exp(-e * 9.0) * 0.28);
    // opposite: Earth's shadow hugging the horizon, the Belt of Venus just above it
    col = mix(col, uBelt, exp(-pow((e - 0.13) / 0.07, 2.0)) * anti * 0.75);
    col = mix(col, uShadow, exp(-pow(e / 0.05, 2.0)) * anti * 0.7);

    // cumulus: a band of distinct puffs low in the sky, drawn in (azimuth, elevation) so they stay round
    // at any heading, smaller toward the horizon, domain-warped so they billow
    float az = atan(d.z, d.x);
    vec2 cu = vec2(az * 3.2 + uTime * 0.004, log(e + 0.035) * 1.7);
    vec2 w = vec2(fbm(cu * 1.3), fbm(cu * 1.3 + vec2(5.2, 1.3)));
    float dens = fbm(cu * 1.6 + 1.2 * w);
    float band = smoothstep(0.015, 0.06, e) * (1.0 - smoothstep(0.26, 0.5, e));
    float c = smoothstep(0.54, 0.66, dens) * band;
    // lit from below (the sun has just set): density falling downward means an underside catching light
    float below = fbm((cu + vec2(0.0, -0.07)) * 1.6 + 1.2 * w);
    float under = clamp((dens - below) * 10.0, 0.0, 1.0);
    float rim = under * (1.0 - smoothstep(0.6, 0.74, dens));
    // toward the sunset: silhouettes with glowing undersides; away from it: bright tops, shaded bases
    vec3 face = mix(uLit, uDark, clamp(under * 0.8 + smoothstep(0.62, 0.8, dens) * 0.2, 0.0, 1.0));
    vec3 body = mix(face, uDark, sunSide * 0.85);
    body = mix(body, uRim, rim * (0.2 + 0.8 * sunSide));
    col = mix(col, body, c);
    // cirrus: faint streaks higher up, stretched along the horizon, catching pink toward the sunset
    float ci = fbm(vec2(az * 1.4 - uTime * 0.002, log(e + 0.05) * 9.0));
    float cir = smoothstep(0.6, 0.76, ci) * smoothstep(0.12, 0.3, e) * (1.0 - smoothstep(0.55, 0.85, e)) * 0.45 * (1.0 - c);
    col = mix(col, mix(uLit, uRim, sunSide * 0.5), cir);
    // stars overhead at night
    if (stars > 0.0) {
      vec2 sc = floor(vec2(atan(d.z, d.x) * 300.0, e * 480.0));
      col = mix(col, vec3(0.96), stars * step(0.9978, h2(sc)) * smoothstep(0.12, 0.35, e) * (1.0 - c));
    }
    return col;
  }

  void main() {
    vec3 d = normalize(vDir);
    vec3 col;
    if (d.y >= 0.0) {
      col = sky(d, uStars);
    } else {
      // the sea: a mirror of the sky, broken by ripple streaks fixed to the water
      float t = max(uCam.y - SEA, 50.0) / -d.y;
      vec2 p = uCam.xz + d.xz * t;
      float rip = fbm(p * vec2(0.0035, 0.018) + vec2(uTime * 0.02, 0.0)) - 0.5;
      vec3 r = normalize(vec3(d.x + rip * 0.05, -d.y + rip * 0.012, d.z));
      vec3 refl = sky(r, uStars * 0.5);
      float fres = pow(1.0 - clamp(-d.y, 0.0, 1.0), 4.0);
      col = mix(uWater, refl, 0.4 + 0.55 * fres);
      // nearer water is deeper, as in a lake at dusk: it darkens toward the viewer
      col = mix(col, uDark, smoothstep(0.2, 1.0, 1.0 - fres) * 0.2);
      // far away the water melts into the horizon's haze
      col = mix(col, ramp(0.0), exp(-(-d.y) * 60.0) * 0.45);
      // wind patches: ruffled water is darker, calm water keeps the mirror
      float patchy = smoothstep(0.35, 0.75, fbm(p * 0.0007 + vec2(uTime * 0.003, 0.0)));
      col = mix(col, uWater, patchy * 0.35 * (1.0 - fres));
      // a glitter path toward the sunset: broken pink streaks on the water
      vec2 hz = normalize(d.xz + vec2(1e-5));
      float toward = dot(hz, normalize(uSun.xz));
      float streak = smoothstep(0.58, 0.72, fbm(p * vec2(0.0025, 0.03) + vec2(0.0, uTime * 0.05)));
      float path = pow(max(toward, 0.0), 14.0) * (0.35 + 0.65 * fres);
      col = mix(col, mix(uGlow, uRim, 0.35), streak * path * 0.85);
    }
    gl_FragColor = vec4(col, 1.0);
  }`;

// just set: low on the horizon, behind the nebula from the home view
const SUN = new Vector3(-0.35, -0.04, -0.94).normalize();

export function Backdrop() {
  const theme = useStore((s) => s.theme);
  const material = useMemo(() => {
    const c = () => ({ value: new Color() });
    return new ShaderMaterial({
      vertexShader: vert,
      fragmentShader: frag,
      side: BackSide,
      depthWrite: false,
      depthTest: false,
      uniforms: {
        uTime: { value: 0 }, uCam: { value: new Vector3() }, uSun: { value: SUN }, uStars: { value: 0 },
        uR0: c(), uR1: c(), uR2: c(), uR3: c(), uR4: c(),
        uGlow: c(), uGlowCore: c(), uBelt: c(), uShadow: c(), uLit: c(), uDark: c(), uRim: c(), uWater: c(),
      },
    });
  }, []);
  useEffect(() => {
    const T = THEMES[theme];
    const u = material.uniforms;
    T.ramp.forEach((hex, i) => u[`uR${i}`].value.set(hex));
    u.uGlow.value.set(T.glow);
    u.uGlowCore.value.set(T.glowCore);
    u.uBelt.value.set(T.belt);
    u.uShadow.value.set(T.shadow);
    u.uLit.value.set(T.cloudLit);
    u.uDark.value.set(T.cloudDark);
    u.uRim.value.set(T.cloudRim);
    u.uWater.value.set(T.water);
    u.uStars.value = T.stars;
  }, [material, theme]);
  const ref = useRef<Mesh>(null);
  useFrame(() => {
    material.uniforms.uTime.value = now();
  });
  // Center the dome on the camera at the moment it's drawn, after anything else has moved the camera this
  // frame; otherwise a fast flight leaves the camera outside the unit sphere and the sky blinks out.
  const follow = (_r: unknown, _s: unknown, camera: Camera) => {
    const m = ref.current;
    if (!m) return;
    m.position.copy(camera.position);
    m.updateMatrixWorld();
    material.uniforms.uCam.value.copy(camera.position);
  };
  return (
    <mesh ref={ref} material={material} renderOrder={-10} frustumCulled={false} onBeforeRender={follow}>
      <sphereGeometry args={[1, 64, 32]} />
    </mesh>
  );
}
