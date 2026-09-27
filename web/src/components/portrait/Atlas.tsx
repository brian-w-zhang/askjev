"use client";

import { useMemo, useState } from "react";
import type { Claim, NodeCard, SourceRow } from "./types";

// The atlas (docs/11-portrait.md §8): every ledger claim, every topic card and the full source table, searchable.
type Tab = "claims" | "nodes" | "sources";
const pctf = (x: unknown) => (typeof x === "number" ? `${Math.round(x * 100)}%` : "–");
const fixed = (x: unknown, d = 2) => (typeof x === "number" ? x.toFixed(d) : "–");
const SECTION: Record<string, string> = {
  landscape: "data landscape", pipeline: "pipeline", defaults: "how Jev answers", personality: "personality", values: "values",
  taste_favorites: "taste: favorites", taste_beyond: "taste: beyond reputation", knowledge: "knowledge", calibration: "calibration",
  work: "work", jaggedness: "jaggedness", stable_core: "stable core", agreement: "crowd agreement", themes: "themes",
  discovery: "discovery", page: "page support",
};

export default function Atlas({ claims, nodes, sources }: { claims: Claim[]; nodes: NodeCard[]; sources: SourceRow[] }) {
  const [tab, setTab] = useState<Tab>("claims");
  const [q, setQ] = useState("");
  const [section, setSection] = useState<string>("");
  const [sort, setSort] = useState<{ key: string; desc: boolean }>({ key: "n", desc: true });
  const needle = q.trim().toLowerCase();

  const shownClaims = useMemo(() => claims.filter((c) => (!section || c.section === section)
    && (!needle || `${c.id} ${c.sentence}`.toLowerCase().includes(needle))), [claims, section, needle]);
  const shownNodes = useMemo(() => {
    const r = nodes.filter((n) => !needle || n.node_id.toLowerCase().includes(needle));
    return [...r].sort((a, b) => {
      const x = a[sort.key] as number | null, y = b[sort.key] as number | null;
      if (x === y) return 0;
      if (x === null || x === undefined) return 1;
      if (y === null || y === undefined) return -1;
      return sort.desc ? y - x : x - y;
    }).slice(0, 400);
  }, [nodes, needle, sort]);
  const shownSources = useMemo(() => sources.filter((s) => !needle || `${s.source} ${s.family}`.toLowerCase().includes(needle)), [sources, needle]);
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
          {(["claims", "nodes", "sources"] as Tab[]).map((t) => (
            <button key={t} type="button" role="tab" aria-selected={tab === t} onClick={() => setTab(t)}>
              {t === "claims" ? `Findings (${claims.length})` : t === "nodes" ? `Topics (${nodes.length})` : `Sources (${sources.length})`}
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
          {tab === "nodes" && (
            <table className="pt-table">
              <thead><tr><th>topic</th>{th("n", "n")}{th("accuracy", "right")}{th("confidence", "confidence")}{th("decisive", "decisive")}{th("stability", "stable")}{th("frame_gap", "self vs people")}{th("crowd_agree", "crowd")}{th("z_max", "unusual")}</tr></thead>
              <tbody>
                {shownNodes.map((n) => (
                  <tr key={n.node_id}>
                    <td style={{ fontFamily: "var(--mono)", fontSize: 11.5, wordBreak: "break-all" }}>{n.node_id}</td>
                    <td className="n">{Number(n.n).toLocaleString("en-US")}</td>
                    <td className="n">{pctf(n.accuracy)}</td><td className="n">{pctf(n.confidence)}</td><td className="n">{pctf(n.decisive)}</td>
                    <td className="n">{pctf(n.stability)}</td><td className="n">{fixed(n.frame_gap)}</td><td className="n">{pctf(n.crowd_agree)}</td><td className="n">{fixed(n.z_max, 1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {tab === "sources" && (
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
        {tab === "nodes" ? <span>Sorted by {sort.key}; showing up to 400. &lsquo;Unusual&rsquo; is the largest standardized distance from the corpus baseline on any indicator.</span>
          : tab === "claims" ? <span>Every finding computed, on the page or not. Tiers: 1 published instrument or real answers · 2 audited authored items · 3 embedding theme · discovery node indicator.</span>
          : <span>Counts include hidden questions; &lsquo;shown&rsquo; is the share on the map.</span>}
      </div>
    </div>
  );
}
