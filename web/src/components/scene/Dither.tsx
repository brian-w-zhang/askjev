"use client";
import { forwardRef, useMemo } from "react";
import { BlendFunction, Effect, EffectAttribute } from "postprocessing";
import { Color, Uniform, Vector2, Vector3 } from "three";

// Ordered (Bayer 8x8) dither onto TypeSafe's palette at chunky pixel cells (docs/07-ui.md, Look).
// Each cell samples the scene once at its center, nudges it by the Bayer threshold, and snaps to the
// nearest palette color, so gradients and clouds come out as halftone stipple like typesafe.ai.
export const PALETTE = ["#D6EAF8", "#FEFEFE", "#F386A1", "#D45BB6", "#09AEA1", "#4B5BD6", "#03AA5C", "#1E1E1E", "#BFDDF3"];

const frag = /* glsl */ `
  uniform vec3 uPalette[${PALETTE.length}];
  uniform float uCell;
  uniform float uSpread;
  uniform vec2 uRes;

  float bayer8(vec2 p) {
    // recursive 2x2 construction of the 8x8 Bayer matrix, in [0, 1)
    vec2 a = mod(p, 2.0), b = mod(floor(p / 2.0), 2.0), c = mod(floor(p / 4.0), 2.0);
    float b2 = (a.x * 2.0 + a.y * 3.0 - 4.0 * a.x * a.y);
    float b4 = (b.x * 2.0 + b.y * 3.0 - 4.0 * b.x * b.y);
    float b8 = (c.x * 2.0 + c.y * 3.0 - 4.0 * c.x * c.y);
    return (b2 * 16.0 + b4 * 4.0 + b8) / 64.0;
  }

  void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
    vec2 cell = floor(uv * uRes / uCell);
    vec2 center = (cell + 0.5) * uCell / uRes;
    vec3 c = texture2D(inputBuffer, center).rgb;
    // colors already on the palette (the flat sky) stay solid; only in-between colors get stippled
    for (int i = 0; i < ${PALETTE.length}; i++) {
      vec3 d0 = c - uPalette[i];
      if (dot(d0, d0) < 2e-5) { outputColor = vec4(uPalette[i], 1.0); return; }
    }
    float t = bayer8(cell) - 0.5;
    c += t * uSpread;
    float best = 1e9; vec3 pick = uPalette[0];
    for (int i = 0; i < ${PALETTE.length}; i++) {
      vec3 d = c - uPalette[i];
      // weight green a little more: closer to how the eye separates these colors
      float e = dot(d * d, vec3(0.3, 0.55, 0.15));
      if (e < best) { best = e; pick = uPalette[i]; }
    }
    outputColor = vec4(pick, 1.0);
  }`;

class DitherEffect extends Effect {
  constructor({ cell = 2, spread = 0.22 }: { cell?: number; spread?: number } = {}) {
    super("DitherEffect", frag, {
      blendFunction: BlendFunction.NORMAL,
      attributes: EffectAttribute.CONVOLUTION,
      uniforms: new Map<string, Uniform>([
        // palette is authored in sRGB; the composer works in linear, so convert once here
        ["uPalette", new Uniform(PALETTE.map((h) => { const c = new Color(h); return new Vector3(c.r, c.g, c.b); }))],
        ["uCell", new Uniform(cell)],
        ["uSpread", new Uniform(spread)],
        ["uRes", new Uniform(new Vector2(1, 1))],
      ]),
    });
  }
  setSize(width: number, height: number) {
    (this.uniforms.get("uRes")!.value as Vector2).set(width, height);
  }
}

export const Dither = forwardRef<DitherEffect, { cell?: number; spread?: number }>(function Dither({ cell = 2, spread = 0.22 }, ref) {
  const effect = useMemo(() => new DitherEffect({ cell, spread }), [cell, spread]);
  return <primitive ref={ref} object={effect} dispose={null} />;
});
