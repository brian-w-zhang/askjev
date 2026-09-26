"use client";
import { forwardRef, useEffect, useMemo } from "react";
import { BlendFunction, Effect, EffectAttribute } from "postprocessing";
import { Color, Uniform, Vector2, Vector3 } from "three";
import { THEMES } from "@/lib/theme";

// Halftone onto TypeSafe's palette at chunky pixel cells (docs/07-ui.md, Look), like a print run with a few
// inks. Each cell samples the scene once, finds the two palette inks it sits between and how far along, and
// picks one by that ink pair's halftone screen: fine grain for sky and cloud shading, round 45° dots for the
// pinks (as in typesafe.ai's hero clouds), line and plus-grid screens for the data colors (as in the
// dithered photos on their site). Colors already on the palette stay solid.
const N = THEMES.light.dither.length;
const toVec = (inks: [string, number][]) => inks.map(([h]) => { const c = new Color(h); return new Vector3(c.r, c.g, c.b); });
const toScreens = (inks: [string, number][]) => inks.map(([, s]) => s);

const frag = /* glsl */ `
  uniform vec3 uPalette[${N}];
  uniform float uScreen[${N}];
  uniform float uCell;
  uniform vec2 uRes;

  // threshold in [0, 1) at cell p for each screen
  float screen(float s, vec2 p) {
    if (s < 0.5) {
      // fine grain: interleaved gradient noise (organic, no repeating motif)
      return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715))));
    }
    if (s < 1.5) {
      // round dots on a 45° grid: dots grow from their centers as the ink gets stronger
      vec2 q = vec2(p.x + p.y, p.x - p.y) * 0.7071 / 3.6;
      return clamp(length(fract(q) - 0.5) * 1.41, 0.0, 0.999);
    }
    if (s < 2.5) {
      // horizontal lines, thickening with the ink
      return clamp(abs(fract((p.y + 0.5) / 3.0) - 0.5) * 2.0, 0.0, 0.999);
    }
    if (s < 3.5) {
      // diagonal lines
      return clamp(abs(fract((p.x + p.y * 0.6) / 3.4) - 0.5) * 2.0, 0.0, 0.999);
    }
    // plus grid
    vec2 f = abs(fract((p + 0.5) / 4.0) - 0.5) * 2.0;
    return clamp(min(f.x, f.y), 0.0, 0.999);
  }

  void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
    vec2 cell = floor(uv * uRes / uCell);
    vec2 center = (cell + 0.5) * uCell / uRes;
    vec3 c = texture2D(inputBuffer, center).rgb;
    // the two nearest inks (perceptual-ish weights), and where c falls between them
    float b1 = 1e9, b2 = 1e9; int i1 = 0, i2 = 0;
    for (int i = 0; i < ${N}; i++) {
      vec3 d = c - uPalette[i];
      float e = dot(d * d, vec3(0.3, 0.55, 0.15));
      if (e < b1) { b2 = b1; i2 = i1; b1 = e; i1 = i; }
      else if (e < b2) { b2 = e; i2 = i; }
    }
    if (b1 < 2e-5) { outputColor = vec4(uPalette[i1], 1.0); return; }
    vec3 a = uPalette[i1], b = uPalette[i2];
    vec3 ab = b - a;
    float t = clamp(dot(c - a, ab) / max(dot(ab, ab), 1e-6), 0.0, 1.0);
    float s = max(uScreen[i1], uScreen[i2]);
    outputColor = vec4(t > screen(s, cell) ? b : a, 1.0);
  }`;

class DitherEffect extends Effect {
  constructor({ cell = 1, palette = THEMES.light.dither }: { cell?: number; palette?: [string, number][] } = {}) {
    super("DitherEffect", frag, {
      blendFunction: BlendFunction.NORMAL,
      attributes: EffectAttribute.CONVOLUTION,
      uniforms: new Map<string, Uniform>([
        // palette is authored in sRGB; the composer works in linear, so convert once here
        ["uPalette", new Uniform(toVec(palette))],
        ["uScreen", new Uniform(toScreens(palette))],
        ["uCell", new Uniform(cell)],
        ["uRes", new Uniform(new Vector2(1, 1))],
      ]),
    });
  }
  setPalette(inks: [string, number][]) {
    this.uniforms.get("uPalette")!.value = toVec(inks);
    this.uniforms.get("uScreen")!.value = toScreens(inks);
  }
  setSize(width: number, height: number) {
    (this.uniforms.get("uRes")!.value as Vector2).set(width, height);
  }
}

export const Dither = forwardRef<DitherEffect, { cell?: number; palette?: [string, number][] }>(function Dither({ cell = 1, palette = THEMES.light.dither }, ref) {
  const effect = useMemo(() => new DitherEffect({ cell }), [cell]);
  useEffect(() => effect.setPalette(palette), [effect, palette]);
  return <primitive ref={ref} object={effect} dispose={null} />;
});
