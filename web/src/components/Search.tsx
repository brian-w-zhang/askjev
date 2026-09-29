"use client";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useStore } from "@/lib/store";
import { feelingLucky, journey, showJevPick } from "@/lib/actions";
import { clearHeat, heatFrom } from "@/lib/heat";
import { starData } from "@/lib/stars";
import { ToolPanel, ToolTabs } from "./Tools";
import { Mic } from "./Mic";
import type { NodeHit, SearchHit } from "@/lib/types";

const RERANK_PAUSE_MS = 700; // wait for the query to settle, so partial words don't each cost a Jev call
const NEAR_EXACT = 0.95;
const KEY_MS = 50; // coalesce bursts of keystrokes; searches take ~30-150 ms, so results still track typing

/**
 * The text actually searched while typing (docs/07-ui.md, Search). An embedding has no prefix matching, so a
 * half-typed last word ("is a hot d") sends results across the map; a trailing fragment under 3 characters
 * is left out until it grows or a space commits it.
 */
export function settled(q: string): string {
  const t = q.replace(/\s+/g, " ").trimStart();
  const words = t.trim().split(" ");
  if (/\s$/.test(t) || words.length < 2 || words[words.length - 1].length >= 3) return t.trim();
  return words.slice(0, -1).join(" ");
}

type Found = { results: SearchHit[]; nodes: NodeHit[] };
const found = new Map<string, Found>(); // recent searches, so backspacing and retyping are instant
const remember = (k: string, d: Found) => {
  found.delete(k);
  found.set(k, d);
  if (found.size > 200) found.delete(found.keys().next().value!);
};


interface Rerank { state: "idle" | "waiting" | "done" | "error"; ms?: number; cached?: boolean; error?: string; match?: number | null }

// Jev's "does anything here answer this?" (asked with the reorder): real questions land 0.77-0.99, nonsense and
// topics the corpus lacks 0.03-0.28 ("how to fix my car's transmission" 0.28)
const MATCH_CLOSE = 0.7;
const MATCH_NONE = 0.35;

export function Search() {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [nodeHits, setNodeHits] = useState<NodeHit[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [rerank, setRerank] = useState<Rerank>({ state: "idle" });
  const showHidden = useStore((s) => s.showHidden);
  const tool = useStore((s) => s.tool);
  const theme = useStore((s) => s.theme);
  const ready = useStore((s) => s.starsReady);
  const seq = useRef(0);
  const inputRef = useRef<HTMLInputElement>(null);
  // "/" or ⌘K / Ctrl+K jumps to the box from anywhere (as on typesafe.ai's docs and most search UIs)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = (e.target as HTMLElement | null)?.closest("input, textarea, select, [contenteditable]");
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !typing)) {
        e.preventDefault();
        inputRef.current?.focus();
        inputRef.current?.select();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  const rerankTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastKey = useRef(0); // when the query last changed at all (a half-typed word still counts as typing)
  const listRef = useRef<HTMLDivElement>(null);
  const tops = useRef(new Map<string, number>());

  async function runRerank(text: string, list: SearchHit[], my: number) {
    if (list.length < 2) return;
    setRerank({ state: "waiting" });
    const t0 = performance.now();
    try {
      const r = await fetch("/api/rerank", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ q: text, candidates: list.slice(0, 20).map((h) => ({ id: h.id, text: h.text })) }),
      });
      const d = await r.json();
      if (my !== seq.current) return;
      if (!r.ok) throw new Error(d.error ?? `rerank ${r.status}`);
      const p = new Map<string, number>(d.order.map((o: { id: string; p: number }) => [o.id, o.p]));
      const byJev = (a: SearchHit, b: SearchHit) => (b.jev_p ?? -1) - (a.jev_p ?? -1) || b.score - a.score;
      const ranked = list.map((h) => ({ ...h, jev_p: p.get(h.id) ?? null })).sort(byJev);
      setHits(ranked);
      showJevPick(ranked[0] ?? null);
      setRerank({ state: "done", ms: performance.now() - t0, cached: d.cached, match: typeof d.match === "number" ? d.match : null });
    } catch (e) {
      if (my === seq.current) setRerank({ state: "error", error: (e as Error).message });
    }
  }

  // Jev refines once typing really pauses (every key restarts the wait, including ones that don't change the
  // searched text): one Choice over the top 20. Skipped when the best match is near-exact (similarity >= 0.95):
  // on 30 test queries Jev never changed the #1 there (web/scripts/rerank_eval.mjs).
  const pending = useRef<{ text: string; list: SearchHit[]; my: number } | null>(null);
  function rerankNow() {
    const p = pending.current;
    pending.current = null;
    if (p && p.my === seq.current && (p.list[0]?.sim ?? 0) < NEAR_EXACT) runRerank(p.text, p.list, p.my);
  }
  useEffect(() => {
    lastKey.current = performance.now();
    if (rerankTimer.current) clearTimeout(rerankTimer.current);
    if (!q.trim()) return;
    rerankTimer.current = setTimeout(rerankNow, RERANK_PAUSE_MS);
    return () => { if (rerankTimer.current) clearTimeout(rerankTimer.current); };
  }, [q, showHidden]); // eslint-disable-line react-hooks/exhaustive-deps

  // Instant results on every keystroke (of the settled text): local embedding + pgvector, and the map's heat.
  const text = settled(q);
  useEffect(() => {
    const my = ++seq.current;
    if (!text) return;
    const key = `${text}|${showHidden ? 1 : 0}`;
    const show = (d: Found) => {
      if (my !== seq.current) return;
      setHits(d.results);
      setNodeHits(d.nodes.slice(0, 3));
      setActive(0);
      setOpen(true);
      setRerank({ state: "idle" });
      heatFrom(d.results);
      showJevPick(null);
      pending.current = { text, list: d.results, my };
      // results that land after the pause has already passed go to Jev straight away
      if (performance.now() - lastKey.current >= RERANK_PAUSE_MS) rerankNow();
    };
    const have = found.get(key);
    if (have) { show(have); return; }
    const ctl = new AbortController();
    const timer = setTimeout(() => {
      fetch(`/api/search?q=${encodeURIComponent(text)}${showHidden ? "&hidden=1" : ""}`, { signal: ctl.signal })
        .then((r) => r.json())
        .then((d: Found) => { remember(key, d); show(d); })
        .catch(() => {});
    }, KEY_MS);
    return () => { clearTimeout(timer); ctl.abort(); };
  }, [text, showHidden]); // eslint-disable-line react-hooks/exhaustive-deps

  // FLIP: results glide to their new places when Jev reorders them.
  useLayoutEffect(() => {
    const el = listRef.current;
    if (!el) return;
    const items = el.querySelectorAll<HTMLElement>("[data-hit]");
    items.forEach((it) => {
      const id = it.dataset.hit!;
      const top = it.offsetTop;
      const old = tops.current.get(id);
      if (old !== undefined && old !== top) {
        it.style.transition = "none";
        it.style.transform = `translateY(${old - top}px)`;
        requestAnimationFrame(() => {
          it.style.transition = "transform 480ms cubic-bezier(0.2, 0.8, 0.2, 1)";
          it.style.transform = "";
        });
      }
      tops.current.set(id, top);
    });
  }, [hits]);

  /** Leaving the list for the map: a pending or in-flight Jev reorder must not land on top of the journey. */
  function settle() {
    seq.current++;
    pending.current = null;
    if (rerankTimer.current) clearTimeout(rerankTimer.current);
    setOpen(false);
  }

  /** Clear the query (✕, a second Esc, or reset view): text, results, heat and Jev's pick all go. */
  function clear() {
    settle();
    setQ("");
    setHits([]);
    setNodeHits([]);
    setRerank({ state: "idle" });
    clearHeat();
    showJevPick(null);
  }
  // reset view (⌂ or Esc on the map) clears the box from outside
  useEffect(() => useStore.subscribe((st, prev) => { if (st.searchReset !== prev.searchReset) clear(); }), []); // eslint-disable-line react-hooks/exhaustive-deps

  async function choose(h: SearchHit) {
    settle();
    useStore.getState().set({ panel: { kind: "none" } });
    await journey({ path: h.path.map((p) => p.id), questionId: h.id });
  }

  async function chooseNode(n: NodeHit) {
    settle();
    await journey({ path: n.path.map((p) => p.id) });
  }

  function ask() {
    setOpen(false);
    useStore.getState().set({ panel: { kind: "ask", text: q.trim() } });
  }

  async function lucky() {
    settle();
    clearHeat();
    await feelingLucky();
  }

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(a + 1, hits.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
    else if (e.key === "Enter" && hits[active]) { e.preventDefault(); choose(hits[active]); }
    else if (e.key === "Enter" && q.trim()) { e.preventDefault(); ask(); }
    else if (e.key === "Escape") {
      // first Esc closes the list, the second clears the query (the page-level Esc never sees keys typed here)
      if (open && q.trim()) setOpen(false);
      else if (q) clear();
      else inputRef.current?.blur();
    }
  };


  // results header state: an exact match skips Jev; otherwise Jev's reorder also says whether anything matches
  const exact = (hits[0]?.sim ?? 0) >= NEAR_EXACT;
  const match = rerank.state === "done" ? rerank.match ?? null : null;
  const none = match !== null && match < MATCH_NONE;
  const related = match !== null && match >= MATCH_NONE && match < MATCH_CLOSE;
  const status = exact ? "Exact match" : rerank.state === "waiting" ? "Jev is ranking" : rerank.state === "done" ? "Ranked by Jev" : rerank.state === "error" ? "Jev unavailable" : "";

  return (
    <div className="search">
      <div className="finder">
        <div className="finder-title">
          <span className="brand">askjev</span>
          <span className="count num">{ready ? `${(starData()?.count ?? 0).toLocaleString()} questions` : "Loading questions"}</span>
          {/* light / dark slider: one control; any click flips it and the white thumb slides to the other icon */}
          <button
            className="themeswitch"
            role="switch"
            aria-checked={theme === "dark"}
            aria-label="Dark mode"
            title={theme === "dark" ? "Switch to light" : "Switch to dark"}
            data-on={theme}
            onClick={() => useStore.getState().set({ theme: theme === "light" ? "dark" : "light" })}
          >
            <i className="thumb" aria-hidden />
            <svg className="ic sun" viewBox="0 0 12 12" aria-hidden>
              <circle cx="6" cy="6" r="2.4" fill="currentColor" />
              <path d="M6 .6v1.5M6 9.9v1.5M.6 6h1.5M9.9 6h1.5M2.2 2.2l1 1M8.8 8.8l1 1M2.2 9.8l1-1M8.8 3.2l1-1" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
            </svg>
            <svg className="ic moon" viewBox="0 0 12 12" aria-hidden>
              <path d="M7.5 0.8A5.3 5.3 0 1 0 11.2 8.3 4.3 4.3 0 0 1 7.5 0.8Z" fill="currentColor" />
            </svg>
          </button>
        </div>
        <div className="search-field">
        <label className="qbox">
        <svg className="qicon" viewBox="0 0 16 16" aria-hidden shapeRendering="crispEdges">
          <path d="M6.5 2.5a4 4 0 1 1 0 8 4 4 0 0 1 0-8Z M9.5 9.5 13.5 13.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
        </svg>
        <input
          ref={inputRef}
          data-testid="search"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            if (!e.target.value.trim()) clear();
          }}
          onFocus={() => { useStore.getState().set({ tool: null }); if (hits.length) setOpen(true); }}
          onKeyDown={onKey}
          placeholder="Ask Jev anything"
          aria-label="Search questions or ask Jev"
          role="combobox"
          aria-expanded={open}
          aria-controls="search-results"
        />
        {q && (
          <button className="qclear" onClick={() => { clear(); inputRef.current?.focus(); }} aria-label="Clear search" title="Clear search (Esc)">
            <span aria-hidden>✕</span>
          </button>
        )}
        </label>
        <Mic onText={(t) => { if (t) setQ(t); else clear(); inputRef.current?.focus(); }} />
        </div>
        <ToolTabs onLucky={lucky} />
      </div>
      <ToolPanel />
      {open && q.trim() && !tool && (
        <div className="results" id="search-results" role="listbox" ref={listRef} data-title="Results">
          <div className="results-status">
            <span className="topics">
              {/* Jev's verdict takes the topics' place in this fixed-height row, so nothing below moves when it lands */}
              {none && <span className="verdict none" title="Jev doesn't think any question here asks this. The nearest are below, or ask it yourself.">No close match</span>}
              {related && <span className="verdict">Related, not exact</span>}
              {!none && !related && nodeHits.slice(0, 3).map((n) => (
                <button key={n.id} className="topicchip" onClick={() => chooseNode(n)} title={n.path.map((p, i) => (i === 0 ? "All" : p.label)).join(" / ")}>
                  <i style={{ background: `var(--${n.hemisphere})` }} />{n.label}
                </button>
              ))}
            </span>
            <span className={`rstate ${rerank.state === "done" || exact ? "jev" : ""}`} title={rerank.state === "done" ? `Jev reordered these in ${((rerank.ms ?? 0) / 1000).toFixed(2)} s${rerank.cached ? " (cached)" : ""}` : undefined}>{status}</span>
          </div>
          {hits.length === 0 && <div className="empty">No questions match yet. Try fewer words, or ask it below.</div>}
          {hits.map((h, i) => {
            const rewordings = (h.similar ?? []).filter((x) => !x.variant).length;
            const variants = (h.similar ?? []).length - rewordings;
            const pick = i === 0 && rerank.state === "done" && !none && !exact;
            const where = h.path.slice(1);
            return (
            <button
              key={h.id}
              data-hit={h.id}
              className={`result ${none ? "faint" : ""}`}
              role="option"
              aria-selected={i === active}
              onMouseEnter={() => setActive(i)}
              onClick={() => choose(h)}
            >
              <span className="dot" style={{ background: `var(--${h.hemisphere})` }} />
              <span className="text">{h.text}</span>
              <span className="ans num" title={h.answer ? `Jev's answer: ${h.answer.label} (${Math.round(h.answer.p * 100)}%)` : "Not answered yet"}>
                {h.answer ? <>{h.answer.label} <b>{Math.round(h.answer.p * 100)}%</b></> : ""}
              </span>
              <span className="where" title={where.map((p) => p.label).join(" / ")}>
                {pick && <span className="tagjev">Jev&apos;s pick</span>}
                {exact && i === 0 && <span className="tagjev">Exact</span>}
                {where.slice(-2).map((p) => p.label).join(" / ")}
                {rewordings > 0 && (
                  <span className="rew" title={(h.similar ?? []).filter((x) => !x.variant).map((x) => x.text).join("\n")}>
                    +{rewordings} rewording{rewordings === 1 ? "" : "s"}
                  </span>
                )}
                {variants > 0 && <span className="rew" title="The same question with other answer options">+{variants} with other options</span>}
                {h.agree === false && <span className="flip" title="Jev gives different answers to rewordings of this question">answers differ</span>}
              </span>
            </button>
            );
          })}
          <button className="askrow" onClick={ask}>
            <span>Ask Jev</span> &ldquo;{q.trim()}&rdquo;
          </button>
        </div>
      )}
    </div>
  );
}
