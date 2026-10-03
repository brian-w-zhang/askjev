import type { ExperimentMeme } from "../../experiments/types";

// Shape of portrait.json's "story" (scripts/portrait/story.py): each chapter's numbers, copied from the experiments.
export type ExLink = { id: string; title: string; rank: number; line?: string };
type VS = { jev: number; people: number };

export type Story = {
  n_experiments: number;
  personality: {
    bigfive: { label: string; pct: number; guess: number; ci: [number, number] }[];
    type: string; type_people: string;
    axes: { pair: string; first: string; other: string; p_first: number; people_p_first: number; jev: string; people: string; n_items: number; ci: [number, number] }[];
    honesty: ({ label: string } & VS)[]; dark: ({ label: string } & VS)[]; links: ExLink[];
    n_rows?: Record<string, number>; twin?: { name: string; work: string; r: number }[];
  };
  taste: {
    domains: {
      domain: string; name: string; games: number | null; link: ExLink; bottom: string[];
      top: { label: string; wins: number | null; img: { file: string; w: number; h: number; title: string; page: string } | null }[];
    }[];
    dodge: { other: number; named_right: number }; links: ExLink[];
  };
  words: {
    probability: ({ phrase: string } & VS)[]; prob_rho: number;
    amounts: { phrase: string; jev: string; people: string }[];
    kiki: VS; bouba: VS; spread: number; n_shapes: number;
    colors: { feeling: string; jev: string; people: string }[];
    stirring: ({ word: string } & VS)[]; hex: number; links: ExLink[];
  };
  numbers: {
    prices: { median_year: number; said_year: number; items: { item: string; year: number; lo?: number; hi?: number; now?: number | null }[] };
    lethal: { slope_jev: number; slope_people: number; rows: { cause: string; truth: number; jev: number; people: number }[] };
    beauty: { crowd: string; pick: number; win: number | null; p: number }[];
    wallets: { rows: { country: string; true: number; jev: number }[]; money_up_true: number; money_up_jev: number; n: number };
    links: ExLink[];
  };
  morals: {
    trolley: Record<"Switch" | "Loop" | "Footbridge", VS>; trolley_n: number;
    machine: ({ label: string } & VS)[]; dropped: string[];
    free_will: ({ item: string } & VS)[]; links: ExLink[];
  };
  pressure: {
    crowd: { true: number; false: number; flip: number; example: string };
    user: { flipped: number; shift_wrong: number; example: string };
    anchor: { jev: number }; links: ExLink[];
  };
  risk: {
    reflection: Record<"gains" | "losses", VS>; ev: VS; effects: { n: number; shows: number; reversed: number };
    ambiguity: VS & { vs_sure: VS }; links: ExLink[];
  };
  howdy: {
    direct: { id: string; q: string; a: string; p: number; people_same: number; people_top: string | null; people_top_p: number | null; n: number | null }[];
    checkin: { q: string; a: string; p: number; people: number; n: number | null }[];
    scales: Record<string, { name: string; items: number; range: [number, number]; self: number; people: number; reversed: number | null; band_self: string; band_people: string }>;
  };
  methods: Methods;
  trip?: { id: string; text: string; source: string; path: string[]; method: string | null; confidence: number | null;
    jev: Record<string, number>; people: Record<string, number> | null; human: Record<string, number>; n: number | null; population: string | null };
  defaults: {
    verbs: { label: string; value: number; ci: number[]; n: number }[];
    other: { topic: string; top: number }[]; middle: { label: string; mid: number }[]; links: ExLink[];
  };
  work: {
    calibration: Record<"noul" | "choice", { label: string; conf: number; acc: number; n: number }[]>;
    errs: { kind: string; label: string; says: number; base: number; right: number; n: number }[];
    links: ExLink[];
  };
  knows: {
    calibration: { label: string; conf: number; acc: number; n: number }[];
    trivia: { label: string; acc: number; ci: number[]; n: number }[];
    fame: { label: string; acc: number; conf: number; n: number }[]; links: ExLink[];
  };
  more?: Record<string, ExLink[]>;
  self_rating?: { n: number; yes: number; unsure: number };
  // two tasks that look alike, one experiment each: a = the one Jev handles, b = its neighbor; coin = b is a yes/no, so 50% is a coin
  jagged_pairs: { field: string; a: string; av: number; b: string; bv: number; coin: boolean; unit: "right" | "caught"; link: ExLink }[];
  field_share: number;
  sure_wrong: { rows: { label: string; right: number; sure: number; chance: number; n: number; honest: boolean }[]; n_over: number; n_tasks: number; link: ExLink };
  edges: (ExLink & { line: string })[];
  jev_top: (ExLink & { line: string })[];
  memes: Record<string, ExperimentMeme>;
};

export type Source = { source: string; n: number; truth: number; humans: number; line?: string; license?: string; url?: string };
export type Methods = {
  families: { family: string; what: string; n: number; sources: Source[] }[];
  total: number; hidden: number; truth: number; humans: number; human_dists: number; median_people: number; real: number;
  tree: { hemisphere: string; source: string; n: number }[]; tree_depth: number; tree_nodes: number;
  placement: Record<string, number>; placement_eval: string | null;
  screen: { first_hidden: number; rechecked: number; released: number; by_rule: number };
  round_trip: { n: number; kept: number }; dedupe: number;
  calls: number; median_ms: number; first_call: string; last_call: string;
  jobs: { calls: Record<string, number>; questions: Record<string, number>; n_calls: number; n_questions: number } | null;
  job_info: Record<string, { type: string; where: string; ask: string; what: string }>;
};
