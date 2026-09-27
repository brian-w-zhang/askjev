"use client";

import { useEffect, useMemo, useState } from "react";
import type { Claim, NodeCard, SourceRow } from "./types";

// The atlas (docs/11-portrait.md §8): every ledger claim, what a human self-portrait would cover, every topic's
// indicators and the source table. Findings open as cards (a first view a person can read); the table is one click
// away. Topic cards and sources load when their tab opens.
type Tab = "claims" | "coverage" | "nodes" | "sources";
type View = "cards" | "table";
const pctf = (x: unknown) => (typeof x === "number" ? `${Math.round(x * 100)}%` : "–");
const fixed = (x: unknown, d = 2) => (typeof x === "number" ? x.toFixed(d) : "–");
const SECTION: Record<string, string> = {
  landscape: "the corpus", pipeline: "how it was built", defaults: "habits", personality: "personality", scales: "online tests",
  values: "values", taste_favorites: "favorites", taste_beyond: "taste vs reputation", knowledge: "knowledge",
  calibration: "calibration", work: "work tasks", jaggedness: "jaggedness", stable_core: "stability",
  agreement: "agreement with crowds", themes: "themes", discovery: "unusual topics",
};
const TIER: Record<string, string> = { "1": "real answers", "2": "audited items", "3": "theme", discovery: "indicator", corpus: "count", pipeline: "logs" };

// What a human self-portrait or census usually covers, and how much of it this corpus covers for Jev.
const COVERAGE: { area: string; have: "have" | "part" | "no"; how: string }[] = [
  { area: "Personality (Big Five)", have: "have", how: "IPIP 50-item markers vs 603k people; bigfive_*" },
  { area: "Type (Myers-Briggs style)", have: "have", how: "OEJTS items, no human norms; type" },
  { area: "Online personality tests (nerdiness, dark triad, attachment, DASS, grit…)", have: "have", how: "Open Psychometrics scales vs everyone who took them; scale_*" },
  { area: "Trait facets, dark side, humor style", have: "have", how: "questions written for this project, audited; muted_self" },
  { area: "Wellbeing and mood", have: "have", how: "SWLS, WHO-5, UCLA-3, PSS-4, Cantril ladder (no norms); DASS vs ~40k people; Reddit polls" },
  { area: "Relationships and attachment", have: "have", how: "ECR attachment anxiety and avoidance vs ~51k people; love and dating polls" },
  { area: "Career interests (RIASEC)", have: "have", how: "48 RIASEC items vs ~145k people; O*NET activities in the corpus, unscored" },
  { area: "Moral values", have: "have", how: "Moral Foundations Questionnaire, Moral Machine; mfq, mm_*" },
  { area: "Risk and money choices", have: "have", how: "real described gambles; risk_gambles" },
  { area: "Taste (film, music, books, food, art, places, games)", have: "have", how: "ratings and head-to-heads; page_ratings, favorites_*, beyond_*" },
  { area: "Social norms and etiquette", have: "have", how: "Social Chemistry, Scruples, AITA-style crowd votes; crowd_*" },
  { area: "General knowledge", have: "have", how: "exams, Wikidata, trivia; knowledge_*" },
  { area: "Calibration (knowing what you know)", have: "have", how: "calibration" },
  { area: "Work skills", have: "have", how: "127 labeled task datasets; task_*" },
  { area: "Humor", have: "have", how: "caption and joke upvotes; humor_*" },
  { area: "Religion and spirituality", have: "part", how: "scattered questions, not scored" },
  { area: "Health behaviors", have: "part", how: "health facts, not self-reported habits" },
  { area: "Cognitive ability", have: "no", how: "no test items (matrices, series) in the corpus" },
  { area: "Worldview (World Values Survey, Schwartz values)", have: "no", how: "not collected" },
  { area: "Chronotype, sleep, time use, media diet", have: "no", how: "only scattered polls" },
  { area: "Politics", have: "no", how: "answered but hidden on purpose" },
  { area: "Demographics (age, location, income)", have: "no", how: "doesn't apply to a model" },
];

export default function Atlas({ claims, nNodes, nSources }: { claims: Claim[]; nNodes: number; nSources: number }) {
  const [tab, setTab] = useState<Tab>("claims");
  const [view, setView] = useState<View>("cards");
  const [q, setQ] = useState("");
  const [section, setSection] = useState<string>("");
  const [sort, setSort] = useState<{ key: string; desc: boolean }>({ key: "n", desc: true });
  const [nodes, setNodes] = useState<NodeCard[] | null>(null);
  const [sources, setSources] = useState<SourceRow[] | null>(null);
  const [failed, setFailed] = useState(false);
  const needle = q.trim().toLowerCase();

  // topic cards and sources are most of the atlas's data: fetched when their tab first opens
  useEffect(() => {
    const part = tab === "nodes" && !nodes ? "nodes" : tab === "sources" && !sources ? "sources" : null;
    if (!part) return;
    fetch(`/portrait/atlas/tables?part=${part}`).then((r) => (r.ok ? r.json() : Promise.reject())).then((x) => (part === "nodes" ? setNodes(x) : setSources(x))).catch(() => setFailed(true));
  }, [tab, nodes, sources]);

  const matches = useMemo(() => claims.filter((c) => !needle || `${c.id} ${c.sentence} ${SECTION[c.section] ?? c.section}`.toLowerCase().includes(needle)), [claims, needle]);
  const shownClaims = useMemo(() => matches.filter((c) => !section || c.section === section), [matches, section]);
  const counts = useMemo(() => {
    const m = new Map<string, number>();
    for (const c of matches) m.set(c.section, (m.get(c.section) ?? 0) + 1);
    return [...m].sort((a, b) => b[1] - a[1]);
  }, [matches]);
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
  const shownCoverage = COVERAGE.filter((c) => !needle || `${c.area} ${c.how}`.toLowerCase().includes(needle));

  const th = (key: string, text: string) => (
    <th aria-sort={sort.key === key ? (sort.desc ? "descending" : "ascending") : undefined}>
      <button type="button" className="thb" onClick={() => setSort({ key, desc: sort.key === key ? !sort.desc : true })}>
        {text}{sort.key === key ? (sort.desc ? " ↓" : " ↑") : ""}</button></th>
  );
  const placeholder = { claims: "Search findings: humor, moral machine, nerdiness…", coverage: "Search coverage", nodes: "Search topics: happiness, spam…", sources: "Search sources" }[tab];

  return (
    <div className="atlas">
      <div className="at-bar">
        <div className="tabs" role="tablist" aria-label="Atlas sections">
          {(["claims", "coverage", "nodes", "sources"] as Tab[]).map((t) => (
            <button key={t} type="button" role="tab" aria-selected={tab === t} onClick={() => setTab(t)}>
              {t === "claims" ? `Findings ${claims.length}` : t === "coverage" ? "Coverage" : t === "nodes" ? `Topics ${nNodes.toLocaleString("en-US")}` : `Sources ${nSources}`}
            </button>
          ))}
        </div>
        <input className="pt-input" placeholder={placeholder} value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search the atlas" />
      </div>

      {tab === "claims" && (
        <>
          <div className="pt-filters" role="group" aria-label="Filter by section">
            <button type="button" className="facet" aria-pressed={!section} onClick={() => setSection("")}>all <em>{matches.length}</em></button>
            {counts.map(([s, n]) => (
              <button key={s} type="button" className="facet" aria-pressed={section === s} onClick={() => setSection(section === s ? "" : s)}>
                {SECTION[s] ?? s} <em>{n}</em>
              </button>
            ))}
            <span className="sp" />
            <span className="viewtoggle" role="group" aria-label="View">
              <button type="button" aria-pressed={view === "cards"} onClick={() => setView("cards")}>cards</button>
              <button type="button" aria-pressed={view === "table"} onClick={() => setView("table")}>table</button>
            </span>
          </div>
          {shownClaims.length === 0 && <p className="at-empty">Nothing matches &ldquo;{q}&rdquo;.</p>}
          {view === "cards" ? (
            <div className="claimgrid">
              {shownClaims.slice(0, 150).map((c) => <ClaimCard key={c.id} c={c} />)}
              {shownClaims.length > 150 && <p className="at-empty">Showing 150 of {shownClaims.length}. Search or pick a section to narrow it.</p>}
            </div>
          ) : (
            <div className="pt-scroll">
              <table className="pt-table">
                <thead><tr><th>finding</th><th>section</th><th>evidence</th><th style={{ textAlign: "right" }}>n</th></tr></thead>
                <tbody>
                  {shownClaims.map((c) => (
                    <tr key={c.id}>
                      <td>{c.sentence}<div className="at-id">{c.id}{c.ci90 ? ` · 90% interval ${c.ci90.map((x) => fixed(x, Math.abs(x) > 2 ? 0 : 3)).join(" to ")}` : ""}</div></td>
                      <td>{SECTION[c.section] ?? c.section}</td><td>{TIER[c.tier] ?? c.tier}</td>
                      <td className="n">{c.n.toLocaleString("en-US")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {tab === "coverage" && (
        <div className="covgrid">
          {shownCoverage.map((c) => (
            <div key={c.area} className={`cov-card ${c.have}`}>
              <span className={`cov ${c.have}`}>{c.have === "have" ? "● covered" : c.have === "part" ? "◐ partly" : "○ not yet"}</span>
              <b>{c.area}</b>
              <span className="how">{c.how}</span>
            </div>
          ))}
        </div>
      )}

      {((tab === "nodes" && !nodes) || (tab === "sources" && !sources)) && (
        <p className="at-empty">{failed ? "Couldn't load this table. Try reloading the page." : "Loading…"}</p>
      )}
      {tab === "nodes" && nodes && (
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
      )}
      {tab === "sources" && sources && (
        <div className="pt-scroll">
          <table className="pt-table">
            <thead><tr><th>source</th><th>family</th><th>side</th><th style={{ textAlign: "right" }}>questions</th><th style={{ textAlign: "right" }}>right answer</th><th style={{ textAlign: "right" }}>human answers</th><th style={{ textAlign: "right" }}>shown</th></tr></thead>
            <tbody>
              {shownSources.map((s) => (
                <tr key={`${s.source}-${s.hemisphere}`}>
                  <td className="at-mono">{s.source}</td><td>{s.family}</td><td>{s.hemisphere}</td>
                  <td className="n">{s.n.toLocaleString("en-US")}</td><td className="n">{pctf(s.truth)}</td><td className="n">{pctf(s.humans)}</td><td className="n">{pctf(s.shown)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="at-foot">
        {tab === "nodes" ? "Topics sorted by the column you pick (up to 400 shown). Unusual: the largest standardized distance from the corpus average on any indicator. Click a topic to open it on the map."
          : tab === "claims" ? "Every finding computed, on the portrait or not. Evidence: real answers (published tests, crowd votes, answer keys), audited items (questions written for this project), themes (found by similarity), indicators (per-topic numbers)."
          : tab === "coverage" ? "Modeled on what surveys, censuses and personality reports ask people about. Partly means the questions exist but aren't scored as a test."
          : "Counts include hidden questions; shown is the share on the map."}
      </p>
    </div>
  );
}

function ClaimCard({ c }: { c: Claim }) {
  const share = typeof c.effect === "number" && c.effect >= 0 && c.effect <= 1 && String(c.sentence).includes("%");
  return (
    <article className="claim">
      <div className="cl-top"><span className="cl-sec">{SECTION[c.section] ?? c.section}</span><span className="cl-tier">{TIER[c.tier] ?? c.tier}</span></div>
      <p className="cl-s">{c.sentence}</p>
      {share && <span className="cl-bar" aria-hidden><i style={{ width: `${(c.effect as number) * 100}%` }} /></span>}
      <div className="cl-meta">n = {c.n.toLocaleString("en-US")}{c.ci90 ? ` · 90% interval ${c.ci90.map((x) => fixed(x, Math.abs(x) > 2 ? 0 : 2)).join("–")}` : ""}<span className="cl-id">{c.id}</span></div>
    </article>
  );
}
