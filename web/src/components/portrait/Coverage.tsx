"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { Coverage as Cov, CoverageBranch, CoverageNode } from "../experiments/types";

// The atlas's Coverage tab: for every branch of the tree, how many of its questions an experiment about that topic
// uses, how many only a corpus-wide one uses, and how many have something to compare with (a right answer or real
// people's answers). Computed by scripts/experiments/coverage.py on every export.
type Sort = "least" | "most" | "size" | "name";
const SORTS: [Sort, string][] = [["least", "Least covered first"], ["most", "Most covered first"], ["size", "Most questions"], ["name", "A to Z"]];

const share = (x: number, n: number) => (n ? x / n : 0);
function pct(x: number, n: number) {
  const p = share(x, n);
  return p > 0 && p < 0.005 ? "<1%" : `${Math.round(p * 100)}%`;
}
const num = (x: number) => x.toLocaleString("en-US");

function Bar({ c }: { c: Pick<CoverageNode, "n" | "topic" | "cross_only"> }) {
  return (
    <span className="cv-bar" role="img" aria-label={`${pct(c.topic, c.n)} in a topic experiment, ${pct(c.cross_only, c.n)} only in a corpus-wide one`}>
      <i className="t" style={{ width: `${share(c.topic, c.n) * 100}%` }} />
      <i className="x" style={{ width: `${share(c.cross_only, c.n) * 100}%` }} />
    </span>
  );
}

function Exps({ c }: { c: CoverageNode }) {
  if (!c.exps.length) return <span className="cv-none">no topic experiment yet</span>;
  return (
    <span className="cv-exps">
      {c.exps.slice(0, 3).map((e) => (
        <Link key={e.id} href={`/portrait/atlas/${e.id}`} prefetch={false} title={`${num(e.n)} of these questions`}>{e.title}</Link>
      ))}
      {c.n_exps > 3 && <em>+{c.n_exps - 3} more</em>}
    </span>
  );
}

function Row({ c, sub, open, onToggle }: { c: CoverageNode; sub?: boolean; open?: boolean; onToggle?: () => void }) {
  const name = onToggle ? (
    <button type="button" className="cv-name" aria-expanded={open} onClick={onToggle}>
      <span className="cv-caret" aria-hidden>{open ? "▾" : "▸"}</span>{c.label}
    </button>
  ) : (
    <a className="cv-name" href={`/?node=${encodeURIComponent(c.id)}`} title="Open on the map">{c.label}</a>
  );
  return (
    <div className={`cv-row${sub ? " sub" : ""}`}>
      <div className="cv-label">{name}{sub && <Exps c={c} />}</div>
      <span className="cv-n">{num(c.n)}</span>
      <Bar c={c} />
      <span className="cv-p">{pct(c.topic, c.n)}</span>
      <span className="cv-k">{c.n_exps}</span>
      <span className="cv-c">{pct(c.comparable, c.n)}</span>
      <span className="cv-meta">{num(c.n)} questions · {c.n_exps} experiments · {pct(c.comparable, c.n)} comparable</span>
    </div>
  );
}

export default function Coverage({ cov }: { cov: Cov }) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<Sort>("least");
  const [open, setOpen] = useState<Set<string>>(new Set());
  const needle = q.trim().toLowerCase();
  const order = useMemo(() => {
    const key: Record<Sort, (c: CoverageNode) => number | string> = {
      least: (c) => share(c.topic, c.n), most: (c) => -share(c.topic, c.n), size: (c) => -c.n, name: (c) => c.label,
    };
    return <T extends CoverageNode>(xs: T[]) => [...xs].sort((a, b) => {
      const x = key[sort](a), y = key[sort](b);
      return typeof x === "string" ? x.localeCompare(y as string) : (x as number) - (y as number) || b.n - a.n;
    });
  }, [sort]);
  // a search keeps a branch when it or any of its topics matches, and opens it to show the matching topics
  const hit = (c: CoverageNode) => !needle || c.label.toLowerCase().includes(needle) || c.id.includes(needle);
  const branchTopics = (b: CoverageBranch) => (needle && !hit(b) ? b.topics.filter(hit) : b.topics);
  const toggle = (id: string) => setOpen((s) => { const t = new Set(s); if (t.has(id)) t.delete(id); else t.add(id); return t; });

  return (
    <div className="cv">
      <div className="cv-tools">
        <label className="ex-search">
          <span aria-hidden>⌕</span>
          <input placeholder="Search topics: love, finance, emotions…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search coverage" />
          {q && <button type="button" className="x" onClick={() => setQ("")} aria-label="Clear search">×</button>}
        </label>
        <label className="ex-sort">
          <span>Sort</span>
          <select value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
            {SORTS.map(([k, label]) => <option key={k} value={k}>{label}</option>)}
          </select>
        </label>
      </div>
      <div className="cv-legend">
        <span><i className="t" />in an experiment about the topic</span>
        <span><i className="x" />only in a corpus-wide one</span>
        <span><i className="o" />not used</span>
      </div>

      {cov.hemispheres.map((h) => {
        const branches = order(h.branches.filter((b) => hit(b) || b.topics.some(hit)));
        if (!branches.length) return null;
        return (
          <section key={h.id} className="cv-hemi">
            <header className="cv-hhead">
              <h2>{h.label}</h2>
              <span>{num(h.n)} questions · {pct(h.topic, h.n)} in a topic experiment · {h.n_exps} experiments</span>
              <Bar c={h} />
            </header>
            <div className="cv-cols" aria-hidden>
              <span>topic</span><span>questions</span><span /><span>covered</span><span>experiments</span><span>comparable</span>
            </div>
            {branches.map((b) => {
              const isOpen = open.has(b.id) || (!!needle && !hit(b));
              return (
                <div key={b.id} className="cv-branch">
                  <Row c={b} open={isOpen} onToggle={b.topics.length ? () => toggle(b.id) : undefined} />
                  {isOpen && order(branchTopics(b)).map((t) => <Row key={t.id} c={t} sub />)}
                </div>
              );
            })}
          </section>
        );
      })}
      <p className="at-foot">
        Covered: the share of a topic&rsquo;s questions used by at least one experiment about that topic. Corpus-wide
        experiments ({cov.cross.length}: calibration, option order, repeat noise, self vs people, torn vs sure and the
        like) use nearly every question, so they&rsquo;re counted apart. Comparable: questions with a right answer or
        real people&rsquo;s answers, which is what an experiment needs to compare Jev with something; a topic low on
        both needs new human data before it can have an experiment. Topics under 50 questions count toward their
        branch only.
      </p>
    </div>
  );
}
