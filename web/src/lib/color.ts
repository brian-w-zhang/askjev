import { Color } from "three";
import type { Indicator, TreeNode } from "./types";
import { HEMI_COLOR } from "./layout";

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

const RAMP = [new Color("#2B6F8F"), new Color("#9D86F0"), new Color("#FF5D86")];
const NODATA = new Color("#343A52");

export function rampColor(t: number, out = new Color()): Color {
  if (t <= 0.5) return out.copy(RAMP[0]).lerp(RAMP[1], t / 0.5);
  return out.copy(RAMP[1]).lerp(RAMP[2], (t - 0.5) / 0.5);
}

export const RAMP_CSS = "linear-gradient(90deg, #2B6F8F, #9D86F0, #FF5D86)";

export function nodeColor(n: TreeNode, ind: Indicator, out = new Color()): Color {
  if (ind === "hemisphere") return out.set(HEMI_COLOR[n.hemisphere]);
  const a = attention(n, ind);
  if (a === null) return out.copy(NODATA);
  return rampColor(a, out);
}
