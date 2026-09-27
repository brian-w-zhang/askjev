"use client";

import { useRef, useState } from "react";

// Draw-first reliability diagram: the reader guesses how often Jev is right at each confidence level, then reveals
// the real rates (dots sized by the number of questions, as in FiveThirtyEight's "Checking Our Work").
type Bin = { lo: number; hi: number; n: number; acc: number };

const W = 420, H = 330, L = 42, R = 14, T = 14, B = 40;
const X0 = 0.3, X1 = 1, Y0 = 0.2, Y1 = 1;
const sx = (v: number) => L + ((v - X0) / (X1 - X0)) * (W - L - R);
const sy = (v: number) => H - B - ((v - Y0) / (Y1 - Y0)) * (H - T - B);
const iy = (py: number) => Y0 + ((H - B - py) / (H - T - B)) * (Y1 - Y0);
const TICKS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1];

export default function Calibration({ bins }: { bins: Bin[] }) {
  const guessBins = bins.filter((b) => b.lo >= 0.5);
  const [guess, setGuess] = useState<Record<number, number>>({});
  const [shown, setShown] = useState(false);
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<number | null>(null);
  const maxN = Math.max(...bins.map((b) => b.n));

  const setFrom = (e: React.PointerEvent, lo: number) => {
    const r = svg.current!.getBoundingClientRect();
    const py = ((e.clientY - r.top) / r.height) * H;
    setGuess((g) => ({ ...g, [lo]: Math.min(Y1, Math.max(Y0, iy(py))) }));
  };
  const count = Object.keys(guess).length;

  return (
    <div>
      <p style={{ margin: "0 0 10px", fontSize: 15 }}>
        {shown ? "Your guesses are the rings; Jev's real rates are the dots." :
          <>Your guess first: drag in each column. When Jev is this sure, how often is it right? <span style={{ color: "var(--w-fg-2)" }}>({count}/{guessBins.length} guessed)</span></>}
      </p>
      <svg ref={svg} className="svgc" viewBox={`0 0 ${W} ${H}`} style={{ touchAction: shown ? "auto" : "none" }}
        role="img" aria-label="Reliability diagram: Jev's confidence against how often it is right"
        onPointerMove={(e) => { if (drag.current !== null && !shown) setFrom(e, drag.current); }}
        onPointerUp={() => { drag.current = null; }} onPointerLeave={() => { drag.current = null; }}>
        {TICKS.map((t) => (
          <g key={t}>
            <line className="grid" x1={sx(X0)} x2={sx(X1)} y1={sy(Math.max(t, Y0))} y2={sy(Math.max(t, Y0))} />
            <line className="grid" x1={sx(t)} x2={sx(t)} y1={sy(Y0)} y2={sy(Y1)} />
            <text x={sx(t)} y={H - B + 14} textAnchor="middle">{Math.round(t * 100)}%</text>
            {t >= Y0 && <text x={L - 6} y={sy(t) + 3} textAnchor="end">{Math.round(t * 100)}%</text>}
          </g>
        ))}
        <line className="diag" x1={sx(X0)} y1={sy(X0)} x2={sx(X1)} y2={sy(X1)} />
        <text x={sx(0.86)} y={sy(0.86) - 8} textAnchor="end" style={{ fontSize: 9.5 }}>perfectly calibrated</text>
        {guessBins.map((b) => (
          <g key={b.lo}>
            {!shown && (
              <rect x={sx(b.lo) + 2} width={sx(b.hi) - sx(b.lo) - 4} y={sy(Y1)} height={sy(Y0) - sy(Y1)} fill="var(--jev-soft)" fillOpacity={guess[b.lo] === undefined ? 0.6 : 0.25}
                style={{ cursor: "ns-resize" }}
                onPointerDown={(e) => { drag.current = b.lo; (e.target as Element).setPointerCapture?.(e.pointerId); setFrom(e, b.lo); }} />
            )}
            {guess[b.lo] !== undefined && (
              <circle cx={(sx(b.lo) + sx(b.hi)) / 2} cy={sy(guess[b.lo])} r={7} className="jevs" strokeWidth={2} pointerEvents="none" />
            )}
          </g>
        ))}
        {shown && bins.map((b) => (
          <g key={b.lo}>
            <circle cx={(sx(b.lo) + sx(b.hi)) / 2} cy={sy(b.acc)} r={3 + 13 * Math.sqrt(b.n / maxN)} className="jev" fillOpacity={0.85} />
            <text className="lab" x={(sx(b.lo) + sx(b.hi)) / 2} y={sy(b.acc) + 20 + 11 * Math.sqrt(b.n / maxN)} textAnchor="middle">{Math.round(b.acc * 100)}%</text>
          </g>
        ))}
        <text x={(L + W - R) / 2} y={H - 6} textAnchor="middle">how sure Jev is</text>
        <text transform={`translate(10 ${(T + H - B) / 2}) rotate(-90)`} textAnchor="middle">how often it is right</text>
      </svg>
      <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
        {!shown ? (
          <>
            <button type="button" className="pt-btn" onClick={() => setShown(true)}>{count ? "Reveal Jev" : "Skip, just show me"}</button>
          </>
        ) : (
          <button type="button" className="pt-btn ghost" onClick={() => { setShown(false); setGuess({}); }}>Guess again</button>
        )}
      </div>
    </div>
  );
}
