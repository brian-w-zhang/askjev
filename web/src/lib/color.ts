import { Color } from "three";
import type { Indicator, TreeNode } from "./types";
import { THEMES, type Theme } from "./theme";

// "Attention" 0..1 per indicator: 1 = where Jev is jagged or worth a look. Never a grade.
export const INDICATORS: { id: Indicator; label: string; hint: string }[] = [
  { id: "hemisphere", label: "Hemisphere", hint: "World, Self and Machine arms" },
  { id: "stability", label: "Stability", hint: "Do answers survive option shuffles? Bright = fragile" },
  { id: "human_gap", label: "Human gap", hint: "Distance between Jev's most-people answer and real human data" },
  { id: "frame_gap", label: "Frame gap", hint: "Jev's own answer vs its answer for most people" },
  { id: "placement_conf", label: "Placement", hint: "How sure Jev is about where questions belong. Bright = unsure" },
  { id: "calibration_ece", label: "Calibration", hint: "Expected calibration error where truth is known" },
];

export function attention(n: TreeNode, ind: Indicator): number | null {
  const v = ind === "hemisphere" ? null : (n[ind] as number | null);
  if (v === null || v === undefined) return null;
  switch (ind) {
    case "stability": return clamp((1 - v) / 0.5);
    case "placement_conf": return clamp((1 - v) / 0.5);
    case "human_gap": return clamp(v / 0.5);
    case "frame_gap": return clamp(v / 0.5);
    case "calibration_ece": return clamp(v / 0.25);
  }
  return null;
}

const clamp = (x: number) => Math.max(0, Math.min(1, x));

// steady = calm blue, worth a look = magenta (TypeSafe palette); no data fades into the sky
const RAMP = [new Color("#7D89E6"), new Color("#F386A1"), new Color("#D45BB6")];

export function rampColor(t: number, out = new Color()): Color {
  if (t <= 0.5) return out.copy(RAMP[0]).lerp(RAMP[1], t / 0.5);
  return out.copy(RAMP[1]).lerp(RAMP[2], (t - 0.5) / 0.5);
}

export const RAMP_CSS = "linear-gradient(90deg, #7D89E6, #F386A1, #D45BB6)";

export function nodeColor(n: TreeNode, ind: Indicator, theme: Theme, out = new Color()): Color {
  if (ind === "hemisphere") return out.set(THEMES[theme].hemi[n.hemisphere]);
  const a = attention(n, ind);
  if (a === null) return out.set(THEMES[theme].nodata);
  return rampColor(a, out);
}

// Each hemisphere spans a small hue range (lib/theme.ts), and each L1 branch takes its own shade of it,
// so neighbouring branches read as different clouds.
const shades = new Map<string, Color[]>();

/** Branch shade: `t` in 0..1 is the L1 branch's position among its siblings. */
export function branchColor(hemisphere: string, t: number, theme: Theme, out = new Color()): Color {
  const key = theme + hemisphere;
  let p = shades.get(key);
  if (!p) {
    const b = THEMES[theme].branches;
    p = (b[hemisphere as keyof typeof b] ?? b.root).map((c) => new Color(c));
    shades.set(key, p);
  }
  if (t <= 0.5) return out.copy(p[0]).lerp(p[1], t / 0.5);
  return out.copy(p[1]).lerp(p[2], (t - 0.5) / 0.5);
}

/** Attention 0..1 for one question's own metric (same scale as `attention` for nodes). */
export function starAttention(v: number | null, ind: Indicator): number | null {
  if (v === null || ind === "hemisphere") return null;
  return attention({ [ind]: v } as unknown as TreeNode, ind);
}
