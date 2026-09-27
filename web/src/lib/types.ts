export type Hemisphere = "root" | "world" | "self" | "machine";

export interface TreeNode {
  id: string;
  parent_id: string | null;
  path: string;
  depth: number;
  hemisphere: Hemisphere;
  label: string;
  description: string;
  ord: number | null;
  n_questions: number;
  n_asked: number;
  kind_counts: Record<string, number> | null;
  stability: number | null;
  frame_gap: number | null;
  human_gap: number | null;
  calibration_ece: number | null;
  placement_conf: number | null;
  fragile_share: number | null;
  n_children: number;
  n_desc: number;
  n_match?: number;
}

export type Indicator = "hemisphere" | "stability" | "human_gap" | "frame_gap" | "placement_conf" | "calibration_ece";

export interface PathStep { id: string; label: string }

export interface SearchHit {
  id: string;
  text: string;
  primitive: "noul" | "choice" | "score";
  node_id: string;
  hemisphere: Hemisphere;
  sim: number;
  score: number;
  path: PathStep[];
  star?: number; // index of the question's dot in the star snapshot (-1: not drawn, e.g. hidden)
  jev_p?: number | null;
  answer?: { label: string; p: number } | null; // Jev's stored top answer to this question
  similar?: { id: string; text: string; variant: boolean }[]; // rewordings (and same-text variants) folded into this row
  agree?: boolean | null; // do Jev's answers to the rewordings agree? (null: fewer than two answered)
}

export interface NodeHit { id: string; label: string; hemisphere: Hemisphere; sim: number; path: PathStep[] }

export interface Filters { kind: string; primitive: string; origin: string }
