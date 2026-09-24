"use client";
import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { BackSide, ShaderMaterial, type Mesh } from "three";
import { now } from "@/lib/anim";

// Distant sky: faint colored dust clouds on a far sphere that follows the camera (never reachable).
const vert = /* glsl */ `
  varying vec3 vDir;
  void main() {
    vDir = normalize(position);
    vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    gl_Position = p.xyww; // always at the far plane
  }`;

const frag = /* glsl */ `
  uniform float uTime;
  varying vec3 vDir;
  float h(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
  float n(vec3 p) {
    vec3 i = floor(p); vec3 f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(h(i), h(i + vec3(1,0,0)), f.x), mix(h(i + vec3(0,1,0)), h(i + vec3(1,1,0)), f.x), f.y),
               mix(mix(h(i + vec3(0,0,1)), h(i + vec3(1,0,1)), f.x), mix(h(i + vec3(0,1,1)), h(i + vec3(1,1,1)), f.x), f.y), f.z);
  }
  float fbm(vec3 p) { float v = 0.0; float a = 0.5; for (int i = 0; i < 5; i++) { v += a * n(p); p *= 2.02; a *= 0.5; } return v; }
  void main() {
    vec3 d = vDir;
    float band = exp(-pow(d.y * 2.4 + 0.25 * sin(d.x * 3.0), 2.0)); // a faint galactic band
    float c1 = fbm(d * 2.2 + vec3(0.0, uTime * 0.002, 0.0));
    float c2 = fbm(d * 4.5 + 7.3);
    float dust = smoothstep(0.45, 0.95, c1) * (0.35 + 0.65 * band);
    vec3 col = mix(vec3(0.10, 0.07, 0.26), vec3(0.03, 0.16, 0.26), c2) * dust * 0.55;
    col += vec3(0.20, 0.10, 0.22) * pow(smoothstep(0.55, 1.0, c2), 3.0) * band * 0.35;
    gl_FragColor = vec4(col, 1.0);
  }`;

export function Backdrop() {
  const material = useMemo(
    () => new ShaderMaterial({ vertexShader: vert, fragmentShader: frag, side: BackSide, depthWrite: false, depthTest: false, uniforms: { uTime: { value: 0 } } }),
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
