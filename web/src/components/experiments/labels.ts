// Display words for the evaluator's labels (scripts/experiments/evaluate.py), shared by the index and the pages.
export const VERDICT: Record<string, string> = {
  headline: "headline", portrait: "portrait-worthy", atlas: "atlas", solid_dull: "solid but dull", needs_data: "needs data",
  muddled: "muddled", noise: "noise", trivial: "trivial", duplicate: "duplicate", wrong: "wrong",
};
export const OUTCOME: Record<string, string> = { keep: "keep", atlas: "atlas", rework: "rework", cut: "cut" };

// Jev's keep-or-discard answer about an experiment (take.py asks it), or null before it has answered
export function keepOf(e: { take?: { scores?: Record<string, number> } }): { verdict: "keep" | "discard"; p: number } | null {
  const k = e.take?.scores?.keep;
  if (typeof k !== "number") return null;
  return k >= 0.5 ? { verdict: "keep", p: k } : { verdict: "discard", p: 1 - k };
}
