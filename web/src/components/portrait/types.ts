// Shapes of data/analysis/portrait.json (scripts/portrait/export_page.py).
import type { Funny } from "./MemeFunny";
import type { Story } from "./story/types";

export type Dist = Record<string, number>;

export type Row = {
  id: string;
  text: string;
  state: string | null;
  options: string[];
  primitive: "noul" | "choice" | "score";
  node: string;
  source: string;
  hemisphere: "world" | "self" | "machine";
  jev: Dist | null;
  people: Dist | null;
  human: { dist: Dist; n: number | null; population: string | null } | null;
  truth: string | number | boolean | null;
  correct: boolean | null;
  top: string;
  p_top: number;
  labels?: Record<string, string>; // option descriptions, when the experiments export has them
};

// A ledger claim: the common fields, plus whatever the claim's script attached (families, facets, reliability...).
export type Claim = {
  id: string;
  section: string;
  sentence: string;
  tier: string;
  n: number;
  effect: unknown;
  ci90: [number, number] | null;
  examples: string[];
  script: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [extra: string]: any;
};

export type Task = { id: string; task: string; acc: number; decisive: number; band: string; n: number; chance: number | null };

export type SourceRow = { source: string; family: string; hemisphere: string; n: number; truth: number; humans: number; shown: number };

export type NodeCard = { node_id: string; n: number; [metric: string]: string | number | null };

export type PortraitData = {
  version: string;
  claims: Record<string, Claim>;
  rows: Record<string, Row>;
  work: Task[];
  sources: SourceRow[];
  nodes: NodeCard[];
  memes?: Record<string, Funny>;
  story?: Story;  // the chapters built from the experiments (scripts/portrait/story.py)  // how funny Jev finds each of the page's memes, by name
};

// What a quiz question needs on the client
export type QuizItem = { id: string; text: string; options: { key: string; label: string }[]; jev: Dist; human: Dist; n: number | null; domain: string };
