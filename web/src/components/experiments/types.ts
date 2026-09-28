import type { Row } from "../portrait/types";

// One experiment as scripts/experiments/export.py writes it (data/analysis/experiments.json, private).
export type Chart = { type: string; [k: string]: unknown };
export type Evaluation = {
  outcome: "keep" | "atlas" | "rework" | "cut" | string;
  strength: number | null;
  top: string | null;
  interest: number | null;
  verdict: Record<string, number> | null;
  checks: Record<string, number> | null;
  version: string | null;
};
export type SourceUse = { name: string; shown: number; nodes: { node: string; n: number; label: string | null }[] };
export type Experiment = {
  id: string; family: string; family_label: string; title: string;
  question: string; why: string; sourcing: string; collection: string; scoring: string; chart_desc: string;
  compared_with: string; limits: string; new_questions: number; sources: SourceUse[];
  result: string; evidence: string; robustness: string; n: number;
  chart: Chart; rows: Row[]; evaluation: Evaluation | null; portrait_rank?: number | null;
  n_rows?: number; n_flagged?: { wrong: number; differs: number }; n_topics?: number;
  topics?: { node: string; n: number; label: string; parent: string; parent_label: string }[];
  case?: { sections: Partial<Record<"why" | "data" | "asked" | "measured" | "found" | "means", string>>; chart_note: string;
           caveats: { label: string; text: string }[]; facts: string[] };
  meme?: { file: string; alt: string | null; caption: string | null };
  take?: Take;
};
export type ExperimentsData = { experiments: Experiment[]; families: Record<string, string> };
// The index needs only the card fields; charts go along as small thumbnails.
export type ExperimentCard = Pick<Experiment, "id" | "family" | "family_label" | "title" | "result" | "n" | "new_questions" | "evaluation" | "portrait_rank" | "meme"> & { chart: Chart };

// Jev's take (docs/17 item 4): its answers to questions about the experiment, and the paragraph built from them.
export type Take = { text: string; answers: { q: string; a: string; p: number | null }[] };
