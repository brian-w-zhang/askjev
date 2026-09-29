"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

const pc = (v: number) => `${Math.round(v * 100)}%`;

// Marks its box data-in once it scrolls into view, so CSS can play the chapter's entrance (bars fill, dots slide).
// The portrait scrolls inside .pt, not the window.
export function Reveal({ children, className = "", as: Tag = "div" }: { children: ReactNode; className?: string; as?: "div" | "section" }) {
  const ref = useRef<HTMLDivElement>(null);
  const [on, setOn] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!("IntersectionObserver" in window)) return; // no observer: the rv-on class never goes on, so nothing is hidden
    document.documentElement.classList.add("rv-on");
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setOn(true); io.disconnect(); } },
      { root: document.querySelector(".pt"), threshold: 0.2 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return <Tag ref={ref} className={`rv ${className}`} data-in={on ? "" : undefined}>{children}</Tag>;
}

// Four letter tiles; the toggle turns the ones that differ, from Jev's own answers to what it thinks most people are.
export function TypeFlip({ jev, people }: { jev: string; people: string }) {
  const [who, setWho] = useState<"jev" | "people">("jev");
  const word: Record<string, string> = { I: "introverted", E: "extraverted", S: "sensing", N: "intuitive", T: "thinking", F: "feeling", J: "judging", P: "perceiving" };
  const s = who === "jev" ? jev : people;
  return (
    <div className="tf">
      <div className="tf-tabs" role="tablist" aria-label="Whose type">
        <button role="tab" aria-selected={who === "jev"} onClick={() => setWho("jev")}>Jev, answering as itself</button>
        <button role="tab" aria-selected={who === "people"} onClick={() => setWho("people")}>Jev, answering for most people</button>
      </div>
      <div className="tf-tiles" aria-live="polite">
        {[...s].map((l, i) => (
          <span key={i} className={`tf-t${jev[i] !== people[i] ? " diff" : ""}`} data-who={who}>
            <b key={l}>{l}</b><small>{word[l]}</small>
          </span>
        ))}
      </div>
    </div>
  );
}

// A 0-100 ruler of probability words; the toggle slides each word from people's reading to Jev's.
export function ProbRuler({ rows }: { rows: { phrase: string; jev: number; people: number }[] }) {
  const [who, setWho] = useState<"jev" | "people">("jev");
  const sorted = [...rows].sort((a, b) => a.people - b.people);
  return (
    <div className="pr">
      <div className="tf-tabs" role="tablist" aria-label="Whose reading">
        <button role="tab" aria-selected={who === "jev"} onClick={() => setWho("jev")}>Jev</button>
        <button role="tab" aria-selected={who === "people"} onClick={() => setWho("people")}>people</button>
      </div>
      <div className="pr-track">
        {sorted.map((r, i) => {
          const v = who === "jev" ? r.jev : r.people;
          const moved = Math.abs(r.jev - r.people) >= 15;
          return (
            // words near either end grow inward, so none hangs off the ruler; six rows keep neighbors apart
            <span key={r.phrase} className={`pr-w${moved ? " moved" : ""}`}
              style={{ left: `${v}%`, top: `${(i % 6) * (100 / 6)}%`, transform: `translateX(${v < 15 ? -8 : v > 85 ? -92 : -50}%)` }}
              title={`${r.phrase}: Jev ${r.jev}%, people ${r.people}%`}>
              <i />{r.phrase.toLowerCase()} <em>{v}%</em>
            </span>
          );
        })}
      </div>
      <div className="pr-axis"><span>0%</span><span>50%</span><span>100%</span></div>
    </div>
  );
}

// The trolley: pick a dilemma, the trolley rolls, the two bars fill: how many say it's OK, Jev and people.
export function Trolley({ rows, peopleLabel }: { rows: { key: string; name: string; ask: string; jev: number; people: number }[]; peopleLabel: string }) {
  const [k, setK] = useState(0);
  const [run, setRun] = useState(0);
  const r = rows[k];
  const push = r.key === "Footbridge";
  const pathRef = useRef<SVGPathElement>(null);
  const carRef = useRef<SVGGElement>(null);
  // move the car along the track in the drawing's own units, easing in and out, each time a dilemma is picked
  useEffect(() => {
    const path = pathRef.current, car = carRef.current;
    if (!path || !car) return;
    const L = path.getTotalLength();
    const place = (t: number) => {
      const e = t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
      const a = path.getPointAtLength(e * L), b = path.getPointAtLength(Math.min(L, e * L + 1));
      const deg = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
      car.setAttribute("transform", `translate(${a.x.toFixed(1)} ${a.y.toFixed(1)}) rotate(${deg.toFixed(1)})`);
    };
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) { place(1); return; }
    let raf = 0;
    const t0 = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - t0) / 2200);
      place(t);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [k, run]);
  return (
    <div className="tr">
      <div className="tf-tabs" role="tablist" aria-label="Dilemma">
        {rows.map((x, i) => (
          <button key={x.key} role="tab" aria-selected={k === i} onClick={() => { setK(i); setRun((n) => n + 1); }}>{x.name}</button>
        ))}
      </div>
      <svg className="tr-scene" viewBox="0 0 400 150" role="img" aria-label={`${r.name}: ${r.ask}`} key={`${k}-${run}`}>
        {/* tracks: the main line splits at the lever; the footbridge crosses above */}
        <path className="rail" d="M0 110 L180 110 L400 110" />
        {!push && <path className="rail" d="M180 110 C 230 110, 250 60, 400 60" />}
        {push && <><rect className="bridge" x="230" y="36" width="90" height="8" /><circle className="man" cx="276" cy="24" r="7" /><rect className="man" x="271" y="30" width="10" height="7" /></>}
        {/* five people on the main line, one on the side line (or under the bridge) */}
        {[0, 1, 2, 3, 4].map((i) => <circle key={i} className="who" cx={336 + i * 12} cy={100} r="5" />)}
        {!push && <circle className="who one" cx={372} cy={50} r="5" />}
        <text className="lbl" x="360" y="92">five people</text>
        {!push && <text className="lbl" x="372" y="40">one</text>}
        {push && <text className="lbl" x="276" y="12">the large man</text>}
        {/* the trolley rolls in; with the lever pulled it takes the branch, at the footbridge it stops short */}
        <path ref={pathRef} d={push ? "M0 108 L250 108" : "M0 108 L180 108 C 230 108, 250 58, 330 58"} fill="none" stroke="none" />
        <g className="trolley" ref={carRef} transform="translate(0 108)">
          <rect x="-34" y="-20" width="34" height="18" rx="2" /><circle cx="-26" cy="0" r="4" /><circle cx="-8" cy="0" r="4" />
        </g>
        {!push && (
          <line className="lever" x1="180" y1="122" x2="180" y2="142">
            <animateTransform attributeName="transform" type="rotate" from="0 180 122" to="-40 180 122" begin="0.9s" dur="0.3s" fill="freeze" />
          </line>
        )}
      </svg>
      <p className="tr-q">{r.ask}</p>
      <div className="tr-bars">
        <div><span>Jev</span><i className="j" style={{ width: pc(r.jev) }} /><b>{pc(r.jev)}</b></div>
        <div><span>{peopleLabel}</span><i className="p" style={{ width: pc(r.people) }} /><b>{pc(r.people)}</b></div>
      </div>
    </div>
  );
}

// A chat where a user claims a crowd; Jev's probability for the named option climbs when the card comes into view.
export function PressureChat({ shift, label, claim }: { shift: number; label: string; claim: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [on, setOn] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setOn(true); io.disconnect(); } },
      { root: document.querySelector(".pt"), threshold: 0.5 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <div className="pc" ref={ref} data-in={on ? "" : undefined}>
      <p className="pc-u">{claim}</p>
      <div className="pc-j">
        <span>{label}</span>
        {/* how far Jev's probability moved toward the claimed side, out of 100 points */}
        <div className="pc-bar"><i style={{ width: on ? pc(shift) : "0%" }} /></div>
        <b>{on ? `+${Math.round(shift * 100)} points` : "…"}</b>
      </div>
    </div>
  );
}
