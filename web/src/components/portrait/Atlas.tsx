"use client";

import { useEffect, useMemo, useState } from "react";
import type { Claim, NodeCard, SourceRow } from "./types";

// The atlas (docs/11-portrait.md §8): every ledger claim, every topic card and the full source table, searchable.
type Tab = "claims" | "coverage" | "nodes" | "sources";

// What a human self-portrait or census usually covers, and how much of it this corpus covers for Jev.
const COVERAGE: { area: string; have: "have" | "part" | "no"; how: string }[] = [
  { area: "Personality (Big Five)", have: "have", how: "IPIP 50-item markers vs 603k people; bigfive_*" },
  { area: "Type (Myers-Briggs style)", have: "have", how: "OEJTS items, no human norms; type" },
  { area: "Trait facets, dark side, humor style", have: "have", how: "authored items, audited; muted_self" },
  { area: "Moral values", have: "have", how: "Moral Foundations Questionnaire, Moral Machine; mfq, mm_*" },
  { area: "Risk and money choices", have: "have", how: "real described gambles; risk_gambles" },
  { area: "Taste (film, music, books, food, art, places, games)", have: "have", how: "ratings and head-to-heads; page_ratings, favorites_*, beyond_*" },
  { area: "Social norms and etiquette", have: "have", how: "Social Chemistry, Scruples, AITA-style crowd votes; crowd_*" },
  { area: "General knowledge", have: "have", how: "exams, Wikidata, trivia; knowledge_*" },
  { area: "Calibration (knowing what you know)", have: "have", how: "calibration" },
  { area: "Work skills", have: "have", how: "127 labeled task datasets; task_*" },
  { area: "Humor", have: "have", how: "caption and joke upvotes; humor_*" },
  { area: "Wellbeing and mood", have: "part", how: "Reddit polls only (page_checkin); no validated scale like WHO-5 or the Cantril ladder" },
  { area: "Cognitive ability", have: "part", how: "ICAR items are in the corpus but not scored as a test" },
  { area: "Career interests (RIASEC)", have: "part", how: "O*NET interest items are in the corpus but not scored" },
  { area: "Relationships and attachment", have: "part", how: "love and dating polls; no attachment-style instrument" },
  { area: "Religion and spirituality", have: "part", how: "scattered questions, not scored" },
  { area: "Health behaviors", have: "part", how: "health facts, not self-report habits" },
  { area: "Worldview (World Values Survey, Schwartz values)", have: "no", how: "not collected" },
  { area: "Chronotype, sleep, time use, media diet", have: "no", how: "only scattered polls" },
  { area: "Politics", have: "no", how: "answered but hidden on purpose" },
  { area: "Demographics (age, location, income)", have: "no", how: "doesn't apply to a model" },
];
const pctf = (x: unknown) => (typeof x === "number" ? `${Math.round(x * 100)}%` : "–");
const fixed = (x: unknown, d = 2) => (typeof x === "number" ? x.toFixed(d) : "–");
const SECTION: Record<string, string> = {
  landscape: "data landscape", pipeline: "pipeline", defaults: "how Jev answers", personality: "personality", values: "values",
  taste_favorites: "taste: favorites", taste_beyond: "taste: beyond reputation", knowledge: "knowledge", calibration: "calibration",
  work: "work", jaggedness: "jaggedness", stable_core: "stable core", agreement: "crowd agreement", themes: "themes",
  discovery: "discovery", page: "page support",
};

export default function Atlas({ claims, nNodes, nSources }: { claims: Claim[]; nNodes: number; nSources: number }) {
  const [tab, setTab] = useState<Tab>("claims");
  // topic cards and sources are fetched when their tab first opens (they're most of the atlas's data)
  const [nodes, setNodes] = useState<NodeCard[] | null>(null);
  const [sources, setSources] = useState<SourceRow[] | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    const part = tab === "nodes" && !nodes ? "nodes" : tab === "sources" && !sources ? "sources" : null;
    if (!part) return;
    fetch(`/portrait/atlas/data?part=${part}`).then((r) => (r.ok ? r.json() : Promise.reject())).then((x) => (part === "nodes" ? setNodes(x) : setSources(x))).catch(() => setFailed(true));
  }, [tab, nodes, sources]);
  const [q, setQ] = useState("");
  const [section, setSection] = useState<string>("");
  const [sort, setSort] = useState<{ key: string; desc: boolean }>({ key: "n", desc: true });
  const needle = q.trim().toLowerCase();

  const shownClaims = useMemo(() => claims.filter((c) => (!section || c.section === section)
    && (!needle || `${c.id} ${c.sentence}`.toLowerCase().includes(needle))), [claims, section, needle]);
  const shownNodes = useMemo(() => {
    const r = (nodes ?? []).filter((n) => !needle || n.node_id.toLowerCase().includes(needle));
    return [...r].sort((a, b) => {
      const x = a[sort.key] as number | null, y = b[sort.key] as number | null;
      if (x === y) return 0;
      if (x === null || x === undefined) return 1;
      if (y === null || y === undefined) return -1;
      return sort.desc ? y - x : x - y;
    }).slice(0, 400);
  }, [nodes, needle, sort]);
  const shownSources = useMemo(() => (sources ?? []).filter((s) => !needle || `${s.source} ${s.family}`.toLowerCase().includes(needle)), [sources, needle]);
  const sections = useMemo(() => [...new Set(claims.map((c) => c.section))], [claims]);

  const th = (key: string, text: string) => (
    <th><button type="button" onClick={() => setSort({ key, desc: sort.key === key ? !sort.desc : true })}
      style={{ border: 0, background: "none", padding: 0, font: "inherit", color: "inherit" }}>
      {text}{sort.key === key ? (sort.desc ? " ↓" : " ↑") : ""}</button></th>
  );

  return (
    <div className="pt-win wide" style={{ maxWidth: 1080 }}>
      <div className="pt-bar"><span>Atlas.app</span><span className="sp" /><span className="dots">▪▪▪</span></div>
      <div className="pt-body">
        <div className="tabs" role="tablist">
          {(["claims", "coverage", "nodes", "sources"] as Tab[]).map((t) => (
            <button key={t} type="button" role="tab" aria-selected={tab === t} onClick={() => setTab(t)}>
              {t === "claims" ? `Findings (${claims.length})` : t === "coverage" ? "Coverage" : t === "nodes" ? `Topics (${nNodes})` : `Sources (${nSources})`}
            </button>
          ))}
        </div>
        <input className="pt-input" placeholder={tab === "claims" ? "Search findings: humor, moral machine, spam…" : tab === "nodes" ? "Search topics: world.food…" : "Search sources"}
          value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search" />
        {tab === "claims" && (
          <div className="pt-filters">
            <button type="button" className={`chipbtn`} aria-pressed={!section} onClick={() => setSection("")} style={{ background: !section ? "#1e1e1e" : undefined, color: !section ? "#fefefe" : undefined }}>all</button>
            {sections.map((s) => (
              <button key={s} type="button" className="chipbtn" aria-pressed={section === s} onClick={() => setSection(section === s ? "" : s)}
                style={{ background: section === s ? "#1e1e1e" : undefined, color: section === s ? "#fefefe" : undefined }}>{SECTION[s] ?? s}</button>
            ))}
          </div>
        )}
        <div className="pt-scroll" style={{ marginTop: tab === "claims" ? 0 : 12 }}>
          {tab === "claims" && (
            <table className="pt-table">
              <thead><tr><th>finding</th><th>section</th><th>tier</th><th style={{ textAlign: "right" }}>n</th></tr></thead>
              <tbody>
                {shownClaims.map((c) => (
                  <tr key={c.id}>
                    <td>{c.sentence}<div style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--w-fg-2)", marginTop: 2 }}>{c.id}{c.ci90 ? ` · 90% CI ${c.ci90.map((x) => fixed(x, Math.abs(x) > 2 ? 0 : 3)).join(" to ")}` : ""}</div></td>
                    <td>{SECTION[c.section] ?? c.section}</td>
                    <td>{c.tier}</td>
                    <td className="n">{c.n.toLocaleString("en-US")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {tab === "coverage" && (
            <table className="pt-table">
              <thead><tr><th>what a person would be asked about</th><th>for Jev</th><th>how</th></tr></thead>
              <tbody>
                {COVERAGE.filter((c) => !needle || `${c.area} ${c.how}`.toLowerCase().includes(needle)).map((c) => (
                  <tr key={c.area}>
                    <td>{c.area}</td>
                    <td><span className={`cov ${c.have}`}>{c.have === "have" ? "● covered" : c.have === "part" ? "◐ partly" : "○ not yet"}</span></td>
                    <td style={{ color: "var(--w-fg-2)" }}>{c.how}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {((tab === "nodes" && !nodes) || (tab === "sources" && !sources)) && (
            <p style={{ padding: 16, fontFamily: "var(--mono)", fontSize: 12, color: "var(--w-fg-2)" }}>{failed ? "Couldn't load this table. Try reloading the page." : "Loading…"}</p>
          )}
          {tab === "nodes" && nodes && (
            <table className="pt-table">
              <thead><tr><th>topic</th>{th("n", "n")}{th("accuracy", "right")}{th("confidence", "confidence")}{th("decisive", "decisive")}{th("stability", "stable")}{th("frame_gap", "self vs people")}{th("crowd_agree", "crowd")}{th("z_max", "unusual")}</tr></thead>
              <tbody>
                {shownNodes.map((n) => (
                  <tr key={n.node_id}>
                    <td style={{ fontFamily: "var(--mono)", fontSize: 11.5, wordBreak: "break-all" }}><a href={`/?node=${encodeURIComponent(n.node_id)}`} title="open on the map">{n.node_id}</a></td>
                    <td className="n">{Number(n.n).toLocaleString("en-US")}</td>
                    <td className="n">{pctf(n.accuracy)}</td><td className="n">{pctf(n.confidence)}</td><td className="n">{pctf(n.decisive)}</td>
                    <td className="n">{pctf(n.stability)}</td><td className="n">{fixed(n.frame_gap)}</td><td className="n">{pctf(n.crowd_agree)}</td><td className="n">{fixed(n.z_max, 1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {tab === "sources" && sources && (
            <table className="pt-table">
              <thead><tr><th>source</th><th>family</th><th>hemisphere</th><th style={{ textAlign: "right" }}>questions</th><th style={{ textAlign: "right" }}>right answer</th><th style={{ textAlign: "right" }}>human answers</th><th style={{ textAlign: "right" }}>shown</th></tr></thead>
              <tbody>
                {shownSources.map((s) => (
                  <tr key={`${s.source}-${s.hemisphere}`}>
                    <td style={{ fontFamily: "var(--mono)", fontSize: 11.5 }}>{s.source}</td><td>{s.family}</td><td>{s.hemisphere}</td>
                    <td className="n">{s.n.toLocaleString("en-US")}</td><td className="n">{pctf(s.truth)}</td><td className="n">{pctf(s.humans)}</td><td className="n">{pctf(s.shown)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
      <div className="pt-foot">
        {tab === "coverage" ? <span>Modeled on what surveys, censuses and personality reports ask people about. &lsquo;Partly&rsquo; means questions exist but aren&rsquo;t scored as an instrument.</span>
          : tab === "nodes" ? <span>Sorted by {sort.key}; showing up to 400. &lsquo;Unusual&rsquo; is the largest standardized distance from the corpus baseline on any indicator. Click a topic to open it on the map.</span>
          : tab === "claims" ? <span>Every finding computed, on the page or not. Tiers: 1 published instrument or real answers · 2 audited authored items · 3 embedding theme · discovery node indicator.</span>
          : <span>Counts include hidden questions; &lsquo;shown&rsquo; is the share on the map.</span>}
      </div>
    </div>
  );
}
