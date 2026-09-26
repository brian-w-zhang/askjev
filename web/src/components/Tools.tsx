"use client";
import { useEffect } from "react";
import { useStore, type ToolId } from "@/lib/store";
import { INDICATORS, RAMP_CSS } from "@/lib/color";
import { LAYOUTS, LAYOUT_KEY, type LayoutKind } from "@/lib/layout";
import { refreshFilters } from "@/lib/actions";

// The search window's tools row (docs/07-ui.md, Search), like the row under a search engine's box: each tab
// names its current setting and opens a panel right under the box. Keys 1-6 switch layouts.
const KINDS = ["factual", "taste", "evaluative", "personality", "values", "social", "forecast", "perception", "detect", "classify", "extract", "compare", "rate"];
const ORIGINS = ["dataset", "template", "wikidata-fact", "typesafe-docs", "synthetic", "mined", "asked"];

/** Switch layout and remember it, only when someone actually picks one (so a new default still reaches them). */
function pickLayout(id: LayoutKind) {
  useStore.getState().set({ layout: id });
  try { localStorage.setItem(LAYOUT_KEY, id); } catch {}
}

export function ToolTabs({ onLucky }: { onLucky: () => void }) {
  const tool = useStore((s) => s.tool);
  const layout = useStore((s) => s.layout);
  const indicator = useStore((s) => s.indicator);
  const filters = useStore((s) => s.filters);
  const showHidden = useStore((s) => s.showHidden);
  const nFilters = [filters.kind, filters.primitive, filters.origin].filter(Boolean).length + (showHidden ? 1 : 0);
  const toggle = (t: ToolId) => useStore.getState().set({ tool: tool === t ? null : t });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (e.metaKey || e.ctrlKey || e.altKey || t?.closest("input, textarea, select, [contenteditable]")) return;
      const l = LAYOUTS[Number(e.key) - 1];
      if (l) pickLayout(l.id);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const tab = (t: ToolId, name: string, value: string) => (
    <button className="tooltab" aria-expanded={tool === t} aria-controls="toolpanel" onClick={() => toggle(t)}>
      {name} <b>{value}</b> <span aria-hidden>{tool === t ? "▴" : "▾"}</span>
    </button>
  );
  return (
    <div className="tooltabs" role="toolbar" aria-label="View">
      {tab("layout", "Layout", LAYOUTS.find((l) => l.id === layout)?.label ?? "")}
      {tab("color", "Color", INDICATORS.find((i) => i.id === indicator)?.label ?? "")}
      {tab("filters", "Filters", nFilters ? String(nFilters) : "Off")}
      <button className="luckybtn" onClick={onLucky} title="Fly to a random question">
        Feeling lucky
      </button>
    </div>
  );
}

/** The open tool's panel, docked under the search window. */
export function ToolPanel() {
  const tool = useStore((s) => s.tool);
  const layout = useStore((s) => s.layout);
  const semanticReady = useStore((s) => !!s.semantic);
  const indicator = useStore((s) => s.indicator);
  const filters = useStore((s) => s.filters);
  const showHidden = useStore((s) => s.showHidden);
  const set = useStore((s) => s.set);

  useEffect(() => {
    refreshFilters();
  }, [filters, showHidden]);

  if (!tool) return null;
  const setFilter = (k: keyof typeof filters, v: string) => set({ filters: { ...filters, [k]: v } });
  const title = tool === "layout" ? "Layout.Tool" : tool === "color" ? "Color.Tool" : "Filter.Tool";

  return (
    <div className="toolpanel" id="toolpanel" data-title={`${title} 1.1`}>
      {tool === "layout" && (
        <>
          <div className="segline" role="radiogroup" aria-label="Layout">
            {LAYOUTS.map((l, i) => (
              <button key={l.id} role="radio" aria-checked={layout === l.id} onClick={() => pickLayout(l.id)} title={`${l.hint} (key ${i + 1})`}>
                {l.label}
              </button>
            ))}
          </div>
          <p className="hint">
            {layout === "semantic" && !semanticReady ? "Placing topics by meaning…" : `${LAYOUTS.find((l) => l.id === layout)?.hint}.`}
            <span className="keys"> Keys 1–6.</span>
          </p>
        </>
      )}
      {tool === "color" && (
        <>
          <div className="seg" role="group" aria-label="Color by indicator">
            {INDICATORS.map((i) => (
              <button key={i.id} aria-pressed={indicator === i.id} onClick={() => set({ indicator: i.id })} title={i.hint}>
                {i.label}
              </button>
            ))}
          </div>
          {indicator === "hemisphere" ? (
            <div className="hemis">
              <span style={{ background: "var(--world)" }}>World</span>
              <span style={{ background: "var(--self)" }}>Self</span>
              <span style={{ background: "var(--machine)" }}>Machine</span>
            </div>
          ) : (
            <>
              <div className="ramp" style={{ background: RAMP_CSS }} />
              <div className="ramp-ends"><span>Steady</span><span>Worth a look</span></div>
            </>
          )}
          <p className="hint">{INDICATORS.find((i) => i.id === indicator)?.hint}.{indicator !== "hemisphere" && " Faint stars have no data yet."}</p>
        </>
      )}
      {tool === "filters" && (
        <>
          <div className="filters">
            <select aria-label="Kind or shape" value={filters.kind} onChange={(e) => setFilter("kind", e.target.value)}>
              <option value="">Any kind</option>
              {KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
            <select aria-label="Primitive" value={filters.primitive} onChange={(e) => setFilter("primitive", e.target.value)}>
              <option value="">Any type</option>
              <option value="noul">Noul</option>
              <option value="choice">Choice</option>
              <option value="score">Score</option>
            </select>
            <select aria-label="Origin" value={filters.origin} onChange={(e) => setFilter("origin", e.target.value)}>
              <option value="">Any origin</option>
              {ORIGINS.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
          <div className="toggles">
            <div className="toggle">
              <span>Show hidden questions (dev)</span>
              <button className="switch" role="switch" aria-checked={showHidden} aria-label="Show hidden questions" onClick={() => set({ showHidden: !showHidden })} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/** A small legend while the sky is colored by an indicator, so the colors stay readable with the tools shut. */
export function Legend() {
  const indicator = useStore((s) => s.indicator);
  if (indicator === "hemisphere") return null;
  return (
    <div className="legend" aria-hidden>
      <span>Steady</span>
      <i style={{ background: RAMP_CSS }} />
      <span>Worth a look</span>
    </div>
  );
}
