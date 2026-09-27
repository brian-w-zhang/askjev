"use client";

import { useState } from "react";

// Feltron-style ranked lists, one tab per domain.
export type FavDomain = { key: string; label: string; pairs: number; rho: number | null; items: string[] };

export default function Favorites({ domains }: { domains: FavDomain[] }) {
  const [on, setOn] = useState(domains[0]?.key);
  const d = domains.find((x) => x.key === on) ?? domains[0];
  return (
    <div>
      <div className="tabs" role="tablist">
        {domains.map((x) => (
          <button key={x.key} type="button" role="tab" aria-selected={x.key === d.key} onClick={() => setOn(x.key)}>{x.label}</button>
        ))}
      </div>
      <ol className="rank" role="tabpanel">
        {d.items.map((it) => <li key={it}><b>{it}</b><span /></li>)}
      </ol>
      <p style={{ margin: "10px 0 0", fontFamily: "var(--mono)", fontSize: 10.5, color: "var(--w-fg-2)" }}>
        Bradley–Terry strengths from {d.pairs.toLocaleString("en-US")} head-to-heads
        {d.rho !== null ? ` · rank agreement with people's own head-to-heads ρ = ${d.rho.toFixed(2)}` : ""}
      </p>
    </div>
  );
}
