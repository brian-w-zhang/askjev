"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import Chart from "./Chart";
import { useMemeFollower } from "./MemeFollower";
import { OUTCOME, VERDICT } from "./labels";
import type { ExperimentCard } from "./types";

// The experiments library (docs/16 pass 4): one card per experiment with its result, a thumbnail of its chart and
// Jev's own verdict on it. Sorted by Jev's head-to-head ranking by default; family facets and search narrow it.
type Sort = "rank" | "family" | "n";

export default function ExperimentsIndex({ cards }: { cards: ExperimentCard[] }) {
  const [q, setQ] = useState("");
  const [family, setFamily] = useState("");
  const [sort, setSort] = useState<Sort>("rank");
  const needle = q.trim().toLowerCase();
  const follower = useMemeFollower();
  const ranks = useMemo(() => new Map(cards.map((c, i) => [c.id, i + 1])), [cards]);
  const rank = (c: ExperimentCard) => ranks.get(c.id) ?? 999;
  const matches = useMemo(() => cards.filter((c) => !needle || `${c.title} ${c.result} ${c.family_label} ${c.id}`.toLowerCase().includes(needle)), [cards, needle]);
  const families = useMemo(() => {
    const m = new Map<string, { label: string; n: number }>();
    for (const c of matches) m.set(c.family, { label: c.family_label, n: (m.get(c.family)?.n ?? 0) + 1 });
    return [...m].sort((a, b) => b[1].n - a[1].n);
  }, [matches]);
  const shown = useMemo(() => {
    const r = matches.filter((c) => !family || c.family === family);
    if (sort === "family") return [...r].sort((a, b) => a.family_label.localeCompare(b.family_label) || (ranks.get(a.id) ?? 999) - (ranks.get(b.id) ?? 999));
    if (sort === "n") return [...r].sort((a, b) => b.n - a.n);
    return r;
  }, [matches, family, sort, ranks]);

  return (
    <>
      <div className="at-bar ex-bar">
        <input className="pt-input" placeholder="Search experiments: probability, taste, moral machine…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search experiments" />
        <div className="pt-filters" role="group" aria-label="Filter by family">
          <button type="button" className="facet" aria-pressed={!family} onClick={() => setFamily("")}>all <em>{matches.length}</em></button>
          {families.map(([f, { label, n }]) => (
            <button key={f} type="button" className="facet" aria-pressed={family === f} onClick={() => setFamily(family === f ? "" : f)}>{label} <em>{n}</em></button>
          ))}
          <span className="sp" />
          <span className="viewtoggle" role="group" aria-label="Sort">
            <button type="button" aria-pressed={sort === "rank"} onClick={() => setSort("rank")}>Jev&rsquo;s rank</button>
            <button type="button" aria-pressed={sort === "family"} onClick={() => setSort("family")}>family</button>
            <button type="button" aria-pressed={sort === "n"} onClick={() => setSort("n")}>size</button>
          </span>
        </div>
      </div>
      {shown.length === 0 && <p className="at-empty">Nothing matches &ldquo;{q}&rdquo;.</p>}
      <div className="ex-grid">
        {shown.map((c) => (
          <Link key={c.id} href={`/portrait/atlas/${c.id}`} prefetch={false} className={`ex-card o-${c.evaluation?.outcome ?? "none"}`} {...follower.handlers(c.meme)}>
            <div className="ex-top">
              <span className="ex-fam">{c.family_label}</span>
              <span className="ex-rank" title="Jev's head-to-head ranking of all experiments">#{rank(c)}</span>
            </div>
            <h3>{c.title}</h3>
            <div className="ex-thumb" aria-hidden><Chart chart={c.chart} mini /></div>
            <p className="ex-res">{c.result}</p>
            <div className="ex-meta">
              {c.evaluation ? (
                <>
                  <span className={`ex-verdict ${c.evaluation.outcome}`}>{OUTCOME[c.evaluation.outcome] ?? c.evaluation.outcome}</span>
                  {c.evaluation.top && <span>Jev: {VERDICT[c.evaluation.top] ?? c.evaluation.top}</span>}
                  {typeof c.evaluation.interest === "number" && <span>interest {c.evaluation.interest.toFixed(1)}/10</span>}
                </>
              ) : <span>not evaluated yet</span>}
              <span className="sp" />
              <span>n = {c.n.toLocaleString("en-US")}{c.new_questions ? ` · ${c.new_questions.toLocaleString("en-US")} new` : ""}</span>
            </div>
          </Link>
        ))}
      </div>
      {follower.layer}
    </>
  );
}
