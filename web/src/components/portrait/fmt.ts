import type { Row } from "./types";

// Rounds like Python's format(x, ".0%") (half to even on the scaled value), so the page matches the ledger's sentences.
export function pct(x: number, digits = 0) {
  const v = x * 100 * 10 ** digits;
  let r = Math.round(v);
  if (Math.abs(v - Math.trunc(v)) === 0.5 && r % 2 !== 0) r -= 1;
  return `${(r / 10 ** digits).toFixed(digits)}%`;
}
export const int = (x: number) => Math.round(x).toLocaleString("en-US");
export const num = (x: number, digits = 2) => x.toFixed(digits);
export const signed = (x: number, digits = 2) => `${x >= 0 ? "+" : "−"}${Math.abs(x).toFixed(digits)}`;
export const ordinal = (x: number) => {
  const n = Math.round(x);
  const s = n % 100 >= 11 && n % 100 <= 13 ? "th" : ["th", "st", "nd", "rd"][n % 10] ?? "th";
  return `${n}${s}`;
};
export const compact = (x: number) =>
  x >= 1e6 ? `${(x / 1e6).toFixed(x >= 1e7 ? 0 : 1)}M` : x >= 1e3 ? `${Math.round(x / 1e3)}k` : String(x);

// Option names are snake_case slugs Jev saw verbatim; show them as words.
export function label(slug: string): string {
  const s = slug.replace(/_s_/g, "'s ").replace(/_t_/g, "'t ").replace(/_/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// Domain (L1) names as display words
export const domain = (l1: string) => label(l1).replace(/^Ai /, "AI ");

// The label for one key of a row's distribution: score levels are indexes into options, the rest are option slugs.
export function optionLabel(row: Row, key: string): string {
  if (row.primitive === "score" && /^\d+$/.test(key) && row.options[+key]) return row.options[+key];
  if (row.primitive === "noul") return key === "true" ? "Yes" : key === "false" ? "No" : label(key);
  // head-to-head options are names (artists, games, films): title case them
  if (row.source.endsWith("_pairs")) return key.split("_").filter(Boolean).map((w) => w[0].toUpperCase() + w.slice(1)).join(" ");
  return label(key);
}

export function truthKey(row: Row): string | null {
  if (row.truth === null || row.truth === undefined) return null;
  if (typeof row.truth === "boolean") return row.truth ? "true" : "false";
  return String(row.truth);
}

export function topOf(d: Record<string, number> | null | undefined): string | null {
  if (!d) return null;
  let best: string | null = null;
  for (const k in d) if (best === null || d[k] > d[best]) best = k;
  return best;
}
