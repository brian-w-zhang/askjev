import type { ExperimentMeme } from "../../experiments/types";

// Shape of portrait.json's "story" (scripts/portrait/story.py): each chapter's numbers, copied from the experiments.
export type ExLink = { id: string; title: string; rank: number };
type VS = { jev: number; people: number };

export type Story = {
  n_experiments: number;
  personality: {
    bigfive: { label: string; pct: number; guess: number; ci: [number, number] }[];
    type: string; type_people: string;
    axes: { pair: string; first: string; other: string; p_first: number; people_p_first: number; jev: string; people: string }[];
    honesty: ({ label: string } & VS)[]; dark: ({ label: string } & VS)[]; links: ExLink[];
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
    prices: { median_year: number; said_year: number; items: { item: string; year: number }[] };
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
  minds: {
    self: { cap: string; jev: number; people: number; above: string | null; below: string | null }[];
    ambiguity: VS; links: ExLink[];
  };
  edges: (ExLink & { line: string })[];
  jev_top: (ExLink & { line: string })[];
  memes: Record<string, ExperimentMeme>;
};
