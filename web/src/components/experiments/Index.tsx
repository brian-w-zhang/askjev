"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import Chart from "./Chart";

import type { ExperimentCard } from "./types";

// The experiments library (docs/16 pass 4): one card per experiment with its result, a thumbnail of its chart and
// Jev's own verdict on it. Sorted by Jev's head-to-head ranking by default; family facets and search narrow it.
// Sorts beyond Jev's rank use its own answers about each experiment; the card then shows the value it's sorted by
type Sort = "rank" | "interesting" | "describes" | "describes_least" | "surprising" | "trust" | "fair" | "n" | "family";
const SORTS: [Sort, string][] = [
  ["rank", "Jev's rank"], ["interesting", "Most interesting, to Jev"], ["describes", "Describes Jev most"],
  ["describes_least", "Describes Jev least"], ["surprising", "Most surprising to Jev"], ["trust", "Most reliable, to Jev"],
  ["fair", "Fairest comparison, to Jev"], ["n", "Most questions"], ["family", "Family"],
];
const pct = (p: number) => `${Math.round(p * 100)}%`;
// the number a card shows for the sort in effect (none for Jev's rank, family or size)
function metric(c: ExperimentCard, sort: Sort): { text: string; title: string } | null {
  const j = c.jev;
  if (!j) return null;
  switch (sort) {
    case "interesting": return { text: `interesting to read: ${pct(j.interesting)}`, title: "Jev's probability that a curious person, not an AI researcher, would find it interesting to read" };
    case "describes": case "describes_least": return { text: `describes Jev: ${pct(j.describes)}`, title: "Jev's probability that the result matches how it sees itself" };
    case "surprising": return { text: `Jev saw it coming: ${pct(j.predicted)}`, title: "Jev's probability that it would have predicted this result about itself" };
    case "trust": return { text: `rely on it: ${j.trustWord.toLowerCase()}`, title: `How much Jev says a reader should rely on the result: ${j.trust.toFixed(1)} of 4` };
    case "fair": return { text: `comparison: ${j.fairWord.toLowerCase()}`, title: `How fair Jev finds the comparison: ${j.fair.toFixed(1)} of 4` };
    default: return null;
  }
}
const KEY: Partial<Record<Sort, (c: ExperimentCard) => number>> = {
  interesting: (c) => -(c.jev?.interesting ?? 0), describes: (c) => -(c.jev?.describes ?? 0), describes_least: (c) => c.jev?.describes ?? 1,
  surprising: (c) => c.jev?.predicted ?? 1, trust: (c) => -(c.jev?.trust ?? 0), fair: (c) => -(c.jev?.fair ?? 0), n: (c) => -(c.n_rows ?? 0),
};
const FEW = 7;

export default function ExperimentsIndex({ cards }: { cards: ExperimentCard[] }) {
  const [q, setQ] = useState("");
  const [family, setFamily] = useState("");
  const [sort, setSort] = useState<Sort>("rank");
  const [open, setOpen] = useState(false);
  const needle = q.trim().toLowerCase();
  const ranks = useMemo(() => new Map(cards.map((c, i) => [c.id, i + 1])), [cards]);
  const rank = (c: ExperimentCard) => ranks.get(c.id) ?? 999;
  const matches = useMemo(() => cards.filter((c) => !needle || `${c.title} ${c.result} ${c.family_label} ${c.id}`.toLowerCase().includes(needle)), [cards, needle]);
  const families = useMemo(() => {
    const m = new Map<string, { label: string; n: number }>();
    for (const c of matches) m.set(c.family, { label: c.family_label, n: (m.get(c.family)?.n ?? 0) + 1 });
    return [...m].sort((a, b) => b[1].n - a[1].n);
  }, [matches]);
  // the biggest families first; the rest behind "more", though a chosen one always stays visible
  const famShown = open ? families : families.filter(([f], i) => i < FEW || f === family);
  const shown = useMemo(() => {
    const r = matches.filter((c) => !family || c.family === family);
    if (sort === "family") return [...r].sort((a, b) => a.family_label.localeCompare(b.family_label) || (ranks.get(a.id) ?? 999) - (ranks.get(b.id) ?? 999));
    const k = KEY[sort];
    return k ? [...r].sort((a, b) => k(a) - k(b) || (ranks.get(a.id) ?? 999) - (ranks.get(b.id) ?? 999)) : r;
  }, [matches, family, sort, ranks]);

  return (
    <>
      <div className="ex-tools">
        <div className="ex-tools-top">
          <label className="ex-search">
            <span aria-hidden>⌕</span>
            <input placeholder="Search experiments" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search experiments" />
            {q && <button type="button" className="x" onClick={() => setQ("")} aria-label="Clear search">×</button>}
          </label>
          <label className="ex-sort">
            <span>Sort</span>
            <select value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
              {SORTS.map(([k, label]) => <option key={k} value={k}>{label}</option>)}
            </select>
          </label>
        </div>
        <div className={`ex-fams${open ? " open" : ""}`} role="group" aria-label="Filter by family" data-scroll="x">
          <button type="button" aria-pressed={!family} onClick={() => setFamily("")}>All <em>{matches.length}</em></button>
          {famShown.map(([f, { label, n }]) => (
            <button key={f} type="button" aria-pressed={family === f} onClick={() => setFamily(family === f ? "" : f)}>{label} <em>{n}</em></button>
          ))}
          {families.length > FEW && (
            <button type="button" className="ex-morefam" onClick={() => setOpen(!open)} aria-expanded={open}>
              {open ? "Show fewer" : `+ ${families.length - FEW} more`}
            </button>
          )}
        </div>
        <p className="ex-count">
          {shown.length === cards.length ? `${cards.length} experiments` : `${shown.length} of ${cards.length} experiments`}
          {(q || family) && <button type="button" onClick={() => { setQ(""); setFamily(""); }}>Clear filters</button>}
        </p>
      </div>
      {shown.length === 0 && <p className="at-empty">Nothing matches &ldquo;{q}&rdquo;.</p>}
      <div className="ex-grid">
        {shown.map((c) => (
          <Link key={c.id} href={`/portrait/atlas/${c.id}`} prefetch={false} className="ex-card">
            <div className="ex-top">
              <span className="ex-fam">{c.family_label}</span>
              <span className="ex-rank" title="Rank from Jev's head-to-heads and its own answers about each experiment">#{rank(c)}</span>
            </div>
            <h3>{c.title}</h3>
            <div className="ex-thumb" aria-hidden><Chart chart={c.chart} mini /></div>
            <p className="ex-res">{c.result}</p>
            <div className="ex-meta">
              <span>{(c.n_rows ?? 0).toLocaleString("en-US")} {c.n_rows === 1 ? "question" : "questions"}</span>
              {(() => { const m = metric(c, sort); return m && <span className="ex-metric" title={m.title}>{m.text}</span>; })()}
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}
