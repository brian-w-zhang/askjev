"use client";
import { useEffect, useState } from "react";
import { useStore } from "@/lib/store";
import { INDICATORS, RAMP_CSS } from "@/lib/color";
import { refreshFilters } from "@/lib/actions";

const KINDS = ["factual", "taste", "evaluative", "personality", "values", "social", "forecast", "perception", "detect", "classify", "extract", "compare", "rate"];
const ORIGINS = ["dataset", "template", "wikidata-fact", "typesafe-docs", "synthetic", "mined", "asked"];

export function Controls() {
  const indicator = useStore((s) => s.indicator);
  const filters = useStore((s) => s.filters);
  const showJevPath = useStore((s) => s.showJevPath);
  const showHidden = useStore((s) => s.showHidden);
  const set = useStore((s) => s.set);
  const [collapsed, setCollapsed] = useState(true);
  const hint = INDICATORS.find((i) => i.id === indicator)?.hint;

  useEffect(() => {
    refreshFilters();
  }, [filters, showHidden]);

  const setFilter = (k: keyof typeof filters, v: string) => set({ filters: { ...filters, [k]: v } });

  return (
    <div className="controls" data-collapsed={collapsed} data-title="Color.Tool 1.1">
      <button className="controls-collapse iconbtn" style={{ width: "100%", marginBottom: collapsed ? 0 : 8 }} onClick={() => setCollapsed(!collapsed)}>
        {collapsed ? "Color and filters" : "Hide"}
      </button>
      <div className="controls-inner">
        <h2>Color the sky by</h2>
        <div className="seg" role="group" aria-label="Color by indicator">
          {INDICATORS.map((i) => (
            <button key={i.id} aria-pressed={indicator === i.id} onClick={() => set({ indicator: i.id })} title={i.hint}>
              {i.label}
            </button>
          ))}
        </div>
        {indicator === "hemisphere" ? (
          <div className="hemis">
            <span style={{ color: "var(--world)" }}>World</span>
            <span style={{ color: "var(--self)" }}>Self</span>
            <span style={{ color: "var(--machine)" }}>Machine</span>
          </div>
        ) : (
          <>
            <div className="ramp" style={{ background: RAMP_CSS }} />
            <div className="ramp-ends"><span>Steady</span><span>Worth a look</span></div>
            <p className="hint">{hint}. Dark stars have no data yet.</p>
          </>
        )}
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
            <span>Show Jev&apos;s path</span>
            <button className="switch" role="switch" aria-checked={showJevPath} aria-label="Show Jev's path" onClick={() => set({ showJevPath: !showJevPath })} />
          </div>
          <div className="toggle">
            <span>Show hidden questions (dev)</span>
            <button className="switch" role="switch" aria-checked={showHidden} aria-label="Show hidden questions" onClick={() => set({ showHidden: !showHidden })} />
          </div>
        </div>
      </div>
    </div>
  );
}
