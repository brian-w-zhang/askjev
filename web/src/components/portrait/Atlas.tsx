"use client";

import Link from "next/link";
import { useEffect, useLayoutEffect, useMemo, useState } from "react";
import type { NodeCard, SourceRow } from "./types";
import ExperimentsIndex from "../experiments/Index";
import Coverage from "./Coverage";
import { TABS, type Tab } from "./atlasTabs";
import type { Coverage as Cov, ExperimentCard } from "../experiments/types";

// The atlas (docs/16 pass 4): the experiments library; how much of each topic they cover; every topic's indicators;
// the source table. The heading, description and figures follow the open tab. Topic cards and sources load when
// their tab first opens.
const pctf = (x: unknown) => (typeof x === "number" ? `${Math.round(x * 100)}%` : "–");
const fixed = (x: unknown, d = 2) => (typeof x === "number" ? x.toFixed(d) : "–");
const num = (x: number) => x.toLocaleString("en-US");
const share = (x: number, n: number) => `${Math.round((n ? x / n : 0) * 100)}%`;

export default function Atlas({ nNodes, nSources, nQuestions, experiments, coverage }: {
  nNodes: number; nSources: number; nQuestions: number; experiments: ExperimentCard[]; coverage: Cov | null;
}) {
  const [tab, setTab] = useState<Tab>("experiments");
  // a link or reload with ?tab= opens on that tab (the page itself is static, so the address is read here)
  useLayoutEffect(() => {
    const want = new URLSearchParams(window.location.search).get("tab");
    if (want && (TABS as string[]).includes(want)) setTab(want as Tab);
  }, []);
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<{ key: string; desc: boolean }>({ key: "n", desc: true });
  const [nodes, setNodes] = useState<NodeCard[] | null>(null);
  const [sources, setSources] = useState<SourceRow[] | null>(null);
  const [failed, setFailed] = useState(false);
  const needle = q.trim().toLowerCase();

  // the open tab goes in the URL, so a link or a reload lands on it
  const pick = (t: Tab) => {
    setTab(t);
    setQ("");
    const u = new URL(window.location.href);
    if (t === "experiments") u.searchParams.delete("tab"); else u.searchParams.set("tab", t);
    window.history.replaceState(null, "", u);
  };

  // topic cards and sources are most of the atlas's data: fetched when their tab first opens
  useEffect(() => {
    const part = tab === "topics" && !nodes ? "nodes" : tab === "sources" && !sources ? "sources" : null;
    if (!part) return;
    fetch(`/portrait/atlas/tables?part=${part}`).then((r) => (r.ok ? r.json() : Promise.reject())).then((x) => (part === "nodes" ? setNodes(x) : setSources(x))).catch(() => setFailed(true));
  }, [tab, nodes, sources]);

  const shownNodes = useMemo(() => {
    const r = (nodes ?? []).filter((n) => !needle || `${n.node_id} ${n.label ?? ""}`.toLowerCase().includes(needle));
    return [...r].sort((a, b) => {
      const x = a[sort.key] as number | null, y = b[sort.key] as number | null;
      if (x === y) return 0;
      if (x === null || x === undefined) return 1;
      if (y === null || y === undefined) return -1;
      return sort.desc ? y - x : x - y;
    }).slice(0, 400);
  }, [nodes, needle, sort]);
  const shownSources = useMemo(() => (sources ?? []).filter((s) => !needle || `${s.source} ${s.family}`.toLowerCase().includes(needle)), [sources, needle]);

  const th = (key: string, text: string) => (
    <th aria-sort={sort.key === key ? (sort.desc ? "descending" : "ascending") : undefined}>
      <button type="button" className="thb" onClick={() => setSort({ key, desc: sort.key === key ? !sort.desc : true })}>
        {text}{sort.key === key ? (sort.desc ? " ↓" : " ↑") : ""}</button></th>
  );

  const t = coverage?.total;
  const head: Record<Tab, { title: string; lede: React.ReactNode; stats: [string, string][] }> = {
    experiments: {
      title: "Experiments",
      lede: <>Each one gathers many of Jev&rsquo;s answers into something you can learn about it in a minute, next to real
        people or a right answer where one exists. The <Link href="/portrait" prefetch={false}>portrait</Link> picks a few;
        here are all of them, the ones Jev finds most interesting first. Indicators, not a benchmark.</>,
      stats: [["experiments", num(experiments.length)], ["families", num(new Set(experiments.map((c) => c.family)).size)], ["questions on the map", num(nQuestions)]],
    },
    coverage: {
      title: "Coverage",
      lede: <>How much of each topic the experiments actually use. Open a branch to see its topics and the experiments
        that draw on them; the thin ones are where the next experiments should go.</>,
      stats: t ? [["in a topic experiment", share(t.topic, t.n)], ["only corpus-wide", share(t.cross_only, t.n)], ["not used", share(t.n - t.topic - t.cross_only, t.n)]] : [],
    },
    topics: {
      title: "Topics",
      lede: <>Every topic in the tree with its indicators: how often Jev is right where there&rsquo;s an answer, how sure
        it is, how stable its answer is when the question is reworded or reordered, and how far its own answer sits from
        its guess about people.</>,
      stats: [["topics", num(nNodes)], ["questions", num(nQuestions)]],
    },
    sources: {
      title: "Sources",
      lede: <>Where the questions came from: published datasets, surveys, polls and question banks written for this
        project, with how many carry a right answer or real people&rsquo;s answers.</>,
      stats: [["sources", num(nSources)]],
    },
  };
  const h = head[tab];

  return (
    <div className="atlas">
      <header className="at-head">
        <div className="at-top">
          <span className="pt-tag">Jev.Atlas</span>
          <div className="tabs at-tabs" role="tablist" aria-label="Atlas sections">
            {TABS.map((x) => (
              <button key={x} type="button" role="tab" aria-selected={tab === x} onClick={() => pick(x)}>
                {x[0].toUpperCase() + x.slice(1)}
              </button>
            ))}
          </div>
        </div>
        <div className="at-intro">
          <div>
            <h1>{h.title}</h1>
            <p>{h.lede}</p>
          </div>
          {h.stats.length > 0 && (
            <dl className="at-stats">
              {h.stats.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}
            </dl>
          )}
        </div>
      </header>

      {tab === "experiments" && (
        <>
          <ExperimentsIndex cards={experiments} />
          <p className="at-foot">The order is Jev&rsquo;s own: it read the case studies two at a time and picked the one
            that teaches a curious reader more, adjusted by how much it would rely on each result and how fair it finds the
            comparison, anchored to a gold set labeled from Brian&rsquo;s feedback (docs/experiments/evaluator.md).</p>
        </>
      )}

      {tab === "coverage" && (coverage ? <Coverage cov={coverage} /> : <p className="at-empty">No coverage data. Run scripts/experiments/export.py.</p>)}

      {(tab === "topics" || tab === "sources") && (
        <label className="ex-search at-search">
          <span aria-hidden>⌕</span>
          <input placeholder={tab === "topics" ? "Search topics: happiness, spam…" : "Search sources"} value={q} onChange={(e) => setQ(e.target.value)} aria-label={`Search ${tab}`} />
          {q && <button type="button" className="x" onClick={() => setQ("")} aria-label="Clear search">×</button>}
        </label>
      )}
      {((tab === "topics" && !nodes) || (tab === "sources" && !sources)) && (
        <p className="at-empty">{failed ? "Couldn't load this table. Try reloading the page." : "Loading…"}</p>
      )}
      {tab === "topics" && nodes && (
        <>
          <div className="pt-scroll">
            <table className="pt-table">
              <thead><tr><th>topic</th>{th("n", "questions")}{th("accuracy", "right")}{th("confidence", "confidence")}{th("decisive", "decisive")}{th("stability", "stable")}{th("frame_gap", "self vs people")}{th("z_max", "unusual")}</tr></thead>
              <tbody>
                {shownNodes.map((n) => (
                  <tr key={n.node_id}>
                    <td><a href={`/?node=${encodeURIComponent(n.node_id)}`} title="Open on the map">{(n.label as string) ?? n.node_id}</a><div className="at-id">{n.node_id}</div></td>
                    <td className="n">{Number(n.n).toLocaleString("en-US")}</td>
                    <td className="n">{pctf(n.accuracy)}</td><td className="n">{pctf(n.confidence)}</td><td className="n">{pctf(n.decisive)}</td>
                    <td className="n">{pctf(n.stability)}</td><td className="n">{fixed(n.frame_gap)}</td><td className="n">{fixed(n.z_max, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="at-foot">Sorted by the column you pick (up to 400 shown). Unusual: the largest standardized distance
            from the corpus average on any indicator. Click a topic to open it on the map.</p>
        </>
      )}
      {tab === "sources" && sources && (
        <>
          <div className="pt-scroll">
            <table className="pt-table">
              <thead><tr><th>source</th><th>family</th><th>side</th><th style={{ textAlign: "right" }}>questions</th><th style={{ textAlign: "right" }}>right answer</th><th style={{ textAlign: "right" }}>human answers</th><th style={{ textAlign: "right" }}>shown</th></tr></thead>
              <tbody>
                {shownSources.map((s) => (
                  <tr key={`${s.source}-${s.hemisphere}-${s.family}`}>
                    <td className="at-mono">{s.source}</td><td>{s.family}</td><td>{s.hemisphere}</td>
                    <td className="n">{s.n.toLocaleString("en-US")}</td><td className="n">{pctf(s.truth)}</td><td className="n">{pctf(s.humans)}</td><td className="n">{pctf(s.shown)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="at-foot">Counts include hidden questions; shown is the share on the map.</p>
        </>
      )}
    </div>
  );
}
