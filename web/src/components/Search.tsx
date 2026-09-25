"use client";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useStore } from "@/lib/store";
import { HEMI_COLOR } from "@/lib/layout";
import { feelingLucky, journey } from "@/lib/actions";
import type { NodeHit, SearchHit } from "@/lib/types";

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
  const showJevPath = useStore((s) => s.showJevPath);
  const walk = useStore((s) => s.jevWalk);
  const nodes = useStore((s) => s.nodes);
  const seq = useRef(0);
  const rerankTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
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
      setHits((cur) =>
        [...cur].map((h) => ({ ...h, jev_p: p.get(h.id) ?? null })).sort((a, b) => (b.jev_p ?? -1) - (a.jev_p ?? -1) || b.score - a.score),
      );
      setRerank({ state: "done", ms: performance.now() - t0, cached: d.cached });
    } catch (e) {
      if (my === seq.current) setRerank({ state: "error", error: (e as Error).message });
    }
  }

  // Instant results: local embedding + pgvector + trigram on every keystroke.
  useEffect(() => {
    const text = q.trim();
    const my = ++seq.current;
    if (rerankTimer.current) clearTimeout(rerankTimer.current);
    if (!text) return;
    const ctl = new AbortController();
    const t0 = performance.now();
    fetch(`/api/search?q=${encodeURIComponent(text)}${showHidden ? "&hidden=1" : ""}`, { signal: ctl.signal })
      .then((r) => r.json())
      .then((d: { results: SearchHit[]; nodes: NodeHit[] }) => {
        if (my !== seq.current) return;
        setLatency(performance.now() - t0);
        setHits(d.results);
        setNodeHits(d.nodes.slice(0, 3));
        setActive(0);
        setOpen(true);
        setRerank({ state: "idle" });
        // Jev refines once typing pauses: one Choice over the top 20.
        rerankTimer.current = setTimeout(() => runRerank(text, d.results, my), 450);
      })
      .catch(() => {});
    return () => ctl.abort();
  }, [q, showHidden]);

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

  async function choose(h: SearchHit) {
    setOpen(false);
    const rel: Record<string, number> = {};
    const top = hits[0]?.score || 1;
    for (const r of hits) for (const p of r.path) rel[p.id] = Math.max(rel[p.id] ?? 0, Math.max(0, r.score / top) * 0.8);
    useStore.getState().set({ relevance: rel, panel: { kind: "none" } });
    await journey({ query: q.trim(), path: h.path.map((p) => p.id), questionId: h.id });
  }

  async function chooseNode(n: NodeHit) {
    setOpen(false);
    useStore.getState().set({ relevance: {} });
    await journey({ query: q.trim(), path: n.path.map((p) => p.id) });
  }

  function ask() {
    setOpen(false);
    useStore.getState().set({ panel: { kind: "ask", text: q.trim() } });
  }

  async function lucky() {
    setOpen(false);
    useStore.getState().set({ relevance: {} });
    await feelingLucky();
  }

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(a + 1, hits.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
    else if (e.key === "Enter" && hits[active]) { e.preventDefault(); choose(hits[active]); }
    else if (e.key === "Enter" && q.trim()) { e.preventDefault(); ask(); }
    else if (e.key === "Escape") setOpen(false);
  };

  const label = (id: string) => nodes[id]?.label ?? id.split(".").pop();
  const agrees = walk.node && walk.node === walk.target;

  return (
    <div className="search">
      <div className="search-field" data-title="Search.Questions 1.1">
        <input
          data-testid="search"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            if (!e.target.value.trim()) { setHits([]); setNodeHits([]); setLatency(null); setRerank({ state: "idle" }); }
          }}
          onFocus={() => hits.length && setOpen(true)}
          onKeyDown={onKey}
          placeholder="Search or ask, like best pizza topping"
          aria-label="Search questions or ask Jev"
          role="combobox"
          aria-expanded={open}
          aria-controls="search-results"
        />
        {latency !== null && q.trim() && <span className="search-meta num" data-testid="latency">{Math.round(latency)} ms</span>}
        <button className="lucky" onClick={lucky} title="Fly to a random question">
          I&apos;m feeling lucky
        </button>
      </div>
      {open && q.trim() && (
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
              <span className="dot" style={{ background: HEMI_COLOR[h.hemisphere] }} />
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
              <span className="dot" style={{ background: HEMI_COLOR[n.hemisphere] }} />
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
      {!open && walk.state !== "idle" && showJevPath && (
        <div className="walkcard" data-testid="walkcard" data-title="Jev.Walk">
          <p className="walk-body">
            {walk.state === "walking" && <>Jev is walking the tree for &ldquo;{walk.query}&rdquo;, one decision per level.</>}
            {walk.state === "error" && <>Jev&apos;s walk is unavailable ({walk.error}), so the tree path runs alone.</>}
            {walk.state === "done" && walk.node && (
              <>
                <span className="gold">Jev</span> filed it under <b>{label(walk.node)}</b>{" "}
                <span className="num">({Math.round((walk.confidence ?? 0) * 100)}% path confidence)</span>.{" "}
                {agrees ? "The question you picked lives there too." : <>The question you picked lives under <b>{label(walk.target!)}</b>; the ink hop shows where the paths part.</>}
              </>
            )}
          </p>
        </div>
      )}
    </div>
  );
}
