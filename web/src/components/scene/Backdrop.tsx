"use client";
import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { BackSide, Color, ShaderMaterial, Vector3, type Camera, type Mesh } from "three";
import { anim, now } from "@/lib/anim";
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
  uniform float uTime; uniform vec3 uCam; uniform vec3 uSun; uniform float uStars; uniform float uSea;
  uniform vec3 uR0; uniform vec3 uR1; uniform vec3 uR2; uniform vec3 uR3; uniform vec3 uR4;
  uniform vec3 uGlow; uniform vec3 uGlowCore; uniform vec3 uBelt; uniform vec3 uShadow;
  uniform vec3 uLit; uniform vec3 uDark; uniform vec3 uRim; uniform vec3 uWater; uniform vec3 uWaterDeep; uniform float uRimAmt; uniform float uGlowFall; uniform float uSeaDim; uniform vec3 uDeckLit; uniform vec3 uDeckShade; uniform vec3 uDeckRim; uniform float uDeckAmt;
  varying vec3 vDir;

  float h2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float n2(vec2 p) { vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(h2(i), h2(i + vec2(1, 0)), f.x), mix(h2(i + vec2(0, 1)), h2(i + vec2(1, 1)), f.x), f.y); }
  float fbm(vec2 p) { float v = 0.0; float a = 0.5; for (int i = 0; i < 5; i++) { v += a * n2(p); p = p * 2.03 + 17.0; a *= 0.5; } return v; }
  // 3D value noise: the sky's low clouds are sampled on a cylinder around the viewer (cos az, sin az, height),
  // so the pattern wraps all the way round with no seam where the azimuth jumps from +180° to -180°
  float h3(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
  float n3(vec3 p) { vec3 i = floor(p); vec3 f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(h3(i), h3(i + vec3(1, 0, 0)), f.x), mix(h3(i + vec3(0, 1, 0)), h3(i + vec3(1, 1, 0)), f.x), f.y),
               mix(mix(h3(i + vec3(0, 0, 1)), h3(i + vec3(1, 0, 1)), f.x), mix(h3(i + vec3(0, 1, 1)), h3(i + vec3(1, 1, 1)), f.x), f.y), f.z); }
  float fbm3(vec3 p) { float v = 0.0; float a = 0.5; for (int i = 0; i < 5; i++) { v += a * n3(p); p = p * 2.03 + 17.0; a *= 0.5; } return v; }
  vec3 cyl(float az, float r, float y) { return vec3(cos(az) * r, sin(az) * r, y); }

  // horizon (e = 0) to zenith (e = 1); bands bunch up low, where the color is
  vec3 ramp(float e) {
    float x = pow(clamp(e, 0.0, 1.0), 0.5) * 4.0;
    if (x < 1.0) return mix(uR0, uR1, x);
    if (x < 2.0) return mix(uR1, uR2, x - 1.0);
    if (x < 3.0) return mix(uR2, uR3, x - 2.0);
    return mix(uR3, uR4, min(x - 3.0, 1.0));
  }

  vec3 sky(vec3 d, float stars, float deckAmt) {
    float e = max(d.y, 0.0);
    vec2 hz = normalize(d.xz + vec2(1e-5));
    vec2 sz = normalize(uSun.xz);
    float toward = dot(hz, sz); // 1 facing the sunset, -1 facing away
    float sunSide = smoothstep(-0.3, 1.0, toward);
    float anti = smoothstep(0.0, 1.0, -toward);
    vec3 col = ramp(e);
    // twilight glow low on the sun's side, with its hot line right at the horizon
    float wrap = 0.5 + 0.5 * toward;
    col = mix(col, uGlow, wrap * wrap * exp(-e * uGlowFall) * 0.9);
    col = mix(col, uGlowCore, pow(max(toward, 0.0), 4.0) * exp(-e * 9.0) * 0.28);
    // opposite: Earth's shadow hugging the horizon, the Belt of Venus just above it
    col = mix(col, uBelt, exp(-pow((e - 0.13) / 0.07, 2.0)) * anti * 0.75);
    col = mix(col, uShadow, exp(-pow(e / 0.05, 2.0)) * anti * 0.7);

    // cumulus: a band of distinct puffs low in the sky, drawn in (azimuth, elevation) so they stay round
    // at any heading, smaller toward the horizon, domain-warped so they billow
    float az = atan(d.z, d.x);
    // they drift slowly along the horizon, and their shapes billow as the warp field itself drifts
    vec3 cu = cyl(az + uTime * 0.004, 3.2, log(e + 0.035) * 1.7);
    vec3 w = vec3(fbm3(cu * 1.3 + vec3(uTime * 0.01, 0.0, 0.0)), fbm3(cu * 1.3 + vec3(5.2, 1.3 + uTime * 0.008, 2.7)), 0.0);
    float dens = fbm3(cu * 1.6 + 1.2 * w);
    float band = smoothstep(0.015, 0.06, e) * (1.0 - smoothstep(0.26, 0.5, e));
    float c = smoothstep(0.54, 0.66, dens) * band;
    // lit from below (the sun has just set): density falling downward means an underside catching light
    float below = fbm3((cu + vec3(0.0, 0.0, -0.07)) * 1.6 + 1.2 * w);
    float under = clamp((dens - below) * 10.0, 0.0, 1.0);
    float rim = under * (1.0 - smoothstep(0.6, 0.74, dens));
    // toward the sunset: silhouettes with glowing undersides; away from it: bright tops, shaded bases
    vec3 face = mix(uLit, uDark, clamp(under * 0.8 + smoothstep(0.62, 0.8, dens) * 0.2, 0.0, 1.0));
    vec3 body = mix(face, uDark, sunSide * 0.85);
    body = mix(body, uRim, rim * (0.2 + 0.8 * sunSide) * uRimAmt);
    col = mix(col, body, c);
    // cirrus: faint streaks higher up, stretched along the horizon, catching pink toward the sunset
    float ci = fbm3(cyl(az - uTime * 0.006, 1.4, log(e + 0.05) * 9.0));
    float cir = smoothstep(0.6, 0.76, ci) * smoothstep(0.12, 0.3, e) * (1.0 - smoothstep(0.55, 0.85, e)) * 0.45 * (1.0 - c);
    col = mix(col, mix(uLit, uRim, sunSide * 0.5), cir);
    // the high deck overhead: mackerel altocumulus on a plane far above, so its cells shrink toward the horizon.
    // Rows of small cells with holes of open sky, lit from below by the set sun: warm toward the sunset, cool
    // away from it, and brightest at the cell edges where the light slips around them.
    float deck = 0.0;
    if (e > 0.3) {
      vec2 uv = d.xz / d.y * 2.4 + vec2(uTime * 0.02, uTime * 0.007);
      vec2 wq = vec2(fbm(uv * 0.5 + uTime * 0.006), fbm(uv * 0.5 + vec2(3.1, 7.7)));
      vec2 q = uv + 0.9 * wq;
      float rows = 0.5 + 0.5 * sin(q.y * 11.0 + fbm(q * 1.5) * 3.0);
      float cells = fbm(q * vec2(9.0, 14.0));
      float holes = smoothstep(0.3, 0.5, fbm(uv * 0.28 + 11.0));
      float m = cells * 0.75 + rows * 0.35;
      deck = smoothstep(0.52, 0.64, m) * holes * smoothstep(0.3, 0.6, e);
      float edge = smoothstep(0.52, 0.58, m) * (1.0 - smoothstep(0.6, 0.72, m));
      float warm = smoothstep(-0.6, 1.0, toward);
      vec3 dc = mix(uDeckShade, uDeckLit, warm * 0.85);
      dc = mix(dc, uDeckRim, edge * warm * warm * 0.6);
      deck *= deckAmt * uDeckAmt;
      col = mix(col, dc, deck);
    }
    // stars overhead at night, through the gaps in the deck
    stars *= 1.0 - deck;
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
      col = sky(d, uStars, 1.0);
    } else {
      // the sea: a mirror of the sky, broken by ripple streaks fixed to the water
      float t = max(uCam.y - uSea, 20.0) / -d.y;
      vec2 p = uCam.xz + d.xz * t;
      float rip = fbm(p * vec2(0.0035, 0.018) + vec2(uTime * 0.04, uTime * 0.015)) - 0.5;
      // the sky's image in the water is soft: three samples spread along the ripples, averaged, and darker
      vec3 r = normalize(vec3(d.x + rip * 0.08, -d.y + rip * 0.02, d.z));
      vec3 r2 = normalize(r + vec3(0.012, 0.01, 0.0));
      vec3 r3 = normalize(r + vec3(-0.012, 0.018, 0.0));
      vec3 refl = (sky(r, uStars * 0.5, 0.45) + sky(r2, 0.0, 0.45) + sky(r3, 0.0, 0.45)) / 3.0;
      float fres = pow(1.0 - clamp(-d.y, 0.0, 1.0), 4.0);
      // looking down you see the water's own deeper color; only toward the horizon does it turn to a mirror
      col = mix(uWaterDeep, refl * 0.86, 0.12 + 0.8 * fres);
      // wavelets: short horizontal crests fixed to the water, finer with distance (they're drawn on the surface),
      // their tops catching the bright sky low on the horizon, their troughs a shade darker
      vec2 wp = p * vec2(0.011, 0.075) + vec2(uTime * 0.03, uTime * 0.07);
      // a second, diagonal swell crossing the first, so the pattern shifts and never reads as one direction
      vec2 sw = mat2(0.8, -0.6, 0.6, 0.8) * p * vec2(0.02, 0.05) + vec2(-uTime * 0.02, uTime * 0.04);
      float wv = fbm(wp) + 0.5 * fbm(wp * 2.3 + 4.0) + 0.35 * (fbm(sw) - 0.5);
      float crest = smoothstep(0.92, 1.1, wv);
      float trough = 1.0 - smoothstep(0.45, 0.75, wv);
      float near = smoothstep(0.02, 0.35, -d.y); // up close the wavelets read; far off they blur into sheen
      col = mix(col, mix(refl, ramp(0.05), 0.6), crest * (0.4 + 0.35 * near));
      col = mix(col, uWaterDeep * 0.85, trough * 0.35 * near);
      // the horizon: the sea stays a shade darker than the sky right up to a clean edge, where a thin bright
      // sheen line sits on the water (as over open sea at dusk)
      col = mix(col, mix(uWater, uShadow, 0.5), exp(-(-d.y) * 70.0) * 0.45);
      col *= uSeaDim; // the water always sits a step darker than the sky, so the horizon never dissolves
      col = mix(col, mix(ramp(0.0), uGlow, 0.6), smoothstep(0.009, 0.0, -d.y) * 0.85);
      // wind patches: ruffled water is darker, calm water keeps the mirror
      float patchy = smoothstep(0.35, 0.75, fbm(p * 0.0007 + vec2(uTime * 0.003, 0.0)));
      col = mix(col, uWater, patchy * 0.35 * (1.0 - fres));
      // the afterglow's path on the water: a soft, wide sheen toward where the sun went down, broken only gently
      // by the slow swell (no moving streaks: at this resolution they read as dancing dashes, not water)
      vec2 hz = normalize(d.xz + vec2(1e-5));
      float toward = dot(hz, normalize(uSun.xz));
      float calm = 0.75 + 0.25 * smoothstep(0.3, 0.7, fbm(p * vec2(0.004, 0.02) + vec2(0.0, uTime * 0.01)));
      float path = pow(max(toward, 0.0), 10.0) * (0.25 + 0.75 * fres) * calm;
      col = mix(col, mix(uGlow, uRim, 0.2), path * 0.35);
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
        uTime: { value: 0 }, uCam: { value: new Vector3() }, uSun: { value: SUN }, uStars: { value: 0 }, uSea: { value: -300 },
        uR0: c(), uR1: c(), uR2: c(), uR3: c(), uR4: c(),
        uGlow: c(), uGlowCore: c(), uBelt: c(), uShadow: c(), uLit: c(), uDark: c(), uRim: c(), uWater: c(), uWaterDeep: c(), uRimAmt: { value: 1 }, uGlowFall: { value: 6 }, uSeaDim: { value: 1 }, uDeckLit: c(), uDeckShade: c(), uDeckRim: c(), uDeckAmt: { value: 1 },
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
    u.uWaterDeep.value.set(T.waterDeep);
    u.uRimAmt.value = T.rimAmt;
    u.uGlowFall.value = T.glowFall;
    u.uSeaDim.value = T.seaDim;
    u.uDeckLit.value.set(T.deckLit);
    u.uDeckShade.value.set(T.deckShade);
    u.uDeckRim.value.set(T.deckRim);
    u.uDeckAmt.value = T.deckAmt;
    u.uStars.value = T.stars;
  }, [material, theme]);
  const ref = useRef<Mesh>(null);
  useFrame((_, dt) => {
    material.uniforms.uTime.value = now();
    anim.sea += (anim.seaTarget - anim.sea) * (1 - Math.exp(-dt * 2));
    material.uniforms.uSea.value = anim.sea;
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
