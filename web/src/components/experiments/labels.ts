import type { Experiment, JevMetrics } from "./types";

// Display words for the evaluator's labels (scripts/experiments/evaluate.py), shared by the index and the pages.
export const VERDICT: Record<string, string> = {
  headline: "headline", portrait: "portrait-worthy", atlas: "atlas", solid_dull: "solid but dull", needs_data: "needs data",
  muddled: "muddled", noise: "noise", trivial: "trivial", duplicate: "duplicate", wrong: "wrong",
};
export const OUTCOME: Record<string, string> = { keep: "keep", atlas: "atlas", rework: "rework", cut: "cut" };


// Jev's answers about an experiment (scripts/experiments/take.py), in the shape the index sorts and labels by
export function jevOf(e: Pick<Experiment, "take">): JevMetrics | null {
  const s = e.take?.scores;
  if (!s) return null;
  const word = (q: string) => (e.take?.answers.find((a) => a.q === q)?.a ?? "").replace(/^The comparison is /, "");
  return {
    interesting: s.interesting ?? 0.5, describes: s.recognize ?? 0.5, predicted: s.expected ?? 0.5,
    trust: s.trust ?? 2, trustWord: word("How much should a reader rely on it?"),
    fair: s.fair ?? 2, fairWord: word("How fair is the comparison?"),
  };
}
