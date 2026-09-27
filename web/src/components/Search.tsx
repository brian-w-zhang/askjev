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


interface Rerank { state: "idle" | "waiting" | "done" | "error"; ms?: number; cached?: boolean; error?: string }

export function Search() {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [nodeHits, setNodeHits] = useState<NodeHit[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [latency, setLatency] = useState<number | null>(null);
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
      setRerank({ state: "done", ms: performance.now() - t0, cached: d.cached });
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
    const t0 = performance.now();
    const show = (d: Found) => {
      if (my !== seq.current) return;
      setLatency(performance.now() - t0);
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
    setLatency(null);
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


  return (
    <div className="search">
      <div className="finder">
        <div className="finder-title">
          <span className="brand">askjev</span>
          <span className="count num">{ready ? `${(starData()?.count ?? 0).toLocaleString()} questions` : "Loading questions"}</span>
          <button
            className="themebtn"
            onClick={() => useStore.getState().set({ theme: theme === "light" ? "dark" : "light" })}
            aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
            title={theme === "light" ? "Dark mode" : "Light mode"}
          >
            <span aria-hidden>{theme === "light" ? "☾" : "☀"}</span>
            {theme === "light" ? "Dark" : "Light"}
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
        {latency !== null && q.trim() && <span className="search-meta num" data-testid="latency">{Math.round(latency)} ms</span>}
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
            <span className="num">{hits.length} match{hits.length === 1 ? "" : "es"}</span>
            <span className={rerank.state === "done" ? "jev" : ""}>
              {rerank.state === "waiting" && "Jev is reordering"}
              {rerank.state === "done" && `Reordered by Jev in ${((rerank.ms ?? 0) / 1000).toFixed(2)} s${rerank.cached ? " (cached)" : ""}`}
              {rerank.state === "error" && "Jev reorder unavailable"}
            </span>
          </div>
          {hits.length === 0 && <div className="empty">No questions match yet. Try fewer words, or ask it below.</div>}
          {hits.map((h, i) => (
            <button
              key={h.id}
              data-hit={h.id}
              className="result"
              role="option"
              aria-selected={i === active}
              onMouseEnter={() => setActive(i)}
              onClick={() => choose(h)}
            >
              <span className="dot" style={{ background: `var(--${h.hemisphere})` }} />
              <span className="text">{h.text}</span>
              <span className="p num">
                {h.jev_p != null && (
                  <>
                    {Math.round(h.jev_p * 100)}%
                    <span className="pbar"><i style={{ ["--p" as string]: `${h.jev_p * 100}%` }} /></span>
                  </>
                )}
              </span>
              <span className="where">{h.path.slice(1).map((p) => p.label).join(" / ")}</span>
            </button>
          ))}
          {nodeHits.length > 0 && <h3>Topics</h3>}
          {nodeHits.map((n) => (
            <button key={n.id} className="result" onClick={() => chooseNode(n)}>
              <span className="dot" style={{ background: `var(--${n.hemisphere})` }} />
              <span className="text">{n.label}</span>
              <span className="p" />
              <span className="where">{n.path.slice(1, -1).map((p) => p.label).join(" / ") || "Hemisphere"}</span>
            </button>
          ))}
          <button className="askrow" onClick={ask}>
            <span>Ask Jev</span> &ldquo;{q.trim()}&rdquo;
          </button>
        </div>
      )}
    </div>
  );
}
