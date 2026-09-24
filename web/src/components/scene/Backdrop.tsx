"use client";
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { BackSide, Color, ShaderMaterial, type Mesh } from "three";
import { now } from "@/lib/anim";

// The sky (docs/07-ui.md, Look): light blue overhead, paler toward the horizon, with far pink cumulus
// banks like the typesafe.ai hero. A sphere that follows the camera, drawn at the far plane.
const vert = /* glsl */ `
  varying vec3 vDir;
  void main() {
    vDir = normalize(position);
    vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    gl_Position = p.xyww;
  }`;

const frag = /* glsl */ `
  uniform float uTime; uniform vec3 uTop; uniform vec3 uLow; uniform vec3 uCloud; uniform vec3 uCloud2;
  varying vec3 vDir;
  float h(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
  float n(vec3 p) {
    vec3 i = floor(p); vec3 f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(h(i), h(i + vec3(1,0,0)), f.x), mix(h(i + vec3(0,1,0)), h(i + vec3(1,1,0)), f.x), f.y),
               mix(mix(h(i + vec3(0,0,1)), h(i + vec3(1,0,1)), f.x), mix(h(i + vec3(0,1,1)), h(i + vec3(1,1,1)), f.x), f.y), f.z);
  }
  float fbm(vec3 p) { float v = 0.0; float a = 0.5; for (int i = 0; i < 5; i++) { v += a * n(p); p *= 2.03; a *= 0.5; } return v; }
  void main() {
    vec3 d = vDir;
    vec3 col = mix(uLow, uTop, smoothstep(-0.35, 0.75, d.y));
    // cloud banks hug the horizon and thin out overhead
    float bank = smoothstep(0.55, -0.15, d.y);
    float c = fbm(d * 3.2 + vec3(uTime * 0.004, 0.0, 0.0));
    float cloud = smoothstep(0.56, 0.74, c * (0.35 + 0.85 * bank));
    col = mix(col, mix(uCloud2, uCloud, smoothstep(0.6, 0.8, c)), cloud * 0.8);
    gl_FragColor = vec4(col, 1.0);
  }`;

export function Backdrop() {
  const material = useMemo(
    () =>
      new ShaderMaterial({
        vertexShader: vert,
        fragmentShader: frag,
        side: BackSide,
        depthWrite: false,
        depthTest: false,
        uniforms: {
          uTime: { value: 0 },
          uTop: { value: new Color("#BFDDF3") },
          uLow: { value: new Color("#EEF5FB") },
          uCloud: { value: new Color("#F386A1") },
          uCloud2: { value: new Color("#F7B8CB") },
        },
      }),
    [],
  );
  const ref = useRef<Mesh>(null);
  useFrame(({ camera }) => {
    material.uniforms.uTime.value = now();
    ref.current?.position.copy(camera.position);
  });
  return (
    <mesh ref={ref} material={material} renderOrder={-10} frustumCulled={false}>
      <sphereGeometry args={[1, 48, 24]} />
    </mesh>
  );
}
