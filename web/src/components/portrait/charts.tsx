import type { ReactNode } from "react";

// Plain HTML/SVG charts. Row charts are HTML so their labels stay legible at phone width.

type Mark = { v: number; kind: "jev" | "guess" | "hum" | "tick"; title?: string };
export type DotRow = {
  key: string; label: ReactNode; sub?: ReactNode; marks: Mark[]; ci?: [number, number]; ciP?: [number, number];
  value?: ReactNode; hi?: boolean; link?: boolean;
};

export function DotRows({ rows, domain, ticks, refs = [], band, fmt = (x) => String(x) }: {
  rows: DotRow[]; domain: [number, number]; ticks: number[]; refs?: { v: number; zero?: boolean }[];
  band?: [number, number]; fmt?: (x: number) => string;
}) {
  const x = (v: number) => `${((Math.min(Math.max(v, domain[0]), domain[1]) - domain[0]) / (domain[1] - domain[0])) * 100}%`;
  const w = (a: number, b: number) => `${((Math.min(b, domain[1]) - Math.max(a, domain[0])) / (domain[1] - domain[0])) * 100}%`;
  const track = (children: ReactNode) => (
    <div className="dp-t">
      {band && <i className="band" style={{ left: x(band[0]), width: w(band[0], band[1]) }} />}
      {refs.map((r) => <i key={r.v} className={`ref${r.zero ? " zero" : ""}`} style={{ left: x(r.v) }} />)}
      {children}
    </div>
  );
  return (
    <div className="dp">
      <div className="dp-axis">
        <span />
        <div className="dp-t">
          {ticks.map((t, i) => (
            <span key={t} className={`tk${i === 0 && t === domain[0] ? " l" : ""}${i === ticks.length - 1 && t === domain[1] ? " r" : ""}${ticks.length > 4 && i % 2 === 1 ? " minor" : ""}`} style={{ left: x(t) }}>{fmt(t)}</span>
          ))}
        </div>
        <span />
      </div>
      {rows.map((r) => {
        const vs = r.marks.filter((m) => m.kind !== "tick").map((m) => m.v);
        return (
          <div key={r.key} className={`dp-row${r.hi ? " hi" : ""}`}>
            <span className="dp-l">{r.label}{r.sub && <small>{r.sub}</small>}</span>
            {track(<>
              {r.link && vs.length > 1 && <i className="link" style={{ left: x(Math.min(...vs)), width: w(Math.min(...vs), Math.max(...vs)) }} />}
              {r.ciP && <i className="ci p" style={{ left: x(r.ciP[0]), width: w(r.ciP[0], r.ciP[1]) }} />}
              {r.ci && <i className="ci" style={{ left: x(r.ci[0]), width: w(r.ci[0], r.ci[1]) }} />}
              {r.marks.map((m, i) => <i key={i} className={`m ${m.kind}`} style={{ left: x(m.v) }} title={m.title} />)}
            </>)}
            <span className="dp-v">{r.value}</span>
          </div>
        );
      })}
    </div>
  );
}

export function HBars({ rows, max = 1, fmt }: {
  rows: { key: string; label: ReactNode; v: number; jev?: boolean }[]; max?: number; fmt: (v: number) => string;
}) {
  return (
    <div className="hbars">
      {rows.map((r) => (
        <div className="hbar" key={r.key}>
          <span className="l">{r.label}</span>
          <span className="t"><i className={r.jev ? "j" : ""} style={{ width: `${(r.v / max) * 100}%` }} /></span>
          <span className="v">{fmt(r.v)}</span>
        </div>
      ))}
    </div>
  );
}

// 100% stacked bars; parts carry a class for their fill (c0..c8, hatch)
export function StackBars({ rows }: {
  rows: { key: string; label: ReactNode; sub?: ReactNode; parts: { key: string; v: number; cls: string; text?: string }[] }[];
}) {
  return (
    <div className="sb">
      {rows.map((r) => {
        const tot = r.parts.reduce((s, p) => s + p.v, 0) || 1;
        return (
          <div className="sb-row" key={r.key}>
            <span className="sb-l">{r.label}{r.sub && <small>{r.sub}</small>}</span>
            <span className="sb-bar">
              {r.parts.map((p) => (
                <span key={p.key} className={p.cls} style={{ width: `${(p.v / tot) * 100}%` }} title={`${p.key}: ${Math.round((p.v / tot) * 100)}%`}>
                  {p.v / tot >= 0.09 ? p.text ?? `${Math.round((p.v / tot) * 100)}%` : ""}
                </span>
              ))}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// SVG scatter on the unit square (or given domains)
export function Scatter({ points, xLabel, yLabel, diag = true, size = 2.2, highlight = [], xDomain = [0, 1], yDomain = [0, 1], bands = [], ticks = [0, 0.25, 0.5, 0.75, 1], yTicks = ticks, fmt }: {
  points: [number, number][]; xLabel: string; yLabel: string; diag?: boolean; size?: number;
  highlight?: { x: number; y: number; label: string; anchor?: "start" | "end" }[];
  xDomain?: [number, number]; yDomain?: [number, number]; bands?: { x0: number; x1: number; label?: string }[];
  ticks?: number[]; yTicks?: number[]; fmt: (v: number) => string;
}) {
  const W = 420, H = 320, L = 40, R = 12, T = 12, B = 36;
  const sx = (v: number) => L + ((v - xDomain[0]) / (xDomain[1] - xDomain[0])) * (W - L - R);
  const sy = (v: number) => H - B - ((v - yDomain[0]) / (yDomain[1] - yDomain[0])) * (H - T - B);
  return (
    <svg className="svgc" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${yLabel} against ${xLabel}`}>
      {bands.map((b, i) => <rect key={i} className="band" x={sx(b.x0)} y={T} width={sx(b.x1) - sx(b.x0)} height={H - T - B} />)}
      {yTicks.map((t) => (
        <g key={`y${t}`}>
          <line className="grid" x1={sx(xDomain[0])} x2={sx(xDomain[1])} y1={sy(t)} y2={sy(t)} />
          <text x={L - 6} y={sy(t) + 3} textAnchor="end">{fmt(t)}</text>
        </g>
      ))}
      {ticks.map((t) => (
        <g key={`x${t}`}>
          <line className="grid" x1={sx(t)} x2={sx(t)} y1={sy(yDomain[0])} y2={sy(yDomain[1])} />
          <text x={sx(t)} y={H - B + 14} textAnchor="middle">{fmt(t)}</text>
        </g>
      ))}
      {diag && <line className="diag" x1={sx(xDomain[0])} y1={sy(yDomain[0])} x2={sx(xDomain[1])} y2={sy(yDomain[1])} />}
      {points.map(([x, y], i) => <circle key={i} className="pt-dot" cx={sx(x)} cy={sy(y)} r={size} />)}
      {highlight.map((h) => (
        <g key={h.label}>
          <circle className="jev" cx={sx(h.x)} cy={sy(h.y)} r={4.5} />
          <text className="lab" x={sx(h.x) + (h.anchor === "end" ? -8 : 8)} y={sy(h.y) + 4} textAnchor={h.anchor ?? "start"}>{h.label}</text>
        </g>
      ))}
      <text x={(L + W - R) / 2} y={H - 4} textAnchor="middle">{xLabel}</text>
      <text transform={`translate(10 ${(T + H - B) / 2}) rotate(-90)`} textAnchor="middle">{yLabel}</text>
    </svg>
  );
}

export function Units({ groups, per }: { groups: { key: string; n: number; cls: string }[]; per: number }) {
  const cells: { cls: string; key: string }[] = [];
  for (const g of groups) for (let i = 0; i < Math.round(g.n / per); i++) cells.push({ cls: g.cls, key: `${g.key}${i}` });
  return (
    <div className="units" role="img" aria-label={`One square per ${per.toLocaleString("en-US")} questions`}>
      {cells.map((c) => <i key={c.key} className={c.cls} />)}
    </div>
  );
}
