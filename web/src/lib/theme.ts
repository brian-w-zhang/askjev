import type { Hemisphere } from "./types";

// Light and dark looks (docs/07-ui.md, Look), both taken from typesafe.ai: the light one is their hero
// (pale sky, pink cloud), the dark one their ink FAQ section. The sky is twilight over a still sea. The 3D scene reads these; the page
// chrome reads the matching CSS variables in globals.css.

export type Theme = "light" | "dark";

export interface ThemeColors {
  sky: string; // the page background behind the canvas (and the upper sky)
  /** The dome, horizon up: [0] horizon, then rising bands, last = zenith. */
  ramp: string[];
  glow: string; // twilight glow low on the sun's side
  glowCore: string; // its brightest line, right at the horizon
  belt: string; // the Belt of Venus: the pink band opposite the sun
  shadow: string; // Earth's shadow: the blue-grey band under the belt
  cloudLit: string; // cloud faces turned to the light
  cloudDark: string; // cloud bodies against the light (silhouettes) and their shadow sides
  cloudRim: string; // the thin rim where light catches a cloud's edge
  water: string; // the sea straight down
  stars: number; // 0..1: stars overhead (night only)
  ink: string; // tree paths, the ink walker
  dim: string; // nodes outside a lit path
  nodata: string; // stars and nodes with no indicator data
  hemi: Record<Hemisphere, string>;
  branches: Record<Hemisphere, [string, string, string]>; // each hemisphere's L1 branch shades
  /**
   * Inks the halftone may print with, each with its screen (as in print, every ink gets its own):
   * 0 fine grain, 1 round dots at 45°, 2 horizontal lines, 3 diagonal lines, 4 plus grid.
   * Same length in both themes (it's a fixed-size shader uniform).
   */
  dither: [string, number][];
}

// Light: a clear evening in typesafe.ai's hero colors (pale blue sky, pink cloud edges, lilac shadows).
// Dark: the same place after sunset, in the colors of their dark docs site (aubergine black, hot-pink accent).
export const THEMES: Record<Theme, ThemeColors> = {
  light: {
    sky: "#DBF0FF",
    ramp: ["#F8DDEA", "#F8DDEA", "#DBF0FF", "#DBF0FF", "#C4D6F5"],
    glow: "#F8DDEA",
    glowCore: "#FFA1FF",
    belt: "#F8CFE3",
    shadow: "#C8CBE4",
    cloudLit: "#FEFEFE",
    cloudDark: "#B7B0D8",
    cloudRim: "#FFA1FF",
    water: "#C4D6F5",
    stars: 0,
    ink: "#1E1E1E",
    dim: "#C9C9C9",
    nodata: "#B7B0D8",
    hemi: { root: "#6E6E6E", world: "#4B5BD6", self: "#F386A1", machine: "#E8663D" },
    branches: {
      world: ["#3A48B8", "#4B5BD6", "#7D89E6"],
      self: ["#E86F90", "#F386A1", "#F7A8BC"],
      machine: ["#D9542B", "#E8663D", "#F09A6E"],
      root: ["#6E6E6E", "#6E6E6E", "#6E6E6E"],
    },
    dither: [
      ["#FEFEFE", 0], ["#F8DDEA", 0], ["#E4DCF6", 0], ["#DBF0FF", 0], ["#C4D6F5", 0], ["#C8CBE4", 0],
      ["#B7B0D8", 0], ["#FFA1FF", 1], ["#D45BB6", 1], ["#F386A1", 4], ["#4B5BD6", 2], ["#7D89E6", 2],
      ["#E8663D", 3], ["#03AA5C", 0], ["#1E1E1E", 0], ["#F8CFE3", 0],
    ],
  },
  dark: {
    sky: "#0D0B14",
    ramp: ["#7E4880", "#443870", "#27234A", "#161630", "#0D0B14"],
    glow: "#7E4880",
    glowCore: "#D45BB6",
    belt: "#443870",
    shadow: "#161630",
    cloudLit: "#443870",
    cloudDark: "#1C1830",
    cloudRim: "#FF78F2",
    water: "#0D0B14",
    stars: 1,
    ink: "#FEFEFE",
    dim: "#4A4660",
    nodata: "#4A4660",
    hemi: { root: "#9A9A9A", world: "#7D89E6", self: "#F386A1", machine: "#F0885E" },
    branches: {
      world: ["#5D6BDE", "#7D89E6", "#A6AEF0"],
      self: ["#E86F90", "#F386A1", "#F7A8BC"],
      machine: ["#E8663D", "#F0885E", "#F5AE8A"],
      root: ["#9A9A9A", "#9A9A9A", "#9A9A9A"],
    },
    dither: [
      ["#0D0B14", 0], ["#161630", 0], ["#27234A", 0], ["#443870", 0], ["#7E4880", 0], ["#1C1830", 0],
      ["#4A4660", 0], ["#FF78F2", 1], ["#D45BB6", 1], ["#F386A1", 4], ["#7D89E6", 2], ["#A6AEF0", 2],
      ["#F0885E", 3], ["#03AA5C", 0], ["#FEFEFE", 0], ["#9DB6E6", 2],
    ],
  },
};

export const JEV_GREEN = "#03AA5C"; // Jev's own path and answers, in both themes
export const HOT = "#D45BB6"; // worth a look
