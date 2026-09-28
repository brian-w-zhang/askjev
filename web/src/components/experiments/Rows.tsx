"use client";

import { useCallback, useEffect, useState } from "react";
import { optionLabel, truthKey } from "../portrait/fmt";
import type { Row } from "../portrait/types";

// Every question behind an experiment (docs/17 items 6-7): one legend on top, five questions at a time with "show more",
// and filters for the rows where Jev misses. Rows come from /portrait/atlas/rows (private), in the order the export
// chose: the experiment's own examples, then the misses, biggest gap first, then the rest.
type Flagged = Row & { flag: string; fields?: [string, string][] | null };
type Filter = "" | "wrong" | "differs";
const pct = (x: number) => `${Math.round(x * 100)}%`;
// field names and placeholders as a reader would say them: `caption_1` -> caption 1
const words = (s: string) => s.replace(/`([^`]+)`/g, "$1").replace(/\b([a-z]+)_([a-z0-9]+)\b/g, "$1 $2");

export function Legend({ human, guess, truth }: { human: boolean; guess: boolean; truth: boolean }) {
  return (
    <div className="ex-rlegend" role="note" aria-label="How to read the questions">
      <span><i className="sw jev" />Jev&rsquo;s own answer</span>
      {guess && <span><i className="sw guess" />what Jev thinks most people would say</span>}
      {human && <span><i className="sw hum" />real people&rsquo;s answers</span>}
      {truth && <span><i className="sw truth">✓</i>the right answer</span>}
    </div>
  );
}

function Question({ row }: { row: Flagged }) {
  const human = row.human?.dist ?? null;
  const keys = Object.keys(row.jev ?? {});
  const t = truthKey(row);
  const score = (k: string) => Math.max(row.jev?.[k] ?? 0, human?.[k] ?? 0, row.people?.[k] ?? 0);
  const keep = new Set([...keys].sort((a, b) => score(b) - score(a)).slice(0, 6));
  const shown = keys.length <= 6 ? keys : keys.filter((k) => keep.has(k) || k === t);
  const order = row.primitive === "score" ? shown.sort((a, b) => Number(a) - Number(b)) : shown.sort((a, b) => score(b) - score(a));
  return (
    <li className={`ex-q${row.flag ? ` f-${row.flag}` : ""}`}>
      <p className="qt">{words(row.text)}</p>
      {row.fields ? (
        <dl className="qf">
          {row.fields.map(([k, v]) => <div key={k}><dt>{words(k)}</dt><dd>{v}</dd></div>)}
        </dl>
      ) : row.state && <p className="qs">{row.state.replace(/^\{|\}$/g, "")}</p>}
      <div className="ex-opts">
        {order.map((k) => (
          <div className={`ex-opt${t === k ? " truth" : ""}`} key={k}>
            <span className="ol">{t === k && <b className="tk" aria-label="the right answer">✓</b>}{optionLabel(row, k)}</span>
            <span className="ob" aria-hidden>
              <i className="b jev" style={{ width: pct(row.jev?.[k] ?? 0) }} />
              {row.people && <i className="b guess" style={{ width: pct(row.people[k] ?? 0) }} />}
              {human && <i className="b hum" style={{ width: pct(human[k] ?? 0) }} />}
            </span>
            <span className="ov">
              <b className="jev">{pct(row.jev?.[k] ?? 0)}</b>
              {row.people && <b className="guess">{pct(row.people[k] ?? 0)}</b>}
              {human && <b className="hum">{pct(human[k] ?? 0)}</b>}
            </span>
          </div>
        ))}
      </div>
      {keys.length > shown.length && <p className="qm">{keys.length - shown.length} more options near 0%</p>}
      <p className="qm">
        {[row.flag === "wrong" ? "Jev's top answer is wrong" : row.flag === "differs" ? "Jev's top answer differs from people's" : "",
          row.human?.n ? `${row.human.n.toLocaleString("en-US")} people${row.human.population ? `: ${row.human.population}` : ""}` : row.human?.population ?? ""]
          .filter(Boolean).join(" · ")}
      </p>
    </li>
  );
}

export default function Rows({ id, total, flagged }: { id: string; total: number; flagged: { wrong: number; differs: number } }) {
  const [filter, setFilter] = useState<Filter>("");
  const [rows, setRows] = useState<Flagged[]>([]);
  const [page, setPage] = useState(0);
  const [pages, setPages] = useState(1);
  const [count, setCount] = useState(total);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  const fetchPage = useCallback(async (p: number, f: Filter) => {
    const r = await fetch(`/portrait/atlas/rows?id=${encodeURIComponent(id)}&page=${p}&filter=${f}`);
    if (!r.ok) throw new Error(String(r.status));
    return (await r.json()) as { rows: Flagged[]; total: number; pages: number };
  }, [id]);

  // first page, and again whenever the filter changes (state is only set once the page arrives)
  useEffect(() => {
    let live = true;
    fetchPage(0, filter)
      .then((d) => { if (live) { setRows(d.rows); setPage(0); setPages(d.pages); setCount(d.total); setFailed(false); } })
      .catch(() => { if (live) setFailed(true); });
    return () => { live = false; };
  }, [fetchPage, filter]);

  const more = async () => {
    setBusy(true);
    try {
      const d = await fetchPage(page + 1, filter);
      setRows((old) => [...old, ...d.rows]);
      setPage(page + 1);
      setPages(d.pages);
      setFailed(false);
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  };

  const anyHuman = rows.some((r) => r.human);
  const anyGuess = rows.some((r) => r.people);
  const anyTruth = rows.some((r) => r.truth !== null && r.truth !== undefined);
  return (
    <div className="ex-rows">
      <div className="ex-rhead">
        <Legend human={anyHuman} guess={anyGuess} truth={anyTruth} />
        {(flagged.wrong > 0 || flagged.differs > 0) && (
          <div className="pt-filters" role="group" aria-label="Filter questions">
            <button type="button" className="facet" aria-pressed={filter === ""} onClick={() => setFilter("")}>all <em>{total.toLocaleString("en-US")}</em></button>
            {flagged.wrong > 0 && <button type="button" className="facet" aria-pressed={filter === "wrong"} onClick={() => setFilter("wrong")}>Jev wrong <em>{flagged.wrong.toLocaleString("en-US")}</em></button>}
            {flagged.differs > 0 && <button type="button" className="facet" aria-pressed={filter === "differs"} onClick={() => setFilter("differs")}>Jev differs from people <em>{flagged.differs.toLocaleString("en-US")}</em></button>}
          </div>
        )}
      </div>
      <ol className="ex-qs">{rows.map((r) => <Question key={r.id} row={r} />)}</ol>
      {failed && <p className="at-empty">Couldn&rsquo;t load these questions. Try again.</p>}
      <div className="ex-more">
        <span className="dim">Showing {rows.length.toLocaleString("en-US")} of {count.toLocaleString("en-US")}</span>
        {page + 1 < pages && (
          <button type="button" className="pt-btn" disabled={busy} onClick={more}>
            {busy ? "Loading…" : "Show 5 more"}
          </button>
        )}
      </div>
    </div>
  );
}
